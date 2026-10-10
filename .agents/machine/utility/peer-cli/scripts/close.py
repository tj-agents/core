"""Close this verified session while retaining its checkout (Python 3.9+)."""
import argparse
import os
import signal
import sys
import time
import close_tab
import session_close


def close_host(entry):
    if os.environ.get("AGENT_FINISH_CLOSE_MODE") == "process":
        os.kill(entry["pid"], signal.SIGTERM)
        return
    close_tab.close_entry(entry)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    entry = session_close.own_host_and_entry()
    worktree = session_close.worktree_from_cwd()
    if not session_close.under_or_equal(os.getcwd(), entry["cwd"]):
        raise session_close.Refusal("current directory is not this session's registered attachment")
    result = session_close.results_path()
    observer = ["--host-pid", str(entry["pid"]), "--host-start", str(entry["pid_started_at"]),
                "--worktree", str(worktree), "--result", str(result), "--session-id", entry["session_id"]]
    session_close.start_observer(observer)
    started = session_close.wait_for_record(result, 15)
    if not started or started.get("host_pid") != entry["pid"]:
        raise session_close.Refusal("session exit observer did not confirm startup; nothing was closed")
    close_host(entry)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except session_close.Refusal as error:
        print("close: " + str(error), file=sys.stderr)
        raise SystemExit(2)
