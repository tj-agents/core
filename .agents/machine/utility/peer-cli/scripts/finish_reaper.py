"""Detached, identity-checked observer for peer-cli close and finish (Python 3.9+)."""
import argparse
import os
import time
from pathlib import Path
import session_close


def arguments():
    parser = argparse.ArgumentParser()
    for name, kind, required in (("host-pid", int, True), ("host-start", float, True), ("worktree", str, True), ("result", str, True), ("parent-pid", int, False), ("parent-start", float, False), ("session-id", str, False), ("head", str, False), ("primary", str, False), ("branch", str, False), ("default", str, False), ("accept-timeout", float, False)):
        parser.add_argument("--" + name, type=kind, required=required, default=60 if name == "accept-timeout" else None)
    return parser.parse_args()


def bounded_timeout(name, default, maximum):
    try:
        value = float(os.environ.get(name, default))
    except ValueError:
        return default
    return value if 0 < value <= maximum else default


def result(path, status, **extra):
    value = session_close.read_json(path) or {}
    value.update({"status": status, "finished": session_close.now()})
    value.update(extra)
    session_close.write_json(path, value)


def await_acceptance(path, pid, started, host_pid, timeout):
    end = session_close.now() + timeout
    while session_close.now() < end:
        if Path(str(path) + ".cancelled").exists():
            return False
        value = session_close.read_json(str(path) + ".accepted")
        if (value and value.get("reaper_pid") == pid and value.get("host_pid") == host_pid
                and session_close.valid_identity(value.get("reaper_pid"), value.get("reaper_started_at"))
                and abs(value["reaper_started_at"] - started) <= 2):
            session_close.write_json(
                str(path) + ".armed",
                {"armed": session_close.now(), "reaper_pid": pid, "reaper_started_at": started},
            )
            return True
        time.sleep(.05)
    return False


def await_exit(args):
    end = session_close.now() + bounded_timeout("AGENT_FINISH_REAPER_TIMEOUT_SECONDS", 600, 3600)
    watched = [(args.host_pid, args.host_start)]
    if os.name == "nt" and args.parent_pid and args.parent_start:
        watched.append((args.parent_pid, args.parent_start))
    while session_close.now() < end:
        if all(session_close.verified_exited(pid, started) for pid, started in watched):
            return True
        time.sleep(.25)
    return False


def registered(worktree, primary):
    code, output, _ = session_close.git(primary, "worktree", "list", "--porcelain")
    return code != 0 or any(line.startswith("worktree ") and session_close.path_key(line[9:]) == session_close.path_key(worktree) for line in output.splitlines())


def branch_checked_out(primary, branch):
    code, output, _ = session_close.git(primary, "worktree", "list", "--porcelain")
    if code:
        return True
    return "branch refs/heads/" + branch in output.splitlines()


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
        ancestor, _, _ = session_close.git(primary, "merge-base", "--is-ancestor", "refs/heads/" + args.branch, "origin/" + args.default)
        if ancestor not in (0, 1):
            return "failed", {"error": "could not verify the cleanup branch relationship"}
        # The branch may have moved after worktree removal; never delete a different ref.
        code, latest, _ = session_close.git(primary, "rev-parse", "--verify", "--quiet", "refs/heads/" + args.branch)
        if code != 0 or latest != args.head:
            preserved = True
        else:
            if Path(str(args.result) + ".cancelled").exists():
                return "cancelled", {"error": "cleanup observer was cancelled"}
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
    target = Path(args.result)
    own = session_close.process_info(os.getpid())
    started = own.started_at if own else session_close.now()
    if not session_close.write_json(target, {
            "started": session_close.now(), "host_pid": args.host_pid, "host_start": args.host_start,
            "worktree": args.worktree, "session_id": args.session_id, "reaper_pid": os.getpid(),
            "reaper_started_at": started,
    }, exclusive=True):
        return 0
    cleanup = all(getattr(args, key) for key in ("head", "primary", "branch", "default"))
    if not await_acceptance(target, os.getpid(), started, args.host_pid, args.accept_timeout):
        result(target, "cancelled" if Path(str(target) + ".cancelled").exists() else "not-accepted")
        return 0
    try:
        if cleanup and os.name != "nt":
            status, extra = remove_worktree_and_branch(args)
            if status not in {"succeeded", "branch-preserved"}:
                result(target, status, **extra)
                return 0
        if not cleanup or os.name == "nt":
            if not await_exit(args):
                result(target, "timeout", error="verified host (or Windows wrapper) did not exit")
                return 0
            if cleanup:
                status, extra = remove_worktree_and_branch(args)
                if status not in {"succeeded", "branch-preserved"}:
                    result(target, status, **extra)
                    return 0
        elif not await_exit(args):
            result(target, "timeout", cleanup=status, **extra)
            return 0
        if cleanup:
            session_close.remove_matching_obligations(worktree=args.worktree)
            result(target, status, host_pid=args.host_pid, host_start=args.host_start,
                   worktree=args.worktree, session_id=args.session_id, session_exited=True, **extra)
        else:
            session_close.remove_matching_obligations(session_id=args.session_id)
            result(target, "session-closed", session_id=args.session_id, checkout_retained=True, session_exited=True)
    except session_close.Refusal as error:
        result(target, "failed", error=str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
