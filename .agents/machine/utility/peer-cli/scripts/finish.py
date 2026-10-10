"""Remove this verified merged linked worktree, then close its exact terminal (Python 3.9+)."""
import argparse
import os
import signal
import sys
import time
from pathlib import Path
import close_tab
import session_close


def close_host(entry):
    if os.environ.get("AGENT_FINISH_CLOSE_MODE") == "process":
        os.kill(entry["pid"], signal.SIGTERM)
    else:
        close_tab.close_entry(entry)


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
    observer = ["--host-pid", str(entry["pid"]), "--host-start", str(entry["pid_started_at"]),
                "--worktree", str(worktree), "--result", str(result), "--session-id", entry["session_id"],
                "--head", receipt["head"], "--primary", receipt["primary"], "--branch", receipt["branch"],
                "--default", receipt["default"]]
    session_close.start_observer(observer)
    started = session_close.wait_for_record(result, 15)
    if not started or started.get("host_pid") != entry["pid"] or not started.get("reaper_pid"):
        raise session_close.Refusal("cleanup observer did not confirm startup; nothing was closed")
    session_close.write_json(str(result) + ".accepted", {"accepted": time.time(), "reaper_pid": started["reaper_pid"], "reaper_started_at": started["reaper_started_at"], "host_pid": entry["pid"]})
    armed = session_close.wait_for_record(str(result) + ".armed", 10)
    if not armed or armed.get("reaper_pid") != started["reaper_pid"]:
        session_close.write_json(str(result) + ".cancelled", {"cancelled": time.time(), "reason": "observer was not armed"})
        raise session_close.Refusal("cleanup observer did not acknowledge acceptance; nothing was closed")
    close_host(entry)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except session_close.Refusal as error:
        print("finish: " + str(error), file=sys.stderr)
        raise SystemExit(2)
