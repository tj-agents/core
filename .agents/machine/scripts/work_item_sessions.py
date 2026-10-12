#!/usr/bin/env python3
"""Claim, inspect and resume work-item sessions recorded in the central session store."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys

HERE = Path(__file__).resolve().parent
WORK_ITEM_RE = re.compile(r"^(?P<feature>[a-z0-9]+(?:-[a-z0-9]+)*)/(?P<item>[a-z0-9]+(?:-[a-z0-9]+)*)$")
WORK_ITEM_STATUSES = ("proposed", "active", "blocked", "paused", "delivery-gated", "done")
END_REASONS = ("finished", "closed", "handed_off")
HEAD_CHECK_TIMEOUT = 5

_SESSION_STORE = None
_AGENT_RECOVERY = None
_REGISTER_SESSION = None


def _session_store():
    global _SESSION_STORE
    if _SESSION_STORE is not None:
        return _SESSION_STORE
    candidate = HERE / "session_store.py"
    if candidate.is_file():
        spec = importlib.util.spec_from_file_location("work_item_sessions_session_store", candidate)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _SESSION_STORE = module
        return module
    raise RuntimeError(f"The shared session_store.py helper was not found relative to {HERE}.")


def _agent_recovery():
    global _AGENT_RECOVERY
    if _AGENT_RECOVERY is not None:
        return _AGENT_RECOVERY
    candidate = HERE / "agent_recovery.py"
    if candidate.is_file():
        spec = importlib.util.spec_from_file_location("work_item_sessions_agent_recovery", candidate)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _AGENT_RECOVERY = module
        return module
    raise RuntimeError(f"The shared agent_recovery.py helper was not found relative to {HERE}.")


def _register_session():
    global _REGISTER_SESSION
    if _REGISTER_SESSION is not None:
        return _REGISTER_SESSION
    peer = HERE.parent / "utility/peer-cli/scripts/register_session.py"
    packaged = tuple(
        HERE.parents[2] / layout / "peer-cli/scripts/register_session.py" for layout in ("skills", "codex-skills")
    ) if len(HERE.parents) > 2 else ()
    for path in (peer, *packaged):
        if path.is_file():
            spec = importlib.util.spec_from_file_location("work_item_sessions_register_session", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            _REGISTER_SESSION = module
            return module
    raise RuntimeError(f"The shared register_session.py helper was not found relative to {HERE}.")


def _parse_work_item(value):
    match = WORK_ITEM_RE.fullmatch(value)
    if not match:
        raise ValueError(f"invalid work item {value!r}; expected <feature>/<item> in lowercase kebab-case")
    return match.group("feature"), match.group("item")


def _require_repo(cwd):
    repo = _session_store().repo_identity(cwd)
    if not repo:
        raise ValueError(f"could not determine a git repository identity from {cwd}")
    return repo


def _current_session_id(host):
    variable = "CODEX_THREAD_ID" if host == "codex" else "CLAUDE_CODE_SESSION_ID"
    return os.environ.get(variable)


def _require_session_id(host):
    session_id = _current_session_id(host)
    if not session_id or not _agent_recovery().SESSION_ID.fullmatch(session_id):
        variable = "CODEX_THREAD_ID" if host == "codex" else "CLAUDE_CODE_SESSION_ID"
        raise ValueError(f"missing or invalid session id in {variable}")
    return session_id


def _path_key(value):
    try:
        return os.path.normcase(str(Path(value).resolve()))
    except OSError:
        return os.path.normcase(str(value))


def _head_is_ancestor(worktree, head):
    try:
        result = subprocess.run(
            ["git", "-C", str(worktree), "merge-base", "--is-ancestor", head, "HEAD"],
            capture_output=True, timeout=HEAD_CHECK_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode not in (0, 1):
        return None
    return result.returncode == 0


def _worktree_status(row):
    worktree = row.get("cwd")
    if not worktree or not Path(worktree).is_dir():
        return "stale"
    branch = _session_store()._git(worktree, "branch", "--show-current")
    if branch is None:
        return "unknown"
    if branch != row.get("branch"):
        return "stale"
    head = row.get("head")
    if not head:
        return "unknown"
    contains = _head_is_ancestor(worktree, head)
    if contains is None:
        return "unknown"
    return "live" if contains else "stale"


def _read_time_status(row, machine):
    if row.get("ended_at") is not None:
        return "closed"
    if (row.get("machine") or "").casefold() != machine.casefold():
        return "foreign"
    liveness = _agent_recovery().liveness({"host": row["host"], "session": row["session_id"]})
    if liveness != "live":
        return liveness
    return _worktree_status(row)


def _pid_is_dead(pid, pid_started_at):
    if not isinstance(pid, int) or pid_started_at is None:
        return False
    try:
        process = _register_session().build_process_lookup()(pid)
    except Exception:
        return False
    if process is None:
        return True
    started = getattr(process, "started_at", None)
    if started is None:
        return False
    return started != pid_started_at


def _resume_roots(row):
    host = row["host"]
    subdirectory = "projects" if host == "claude" else "sessions"
    return {host: Path(row["profile"]) / subdirectory}


def cmd_claim(work_item, host, role=None, predecessor=None, cwd=None):
    store = _session_store()
    cwd = cwd or Path.cwd()
    feature, item = _parse_work_item(work_item)
    repo = _require_repo(cwd)
    key = store.work_item_key(repo, feature, item)
    session_id = _require_session_id(host)
    handle = store.session_handle(host, session_id)
    role = role or "owner"
    branch, _head = store.current_branch_and_head(cwd)
    connection = store.connect()
    try:
        store.ensure_session(connection, host, session_id, cwd)
        if store.get_work_item(connection, key) is None:
            store.upsert_work_item(connection, key, repo, feature, item, status="active", branch=branch)
        result = {"handle": handle, "work_item": f"{feature}/{item}"}
        if role == "owner":
            others = [row for row in store.live_owners(connection, key) if row["handle"] != handle]
            if others:
                other = others[0]
                if predecessor and predecessor == other["handle"]:
                    store.transfer_ownership(connection, predecessor, handle, key, role=role)
                    result["removed"] = predecessor
                    return result
                raise ValueError(f"{other['handle']} already owns this work item; hand off before taking ownership")
        store.set_session_ownership(connection, handle, role, key, predecessor=predecessor)
        return result
    finally:
        connection.close()


def cmd_status(work_item, cwd=None):
    store = _session_store()
    feature, item = _parse_work_item(work_item)
    repo = _require_repo(cwd or Path.cwd())
    key = store.work_item_key(repo, feature, item)
    connection = store.connect()
    try:
        item_row = store.get_work_item(connection, key)
        rows = store.sessions_for_work_item(connection, key)
    finally:
        connection.close()
    machine = socket.gethostname()
    sessions = [
        {
            "handle": row["handle"],
            "role": row["role"],
            "turn_state": row["turn_state"],
            "ended": row["ended_at"] is not None,
            "status": _read_time_status(row, machine),
        }
        for row in rows
    ]
    return {
        "work_item": f"{feature}/{item}",
        "status": item_row["status"] if item_row else None,
        "sessions": sessions,
    }


def cmd_find(worktree):
    store = _session_store()
    target = _path_key(worktree)
    connection = store.connect()
    try:
        rows = connection.execute("SELECT * FROM sessions WHERE work_item IS NOT NULL").fetchall()
        matches = []
        for row in rows:
            if row["cwd"] and _path_key(row["cwd"]) == target:
                item_row = store.get_work_item(connection, row["work_item"])
                if item_row:
                    matches.append({
                        "work_item": f"{item_row['feature']}/{item_row['item']}",
                        "handle": row["handle"],
                        "role": row["role"],
                    })
    finally:
        connection.close()
    return {"matches": matches}


def cmd_resume(work_item, handle=None, cwd=None, prompt=None, prompt_path=None, title=None):
    store = _session_store()
    feature, item = _parse_work_item(work_item)
    repo = _require_repo(cwd or Path.cwd())
    key = store.work_item_key(repo, feature, item)
    connection = store.connect()
    try:
        rows = store.sessions_for_work_item(connection, key)
    finally:
        connection.close()
    if not rows:
        raise ValueError("no recorded session; start a new owner from the work item README's ## Next Steps")
    if handle:
        matched = [row for row in rows if row["handle"] == handle]
        if not matched:
            raise ValueError(f"no recorded session with handle {handle!r}")
        selected = matched[0]
    else:
        owners = [row for row in rows if row["role"] == "owner" and row["ended_at"] is None]
        if len(owners) != 1:
            raise ValueError("specify --handle; recorded sessions: " + ", ".join(row["handle"] for row in rows))
        selected = owners[0]
    machine = socket.gethostname()
    status = _read_time_status(selected, machine)
    if status != "closed":
        raise ValueError(f"{selected['handle']}: {status}; reconcile before resuming")
    recovery = _agent_recovery()
    roots = _resume_roots(selected)
    if prompt_path:
        return recovery.open_session(
            selected["host"], selected["session_id"], prompt=None, title=title, roots=roots, prompt_path=prompt_path,
        )
    return recovery.open_session(
        selected["host"], selected["session_id"], prompt=prompt or "Continue the requested work.",
        title=title, roots=roots,
    )


def cmd_interrupted(resume_handles=None, cwd=None):
    store = _session_store()
    repo = _require_repo(cwd or Path.cwd())
    connection = store.connect()
    try:
        candidates = store.interrupted_candidates(connection, repo=repo)
        item_names = {}
        for row in candidates:
            if row["work_item"] and row["work_item"] not in item_names:
                item_row = store.get_work_item(connection, row["work_item"])
                item_names[row["work_item"]] = f"{item_row['feature']}/{item_row['item']}" if item_row else row["work_item"]
    finally:
        connection.close()
    machine = socket.gethostname()
    dead = [
        row for row in candidates
        if (row.get("machine") or "").casefold() == machine.casefold()
        and _pid_is_dead(row.get("pid"), row.get("pid_started_at"))
    ]
    grouped = {}
    for row in dead:
        label = item_names.get(row["work_item"], "(unclaimed)")
        grouped.setdefault(label, []).append({"handle": row["handle"], "turn_state": row["turn_state"]})
    result = {"interrupted": grouped}
    if resume_handles:
        by_handle = {row["handle"]: row for row in dead}
        for handle in resume_handles:
            if handle not in by_handle:
                raise ValueError(f"{handle!r} is not a listed interrupted session")
        recovery = _agent_recovery()
        resumed = []
        for handle in resume_handles:
            row = by_handle[handle]
            resumed.append(recovery.open_session(
                row["host"], row["session_id"], prompt="Continue the requested work.", roots=_resume_roots(row),
            ))
        result["resumed"] = resumed
    return result


def cmd_end(host, reason, successor=None):
    store = _session_store()
    session_id = _require_session_id(host)
    handle = store.session_handle(host, session_id)
    connection = store.connect()
    try:
        store.end_session(connection, handle, reason, successor=successor)
    finally:
        connection.close()
    return {"handle": handle, "reason": reason}


def cmd_item(work_item, status, pr=None, cwd=None):
    store = _session_store()
    feature, item = _parse_work_item(work_item)
    cwd = cwd or Path.cwd()
    repo = _require_repo(cwd)
    key = store.work_item_key(repo, feature, item)
    connection = store.connect()
    try:
        if store.get_work_item(connection, key) is None:
            branch, _head = store.current_branch_and_head(cwd)
            store.upsert_work_item(connection, key, repo, feature, item, status=status, branch=branch, pr=pr)
        else:
            store.set_work_item_status(connection, key, status, pr=pr)
    finally:
        connection.close()
    return {"work_item": f"{feature}/{item}", "status": status}


def _build_parser():
    parser = argparse.ArgumentParser(
        description="Claim, inspect and resume work-item sessions recorded in the central session store.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    claim_parser = subparsers.add_parser("claim")
    claim_parser.add_argument("work_item")
    claim_parser.add_argument("--host", required=True, choices=("claude", "codex"))
    claim_parser.add_argument("--role", default="owner")
    claim_parser.add_argument("--predecessor")

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("work_item")

    find_parser = subparsers.add_parser("find")
    find_parser.add_argument("--worktree", required=True)

    resume_parser = subparsers.add_parser("resume")
    resume_parser.add_argument("work_item")
    resume_parser.add_argument("--handle")
    prompt_group = resume_parser.add_mutually_exclusive_group()
    prompt_group.add_argument("--prompt")
    prompt_group.add_argument("--prompt-path")
    resume_parser.add_argument("--title")

    interrupted_parser = subparsers.add_parser("interrupted")
    interrupted_parser.add_argument("--resume", dest="resume_handles", action="append", default=[])

    end_parser = subparsers.add_parser("end")
    end_parser.add_argument("--host", required=True, choices=("claude", "codex"))
    end_parser.add_argument("--reason", required=True, choices=END_REASONS)
    end_parser.add_argument("--successor")

    item_parser = subparsers.add_parser("item")
    item_parser.add_argument("work_item")
    item_parser.add_argument("--status", required=True, choices=WORK_ITEM_STATUSES)
    item_parser.add_argument("--pr")

    return parser


def main(argv=None):
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "claim":
            result = cmd_claim(args.work_item, args.host, role=args.role, predecessor=args.predecessor)
        elif args.command == "status":
            result = cmd_status(args.work_item)
        elif args.command == "find":
            result = cmd_find(args.worktree)
        elif args.command == "resume":
            result = cmd_resume(
                args.work_item, handle=args.handle, prompt=args.prompt,
                prompt_path=args.prompt_path, title=args.title,
            )
        elif args.command == "interrupted":
            result = cmd_interrupted(resume_handles=args.resume_handles)
        elif args.command == "end":
            result = cmd_end(args.host, args.reason, successor=args.successor)
        elif args.command == "item":
            result = cmd_item(args.work_item, args.status, pr=args.pr)
        else:
            raise ValueError(f"Unknown command: {args.command}")
    except (ValueError, RuntimeError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    print(json.dumps(result, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
