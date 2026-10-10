"""Detached, identity-checked observer for peer-cli close and finish (Python 3.9+)."""
import argparse
import os
import time
from pathlib import Path
import session_close


def arguments():
    parser = argparse.ArgumentParser()
    values = (
        ("host-pid", int, True), ("host-start", float, True),
        ("worktree", str, True), ("result", str, True),
        ("session-id", str, True), ("invocation-id", str, True),
        ("parent-pid", int, False), ("parent-start", float, False),
        ("head", str, False), ("primary", str, False),
        ("branch", str, False), ("default", str, False),
        ("spawn-timeout", float, False), ("armed-timeout", float, False),
        ("accept-timeout", float, False), ("reaper-timeout", float, False),
        ("state-directory", str, False), ("host-names", str, False),
    )
    for name, kind, required in values:
        parser.add_argument("--" + name, type=kind, required=required)
    return parser.parse_args()


def bounded_timeout(value, name):
    if value is None:
        return session_close.bounded_timeout(name)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return session_close.DEFAULT_TIMEOUTS[name]
    if (not session_close.math.isfinite(parsed) or parsed <= 0
            or parsed > session_close.MAX_TIMEOUTS[name]):
        return session_close.DEFAULT_TIMEOUTS[name]
    return parsed


def result(path, status, **extra):
    value = session_close.read_json(path) or {}
    value.update({"status": status, "finished": session_close.now()})
    value.update(extra)
    session_close.write_json(path, value)


def await_acceptance(path, observer, expected, timeout):
    end = session_close.now() + timeout
    while session_close.now() < end:
        if Path(str(path) + ".cancelled").exists():
            return False
        value = session_close.read_json(str(path) + ".accepted")
        if value and session_close.valid_acknowledgement(value, expected, observer):
            session_close.write_json(
                str(path) + ".armed",
                {**expected, "armed": session_close.now(),
                 "reaper_pid": observer["reaper_pid"],
                 "reaper_started_at": observer["reaper_started_at"],
                 "observer_pid": observer["reaper_pid"],
                 "observer_started_at": observer["reaper_started_at"]},
            )
            return True
        time.sleep(.05)
    return False


def await_exit(args):
    end = session_close.now() + bounded_timeout(args.reaper_timeout, "AGENT_FINISH_REAPER_TIMEOUT_SECONDS")
    watched = [(args.host_pid, args.host_start)]
    if os.name == "nt" and args.parent_pid and args.parent_start:
        watched.append((args.parent_pid, args.parent_start))
    while session_close.now() < end:
        if Path(str(args.result) + ".cancelled").exists():
            return False
        if all(session_close.verified_exited(pid, started) for pid, started in watched):
            return True
        time.sleep(.25)
    return False


def registered(worktree, primary):
    code, output, _ = session_close.git(primary, "worktree", "list", "--porcelain")
    return code != 0 or any(line.startswith("worktree ") and session_close.path_key(line[9:]) == session_close.path_key(worktree) for line in output.splitlines())


def branch_checked_out(primary, branch):
    try:
        records = session_close.worktree_registrations(primary)
    except session_close.Refusal:
        return True
    return any(record["branch"] == "refs/heads/" + branch for record in records)


def final_preflight(args):
    worktree = Path(args.worktree)
    receipt = session_close.fresh_removable_receipt(worktree)
    if any(receipt.get(key) != getattr(args, key) for key in ("head", "primary", "branch", "default")):
        raise session_close.Refusal("cleanup receipt no longer matches the accepted cleanup target")
    if session_close.other_live_claimant(worktree, args.session_id):
        raise session_close.Refusal("another verified live session claims this worktree")
    code, dirty, _ = session_close.git(worktree, "status", "--porcelain")
    if code or dirty:
        raise session_close.Refusal("worktree is no longer clean")


def remove_worktree_and_branch(args):
    # This is intentionally the final action before each irreversible operation, not an earlier hint.
    if Path(str(args.result) + ".cancelled").exists():
        return "cancelled", {"error": "cleanup observer was cancelled"}
    final_preflight(args)
    worktree, primary = Path(args.worktree), Path(args.primary)
    if Path(str(args.result) + ".cancelled").exists():
        return "cancelled", {"error": "cleanup observer was cancelled"}
    code, _out, error = session_close.git(primary, "worktree", "remove", "--", str(worktree))
    if code and (worktree.exists() or registered(worktree, primary)):
        return "failed", {"error": "git worktree remove failed: " + error}
    code, branch_head, _ = session_close.git(primary, "rev-parse", "--verify", "--quiet", "refs/heads/" + args.branch)
    preserved = code != 0 or branch_head != args.head
    if not preserved and branch_checked_out(primary, args.branch):
        preserved = True
    if not preserved:
        # The branch may have moved or become checked out after removal.
        code, latest, _ = session_close.git(primary, "rev-parse", "--verify", "--quiet", "refs/heads/" + args.branch)
        if code != 0 or latest != args.head:
            preserved = True
        else:
            if Path(str(args.result) + ".cancelled").exists():
                return "cancelled", {"error": "cleanup observer was cancelled"}
            if branch_checked_out(primary, args.branch):
                preserved = True
            else:
                code, _out, error = session_close.git(
                    primary, "update-ref", "-d", "refs/heads/" + args.branch, args.head,
                )
                if code:
                    return "failed", {"error": "git branch deletion failed: " + error}
    if worktree.exists() or registered(worktree, primary):
        return "failed", {"error": "worktree remains registered or present"}
    return ("branch-preserved" if preserved else "succeeded"), {}


def main():
    args = arguments()
    if args.state_directory:
        os.environ["AGENT_STATE_DIRECTORY"] = args.state_directory
    if args.host_names:
        os.environ["AGENT_CLI_HOST_NAMES"] = args.host_names
    target = Path(args.result)
    own = session_close.process_info(os.getpid())
    if own is None:
        return 0
    cleanup_fields = {
        key: getattr(args, key)
        for key in ("head", "primary", "branch", "default")
        if getattr(args, key) is not None
    }
    expected = session_close.binding(
        args.host_pid, args.host_start, args.worktree, args.session_id,
        args.invocation_id, cleanup_fields,
    )
    if args.parent_pid is not None or args.parent_start is not None:
        expected.update({"parent_pid": args.parent_pid, "parent_start": args.parent_start})
    observer = {
        **expected,
        "started": session_close.now(),
        "reaper_pid": own.pid,
        "reaper_started_at": own.started_at,
        "observer_pid": own.pid,
        "observer_started_at": own.started_at,
    }
    if not session_close.write_json(target, observer, exclusive=True):
        return 0
    cleanup = all(getattr(args, key) for key in ("head", "primary", "branch", "default"))
    accept_timeout = bounded_timeout(args.accept_timeout, "AGENT_FINISH_ACCEPT_TIMEOUT_SECONDS")
    if not await_acceptance(target, observer, expected, accept_timeout):
        result(target, "cancelled" if Path(str(target) + ".cancelled").exists() else "not-accepted")
        return 0
    try:
        if not await_exit(args):
            status = "cancelled" if Path(str(target) + ".cancelled").exists() else "timeout"
            result(target, status, error="verified host (or Windows wrapper) did not exit")
            return 0
        if cleanup:
            status, extra = remove_worktree_and_branch(args)
            if status not in {"succeeded", "branch-preserved"}:
                result(target, status, **extra)
                return 0
            session_close.remove_matching_obligations(args.worktree, args.session_id)
            result(target, status, session_exited=True, **extra)
        else:
            session_close.remove_matching_obligations(args.worktree, args.session_id)
            result(target, "session-closed", checkout_retained=True, session_exited=True)
    except session_close.Refusal as error:
        result(target, "failed", error=str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
