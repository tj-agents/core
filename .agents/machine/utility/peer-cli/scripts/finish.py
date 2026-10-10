"""Remove this verified merged linked worktree, then close its exact terminal (Python 3.9+)."""
import argparse
import os
import signal
import sys
import time
import uuid
from pathlib import Path
import close_tab
import session_close


def close_host(entry, wrapper=None):
    if not session_close.verified_live(entry["pid"], entry["pid_started_at"]):
        raise session_close.Refusal("registered host identity changed before close")
    if os.environ.get("AGENT_FINISH_CLOSE_MODE") == "process":
        os.kill(entry["pid"], signal.SIGTERM)
        return
    try:
        close_tab.close_entry(entry)
    except close_tab.TerminalUnavailable:
        if not session_close.verified_live(entry["pid"], entry["pid_started_at"]):
            raise session_close.Refusal("registered host identity changed before fallback close")
        os.kill(entry["pid"], signal.SIGTERM)
        if wrapper and session_close.verified_live(wrapper["pid"], wrapper["started_at"]):
            os.kill(wrapper["pid"], signal.SIGTERM)


def refresh_cleanup(entry, worktree, expected_receipt):
    refreshed = session_close.own_host_and_entry()
    if (refreshed["session_id"] != entry["session_id"]
            or refreshed["pid"] != entry["pid"]
            or refreshed["pid_started_at"] != entry["pid_started_at"]
            or session_close.path_key(session_close.worktree_from_cwd()) != session_close.path_key(worktree)
            or not session_close.under_or_equal(os.getcwd(), refreshed["cwd"])):
        raise session_close.Refusal("session attachment changed while observer started")
    receipt = session_close.fresh_removable_receipt(worktree)
    if any(receipt.get(key) != expected_receipt[key] for key in expected_receipt):
        raise session_close.Refusal("cleanup receipt changed while observer started")
    if session_close.other_live_claimant(worktree, entry["session_id"]):
        raise session_close.Refusal("another registered session claims this worktree")
    code, dirty, _ = session_close.git(worktree, "status", "--porcelain")
    if code or dirty:
        raise session_close.Refusal("worktree is no longer clean")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worktree", help="test-only explicit target; normal use is argument-free")
    args = parser.parse_args(argv)
    entry = session_close.own_host_and_entry()
    attached = session_close.worktree_from_cwd()
    worktree = Path(args.worktree).resolve() if args.worktree else attached
    if session_close.path_key(worktree) != session_close.path_key(attached) or not session_close.under_or_equal(os.getcwd(), entry["cwd"]):
        raise session_close.Refusal("target is not this session's own attachment")
    receipt = session_close.fresh_removable_receipt(worktree)
    if session_close.other_live_claimant(worktree, entry["session_id"]):
        raise session_close.Refusal("another verified live registered session claims this worktree")
    code, dirty, _ = session_close.git(worktree, "status", "--porcelain")
    if code or dirty:
        raise session_close.Refusal("worktree is not clean")
    result = session_close.results_path()
    invocation_id = uuid.uuid4().hex
    wrapper = session_close.qualified_windows_wrapper(entry)
    cleanup = {key: receipt[key] for key in ("head", "primary", "branch", "default")}
    expected = session_close.binding(
        entry["pid"], entry["pid_started_at"], worktree, entry["session_id"], invocation_id, cleanup,
    )
    if wrapper:
        expected.update({"parent_pid": wrapper["pid"], "parent_start": wrapper["started_at"]})
    observer = [
        "--host-pid", str(entry["pid"]), "--host-start", str(entry["pid_started_at"]),
        "--worktree", str(worktree), "--result", str(result), "--session-id", entry["session_id"],
        "--invocation-id", invocation_id,
        "--head", receipt["head"], "--primary", receipt["primary"],
        "--branch", receipt["branch"], "--default", receipt["default"],
        "--state-directory", str(session_close.state_directory()),
        "--host-names", os.environ.get("AGENT_CLI_HOST_NAMES", ""),
        "--spawn-timeout", str(session_close.bounded_timeout("AGENT_FINISH_SPAWN_TIMEOUT_SECONDS")),
        "--armed-timeout", str(session_close.bounded_timeout("AGENT_FINISH_ARMED_TIMEOUT_SECONDS")),
        "--accept-timeout", str(session_close.bounded_timeout("AGENT_FINISH_ACCEPT_TIMEOUT_SECONDS")),
        "--reaper-timeout", str(session_close.bounded_timeout("AGENT_FINISH_REAPER_TIMEOUT_SECONDS")),
    ]
    if wrapper:
        observer.extend(["--parent-pid", str(wrapper["pid"]),
                         "--parent-start", str(wrapper["started_at"])])
    try:
        spawned_at = time.time()
        observer_pid = session_close.start_observer(observer)
        started = session_close.wait_for_record(
            result, session_close.bounded_timeout("AGENT_FINISH_SPAWN_TIMEOUT_SECONDS"),
        )
        if not session_close.valid_observer_start(
                started, observer_pid, entry["pid"], entry["pid_started_at"], worktree,
                entry["session_id"], invocation_id, cleanup, minimum_started=spawned_at,
        ):
            raise session_close.Refusal("cleanup observer did not confirm startup")
        refresh_cleanup(entry, worktree, cleanup)
        accepted = {
            **expected,
            "accepted": time.time(),
            "reaper_pid": started["reaper_pid"],
            "reaper_started_at": started["reaper_started_at"],
            "observer_pid": started["reaper_pid"],
            "observer_started_at": started["reaper_started_at"],
        }
        session_close.write_json(str(result) + ".accepted", accepted)
        armed = session_close.wait_for_record(
            str(result) + ".armed", session_close.bounded_timeout("AGENT_FINISH_ARMED_TIMEOUT_SECONDS"),
        )
        if not session_close.valid_armed(armed, expected, started, accepted):
            raise session_close.Refusal("cleanup observer did not acknowledge acceptance")
        close_host(entry, wrapper)
    except Exception as error:
        session_close.cancel_observer(result, str(error))
        raise
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (session_close.Refusal, close_tab.TerminalRefusal) as error:
        print("finish: " + str(error), file=sys.stderr)
        raise SystemExit(2)
