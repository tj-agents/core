#!/usr/bin/env python3
"""Claim, inspect and resume work-item sessions recorded in the central session store."""

import argparse
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import socket
import subprocess
import sys

HERE = Path(__file__).resolve().parent
WORK_ITEM_RE = re.compile(r"^(?P<feature>[a-z0-9]+(?:-[a-z0-9]+)*)/(?P<item>[a-z0-9]+(?:-[a-z0-9]+)*)$")
WORK_ITEM_STATUSES = ("proposed", "active", "blocked", "paused", "delivery-gated", "done")
END_REASONS = ("finished", "closed", "handed_off")
HEAD_CHECK_TIMEOUT = 5
_BOUNDED_ROLE_RE = re.compile(r"^bounded: (?P<scope>.+)$")

_SESSION_STORE = None
_AGENT_RECOVERY = None
_REGISTER_SESSION = None
_SESSION_CLOSE = None


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


def _peer_cli_script(name):
    peer = HERE.parent / "utility/peer-cli/scripts" / f"{name}.py"
    packaged = tuple(
        HERE.parents[2] / layout / "peer-cli/scripts" / f"{name}.py"
        for layout in ("skills", "codex-skills")
    ) if len(HERE.parents) > 2 else ()
    for candidate in (peer, *packaged):
        if candidate.is_file():
            return candidate
    raise RuntimeError(f"The shared {name}.py helper was not found relative to {HERE}.")


def _register_session():
    global _REGISTER_SESSION
    if _REGISTER_SESSION is not None:
        return _REGISTER_SESSION
    candidate = _peer_cli_script("register_session")
    spec = importlib.util.spec_from_file_location("work_item_sessions_register_session", candidate)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _REGISTER_SESSION = module
    return module


def _session_close():
    global _SESSION_CLOSE
    if _SESSION_CLOSE is not None:
        return _SESSION_CLOSE
    candidate = _peer_cli_script("session_close")
    parent = str(candidate.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    spec = importlib.util.spec_from_file_location("work_item_sessions_session_close", candidate)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _SESSION_CLOSE = module
    return module


def _parse_work_item(value):
    match = WORK_ITEM_RE.fullmatch(value)
    if not match:
        raise ValueError(f"invalid work item {value!r}; expected <feature>/<item> in lowercase kebab-case")
    return match.group("feature"), match.group("item")


def _validate_role(role):
    if role is None or role == "owner":
        return "owner"
    match = _BOUNDED_ROLE_RE.fullmatch(role)
    if match and match.group("scope").strip():
        return role
    raise ValueError(f"invalid --role {role!r}; expected 'owner' or 'bounded: <non-empty scope>'")


def _default_branch(cwd, current_branch):
    output = _session_store()._git(cwd, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if output:
        return output.split("/", 1)[1] if output.startswith("origin/") else output
    if current_branch in ("main", "master"):
        return current_branch
    return None


def _branch_to_record(cwd, branch):
    if not branch:
        return None
    return None if branch == _default_branch(cwd, branch) else branch


def _require_repo(cwd):
    repo = _session_store().repo_identity(cwd)
    if not repo:
        raise ValueError(f"could not determine a git repository identity from {cwd}")
    return repo


def _require_repo_branch_head(cwd):
    store = _session_store()
    repo, branch, head = store._collect_repo_branch_head(cwd, timeout=store.GIT_TIMEOUT)
    if not repo:
        raise ValueError(f"could not determine a git repository identity from {cwd}")
    return repo, branch, head


def _repository_root(cwd):
    root = _session_store()._git(cwd, "rev-parse", "--show-toplevel")
    if not root:
        raise ValueError(f"could not determine the repository root from {cwd}")
    return Path(root).resolve()


def _validate_title(title):
    if title is None:
        return None
    if not isinstance(title, str) or not title.strip():
        raise ValueError("--title must be non-empty")
    return title.strip()


def _validate_plan_path(plan_path, cwd):
    if plan_path is None:
        return None
    if not isinstance(plan_path, str) or not plan_path.strip():
        raise ValueError("--plan-path must be a non-empty repository-relative path")
    value = plan_path.strip()
    if "\\" in value or value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise ValueError("--plan-path must be a repository-relative '/' path")
    path = PurePosixPath(value)
    if not path.parts or any(part in (".", "..") for part in path.parts):
        raise ValueError("--plan-path must not traverse outside the repository")
    root = _repository_root(cwd)
    target = root.joinpath(*path.parts)
    try:
        resolved = target.resolve(strict=True)
    except OSError as error:
        raise ValueError(f"--plan-path does not name an existing repository file: {value}") from error
    if not resolved.is_file() or not resolved.is_relative_to(root):
        raise ValueError("--plan-path must name an existing file inside the repository")
    return path.as_posix()


def _current_session_id(host):
    variable = "CODEX_THREAD_ID" if host == "codex" else "CLAUDE_CODE_SESSION_ID"
    return os.environ.get(variable)


def _require_session_id(host):
    session_id = _current_session_id(host)
    if not session_id or not _agent_recovery().SESSION_ID.fullmatch(session_id):
        variable = "CODEX_THREAD_ID" if host == "codex" else "CLAUDE_CODE_SESSION_ID"
        raise ValueError(f"missing or invalid session id in {variable}")
    return session_id


def _registered_current_session(connection, host, cwd):
    session_id = _current_session_id(host)
    if session_id and _agent_recovery().SESSION_ID.fullmatch(session_id):
        handle = _session_store().session_handle(host, session_id)
        session = _session_store().get_session(connection, handle)
        if session is not None and session["pid"] is not None and session["pid_started_at"] is not None:
            return session_id, None
    try:
        entry = _session_close().own_host_and_entry(cwd)
    except Exception as error:
        raise ValueError(f"could not verify the current native {host} session: {error}") from error
    if entry.get("host") != host:
        raise ValueError(f"the verified current native session is {entry.get('host')!r}, not {host!r}")
    registered_id = entry.get("session_id")
    if not isinstance(registered_id, str) or not _agent_recovery().SESSION_ID.fullmatch(registered_id):
        raise ValueError("the verified native session has no valid session id")
    if session_id and session_id != registered_id:
        raise ValueError("the native session id does not match the verified registry attachment")
    return registered_id, entry


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
    if (row.get("machine") or "").casefold() != machine.casefold():
        return "foreign"
    ended = row.get("ended_at") is not None
    if not ended:
        liveness = _agent_recovery().liveness({"host": row["host"], "session": row["session_id"]})
        if liveness == "live":
            return "live"
        if liveness == "unknown":
            return "unknown"
    if ended and row.get("end_reason") in ("finished", "handed_off"):
        return row["end_reason"]
    worktree = _worktree_status(row)
    return worktree if worktree in ("stale", "unknown") else "closed"


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


def cmd_claim(work_item, host, role=None, predecessor=None, status=None, title=None, plan_path=None, cwd=None):
    store = _session_store()
    cwd = cwd or Path.cwd()
    feature, item = _parse_work_item(work_item)
    role = _validate_role(role)
    title = _validate_title(title)
    plan_path = _validate_plan_path(plan_path, cwd)
    repo, branch, head = _require_repo_branch_head(cwd)
    key = store.work_item_key(repo, feature, item)
    record_branch = _branch_to_record(cwd, branch)
    connection = store.connect()
    try:
        session_id, registration = _registered_current_session(connection, host, cwd)
        handle = store.session_handle(host, session_id)
        result = {"handle": handle, "work_item": f"{feature}/{item}"}
        removed = store.claim_registered_work_item(
            connection, host, session_id, cwd, key, repo, feature, item, role,
            status=status, branch=record_branch, session_branch=branch, head=head,
            title=title, plan_path=plan_path,
            predecessor=predecessor, registration=registration,
        )
        if removed:
            result["removed"] = removed
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
        "title": item_row["title"] if item_row else None,
        "plan_path": item_row["plan_path"] if item_row else None,
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
        owners = [
            row for row in rows
            if row["role"] == "owner" and (row["ended_at"] is None or row["end_reason"] == "closed")
        ]
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
    statuses = {row["handle"]: _read_time_status(row, machine) for row in dead}
    grouped = {}
    for row in dead:
        label = item_names.get(row["work_item"], "(unclaimed)")
        grouped.setdefault(label, []).append(
            {"handle": row["handle"], "turn_state": row["turn_state"], "status": statuses[row["handle"]]}
        )
    result = {"interrupted": grouped}
    if resume_handles:
        by_handle = {row["handle"]: row for row in dead}
        for handle in resume_handles:
            if handle not in by_handle:
                raise ValueError(f"{handle!r} is not a listed interrupted session")
            status = statuses[handle]
            if status != "closed":
                raise ValueError(f"{handle}: {status}; resume only a session confirmed closed on this machine")
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


def cmd_item(work_item, status, pr=None, title=None, plan_path=None, cwd=None):
    store = _session_store()
    feature, item = _parse_work_item(work_item)
    cwd = cwd or Path.cwd()
    title = _validate_title(title)
    plan_path = _validate_plan_path(plan_path, cwd)
    repo, branch, _head = _require_repo_branch_head(cwd)
    record_branch = _branch_to_record(cwd, branch)
    key = store.work_item_key(repo, feature, item)
    connection = store.connect()
    try:
        if store.get_work_item(connection, key) is None:
            if title is None:
                raise ValueError("a non-empty --title is required when creating a work item")
            store.upsert_work_item(
                connection, key, repo, feature, item, status=status, branch=record_branch, pr=pr,
                title=title, plan_path=plan_path,
            )
        else:
            store.upsert_work_item(
                connection, key, repo, feature, item, status=status, branch=record_branch, pr=pr,
                title=title, plan_path=plan_path,
            )
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
    claim_parser.add_argument("--status", choices=WORK_ITEM_STATUSES)
    claim_parser.add_argument("--title")
    claim_parser.add_argument("--plan-path")

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
    item_parser.add_argument("--title")
    item_parser.add_argument("--plan-path")

    return parser


def main(argv=None):
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "claim":
            result = cmd_claim(
                args.work_item, args.host, role=args.role, predecessor=args.predecessor,
                status=args.status, title=args.title, plan_path=args.plan_path,
            )
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
            result = cmd_item(
                args.work_item, args.status, pr=args.pr, title=args.title, plan_path=args.plan_path,
            )
        else:
            raise ValueError(f"Unknown command: {args.command}")
    except (ValueError, RuntimeError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    print(json.dumps(result, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
