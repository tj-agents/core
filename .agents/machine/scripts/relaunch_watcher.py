"""Reopen one armed CLI session after its old process has exited (Python 3.9+).

Started detached by `session_relaunch.py`. A cancelled or replaced record, or the timeout, ends it without
launching anything, so the conversation never has two writers.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import session_close

POLL_SECONDS = 0.5
LAUNCH_TIMEOUT_SECONDS = 600
SESSION_ENVIRONMENT = ("CLAUDECODE", "CLAUDE_CODE_SESSION_ID", "CLAUDE_PID", "CLAUDE_CODE_ENTRYPOINT",
                       "CODEX_THREAD_ID", "CODEX_SESSION_ID", "CODEX_TUI_RECORD_SESSION",
                       "CODEX_TUI_SESSION_LOG_PATH")


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("claude", "codex"), default="claude")
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--pid-started-at", type=float, required=True)
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--recovery", type=Path, required=True)
    parser.add_argument("--title", default="Claude")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--timeout", type=float, default=960.0)
    parser.add_argument("--native-argument", action="append", default=[])
    return parser.parse_args(argv)


def read_record(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def settle(args, state, **details):
    record = read_record(args.record)
    if record.get("token") != args.token:
        return
    record.update(details, state=state, at=time.time())
    temporary = args.record.with_name(args.record.name + ".watcher")
    temporary.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, args.record)


def wait_for_exit(args, exited=session_close.verified_exited, clock=time.monotonic, sleep=time.sleep):
    deadline = clock() + args.timeout
    while clock() < deadline:
        record = read_record(args.record)
        if record.get("token") != args.token or record.get("state") != "waiting":
            return False
        if args.host == "codex":
            armed_at = record.get("close_armed_at")
            close_path = args.record.parents[1] / "session-close" / args.session_id
            armed = read_record(close_path.with_suffix(".armed.json"))
            outcome = read_record(close_path.with_suffix(".json"))
            if armed_at is not None and armed.get("armed_at") != armed_at:
                settle(args, "cancelled", reason="the close was superseded")
                return False
            fresh = (isinstance(armed_at, (int, float)) and isinstance(outcome.get("at"), (int, float))
                     and outcome["at"] >= armed_at)
            if fresh and outcome.get("status") != "closed":
                settle(args, "cancelled", reason="the close was cancelled or refused")
                return False
            if not fresh or outcome.get("status") != "closed":
                sleep(POLL_SECONDS)
                continue
        if exited(args.pid, args.pid_started_at):
            return True
        sleep(POLL_SECONDS)
    settle(args, "expired")
    return False


def launch_command(args):
    profile = ([f"--{args.host}-history-root", str(args.profile / ("sessions" if args.host == "codex" else "projects"))]
               if args.profile else [])
    return [sys.executable, "-B", str(args.recovery), "open", "--host", args.host, "--id", args.session_id,
            "--title", args.title, "--prompt", args.prompt,
            *profile,
            *[f"--native-argument={value}" for value in args.native_argument]]


def launch(args, run=subprocess.run):
    record = read_record(args.record)
    if record.get("token") != args.token or record.get("state") != "waiting":
        return 1
    environment = {key: value for key, value in os.environ.items() if key not in SESSION_ENVIRONMENT}
    try:
        result = run(launch_command(args), env=environment, cwd=str(args.recovery.parent), capture_output=True,
                     text=True, encoding="utf-8", errors="replace", timeout=LAUNCH_TIMEOUT_SECONDS, check=False)
    except (OSError, subprocess.SubprocessError) as error:
        settle(args, "failed", error=str(error))
        return 1
    state = "launched" if result.returncode == 0 else "unverified" if result.returncode == 3 else "failed"
    settle(args, state, returncode=result.returncode,
           output=(result.stdout + result.stderr)[-4000:])
    return result.returncode


def main(argv=None):
    args = arguments(argv)
    if not wait_for_exit(args):
        return 1
    return launch(args)


if __name__ == "__main__":
    raise SystemExit(main())
