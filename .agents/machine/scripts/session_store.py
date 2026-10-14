#!/usr/bin/env python3
"""Single SQLite-backed store for session and work-item status, written by hooks (Python 3.9+)."""

import argparse
import importlib.util
import json
import math
import os
import re
import socket
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
SCHEMA_VERSION = 2
GIT_TIMEOUT = 3
HOOK_GIT_TIMEOUT = 2
_LOCK_RETRY_DELAY = 0.05
_REGISTER_SESSION = None

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

SESSIONS_ONE_OWNER_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_one_owner_per_work_item
ON sessions(work_item) WHERE role = 'owner'
"""

_SSH_SCP_RE = re.compile(r"^[^/@\s]+@(?P<host>[^:/\s]+):(?P<path>.+)$")


def state_directory():
    override = os.environ.get("AGENT_STATE_DIRECTORY")
    return Path(override) if override else Path.home() / ".agents-state"


def database_path():
    return state_directory() / "sessions.db"


def _register_session():
    global _REGISTER_SESSION
    if _REGISTER_SESSION is not None:
        return _REGISTER_SESSION
    source = HERE.parent / "utility/peer-cli/scripts/register_session.py"
    packaged = tuple(
        HERE.parents[2] / layout / "peer-cli/scripts/register_session.py" for layout in ("skills", "codex-skills")
    ) if len(HERE.parents) > 2 else ()
    for path in (source, *packaged):
        if path.is_file():
            spec = importlib.util.spec_from_file_location("session_store_register_session", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            _REGISTER_SESSION = module
            return module
    raise RuntimeError(f"The shared register_session.py helper was not found relative to {HERE}.")


def _execute_with_lock_retry(connection, statement):
    deadline = time.monotonic() + 5
    while True:
        try:
            return connection.execute(statement)
        except sqlite3.OperationalError as error:
            message = str(error).lower()
            if ("locked" not in message and "busy" not in message) or time.monotonic() >= deadline:
                raise
            time.sleep(_LOCK_RETRY_DELAY)


def connect(path=None):
    target = Path(path) if path is not None else database_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(target), timeout=5)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 5000")
        _execute_with_lock_retry(connection, "PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA foreign_keys = ON")
        _ensure_schema(connection)
        return connection
    except Exception:
        connection.close()
        raise


def _ensure_schema(connection):
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute(WORK_ITEMS_SCHEMA)
        connection.execute(SESSIONS_SCHEMA)
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version < 2:
            _deduplicate_owner_rows(connection)
        connection.execute(SESSIONS_ONE_OWNER_INDEX)
        if version < SCHEMA_VERSION:
            connection.execute("PRAGMA user_version = %d" % SCHEMA_VERSION)
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def _deduplicate_owner_rows(connection):
    work_items = connection.execute(
        """
        SELECT work_item FROM sessions
        WHERE role = 'owner' AND work_item IS NOT NULL
        GROUP BY work_item HAVING COUNT(*) > 1
        """
    ).fetchall()
    for row in work_items:
        keep = connection.execute(
            """
            SELECT handle FROM sessions WHERE work_item = ? AND role = 'owner'
            ORDER BY COALESCE(last_activity_at, started_at, ended_at, 0) DESC, handle DESC
            LIMIT 1
            """,
            (row["work_item"],),
        ).fetchone()
        connection.execute(
            "UPDATE sessions SET role = NULL WHERE work_item = ? AND role = 'owner' AND handle != ?",
            (row["work_item"], keep["handle"]),
        )


def current_machine():
    return socket.gethostname()


def profile_directory(host):
    if host == "claude":
        value = os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")
    else:
        value = os.environ.get("CODEX_HOME") or str(Path.home() / ".codex")
    return str(Path(value))


def _run_git(cwd, args, timeout):
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None, True
    except (OSError, subprocess.SubprocessError):
        return None, False
    if result.returncode != 0:
        return None, False
    output = result.stdout.strip()
    return (output or None), False


def _git(cwd, *args, timeout=GIT_TIMEOUT):
    output, _timed_out = _run_git(cwd, args, timeout)
    return output


def _host_and_path(url):
    if url.startswith(("ssh://", "https://", "http://", "git://")):
        parsed = urlparse(url)
        host = (parsed.hostname or "").casefold()
        return (host or None), parsed.path
    match = _SSH_SCP_RE.match(url)
    if not match:
        return None, None
    return match.group("host").casefold(), match.group("path")


def _normalise_remote(url):
    url = (url or "").strip()
    if not url:
        return None
    host, path = _host_and_path(url)
    if not host or not path:
        return None
    path = path.strip("/")
    if path.endswith(".git"):
        path = path[: -len(".git")]
    if not path:
        return None
    if host in ("ssh.dev.azure.com", "vs-ssh.visualstudio.com"):
        parts = [part for part in path.split("/") if part]
        if parts and parts[0] == "v3":
            parts = parts[1:]
        if len(parts) != 3:
            return None
        org, project, repository = parts
        host = "dev.azure.com"
        path = f"{org}/{project}/_git/{repository}"
    elif host.endswith(".visualstudio.com"):
        org = host[: -len(".visualstudio.com")]
        if not org or "." in org:
            return None
        parts = [part for part in path.split("/") if part]
        if parts and parts[0].casefold() == "defaultcollection":
            parts = parts[1:]
        if len(parts) == 2 and parts[0] == "_git":
            repository = parts[1]
            project = repository
        elif len(parts) == 3 and parts[1] == "_git":
            project, _git_segment, repository = parts
        else:
            return None
        host = "dev.azure.com"
        path = f"{org}/{project}/_git/{repository}"
    return f"{host}/{path}".casefold()


def _branch_from_symbolic_ref(value):
    if not value:
        return None
    prefix = "refs/heads/"
    return value[len(prefix):] if value.startswith(prefix) else None


def _rev_parse_probe(cwd, timeout):
    output, timed_out = _run_git(
        cwd, ["rev-parse", "HEAD", "--git-common-dir", "--symbolic-full-name", "HEAD"], timeout,
    )
    if output:
        lines = output.splitlines()
        if len(lines) >= 3:
            head = lines[0].strip() or None
            common_dir = lines[1].strip() or None
            branch = _branch_from_symbolic_ref(lines[2].strip())
            return head, branch, common_dir
    if timed_out:
        return None, None, None
    common_dir = _git(cwd, "rev-parse", "--git-common-dir", timeout=timeout)
    if not common_dir:
        return None, None, None
    symbolic = _git(cwd, "symbolic-ref", "-q", "HEAD", timeout=timeout)
    branch = _branch_from_symbolic_ref(symbolic)
    return None, branch, common_dir


def _collect_repo_branch_head(cwd, timeout=HOOK_GIT_TIMEOUT):
    origin = _git(cwd, "config", "--get", "remote.origin.url", timeout=timeout)
    head, branch, common_dir = _rev_parse_probe(cwd, timeout)
    repo = _normalise_remote(origin) if origin else None
    if not repo and common_dir:
        path = Path(common_dir)
        if not path.is_absolute():
            path = Path(cwd) / path
        try:
            repo = str(path.resolve())
        except OSError:
            repo = None
    return repo, branch, head


def repo_identity(cwd):
    repo, _branch, _head = _collect_repo_branch_head(cwd, timeout=GIT_TIMEOUT)
    return repo


def current_branch_and_head(cwd):
    _repo, branch, head = _collect_repo_branch_head(cwd, timeout=GIT_TIMEOUT)
    return branch, head


def session_handle(host, session_id):
    return f"{host}:{session_id}"


def work_item_key(repo, feature, item):
    return f"{repo}:{feature}/{item}"


def start_session(connection, host, session_id, cwd, title=None, pid=None, pid_started_at=None, only_if_missing=False):
    handle = session_handle(host, session_id)
    machine = current_machine()
    profile = profile_directory(host)
    repo, branch, head = _collect_repo_branch_head(cwd)
    now = time.time()
    cursor = connection.execute(
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
            end_reason = NULL,
            role = CASE WHEN sessions.end_reason = 'handed_off' THEN NULL ELSE sessions.role END
        WHERE NOT ?
        """,
        (handle, host, session_id, machine, profile, title, str(cwd), repo, branch, head,
         pid, pid_started_at, now, now, only_if_missing),
    )
    changed = cursor.rowcount != 0
    connection.commit()
    if not changed:
        return None
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
    repo, branch, head = _collect_repo_branch_head(cwd) if cwd else (None, None, None)
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
    repo, branch, head = _collect_repo_branch_head(cwd)
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


def _end_session_locked(connection, handle, reason, successor=None):
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


def end_session(connection, handle, reason, successor=None):
    _end_session_locked(connection, handle, reason, successor=successor)
    connection.commit()


def reopen_session(connection, handle, reason):
    connection.execute(
        "UPDATE sessions SET ended_at = NULL, end_reason = NULL WHERE handle = ? AND end_reason = ?",
        (handle, reason),
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


def set_work_item_status(connection, key, status, pr=None, branch=None):
    connection.execute(
        """
        UPDATE work_items SET status = ?, pr = COALESCE(?, pr), branch = COALESCE(branch, ?), updated_at = ?
        WHERE key = ?
        """,
        (status, pr, branch, time.time(), key),
    )
    connection.commit()


def _set_session_ownership_locked(connection, handle, role, item, predecessor=None):
    connection.execute(
        "UPDATE sessions SET role = ?, work_item = ?, predecessor = COALESCE(?, predecessor) WHERE handle = ?",
        (role, item, predecessor, handle),
    )


def set_session_ownership(connection, handle, role, item, predecessor=None):
    _set_session_ownership_locked(connection, handle, role, item, predecessor=predecessor)
    connection.commit()


def _demote_other_owners_locked(connection, item, keep_handle):
    connection.execute(
        "UPDATE sessions SET role = NULL WHERE work_item = ? AND role = 'owner' AND handle != ?",
        (item, keep_handle),
    )


def claim_work_item(connection, handle, key, role, predecessor=None, branch=None):
    connection.execute("BEGIN IMMEDIATE")
    try:
        removed = None
        if role == "owner":
            others = [row for row in live_owners(connection, key) if row["handle"] != handle]
            if others:
                other = others[0]
                if predecessor and predecessor == other["handle"]:
                    _end_session_locked(connection, predecessor, "handed_off", successor=handle)
                    removed = predecessor
                else:
                    raise ValueError(
                        f"{other['handle']} already owns this work item; hand off before taking ownership"
                    )
            _demote_other_owners_locked(connection, key, handle)
        _set_session_ownership_locked(connection, handle, role, key, predecessor=predecessor)
        if role == "owner" and branch:
            connection.execute(
                "UPDATE work_items SET branch = COALESCE(branch, ?), updated_at = ? WHERE key = ?",
                (branch, time.time(), key),
            )
        connection.commit()
        return removed
    except Exception:
        connection.rollback()
        raise


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


def _valid_process_identity(pid, started_at):
    return (
        isinstance(pid, int)
        and not isinstance(pid, bool)
        and not isinstance(started_at, bool)
        and isinstance(started_at, (int, float))
        and math.isfinite(started_at)
    )


def _registry_path(session_id):
    return state_directory() / "cli-sessions" / f"{session_id}.json"


def _record_registry(registrar, host, session_id, payload, pid, pid_started_at):
    try:
        entry = registrar.record_registry(payload, pid, host, pid_started_at)
    except Exception:
        entry = None
    return (
        isinstance(entry, dict)
        and entry.get("session_id") == session_id
        and entry.get("host") == host
        and entry.get("pid") == pid
        and entry.get("pid_started_at") == pid_started_at
    )


def _resolve_recovery_identity(host, session_id):
    try:
        registrar = _register_session()
        pid, recorded_host, pid_started_at = registrar.resolve_recorded_pid(os.getppid())
    except Exception:
        registrar = None
        pid = recorded_host = pid_started_at = None
    if (
        registrar is None
        or recorded_host != host
        or not _valid_process_identity(pid, pid_started_at)
    ):
        print(f"session persistence: could not recover {host}:{session_id}", file=sys.stderr)
        return None
    return registrar, pid, pid_started_at


def _recover_missing_session(host, session_id, payload):
    identity = _resolve_recovery_identity(host, session_id)
    if identity is None:
        return False
    registrar, pid, pid_started_at = identity
    try:
        connection = connect()
    except Exception:
        print(f"session persistence: could not recover {host}:{session_id}", file=sys.stderr)
        return False
    try:
        title = os.environ.get(getattr(registrar, "TITLE_ENV", "AGENT_CLI_TAB_TITLE")) or None
        created = start_session(
            connection, host, session_id, payload.get("cwd") or os.getcwd(), title=title,
            pid=pid, pid_started_at=pid_started_at, only_if_missing=True,
        )
        row = get_session(connection, session_handle(host, session_id))
    finally:
        connection.close()
    if (
        row is None
        or row.get("host") != host
        or row.get("session_id") != session_id
        or row.get("pid") != pid
        or row.get("pid_started_at") != pid_started_at
    ):
        print(f"session persistence: could not recover {host}:{session_id}", file=sys.stderr)
        return False
    if created is None:
        return False
    if not _record_registry(registrar, host, session_id, payload, pid, pid_started_at):
        print(f"session persistence: could not recover {host}:{session_id}", file=sys.stderr)
        return False
    return True


def _recover_missing_registry(host, session_id, payload, row):
    identity = _resolve_recovery_identity(host, session_id)
    if identity is None:
        return False
    registrar, pid, pid_started_at = identity
    if (
        row.get("host") != host
        or row.get("session_id") != session_id
        or row.get("pid") != pid
        or row.get("pid_started_at") != pid_started_at
    ):
        print(f"session persistence: could not recover {host}:{session_id}", file=sys.stderr)
        return False
    if not _record_registry(registrar, host, session_id, payload, pid, pid_started_at):
        print(f"session persistence: could not recover {host}:{session_id}", file=sys.stderr)
        return False
    return True


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
    session_id = None
    try:
        payload = _read_json_stdin()
        session_id = payload.get("session_id") or payload.get("sessionId")
        if not isinstance(session_id, str) or not session_id:
            return 0
        cwd = payload.get("cwd") or os.getcwd()
        handle = session_handle(host, session_id)
        if event in ("prompt", "stop"):
            connection = connect()
            try:
                row = get_session(connection, handle)
            finally:
                connection.close()
            if row is None:
                if not _recover_missing_session(host, session_id, payload):
                    return 0
            elif (
                _valid_process_identity(row.get("pid"), row.get("pid_started_at"))
                and not _registry_path(session_id).is_file()
                and not _recover_missing_registry(host, session_id, payload, row)
            ):
                return 0
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
        label = f"{host}:{session_id}" if isinstance(session_id, str) and session_id else host
        print(f"session persistence: could not record {label}", file=sys.stderr)
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
