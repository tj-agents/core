"""Close one armed session once its turn has ended and stayed idle (Python 3.9+).

Started detached by `close_session.py arm`. A new prompt, an ended or replaced session, or the timeout
cancels it without closing anything. It preserves the shared backend, terminal and checkout.
"""

import argparse
import json
import os
import sqlite3
import sys
import time

import close
import session_close
from session_close import Refusal

POLL_SECONDS = 0.25
EXIT_WAIT_SECONDS = 30.0


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--pid-started-at", type=float, required=True)
    parser.add_argument("--armed-at", type=float, required=True)
    parser.add_argument("--idle", type=float, default=3.0)
    parser.add_argument("--timeout", type=float, default=900.0)
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
    uri = store.database_path().resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=5)
    try:
        connection.row_factory = sqlite3.Row
        return store.get_session(connection, store.session_handle(args.host, args.session_id))
    finally:
        connection.close()


def is_prompt(record):
    if record.get("type") != "user" or record.get("isMeta") or record.get("isCompactSummary"):
        return False
    content = (record.get("message") or {}).get("content")
    return isinstance(content, str) or (isinstance(content, list) and not any(
        isinstance(item, dict) and item.get("type") == "tool_result" for item in content))


def transcript_verdict(args):
    """Judge the Claude transcript written since arming: "cancel", "finished", "pending", or None without one."""
    if not args.transcript:
        return None
    try:
        with open(args.transcript, "rb") as stream:
            stream.seek(args.transcript_offset)
            lines = stream.read().splitlines()
    except OSError:
        return "pending"
    verdict = "pending"
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
            return "cancel"
        if record.get("type") == "system" and record.get("subtype") == "stop_hook_summary":
            verdict = "finished"
        elif record.get("type") in ("user", "assistant") and (verdict == "finished" or is_prompt(record)):
            return "cancel"
    return verdict


def superseded(args):
    record = session_close.read_json(armed_path(args.session_id)) or {}
    return record.get("armed_at") not in (None, args.armed_at)


def wait_for_idle(args, clock=time.time, sleep=time.sleep):
    """Return the idle turn's activity token, or None when the close is cancelled or re-armed."""
    deadline = clock() + args.timeout
    stopped, since, settled = None, None, None
    while clock() < deadline:
        if superseded(args):
            return None
        if not session_close.verified_live(args.pid, args.pid_started_at):
            return None
        row = session_row(args)
        if not isinstance(row, dict) or row.get("ended_at") is not None or row.get("pid") != args.pid:
            return None
        activity = row.get("last_activity_at")
        if not session_close.finite_positive(activity):
            return None
        verdict = transcript_verdict(args)
        if verdict == "cancel":
            return None
        if activity > args.armed_at:
            awaiting = row.get("turn_state") == "awaiting_input"
            if not awaiting or stopped not in (None, activity):
                if verdict is None:
                    return None
                stopped = settled = None
                if not awaiting:
                    sleep(POLL_SECONDS)
                    continue
            verdict = verdict or "finished"
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
    session_close.awaiting_input_activity(entry, activity)
    close.close_host(entry, lambda: session_close.awaiting_input_activity(entry, activity))
    deadline = time.time() + EXIT_WAIT_SECONDS
    while not session_close.verified_exited(entry["pid"], entry["pid_started_at"]):
        if time.time() >= deadline:
            raise Refusal("CLI client exit was not confirmed")
        time.sleep(POLL_SECONDS)
    session_close._record_own_end(entry, "closed")


def outcome_path(session_id):
    return session_close.state_directory() / "session-close" / (session_id + ".json")


def armed_path(session_id):
    return session_close.state_directory() / "session-close" / (session_id + ".armed.json")


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
    if status == "cancelled" and superseded(args):
        return 0
    process = session_close.process_info(os.getpid())
    session_close.write_json(outcome_path(args.session_id), {
        "status": status, "at": time.time(), "watcher_pid": os.getpid(),
        "watcher_started_at": process.started_at if process else None,
    })
    return 0 if status in ("closed", "cancelled") else 2


if __name__ == "__main__":
    raise SystemExit(main())
