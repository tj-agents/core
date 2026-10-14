#!/usr/bin/env python3
"""Claim, inspect and resume work-item sessions recorded in the central session store."""

import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
WORK_ITEM_RE = re.compile(r"^(?P<feature>[a-z0-9]+(?:-[a-z0-9]+)*)/(?P<item>[a-z0-9]+(?:-[a-z0-9]+)*)$")
WORK_ITEM_STATUSES = ("proposed", "active", "blocked", "paused", "delivery-gated", "done")
END_REASONS = ("finished", "closed", "handed_off")
HEAD_CHECK_TIMEOUT = 5
BULK_REGISTRATION_TIMEOUT = 15
BULK_REGISTRATION_INTERVAL = 0.25
_BOUNDED_ROLE_RE = re.compile(r"^bounded: (?P<scope>.+)$")

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
    if row.get("repo") is None and row.get("branch") is None and row.get("head") is None:
        return "live"
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
    if not isinstance(pid, int) or isinstance(pid, bool) or not isinstance(pid_started_at, (int, float)) or isinstance(pid_started_at, bool):
        return False
    if not math.isfinite(pid_started_at):
        return False
    try:
        process = _register_session().build_process_lookup()(pid)
    except Exception:
        return False
    if process is None:
        return True
    started = getattr(process, "started_at", None)
    if isinstance(started, bool) or not isinstance(started, (int, float)) or not math.isfinite(started):
        return False
    return started != pid_started_at


def _pid_is_live(pid, pid_started_at):
    if not isinstance(pid, int) or isinstance(pid, bool) or isinstance(pid_started_at, bool) or not isinstance(pid_started_at, (int, float)):
        return False
    if not math.isfinite(pid_started_at):
        return False
    try:
        process = _register_session().build_process_lookup()(pid)
    except Exception:
        return False
    if process is None:
        return False
    started = getattr(process, "started_at", None)
    return isinstance(started, (int, float)) and not isinstance(started, bool) and started == pid_started_at


def _started_after(value, previous):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return False
    if previous is None:
        return True
    return value > previous


def _wait_for_fresh_registration(handle, previous_started_at, timeout=BULK_REGISTRATION_TIMEOUT,
                                 interval=BULK_REGISTRATION_INTERVAL, clock=time.monotonic, wait=time.sleep):
    deadline = clock() + timeout
    while True:
        connection = _session_store().connect()
        try:
            row = _session_store().get_session(connection, handle)
        finally:
            connection.close()
        if row and _started_after(row.get("started_at"), previous_started_at) and _pid_is_live(
            row.get("pid"), row.get("pid_started_at"),
        ):
            return row
        remaining = deadline - clock()
        if remaining <= 0:
            return None
        wait(min(interval, remaining))


def _resume_roots(row):
    host = row["host"]
    subdirectory = "projects" if host == "claude" else "sessions"
    return {host: Path(row["profile"]) / subdirectory}


def cmd_claim(work_item, host, role=None, predecessor=None, cwd=None):
    store = _session_store()
    cwd = cwd or Path.cwd()
    feature, item = _parse_work_item(work_item)
    role = _validate_role(role)
    repo, branch, _head = _require_repo_branch_head(cwd)
    key = store.work_item_key(repo, feature, item)
    session_id = _require_session_id(host)
    handle = store.session_handle(host, session_id)
    record_branch = _branch_to_record(cwd, branch)
    connection = store.connect()
    try:
        store.ensure_session(connection, host, session_id, cwd)
        if store.get_work_item(connection, key) is None:
            store.upsert_work_item(connection, key, repo, feature, item, status="active", branch=record_branch)
        result = {"handle": handle, "work_item": f"{feature}/{item}"}
        removed = store.claim_work_item(connection, handle, key, role, predecessor=predecessor, branch=record_branch)
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


def _interrupted_rows(all_repos, cwd):
    store = _session_store()
    repo = None if all_repos else _require_repo(cwd or Path.cwd())
    connection = store.connect()
    try:
        if repo is None:
            rows = connection.execute("SELECT * FROM sessions ORDER BY handle").fetchall()
        else:
            rows = connection.execute("SELECT * FROM sessions WHERE repo = ? ORDER BY handle", (repo,)).fetchall()
        item_names = {}
        item_statuses = {}
        for row in rows:
            if row["work_item"] and row["work_item"] not in item_names:
                item_row = store.get_work_item(connection, row["work_item"])
                item_names[row["work_item"]] = f"{item_row['feature']}/{item_row['item']}" if item_row else row["work_item"]
                item_statuses[row["work_item"]] = item_row["status"] if item_row else None
    finally:
        connection.close()
    return [dict(row) for row in rows], item_names, item_statuses


def _bulk_skip_reason(row, machine, recovery, item_statuses):
    if row.get("ended_at") is not None:
        return "ended"
    if (row.get("machine") or "").casefold() != machine.casefold():
        return "foreign"
    if item_statuses.get(row.get("work_item")) == "done":
        return "done"
    if not _pid_is_dead(row.get("pid"), row.get("pid_started_at")):
        return "live"
    if recovery.liveness({"host": row["host"], "session": row["session_id"]}) != "closed":
        return "unknown"
    worktree = _worktree_status(row)
    if worktree != "live":
        return worktree
    return None


def _is_pending_launch(error):
    return "pending or ambiguous" in str(error).casefold() or type(error).__name__ == "LaunchTimeout"


def _resume_all(rows, item_statuses, machine):
    recovery = _agent_recovery()
    outcomes = []
    failed = False
    for row in rows:
        try:
            skip = _bulk_skip_reason(row, machine, recovery, item_statuses)
        except Exception as error:
            outcomes.append({"handle": row["handle"], "outcome": "failed", "reason": str(error)})
            failed = True
            continue
        if skip:
            outcomes.append({"handle": row["handle"], "outcome": "skipped", "reason": skip})
            continue
        previous_started_at = row.get("started_at")
        try:
            launched = recovery.open_session(
                row["host"], row["session_id"], prompt="Continue the requested work.", roots=_resume_roots(row),
                refresh_plugins=False,
            )
        except Exception as error:
            if _is_pending_launch(error):
                outcomes.append({"handle": row["handle"], "outcome": "pending", "reason": str(error)})
            elif "verified live" in str(error).casefold():
                outcomes.append({"handle": row["handle"], "outcome": "skipped", "reason": "live"})
            else:
                outcomes.append({"handle": row["handle"], "outcome": "failed", "reason": str(error)})
            failed = failed or outcomes[-1]["outcome"] != "skipped"
            continue
        try:
            registered = _wait_for_fresh_registration(row["handle"], previous_started_at)
        except Exception as error:
            outcomes.append({"handle": row["handle"], "outcome": "pending", "reason": str(error), "launch": launched})
            failed = True
            continue
        if registered is None:
            outcomes.append({"handle": row["handle"], "outcome": "pending", "launch": launched})
            failed = True
        else:
            outcomes.append({"handle": row["handle"], "outcome": "resumed", "launch": launched})
    return outcomes, failed


def cmd_interrupted(resume_handles=None, resume_all=False, all_repos=False, cwd=None):
    rows, item_names, item_statuses = _interrupted_rows(all_repos, cwd)
    machine = socket.gethostname()
    dead = [
        row for row in rows
        if row.get("ended_at") is None
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
    if resume_all:
        outcomes, failed = _resume_all(rows, item_statuses, machine)
        result["bulk"] = outcomes
        result["bulk_failed"] = failed
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
    repo, branch, _head = _require_repo_branch_head(cwd)
    record_branch = _branch_to_record(cwd, branch)
    key = store.work_item_key(repo, feature, item)
    connection = store.connect()
    try:
        if store.get_work_item(connection, key) is None:
            store.upsert_work_item(connection, key, repo, feature, item, status=status, branch=record_branch, pr=pr)
        else:
            store.set_work_item_status(connection, key, status, pr=pr, branch=record_branch)
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
    interrupted_parser.add_argument("--all-repos", action="store_true")
    interrupted_resume = interrupted_parser.add_mutually_exclusive_group()
    interrupted_resume.add_argument("--resume", dest="resume_handles", action="append", default=[])
    interrupted_resume.add_argument("--resume-all", action="store_true")

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
            result = cmd_interrupted(
                resume_handles=args.resume_handles, resume_all=args.resume_all, all_repos=args.all_repos,
            )
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
    return 1 if args.command == "interrupted" and args.resume_all and result.get("bulk_failed") else 0


if __name__ == "__main__":
    sys.exit(main())
