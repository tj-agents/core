r"""PermissionDenied + PreToolUse hook: turn an auto-mode block into a prompt for the user.

On `PermissionDenied` it records the exact denied call and answers `retry: true`. When the same
session retries that identical call, `PreToolUse` consumes the record and answers `ask`, so the
user decides instead of the classifier. Nothing is ever approved here: every path either asks or
stays silent. A record expires after RECORD_TTL_SECONDS and is used at most once.
"""

import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path

RECORD_PREFIX = "agents-denial-"
RECORD_TTL_SECONDS = 15 * 60


def record_path(data):
    session = data.get("session_id") or data.get("sessionId")
    tool = data.get("tool_name")
    if not session or not tool:
        return None
    identity = json.dumps(
        [session, tool, data.get("tool_input")], sort_keys=True, separators=(",", ":")
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return Path(tempfile.gettempdir()) / (RECORD_PREFIX + digest + ".json")


def respond(event, fields):
    sys.stdout.write(json.dumps({"hookSpecificOutput": {"hookEventName": event, **fields}}))
    sys.exit(0)


def on_denied(data):
    path = record_path(data)
    if path is None:
        sys.exit(0)
    prune_expired(path.parent)
    try:
        path.write_text(json.dumps({"denied_at": time.time()}), encoding="utf-8")
    except OSError:
        sys.exit(0)
    respond("PermissionDenied", {"retry": True})


def prune_expired(directory):
    cutoff = time.time() - RECORD_TTL_SECONDS
    for stale in directory.glob(RECORD_PREFIX + "*.json"):
        try:
            if stale.stat().st_mtime < cutoff:
                stale.unlink()
        except OSError:
            continue


def on_pre_tool_use(data):
    path = record_path(data)
    if path is None:
        sys.exit(0)
    try:
        denied_at = json.loads(path.read_text(encoding="utf-8")).get("denied_at", 0)
        path.unlink()
    except (OSError, ValueError, AttributeError):
        sys.exit(0)
    if not isinstance(denied_at, (int, float)) or time.time() - denied_at > RECORD_TTL_SECONDS:
        sys.exit(0)
    respond(
        "PreToolUse",
        {
            "permissionDecision": "ask",
            "permissionDecisionReason": "Auto mode blocked this call; approve or reject it yourself.",
        },
    )


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)
    if not isinstance(data, dict) or "turn_id" in data or "turnId" in data:
        sys.exit(0)
    event = data.get("hook_event_name") or data.get("hookEventName")
    if event == "PermissionDenied":
        on_denied(data)
    elif event == "PreToolUse":
        on_pre_tool_use(data)
    sys.exit(0)


if __name__ == "__main__":
    main()
