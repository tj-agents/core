#!/usr/bin/env python3
"""Single SQLite-backed store for session and work-item status, written by hooks (Python 3.9+)."""

import argparse
import json
import os
import re
import socket
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

SCHEMA_VERSION = 1
GIT_TIMEOUT = 3

WORK_ITEMS_SCHEMA = """
CREATE TABLE IF NOT EXISTS work_items (
    key TEXT PRIMARY KEY,
    repo TEXT NOT NULL,
    feature TEXT NOT NULL,
    item TEXT NOT NULL,
    status TEXT NOT NULL,
    branch TEXT,
    pr TEXT,
    updated_at REAL
)
"""

SESSIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    handle TEXT PRIMARY KEY,
    host TEXT NOT NULL,
    session_id TEXT NOT NULL,
    machine TEXT,
    profile TEXT,
    title TEXT,
    cwd TEXT,
    repo TEXT,
    branch TEXT,
    head TEXT,
    work_item TEXT REFERENCES work_items(key),
    role TEXT,
    pid INTEGER,
    pid_started_at REAL,
    started_at REAL,
    last_activity_at REAL,
    turn_state TEXT,
    ended_at REAL,
    end_reason TEXT,
    predecessor TEXT,
    successor TEXT
)
"""

_SSH_SCP_RE = re.compile(r"^[^/@\s]+@[^:/\s]+:(?P<path>.+)$")


def state_directory():
    override = os.environ.get("AGENT_STATE_DIRECTORY")
    return Path(override) if override else Path.home() / ".agents-state"


def database_path():
    return state_directory() / "sessions.db"


def connect(path=None):
    target = Path(path) if path is not None else database_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(target), timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA foreign_keys = ON")
    _ensure_schema(connection)
    return connection


def _ensure_schema(connection):
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version < SCHEMA_VERSION:
        connection.execute(WORK_ITEMS_SCHEMA)
        connection.execute(SESSIONS_SCHEMA)
        connection.execute("PRAGMA user_version = %d" % SCHEMA_VERSION)
        connection.commit()


def current_machine():
    return socket.gethostname()


def profile_directory(host):
    if host == "claude":
        value = os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")
    else:
        value = os.environ.get("CODEX_HOME") or str(Path.home() / ".codex")
    return str(Path(value))


def _git(cwd, *args, timeout=GIT_TIMEOUT):
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True, text=True, timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    output = result.stdout.strip()
    return output or None


def _normalise_remote(url):
    url = (url or "").strip()
    if not url:
        return None
    path = None
    if url.startswith(("ssh://", "https://", "http://", "git://")):
        path = urlparse(url).path
    else:
        match = _SSH_SCP_RE.match(url)
        if match:
            path = match.group("path")
    if not path:
        return None
    path = path.strip("/")
    if path.endswith(".git"):
        path = path[: -len(".git")]
    parts = [part for part in path.split("/") if part]
    if len(parts) < 2:
        return None
    return "/".join(parts[-2:])


def repo_identity(cwd):
    origin = _git(cwd, "config", "--get", "remote.origin.url")
    normalised = _normalise_remote(origin) if origin else None
    if normalised:
        return normalised
    common_dir = _git(cwd, "rev-parse", "--git-common-dir")
    if not common_dir:
        return None
    path = Path(common_dir)
    if not path.is_absolute():
        path = Path(cwd) / path
    try:
        return str(path.resolve())
    except OSError:
        return None


def current_branch_and_head(cwd):
    branch = _git(cwd, "branch", "--show-current")
    head = _git(cwd, "rev-parse", "HEAD")
    return branch, head


def session_handle(host, session_id):
    return f"{host}:{session_id}"


def work_item_key(repo, feature, item):
    return f"{repo}:{feature}/{item}"


def start_session(connection, host, session_id, cwd, title=None, pid=None, pid_started_at=None):
    handle = session_handle(host, session_id)
    machine = current_machine()
    profile = profile_directory(host)
    repo = repo_identity(cwd)
    branch, head = current_branch_and_head(cwd)
    now = time.time()
    connection.execute(
        """
        INSERT INTO sessions (
            handle, host, session_id, machine, profile, title, cwd, repo, branch, head,
            pid, pid_started_at, started_at, last_activity_at, turn_state, ended_at, end_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'working', NULL, NULL)
        ON CONFLICT(handle) DO UPDATE SET
            machine = excluded.machine,
            profile = excluded.profile,
            title = COALESCE(excluded.title, sessions.title),
            cwd = excluded.cwd,
            repo = excluded.repo,
            branch = excluded.branch,
            head = excluded.head,
            pid = excluded.pid,
            pid_started_at = excluded.pid_started_at,
            started_at = excluded.started_at,
            last_activity_at = excluded.started_at,
            turn_state = 'working',
            ended_at = NULL,
            end_reason = NULL
        """,
        (handle, host, session_id, machine, profile, title, str(cwd), repo, branch, head,
         pid, pid_started_at, now, now),
    )
    connection.commit()
    if repo and branch:
        attach_work_item_if_unique(connection, repo, branch, handle)
        connection.commit()
    return handle


def ensure_session(connection, host, session_id, cwd=None):
    handle = session_handle(host, session_id)
    if get_session(connection, handle) is not None:
        return handle
    machine = current_machine()
    profile = profile_directory(host)
    repo = repo_identity(cwd) if cwd else None
    branch, head = current_branch_and_head(cwd) if cwd else (None, None)
    now = time.time()
    connection.execute(
        """
        INSERT INTO sessions (
            handle, host, session_id, machine, profile, cwd, repo, branch, head,
            started_at, last_activity_at, turn_state
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'working')
        ON CONFLICT(handle) DO NOTHING
        """,
        (handle, host, session_id, machine, profile, str(cwd) if cwd else None, repo, branch, head, now, now),
    )
    connection.commit()
    return handle


def record_prompt(connection, handle):
    connection.execute(
        "UPDATE sessions SET turn_state = 'working', last_activity_at = ? WHERE handle = ?",
        (time.time(), handle),
    )
    connection.commit()


def record_stop(connection, handle, cwd):
    repo = repo_identity(cwd)
    branch, head = current_branch_and_head(cwd)
    now = time.time()
    connection.execute(
        """
        UPDATE sessions SET turn_state = 'awaiting_input', last_activity_at = ?, cwd = ?,
            repo = COALESCE(?, repo), branch = COALESCE(?, branch), head = COALESCE(?, head)
        WHERE handle = ?
        """,
        (now, str(cwd), repo, branch, head, handle),
    )
    connection.commit()
    if repo and branch:
        attach_work_item_if_unique(connection, repo, branch, handle)
        connection.commit()


def end_session(connection, handle, reason, successor=None):
    connection.execute(
        """
        UPDATE sessions SET
            ended_at = COALESCE(ended_at, ?),
            end_reason = COALESCE(end_reason, ?),
            successor = COALESCE(successor, ?)
        WHERE handle = ?
        """,
        (time.time(), reason, successor, handle),
    )
    connection.commit()


def attach_work_item_if_unique(connection, repo, branch, handle):
    row = connection.execute("SELECT work_item FROM sessions WHERE handle = ?", (handle,)).fetchone()
    if row is None or row["work_item"] is not None:
        return
    matches = connection.execute(
        "SELECT key FROM work_items WHERE repo = ? AND branch = ? AND status != 'done'",
        (repo, branch),
    ).fetchall()
    if len(matches) == 1:
        connection.execute("UPDATE sessions SET work_item = ? WHERE handle = ?", (matches[0]["key"], handle))


def get_work_item(connection, key):
    row = connection.execute("SELECT * FROM work_items WHERE key = ?", (key,)).fetchone()
    return dict(row) if row else None


def upsert_work_item(connection, key, repo, feature, item, status=None, branch=None, pr=None):
    now = time.time()
    connection.execute(
        """
        INSERT INTO work_items (key, repo, feature, item, status, branch, pr, updated_at)
        VALUES (?, ?, ?, ?, COALESCE(?, 'active'), ?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            status = COALESCE(?, work_items.status),
            branch = COALESCE(?, work_items.branch),
            pr = COALESCE(?, work_items.pr),
            updated_at = ?
        """,
        (key, repo, feature, item, status, branch, pr, now, status, branch, pr, now),
    )
    connection.commit()


def set_work_item_status(connection, key, status, pr=None):
    connection.execute(
        "UPDATE work_items SET status = ?, pr = COALESCE(?, pr), updated_at = ? WHERE key = ?",
        (status, pr, time.time(), key),
    )
    connection.commit()


def set_session_ownership(connection, handle, role, item, predecessor=None):
    connection.execute(
        "UPDATE sessions SET role = ?, work_item = ?, predecessor = COALESCE(?, predecessor) WHERE handle = ?",
        (role, item, predecessor, handle),
    )
    connection.commit()


def transfer_ownership(connection, predecessor_handle, successor_handle, item, role="owner"):
    end_session(connection, predecessor_handle, "handed_off", successor=successor_handle)
    set_session_ownership(connection, successor_handle, role, item, predecessor=predecessor_handle)


def get_session(connection, handle):
    row = connection.execute("SELECT * FROM sessions WHERE handle = ?", (handle,)).fetchone()
    return dict(row) if row else None


def sessions_for_work_item(connection, item):
    rows = connection.execute(
        "SELECT * FROM sessions WHERE work_item = ? ORDER BY started_at", (item,),
    ).fetchall()
    return [dict(row) for row in rows]


def live_owners(connection, item):
    rows = connection.execute(
        "SELECT * FROM sessions WHERE work_item = ? AND role = 'owner' AND ended_at IS NULL", (item,),
    ).fetchall()
    return [dict(row) for row in rows]


def sessions_by_repo(connection, repo):
    rows = connection.execute("SELECT * FROM sessions WHERE repo = ?", (repo,)).fetchall()
    return [dict(row) for row in rows]


def interrupted_candidates(connection, repo=None):
    if repo:
        rows = connection.execute(
            "SELECT * FROM sessions WHERE ended_at IS NULL AND repo = ?", (repo,),
        ).fetchall()
    else:
        rows = connection.execute("SELECT * FROM sessions WHERE ended_at IS NULL").fetchall()
    return [dict(row) for row in rows]


def _read_json_stdin():
    try:
        raw = sys.stdin.read()
    except (OSError, ValueError):
        return {}
    try:
        value = json.loads(raw) if raw.strip() else {}
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def run_hook(event, host):
    try:
        payload = _read_json_stdin()
        session_id = payload.get("session_id") or payload.get("sessionId")
        if not isinstance(session_id, str) or not session_id:
            return 0
        cwd = payload.get("cwd") or os.getcwd()
        handle = session_handle(host, session_id)
        connection = connect()
        try:
            if event == "session-start":
                start_session(connection, host, session_id, cwd)
            elif event == "prompt":
                record_prompt(connection, handle)
            elif event == "stop":
                record_stop(connection, handle, cwd)
            elif event == "session-end":
                end_session(connection, handle, "closed")
        finally:
            connection.close()
    except Exception:
        pass
    return 0


def _build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    hook_parser = subparsers.add_parser("hook")
    hook_parser.add_argument("event", choices=("session-start", "prompt", "stop", "session-end"))
    hook_parser.add_argument("--host", required=True, choices=("claude", "codex"))
    return parser


def main(argv=None):
    args = _build_parser().parse_args(argv)
    if args.command == "hook":
        return run_hook(args.event, args.host)
    return 0


if __name__ == "__main__":
    sys.exit(main())
