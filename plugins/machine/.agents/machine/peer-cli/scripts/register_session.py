"""SessionStart hook: record this session's id, tab title, directory and pid.

`agent-cli.ps1` exports `AGENT_CLI_TAB_TITLE` when it launches a tab; a session started by hand exports
nothing and records a null title. `peer-cli.ps1` reads these entries to resolve a session from the tab
title a user can see, and the reverse.

Contract: exit 0 always. Bookkeeping must never stop a session starting.
"""

import json
import os
import sys
import time
from pathlib import Path


STATE_DIRECTORY_ENV = "AGENT_STATE_DIRECTORY"
TITLE_ENV = "AGENT_CLI_TAB_TITLE"


def state_directory():
    override = os.environ.get(STATE_DIRECTORY_ENV)
    root = Path(override) if override else Path.home() / ".agents-state"
    return root / "cli-sessions"


def read_payload():
    try:
        raw = sys.stdin.read()
    except (OSError, ValueError):
        return {}
    try:
        value = json.loads(raw) if raw.strip() else {}
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def record(data):
    session = data.get("session_id") or data.get("sessionId")
    if not session:
        return None
    entry = {
        "session_id": str(session),
        "title": os.environ.get(TITLE_ENV) or None,
        "cwd": data.get("cwd") or os.getcwd(),
        "pid": os.getppid(),
        "started_at": time.time(),
    }
    destination = state_directory() / f"{session}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    staging.write_text(json.dumps(entry, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(staging, destination)
    return entry


def main():
    try:
        record(read_payload())
    except Exception:  # noqa: BLE001 - bookkeeping must never stop a session starting
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
