"""Close one armed session once its turn has ended and stayed idle (Python 3.9+).

Started detached by `close_session.py arm`. A new prompt, an ended or replaced session, or the timeout
cancels it without closing anything. After a close it runs the worktree sweep for the session's repository.
"""

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time

import close
import session_close
from session_close import Refusal

POLL_SECONDS = 0.25
EXIT_WAIT_SECONDS = 30.0
SWEEP_TIMEOUT_SECONDS = 1800


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--pid-started-at", type=float, required=True)
    parser.add_argument("--armed-at", type=float, required=True)
    parser.add_argument("--idle", type=float, default=3.0)
    parser.add_argument("--timeout", type=float, default=900.0)
    parser.add_argument("--repo")
    parser.add_argument("--sweep")
    parser.add_argument("--state-directory")
    parser.add_argument("--host-names")
    parser.add_argument("--transcript")
    parser.add_argument("--transcript-offset", type=int, default=0)
    return parser.parse_args(argv)


def registered_entry(args):
    for _path, entry in session_close.entries():
        if (entry.get("host") == args.host and entry.get("session_id") == args.session_id
                and entry.get("pid") == args.pid and entry.get("pid_started_at") == args.pid_started_at):
            return entry
    return None


def session_row(args):
    store = session_close.register_session._load_session_store()
    if store is None:
        raise Refusal("session turn store is unavailable")
    connection = sqlite3.connect(store.database_path().as_uri() + "?mode=ro", uri=True, timeout=5)
    try:
        connection.row_factory = sqlite3.Row
        return store.get_session(connection, store.session_handle(args.host, args.session_id))
    finally:
        connection.close()


def stop_hooks_verdict(args):
    """Read the Claude transcript written since arming: "blocked", "finished" or "pending"."""
    if not args.transcript:
        return "finished"
    try:
        with open(args.transcript, "rb") as stream:
            stream.seek(args.transcript_offset)
            lines = stream.read().splitlines()
    except OSError:
        return "pending"
    finished = False
    for line in lines:
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if not isinstance(record, dict):
            continue
        attachment = record.get("attachment")
        if (isinstance(attachment, dict) and attachment.get("type") == "hook_blocking_error"
                and attachment.get("hookEvent") == "Stop"):
            return "blocked"
        if record.get("type") == "system" and record.get("subtype") == "stop_hook_summary":
            finished = True
    return "finished" if finished else "pending"


def wait_for_idle(args, clock=time.time, sleep=time.sleep):
    """Return the idle turn's activity token, or None when the close is cancelled."""
    deadline = clock() + args.timeout
    stopped, since, settled = None, None, None
    while clock() < deadline:
        if not session_close.verified_live(args.pid, args.pid_started_at):
            return None
        row = session_row(args)
        if not isinstance(row, dict) or row.get("ended_at") is not None or row.get("pid") != args.pid:
            return None
        activity = row.get("last_activity_at")
        if not session_close.finite_positive(activity):
            return None
        if activity > args.armed_at:
            if row.get("turn_state") != "awaiting_input" or stopped not in (None, activity):
                return None
            verdict = stop_hooks_verdict(args)
            if verdict == "blocked":
                return None
            if stopped is None or verdict != settled:
                stopped, since, settled = activity, clock(), verdict
            elif verdict == "finished" and clock() - since >= args.idle:
                return stopped
        sleep(POLL_SECONDS)
    return None


def close_session(args, activity):
    entry = registered_entry(args)
    if entry is None:
        raise Refusal("the armed session is no longer registered")
    wrapper = session_close.qualified_windows_wrapper(entry)
    session_close.awaiting_input_activity(entry, activity)
    session_close._record_own_end(entry, "closed")
    try:
        close.close_host(entry, wrapper)
        deadline = time.time() + EXIT_WAIT_SECONDS
        while not session_close.verified_exited(entry["pid"], entry["pid_started_at"]):
            if time.time() >= deadline:
                raise Refusal("terminal tab closed but registered host exit was not confirmed")
            time.sleep(POLL_SECONDS)
    except Exception:
        session_close._reopen_own_end(entry, "closed")
        raise


def sweep(args):
    if not (args.sweep and args.repo):
        return
    try:
        subprocess.run([sys.executable, "-B", args.sweep, "--repo", args.repo], stdin=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=SWEEP_TIMEOUT_SECONDS,
                       check=False)
    except (OSError, subprocess.SubprocessError):
        pass


def outcome_path(session_id):
    return session_close.state_directory() / "session-close" / (session_id + ".json")


def main(argv=None):
    args = arguments(argv)
    if args.state_directory:
        os.environ["AGENT_STATE_DIRECTORY"] = args.state_directory
    if args.host_names:
        os.environ["AGENT_CLI_HOST_NAMES"] = args.host_names
    try:
        activity = wait_for_idle(args)
        if activity is None:
            status = "cancelled"
        else:
            close_session(args, activity)
            status = "closed"
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as error:
        status = "refused: " + str(error)
    session_close.write_json(outcome_path(args.session_id), {"status": status, "at": time.time()})
    if status == "closed":
        sweep(args)
    return 0 if status in ("closed", "cancelled") else 2


if __name__ == "__main__":
    raise SystemExit(main())
