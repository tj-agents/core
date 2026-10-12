#!/usr/bin/env python3
import argparse
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import socket
import subprocess
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
HEADER = "# Active sessions"
FIELDS = (
    "Role", "State", "Machine", "Profile", "Title", "Worktree", "Branch",
    "PR", "Head", "Predecessor", "Successor", "Verified", "Resume",
)
FIELD_LINE = re.compile(r"^- ([A-Za-z]+): (.*)$")
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")
VERIFIED_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
GIT_TIMEOUT = 15

_AGENT_RECOVERY = None


class SessionError(ValueError):
    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


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


def _valid_handle(value):
    host, separator, session_id = value.partition(":")
    if not separator or host not in ("claude", "codex") or not session_id:
        return False
    return bool(_agent_recovery().SESSION_ID.fullmatch(session_id))


def _resume_command(host, session_id):
    if host == "claude":
        return f"`machine:open-claude --resume {session_id}`"
    if host == "codex":
        return f"`machine:open-codex --id {session_id}`"
    raise ValueError(f"Unsupported host: {host}")


def _is_absolute_path(value):
    return PureWindowsPath(value).is_absolute() or PurePosixPath(value).is_absolute()


def _valid_https_url(value):
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sessions_path(work_item_dir):
    return Path(work_item_dir) / "ACTIVE_SESSIONS.md"


def _split_sections(text):
    lines = text.split("\n")
    errors = []
    index = 0
    while index < len(lines) and lines[index].strip() == "":
        index += 1
    if index >= len(lines) or lines[index].rstrip("\r") != HEADER:
        errors.append(f"file must start with '{HEADER}'")
        return [], errors
    index += 1
    sections = []
    current_handle = None
    current_pairs = None
    for line_number in range(index, len(lines)):
        line = lines[line_number].rstrip("\r")
        if line.startswith("## "):
            if current_handle is not None:
                sections.append((current_handle, current_pairs))
            current_handle = line[3:].strip()
            current_pairs = []
        elif line.strip() == "":
            continue
        else:
            match = FIELD_LINE.match(line)
            if not match:
                errors.append(f"line {line_number + 1}: malformed line: {line!r}")
                continue
            if current_handle is None:
                errors.append(f"line {line_number + 1}: field line before any session heading")
                continue
            current_pairs.append((match.group(1), match.group(2)))
    if current_handle is not None:
        sections.append((current_handle, current_pairs))
    return sections, errors


def _dedupe_fields(handle, pairs):
    errors = []
    fields = {}
    for name, value in pairs:
        if name not in FIELDS:
            errors.append(f"{handle}: unknown field {name!r}")
            continue
        if name in fields:
            errors.append(f"{handle}: duplicate field {name!r}")
            continue
        fields[name] = value
    return fields, errors


def parse(text):
    sections, errors = _split_sections(text)
    records = []
    for handle, pairs in sections:
        fields, field_errors = _dedupe_fields(handle, pairs)
        errors.extend(field_errors)
        records.append((handle, fields))
    return records, errors


def validate(records):
    errors = []
    seen = set()
    owners = []
    for handle, fields in records:
        if not _valid_handle(handle):
            errors.append(f"invalid session handle: {handle!r}")
        if handle in seen:
            errors.append(f"duplicate session handle: {handle!r}")
        seen.add(handle)
        missing = [name for name in FIELDS if name not in fields]
        unknown = [name for name in fields if name not in FIELDS]
        for name in missing:
            errors.append(f"{handle}: missing field {name!r}")
        for name in unknown:
            errors.append(f"{handle}: unknown field {name!r}")
        if missing or unknown:
            continue
        role = fields["Role"]
        if role != "owner" and not (role.startswith("bounded: ") and role[len("bounded: "):].strip()):
            errors.append(f"{handle}: invalid Role {role!r}")
        elif role == "owner":
            owners.append(handle)
        if fields["State"] not in ("active", "handing-off"):
            errors.append(f"{handle}: invalid State {fields['State']!r}")
        if not _is_absolute_path(fields["Worktree"]):
            errors.append(f"{handle}: Worktree must be absolute: {fields['Worktree']!r}")
        pr = fields["PR"]
        if pr != "not opened" and not _valid_https_url(pr):
            errors.append(f"{handle}: invalid PR {pr!r}")
        if not HEAD_RE.match(fields["Head"]):
            errors.append(f"{handle}: invalid Head {fields['Head']!r}")
        for name in ("Predecessor", "Successor"):
            value = fields[name]
            if value != "none" and not _valid_handle(value):
                errors.append(f"{handle}: invalid {name} {value!r}")
        if not VERIFIED_RE.match(fields["Verified"]):
            errors.append(f"{handle}: invalid Verified {fields['Verified']!r}")
        if _valid_handle(handle):
            host, _, session_id = handle.partition(":")
            if fields["Resume"] != _resume_command(host, session_id):
                errors.append(f"{handle}: invalid Resume {fields['Resume']!r}")
    if len(owners) > 1:
        errors.append("multiple owner rows: " + ", ".join(owners))
    return errors


def render(sessions):
    lines = [HEADER, ""]
    for index, (handle, fields) in enumerate(sessions):
        lines.append(f"## {handle}")
        lines.extend(f"- {name}: {fields[name]}" for name in FIELDS)
        if index != len(sessions) - 1:
            lines.append("")
    return "\n".join(lines) + "\n"


def validate_text(text):
    records, errors = parse(text)
    errors = list(errors) + validate(records)
    handles = [handle for handle, _ in records]
    return not errors, errors, handles


def load(work_item_dir):
    path = sessions_path(work_item_dir)
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    valid, errors, _ = validate_text(text)
    if not valid:
        raise SessionError(errors)
    records, _ = parse(text)
    return [(handle, {name: fields[name] for name in FIELDS}) for handle, fields in records]


def write(work_item_dir, sessions):
    path = sessions_path(work_item_dir)
    if not sessions:
        if path.is_file():
            path.unlink()
        return
    path.write_bytes(render(sessions).encode("utf-8"))


def _run_git(cwd, *args):
    try:
        completed = subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True, encoding="utf-8", timeout=GIT_TIMEOUT, shell=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def _current_session_id(host):
    variable = "CODEX_THREAD_ID" if host == "codex" else "CLAUDE_CODE_SESSION_ID"
    return os.environ.get(variable)


def _profile_dir(host):
    if host == "claude":
        value = os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")
    else:
        value = os.environ.get("CODEX_HOME") or str(Path.home() / ".codex")
    return str(Path(value))


def stale_reasons(fields):
    worktree = Path(fields["Worktree"])
    if not worktree.is_dir():
        return ["worktree-missing"]
    reasons = []
    branch = _run_git(worktree, "branch", "--show-current")
    if branch is None:
        reasons.append("branch-unknown")
    elif branch != fields["Branch"]:
        reasons.append("branch-mismatch")
    head = _run_git(worktree, "rev-parse", "HEAD")
    if head is None:
        reasons.append("head-unknown")
    elif head != fields["Head"]:
        reasons.append("head-mismatch")
    return reasons


def cmd_validate(work_item_dir):
    path = sessions_path(work_item_dir)
    if not path.is_file():
        return {"valid": True, "errors": [], "sessions": []}
    valid, errors, handles = validate_text(path.read_text(encoding="utf-8"))
    return {"valid": valid, "errors": errors, "sessions": handles}


def cmd_status(work_item_dir):
    result = cmd_validate(work_item_dir)
    if not result["valid"]:
        return result
    records = load(work_item_dir)
    recovery = _agent_recovery()
    machine = socket.gethostname()
    rows = []
    for handle, fields in records:
        host, _, session_id = handle.partition(":")
        foreign = fields["Machine"].casefold() != machine.casefold()
        if foreign:
            liveness = "foreign"
            stale = []
        else:
            liveness = recovery.liveness({"host": host, "session": session_id})
            stale = stale_reasons(fields)
        rows.append({
            "handle": handle, "role": fields["Role"], "state": fields["State"],
            "liveness": liveness, "stale": stale, "resume": fields["Resume"],
        })
    return {"valid": True, "errors": [], "sessions": rows}


def cmd_find(worktree, roots):
    target = os.path.normcase(os.path.abspath(str(worktree)))
    matches = []
    invalid = []
    for root in roots:
        for path in sorted(Path(root).glob("plans/features/*/work-items/*/ACTIVE_SESSIONS.md")):
            work_item_dir = path.parent
            try:
                records = load(work_item_dir)
            except SessionError as error:
                invalid.append({"path": str(path), "errors": error.errors})
                continue
            feature = work_item_dir.parent.parent.name
            item = work_item_dir.name
            for handle, fields in records:
                if os.path.normcase(os.path.abspath(fields["Worktree"])) == target:
                    matches.append({
                        "work_item": f"{feature}/{item}", "path": str(path),
                        "handle": handle, "role": fields["Role"],
                    })
    return {"matches": matches, "invalid": invalid}


def resume(work_item_dir, handle=None, prompt=None, prompt_path=None, confirm_closed=False, title=None):
    records = load(work_item_dir)
    if not records:
        raise ValueError("no recorded session; start a new owner from the work item README's ## Next Steps")
    if handle:
        matched = [record for record in records if record[0] == handle]
        if not matched:
            raise ValueError(f"no recorded session with handle {handle!r}")
        selected = matched[0]
    else:
        owners = [record for record in records if record[1]["Role"] == "owner"]
        if len(owners) != 1:
            raise ValueError("specify --handle; recorded sessions: " + ", ".join(record[0] for record in records))
        selected = owners[0]
    selected_handle, fields = selected
    host, _, session_id = selected_handle.partition(":")
    machine = socket.gethostname()
    if fields["Machine"].casefold() != machine.casefold():
        raise ValueError(f"{selected_handle}: recorded on a different machine; reconcile before resuming")
    reasons = stale_reasons(fields)
    if reasons:
        raise ValueError(f"{selected_handle}: stale ({', '.join(reasons)}); reconcile before resuming")
    recovery = _agent_recovery()
    roots = {host: Path(fields["Profile"]) / ("projects" if host == "claude" else "sessions")}
    if prompt_path:
        return recovery.open_session(
            host, session_id, prompt=None, title=title, roots=roots,
            confirm_closed=confirm_closed, prompt_path=prompt_path,
        )
    return recovery.open_session(
        host, session_id, prompt=prompt or "Continue the requested work.", title=title,
        roots=roots, confirm_closed=confirm_closed,
    )


def record(work_item_dir, host, role, state=None, title=None, pr=None, predecessor=None, successor=None, cwd=None):
    session_id = _current_session_id(host)
    if not session_id or not _agent_recovery().SESSION_ID.fullmatch(session_id):
        variable = "CODEX_THREAD_ID" if host == "codex" else "CLAUDE_CODE_SESSION_ID"
        raise ValueError(f"missing or invalid session id in {variable}")
    handle = f"{host}:{session_id}"
    cwd = Path(cwd) if cwd is not None else Path.cwd()
    toplevel = _run_git(cwd, "rev-parse", "--show-toplevel")
    if toplevel is None:
        raise ValueError(f"could not determine a git worktree from {cwd}")
    worktree = str(Path(toplevel).resolve())
    branch = _run_git(worktree, "branch", "--show-current")
    head = _run_git(worktree, "rev-parse", "HEAD")
    if branch is None or head is None:
        raise ValueError(f"could not determine the branch or HEAD of {worktree}")

    records = load(work_item_dir)
    existing = dict(records)
    current = existing.get(handle, {})

    other_owner = next((h for h, f in records if h != handle and f["Role"] == "owner"), None)
    if role == "owner" and other_owner is not None:
        if not (predecessor and other_owner == predecessor and existing[other_owner]["State"] == "handing-off"):
            raise ValueError(f"{other_owner} already owns this work item; hand off before taking ownership")

    removed = None
    if predecessor and predecessor in existing and existing[predecessor].get("State") == "handing-off":
        removed = predecessor

    fields = {
        "Role": role,
        "State": state or "active",
        "Machine": socket.gethostname(),
        "Profile": _profile_dir(host),
        "Title": title or os.environ.get("AGENT_CLI_TAB_TITLE") or "none",
        "Worktree": worktree,
        "Branch": branch,
        "PR": pr or current.get("PR", "not opened"),
        "Head": head,
        "Predecessor": predecessor or current.get("Predecessor", "none"),
        "Successor": successor or current.get("Successor", "none"),
        "Verified": _now_iso(),
        "Resume": _resume_command(host, session_id),
    }

    new_records = [(h, f) for h, f in records if h != handle and h != removed]
    new_records.append((handle, fields))

    errors = validate(new_records)
    if errors:
        raise ValueError("would produce an invalid file: " + "; ".join(errors))
    write(work_item_dir, new_records)
    return {"handle": handle, "removed": removed}


def remove(work_item_dir, handle=None, host=None):
    records = load(work_item_dir)
    if handle is None:
        if not host:
            raise ValueError("either --handle or --host is required")
        session_id = _current_session_id(host)
        if not session_id:
            raise ValueError(f"no current session id for host {host!r}; specify --handle")
        handle = f"{host}:{session_id}"
    remaining = [(h, f) for h, f in records if h != handle]
    if len(remaining) == len(records):
        raise ValueError(f"no recorded session with handle {handle!r}")
    write(work_item_dir, remaining)
    return {"removed": handle}


def _build_parser():
    parser = argparse.ArgumentParser(description="Parse, validate and maintain a work item's ACTIVE_SESSIONS.md.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("work_item_dir")

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("work_item_dir")

    find_parser = subparsers.add_parser("find")
    find_parser.add_argument("--worktree", required=True)
    find_parser.add_argument("--root", dest="roots", action="append", default=[])

    resume_parser = subparsers.add_parser("resume")
    resume_parser.add_argument("work_item_dir")
    resume_parser.add_argument("--handle")
    prompt_group = resume_parser.add_mutually_exclusive_group()
    prompt_group.add_argument("--prompt")
    prompt_group.add_argument("--prompt-path")
    resume_parser.add_argument("--confirm-closed", action="store_true")
    resume_parser.add_argument("--title")

    record_parser = subparsers.add_parser("record")
    record_parser.add_argument("work_item_dir")
    record_parser.add_argument("--host", required=True, choices=("claude", "codex"))
    record_parser.add_argument("--role", required=True)
    record_parser.add_argument("--state", choices=("active", "handing-off"))
    record_parser.add_argument("--title")
    record_parser.add_argument("--pr")
    record_parser.add_argument("--predecessor")
    record_parser.add_argument("--successor")

    remove_parser = subparsers.add_parser("remove")
    remove_parser.add_argument("work_item_dir")
    remove_parser.add_argument("--handle")
    remove_parser.add_argument("--host", choices=("claude", "codex"))

    return parser


def main(argv=None):
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "validate":
            result = cmd_validate(args.work_item_dir)
            ok = result["valid"]
        elif args.command == "status":
            result = cmd_status(args.work_item_dir)
            ok = result["valid"]
        elif args.command == "find":
            if not args.roots:
                raise ValueError("at least one --root is required")
            result = cmd_find(args.worktree, args.roots)
            ok = True
        elif args.command == "resume":
            result = resume(
                args.work_item_dir, handle=args.handle, prompt=args.prompt,
                prompt_path=args.prompt_path, confirm_closed=args.confirm_closed, title=args.title,
            )
            ok = True
        elif args.command == "record":
            result = record(
                args.work_item_dir, args.host, args.role, state=args.state, title=args.title,
                pr=args.pr, predecessor=args.predecessor, successor=args.successor,
            )
            ok = True
        elif args.command == "remove":
            result = remove(args.work_item_dir, handle=args.handle, host=args.host)
            ok = True
        else:
            raise ValueError(f"Unknown command: {args.command}")
    except (ValueError, RuntimeError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    print(json.dumps(result))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
