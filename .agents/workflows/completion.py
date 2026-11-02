import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Any, cast

from pr_body import unchecked_tasks

FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})completion\s*$", re.IGNORECASE)
SHA = re.compile(r"[0-9a-f]{40}")
STATE_DIRECTORY_ENV = "AGENT_STATE_DIRECTORY"
FORGE_TIMEOUT_SECONDS = 30
TERMINAL_ACCEPTANCE_DIRECTORY = "terminal-acceptance"
TERMINAL_ACCEPTANCE_SCHEMA_VERSION = 1
Json = dict[str, Any]


@contextmanager
def receipt_lock(path: Path) -> Iterator[None]:
    lock = path.with_suffix('.lock')
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('a+b') as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b'\0')
            stream.flush()
        stream.seek(0)
        try:
            if sys.platform == 'win32':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise CompletionError('another terminal receipt operation is active') from error
        try:
            yield
        finally:
            stream.seek(0)
            if sys.platform == 'win32':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def locked_receipt(operation: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(operation)
    def invoke(path: str | Path, *args: Any, **kwargs: Any) -> Any:
        with receipt_lock(Path(path)):
            return operation(path, *args, **kwargs)
    return invoke


class CompletionError(RuntimeError):
    pass


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def state_directory() -> Path:
    configured = os.environ.get(STATE_DIRECTORY_ENV)
    return Path(configured) if configured else Path.home() / ".agents-state"


def resolve_path(value: Any) -> Path | None:
    try:
        return Path(value).expanduser().resolve()
    except (OSError, TypeError):
        return None


def same_path(left: Any, right: Any) -> bool:
    return os.path.normcase(str(left)) == os.path.normcase(str(right))


def relevant_cleanup(root: Any) -> tuple[str, list[Json]]:
    root = resolve_path(root)
    if root is None:
        return "unobserved", []
    directory = state_directory() / "merge-cleanup" / "obligations"
    try:
        paths = list(directory.glob("*.json"))
    except OSError:
        return "unobserved", []
    pending = []
    verified = False
    for path in paths:
        try:
            obligation = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(obligation, dict):
            continue
        worktree = resolve_path(obligation.get("worktree"))
        if worktree is None or not same_path(worktree, root):
            continue
        disposition = obligation.get("disposition")
        keep_open = isinstance(disposition, dict) and disposition.get("reason") == "keep-open"
        session_exit = obligation.get("session_exit_required") is True
        checkout_exists = worktree.is_dir() and not obligation.get("checkout_retained")
        if keep_open or session_exit or checkout_exists:
            kind = "keep-open" if keep_open else "session-exit" if session_exit else "worktree"
            pending.append({
                "worktree": str(worktree),
                "session_id": obligation.get("session_id"),
                "kind": kind,
                "reason": disposition.get("reason") if isinstance(disposition, dict) else None,
            })
        elif obligation.get("cleanup_status") == "verified":
            verified = True
    if pending:
        return "pending", pending
    return ("verified" if verified else "unobserved"), []


def visible_tasks(markdown: str) -> list[str]:
    return cast(Callable[[str], list[str]], unchecked_tasks)(markdown)


def completion_document(goal: str | Path) -> tuple[str, Any]:
    try:
        body = Path(goal).read_text(encoding="utf-8")
    except OSError as error:
        raise CompletionError(f"completion goal could not be read: {error}") from error
    blocks = []
    lines = re.sub(r"<!--[\s\S]*?(?:-->|$)", "", body.lstrip("\ufeff")).splitlines()
    index = 0
    outer = None
    while index < len(lines):
        fence = re.match(r"^ {0,3}(`{3,}|~{3,})", lines[index])
        if outer is not None:
            if fence and fence.group(1)[0] == outer[0] and len(fence.group(1)) >= len(outer) and not lines[index][fence.end():].strip():
                outer = None
            index += 1
            continue
        marker = FENCE.match(lines[index])
        if marker is None:
            if fence:
                outer = fence.group(1)
            index += 1
            continue
        token = marker.group(1)
        end = index + 1
        while end < len(lines):
            close = re.match(r"^ {0,3}(`{3,}|~{3,})\s*$", lines[end])
            if close and close.group(1)[0] == token[0] and len(close.group(1)) >= len(token):
                break
            end += 1
        if end == len(lines):
            raise CompletionError("completion fence is not closed")
        try:
            blocks.append(json.loads("\n".join(lines[index + 1:end])))
        except json.JSONDecodeError as error:
            raise CompletionError(f"completion JSON is invalid: {error.msg}") from error
        index = end + 1
    if len(blocks) != 1:
        raise CompletionError("goal requires exactly one completion JSON fence")
    return body, blocks[0]


def identity(value: Any, name: str) -> Json:
    if not isinstance(value, dict) or set(value) != {"repository", "pr", "head"}:
        raise CompletionError(f"{name} requires repository, pr, and head")
    if not nonempty(value["repository"]) or type(value["pr"]) is not int or value["pr"] < 1:
        raise CompletionError(f"{name} has an invalid repository or PR")
    if not isinstance(value["head"], str) or SHA.fullmatch(value["head"]) is None:
        raise CompletionError(f"{name} requires a forty-character head SHA")
    return {"repository": value["repository"].strip(), "pr": value["pr"], "head": value["head"]}


def bound_identity(binding: Any) -> Json | None:
    if binding is None:
        return None
    if not isinstance(binding, dict):
        raise CompletionError("runtime delivery binding is unreadable")
    value = {
        "repository": binding.get("repository", binding.get("repo")),
        "pr": binding.get("pr", binding.get("pr_number")),
        "head": binding.get("head", binding.get("remote_head_sha")),
    }
    return identity(value, "runtime delivery binding")


def validate_document(document: Any) -> tuple[list[Json], list[Json], list[Json], list[Json]]:
    if not isinstance(document, dict) or set(document) != {"outcome", "acceptance", "deliveries", "open_tasks"}:
        raise CompletionError("completion JSON requires outcome, acceptance, deliveries, and open_tasks")
    if not nonempty(document["outcome"]):
        raise CompletionError("completion outcome is required")
    acceptance = document["acceptance"]
    if not isinstance(acceptance, list) or not acceptance:
        raise CompletionError("completion acceptance is required")
    seen = set()
    pending = []
    for item in acceptance:
        if not isinstance(item, dict) or set(item) != {"id", "criterion", "evidence", "owner", "next_action"}:
            raise CompletionError("completion acceptance has an invalid shape")
        if not nonempty(item["id"]) or not nonempty(item["criterion"]):
            raise CompletionError("completion acceptance requires id and criterion")
        if item["id"] in seen:
            raise CompletionError("completion acceptance ids must be unique")
        seen.add(item["id"])
        if not isinstance(item["evidence"], list):
            raise CompletionError("completion acceptance evidence must be a list")
        for evidence in item["evidence"]:
            if not isinstance(evidence, dict) or set(evidence) != {"source", "result"}:
                raise CompletionError("completion evidence requires source and result")
            if not nonempty(evidence["source"]) or not nonempty(evidence["result"]):
                raise CompletionError("completion evidence source and result are required")
        if not item["evidence"]:
            if not nonempty(item["owner"]) or not nonempty(item["next_action"]):
                raise CompletionError("pending completion acceptance requires owner and next_action")
            pending.append({"id": item["id"], "text": item["criterion"], "owner": item["owner"], "next_action": item["next_action"]})
    deliveries = []
    identities = set()
    if not isinstance(document["deliveries"], list):
        raise CompletionError("completion deliveries must be a list")
    for item in document["deliveries"]:
        entry = identity(item, "completion delivery")
        key = tuple(entry.values())
        if key in identities:
            raise CompletionError("completion deliveries must be unique")
        identities.add(key)
        deliveries.append(entry)
    if not isinstance(document["open_tasks"], list):
        raise CompletionError("completion open_tasks must be a list")
    tasks = []
    task_keys = set()
    for item in document["open_tasks"]:
        if not isinstance(item, dict) or set(item) != {"repository", "pr", "head", "text", "owner", "next_action"}:
            raise CompletionError("completion open task has an invalid shape")
        entry = identity({key: item[key] for key in ("repository", "pr", "head")}, "completion open task")
        if any(not nonempty(item[key]) for key in ("text", "owner", "next_action")):
            raise CompletionError("completion open task requires text, owner, and next_action")
        key = (*entry.values(), item["text"])
        if key in task_keys:
            raise CompletionError("completion open tasks must be unique")
        task_keys.add(key)
        tasks.append({**entry, "text": item["text"], "owner": item["owner"], "next_action": item["next_action"]})
    return acceptance, deliveries, pending, tasks


def forge_state(delivery: Json, root: Path | None) -> Any:
    try:
        result = subprocess.run(
            ["gh", "pr", "view", str(delivery["pr"]), "--repo", delivery["repository"],
             "--json", "number,headRefOid,state,body"],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=FORGE_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CompletionError(f"could not refresh delivery PR #{delivery['pr']}: {error}") from error
    if result.returncode:
        raise CompletionError(f"could not refresh delivery PR #{delivery['pr']}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise CompletionError(f"delivery PR #{delivery['pr']} returned invalid forge data") from error


def completion_check(goal: str | Path, bound_delivery: Json | None = None, root: Path | None = None,
                     viewer: Callable[[Json, Path | None], Any] | None = None) -> Json:
    body, document = completion_document(goal)
    _acceptance, deliveries, pending, open_tasks = validate_document(document)
    required = bound_identity(bound_delivery)
    identities = {tuple(item.values()) for item in deliveries}
    blockers = []
    unresolved = list(pending)
    if required is not None and tuple(required.values()) not in identities:
        blockers.append("bound delivery is absent from completion deliveries")
    if pending:
        blockers.extend(f"acceptance {item['id']} lacks evidence" for item in pending)
    for open_task in open_tasks:
        blockers.append(f"open task remains: {open_task['text']}")
        unresolved.append(open_task)
    for task in visible_tasks(body):
        blockers.append(f"goal task is unchecked: {task}")
    fetched = []
    for delivery in deliveries:
        value = (viewer or forge_state)(delivery, root)
        if not isinstance(value, dict):
            raise CompletionError(f"delivery PR #{delivery['pr']} returned unreadable forge data")
        if value.get("number") != delivery["pr"] or value.get("headRefOid") != delivery["head"]:
            blockers.append(f"delivery PR #{delivery['pr']} identity changed")
        if value.get("state") != "MERGED":
            blockers.append(f"delivery PR #{delivery['pr']} is not merged")
        remote_body = value.get("body")
        if not isinstance(remote_body, str):
            blockers.append(f"delivery PR #{delivery['pr']} body is unreadable")
            remote_body = ""
        for task in visible_tasks(remote_body):
            owned = next((item for item in open_tasks if item["repository"] == delivery["repository"]
                          and item["pr"] == delivery["pr"] and item["head"] == delivery["head"]
                          and item["text"] == task), None)
            if owned is None:
                blockers.append(f"delivery PR #{delivery['pr']} unchecked task lacks owner: {task}")
                unresolved.append({**delivery, "text": task, "owner": None, "next_action": None})
            blockers.append(f"delivery PR #{delivery['pr']} has unchecked task: {task}")
        fetched.append({"repository": delivery["repository"], "pr": delivery["pr"], "head": delivery["head"],
                        "state": value.get("state")})
    report_ready = not blockers
    cleanup_status, pending_cleanup = relevant_cleanup(root if root is not None else Path(goal).parent)
    if pending_cleanup:
        blockers.append("cleanup remains pending")
    return {
        "operation": "completion-check",
        "outcome": document["outcome"],
        "report_ready": report_ready,
        "ready": report_ready and not pending_cleanup,
        "blockers": blockers,
        "open_tasks": unresolved,
        "deliveries": fetched,
        "cleanup_status": cleanup_status,
        "pending_cleanup": pending_cleanup,
    }


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def atomic_json(path: Path, value: Json) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(value, sort_keys=True))
            handle.write("\n")
        Path(temporary).replace(path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def read_json(path: str | Path, name: str) -> Any:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise CompletionError(f"{name} is unreadable: {error}") from error
    return value


def source(path: str | Path, name: str) -> dict[str, str]:
    resolved = resolve_path(path)
    if resolved is None or not resolved.is_file():
        raise CompletionError(f"{name} is not a readable file")
    try:
        return {"path": str(resolved), "sha256": sha256(resolved.read_bytes())}
    except OSError as error:
        raise CompletionError(f"{name} is unreadable: {error}") from error


def source_digest(sources: list[dict[str, str]]) -> str:
    return sha256(canonical_bytes(sources))


def checkpoint_source(recorded: dict[str, str]) -> dict[str, str]:
    content = Path(recorded['path']).read_bytes()
    if sha256(content) != recorded['sha256']:
        raise CompletionError('source changed while preserving the terminal checkpoint')
    destination = state_directory() / TERMINAL_ACCEPTANCE_DIRECTORY / 'checkpoints' / recorded['sha256']
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=destination.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(content)
        Path(temporary).replace(destination)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return {'path': str(destination.resolve()), 'sha256': recorded['sha256']}


def receipt_source_path(receipt: dict[str, Any], index: int) -> Path:
    original = Path(receipt['sources'][index]['path'])
    checkpoint = receipt['checkpoint']
    if str(original) in checkpoint['retired_sources'] and not original.exists():
        return Path(checkpoint['sources'][index]['path'])
    return original


def terminal_receipt_path(candidate_id: str) -> Path:
    return state_directory() / TERMINAL_ACCEPTANCE_DIRECTORY / "receipts" / f"{candidate_id}.json"


def require_owner(host: Any, session_id: Any) -> dict[str, str]:
    if not nonempty(host) or not nonempty(session_id):
        raise CompletionError("terminal acceptance requires owner host and session id")
    return {"host": host.strip(), "session_id": session_id.strip()}


def aggregate_blockers(aggregate: Any) -> list[str]:
    if not isinstance(aggregate, dict):
        return ["aggregate is unreadable"]
    required = ("known", "owned", "responsibilities", "children", "waits")
    missing = [key for key in required if key not in aggregate]
    if missing:
        return ["aggregate is missing " + ", ".join(missing)]
    blockers = []
    if aggregate["known"] is not True:
        blockers.append("aggregate responsibility inventory is unknown")
    for collection in required[1:]:
        values = aggregate[collection]
        if not isinstance(values, list):
            blockers.append(f"aggregate {collection} is unreadable")
            continue
        for entry in values:
            if not isinstance(entry, dict):
                blockers.append(f"aggregate {collection} contains an unreadable responsibility")
                continue
            identifier = entry.get("id") or entry.get("name") or entry.get("text") or collection
            if entry.get("complete") is not True and entry.get("resolved") is not True:
                blockers.append(f"aggregate responsibility remains unresolved: {identifier}")
    return blockers


def terminal_sources(goal: Path, aggregate_path: Path, artifacts: Sequence[str | Path]) -> list[dict[str, str]]:
    paths = [goal, aggregate_path, *artifacts]
    labels = ["goal", "aggregate", *("declared evidence artifact" for _ in artifacts)]
    values = [source(path, label) for path, label in zip(paths, labels, strict=True)]
    seen = set()
    for value in values:
        if value["path"] in seen:
            raise CompletionError("terminal acceptance sources must be unique")
        seen.add(value["path"])
    return values


def terminal_candidate_id(owner: Json, sources: list[dict[str, str]], bound_delivery: Json | None) -> str:
    return sha256(canonical_bytes({"owner": owner, "sources": sources, "bound_delivery": bound_delivery}))


def terminal_check(goal: Path, root: Path, bound_delivery: Json | None, aggregate: Json) -> tuple[list[str], Json]:
    result = completion_check(goal, bound_delivery, root)
    blockers = [blocker for blocker in result["blockers"] if blocker != "cleanup remains pending"]
    return [*blockers, *aggregate_blockers(aggregate)], result


def initial_audit(candidate_id: str, sources: list[dict[str, str]]) -> Json:
    return {
        "state": "required",
        "candidate_id": candidate_id,
        "sources_sha256": source_digest(sources),
    }


def terminal_cleanup_reference(path: str | Path | None) -> Json:
    if path is None:
        return {"state": "unnecessary"}
    obligation_path = resolve_path(path)
    if obligation_path is None or not obligation_path.is_file():
        raise CompletionError("targeted cleanup obligation is not a readable file")
    obligation = read_json(obligation_path, "targeted cleanup obligation")
    required = {"kind", "obligation_id", "state", "owner", "worktree"}
    if not isinstance(obligation, dict) or not required.issubset(obligation):
        raise CompletionError("targeted cleanup obligation has an invalid shape")
    if obligation["kind"] != "targeted-cleanup" or obligation["state"] not in {
        "pending", "running", "verified", "retained", "refused", "timed_out",
    }:
        raise CompletionError("targeted cleanup obligation has an invalid state")
    if not isinstance(obligation["owner"], dict) or not nonempty(obligation["owner"].get("host")) \
            or not nonempty(obligation["owner"].get("session_id")) or not nonempty(obligation["worktree"]):
        raise CompletionError("targeted cleanup obligation has invalid ownership")
    receipt = obligation_path.parent.parent / "targeted-receipts" / f"{obligation['obligation_id']}.json"
    return {
        "state": obligation["state"] if obligation["state"] in {'verified', 'retained'} else 'pending',
        "obligation_id": obligation["obligation_id"],
        "obligation_path": str(obligation_path),
        "receipt_path": str(receipt),
        "owner": obligation["owner"],
        "worktree": obligation["worktree"],
    }


def receipt_sources_match(receipt: Json) -> tuple[bool, list[dict[str, str]], str | None]:
    current = []
    for index, recorded in enumerate(receipt.get("sources", [])):
        if not isinstance(recorded, dict) or set(recorded) != {"path", "sha256"}:
            return False, [], "receipt sources are unreadable"
        try:
            if recorded['path'] in receipt['checkpoint']['retired_sources']:
                preserved = receipt['checkpoint']['sources'][index]
                if source(preserved['path'], 'retired source checkpoint') != preserved:
                    return False, [], 'retired source checkpoint changed'
            observed = source(receipt_source_path(receipt, index), "receipt source")
            observed['path'] = recorded['path']
        except CompletionError as error:
            return False, [], str(error)
        current.append(observed)
    if current != receipt["sources"]:
        return False, current, "frozen terminal acceptance sources changed"
    return True, current, None


def load_terminal_receipt(path: str | Path) -> Json:
    receipt = read_json(path, "terminal acceptance receipt")
    required = {
        "schema_version", "kind", "candidate_id", "acceptance_generation", "state", "owner", "sources",
        "aggregate", "audit", "cleanup", "checked_at", "bound_delivery", "deterministic",
        'checkpoint',
    }
    if not isinstance(receipt, dict) or set(receipt) != required:
        raise CompletionError("terminal acceptance receipt has an invalid shape")
    if receipt["schema_version"] != TERMINAL_ACCEPTANCE_SCHEMA_VERSION or receipt["kind"] != "terminal-acceptance":
        raise CompletionError("terminal acceptance receipt has an unsupported schema")
    if receipt["state"] not in {"candidate", "accepted"}:
        raise CompletionError("terminal acceptance receipt has an invalid state")
    owner = require_owner(receipt["owner"].get("host") if isinstance(receipt["owner"], dict) else None,
                          receipt["owner"].get("session_id") if isinstance(receipt["owner"], dict) else None)
    if not isinstance(receipt["sources"], list) or len(receipt["sources"]) < 2:
        raise CompletionError("terminal acceptance receipt has invalid sources")
    for recorded in receipt["sources"]:
        if not isinstance(recorded, dict) or set(recorded) != {"path", "sha256"} or not nonempty(recorded["path"]):
            raise CompletionError("terminal acceptance receipt has invalid sources")
    checkpoint = receipt['checkpoint']
    if (not isinstance(checkpoint, dict)
            or set(checkpoint) != {'sources', 'retired_sources'}
            or not isinstance(checkpoint.get('retired_sources'), list)
            or not isinstance(checkpoint.get('sources'), list)
            or len(checkpoint['sources']) != len(receipt['sources'])):
        raise CompletionError('terminal acceptance checkpoint is unreadable')
    eligible = {
        recorded['path'] for index, recorded in enumerate(receipt['sources']) if index != 1
    }
    retired = checkpoint['retired_sources']
    if (not all(isinstance(item, str) and item in eligible for item in retired)
            or len(retired) != len(set(retired))):
        raise CompletionError(
            'terminal acceptance checkpoint has invalid retired sources'
        )
    for original, preserved in zip(receipt['sources'], checkpoint['sources'], strict=True):
        if (not isinstance(preserved, dict) or set(preserved) != {'path', 'sha256'}
                or not nonempty(preserved.get('path')) or preserved.get('sha256') != original['sha256']
                or not Path(preserved['path']).is_absolute()):
            raise CompletionError('terminal acceptance checkpoint differs from its sources')
    candidate = terminal_candidate_id(owner, receipt["sources"], receipt["bound_delivery"])
    if receipt["candidate_id"] != candidate or receipt["acceptance_generation"] != candidate:
        raise CompletionError("terminal acceptance receipt candidate does not match its sources")
    if (not isinstance(receipt["aggregate"], dict) or not isinstance(receipt["audit"], dict)
            or not isinstance(receipt["deterministic"], dict) or not isinstance(receipt["cleanup"], dict)):
        raise CompletionError("terminal acceptance receipt is unreadable")
    cleanup = receipt["cleanup"]
    if cleanup.get("state") == "unnecessary":
        if set(cleanup) != {"state"}:
            raise CompletionError("terminal acceptance cleanup reference is invalid")
    elif (cleanup.get("state") not in {"pending", "running", "verified", "retained", "refused", "timed_out"}
          or set(cleanup) != {"state", "obligation_id", "obligation_path", "receipt_path", "owner", "worktree"}
          or not isinstance(cleanup["owner"], dict)):
        raise CompletionError("terminal acceptance cleanup reference is invalid")
    return receipt


def save_terminal_receipt(path: Path, receipt: Json) -> Json:
    receipt["checked_at"] = time.time()
    atomic_json(path, receipt)
    return receipt


def prepare_terminal_acceptance(goal: str | Path, aggregate_path: str | Path, owner: Json, root: Path,
                                artifacts: Sequence[str | Path] = (), bound_delivery: Json | None = None,
                                cleanup_obligation: str | Path | None = None) -> tuple[Path, Json]:
    goal = Path(goal)
    aggregate_path = Path(aggregate_path)
    aggregate = read_json(aggregate_path, "aggregate")
    sources = terminal_sources(goal, aggregate_path, artifacts)
    candidate_id = terminal_candidate_id(owner, sources, bound_delivery)
    path = terminal_receipt_path(candidate_id)
    if path.resolve().is_relative_to(Path(root).resolve()):
        raise CompletionError('terminal acceptance state must be outside the execution checkout')
    with receipt_lock(path):
        return _prepare_terminal_acceptance(path, goal, aggregate, sources, owner, root,
                                            bound_delivery, cleanup_obligation)


def _prepare_terminal_acceptance(path: Path, goal: Path, aggregate: Json, sources: list[dict[str, str]],
                                 owner: Json, root: Path, bound_delivery: Json | None,
                                 cleanup_obligation: str | Path | None) -> tuple[Path, Json]:
    candidate_id = terminal_candidate_id(owner, sources, bound_delivery)
    cleanup = terminal_cleanup_reference(cleanup_obligation)
    if cleanup.get('owner', owner) != owner:
        raise CompletionError('targeted cleanup belongs to another owner')
    if path.is_file():
        receipt = load_terminal_receipt(path)
        if receipt["owner"] != owner or receipt["sources"] != sources or receipt["bound_delivery"] != bound_delivery:
            raise CompletionError("existing terminal acceptance receipt does not match its candidate")
        if cleanup_obligation is not None and receipt['cleanup'] != cleanup:
            receipt['cleanup'] = cleanup
            atomic_json(path, receipt)
        return path, receipt
    blockers, completion = terminal_check(goal, root, bound_delivery, aggregate)
    receipt = {
        "schema_version": TERMINAL_ACCEPTANCE_SCHEMA_VERSION,
        "kind": "terminal-acceptance",
        "candidate_id": candidate_id,
        "acceptance_generation": candidate_id,
        "state": "candidate",
        "owner": owner,
        "sources": sources,
        'checkpoint': {
            'sources': [checkpoint_source(item) for item in sources], 'retired_sources': [],
        },
        "aggregate": aggregate,
        "audit": initial_audit(candidate_id, sources),
        "cleanup": cleanup,
        "checked_at": time.time(),
        "bound_delivery": bound_delivery,
        "deterministic": {"blockers": blockers, "completion": completion, "root": str(Path(root).resolve())},
    }
    atomic_json(path, receipt)
    return path, receipt


def require_candidate(receipt: Json) -> None:
    if receipt["state"] != "candidate":
        raise CompletionError("terminal acceptance receipt is already accepted")


@locked_receipt
def reserve_terminal_audit(path: str | Path) -> tuple[Json, bool]:
    receipt = load_terminal_receipt(path)
    if receipt['state'] == 'accepted' or receipt['audit'].get('state') == 'passed':
        return receipt, False
    refresh_terminal_conditions(receipt)
    save_terminal_receipt(Path(path), receipt)
    if receipt["deterministic"].get("blockers"):
        raise CompletionError("deterministic blockers prevent native audit reservation")
    audit = receipt["audit"]
    if audit.get("state") == "required":
        valid, _sources, reason = receipt_sources_match(receipt)
        if not valid:
            raise CompletionError(reason)
        audit.update({"state": "reserved", "reservation_id": str(uuid.uuid4()), "native_child_id": None})
        return save_terminal_receipt(Path(path), receipt), True
    if audit.get("state") in {"reserved", "bound", "unknown"}:
        return receipt, False
    raise CompletionError("terminal acceptance audit is not available for reservation")


@locked_receipt
def bind_terminal_audit(path: str | Path, reservation_id: str, native_child_id: str,
                        reconciled: bool = False) -> Json:
    receipt = load_terminal_receipt(path)
    require_candidate(receipt)
    audit = receipt["audit"]
    if audit.get("state") == 'bound' and audit.get('reservation_id') == reservation_id \
            and audit.get('native_child_id') == native_child_id:
        return receipt
    allowed = audit.get('state') == 'reserved' or (audit.get('state') == 'unknown' and reconciled)
    if not allowed or audit.get("reservation_id") != reservation_id:
        raise CompletionError("terminal acceptance audit reservation does not match")
    if not nonempty(native_child_id):
        raise CompletionError("terminal acceptance audit requires a native child id")
    audit.update({"state": "bound", "native_child_id": native_child_id.strip()})
    return save_terminal_receipt(Path(path), receipt)


@locked_receipt
def record_terminal_audit(path: str | Path, reservation_id: str, result_path: str | Path) -> Json:
    receipt = load_terminal_receipt(path)
    require_candidate(receipt)
    audit = receipt["audit"]
    if audit.get("state") != "bound" or audit.get("reservation_id") != reservation_id:
        raise CompletionError("terminal acceptance audit binding does not match")
    valid, sources, reason = receipt_sources_match(receipt)
    if not valid:
        audit.update({"state": "failed", "reason": reason})
        return save_terminal_receipt(Path(path), receipt)
    result_source = checkpoint_source(source(result_path, "native audit result"))
    result = read_json(result_source['path'], "native audit result")
    if not isinstance(result, dict) or result.get("candidate_id") != receipt["candidate_id"]:
        raise CompletionError("native audit result does not match terminal acceptance candidate")
    if (result.get('reservation_id') != audit['reservation_id']
            or result.get('native_child_id') != audit['native_child_id']
            or result.get('sources_sha256') != audit['sources_sha256']):
        raise CompletionError('native audit result does not match its reserved child and sources')
    if result.get("state") != "passed" or result.get("findings") != []:
        audit.update({"state": "failed", "result": result_source})
        return save_terminal_receipt(Path(path), receipt)
    audit.update({"state": "passed", "result": result_source, "sources_sha256": source_digest(sources)})
    return save_terminal_receipt(Path(path), receipt)


def refresh_terminal_conditions(receipt: Json) -> tuple[bool, list[dict[str, str]]]:
    root_value = receipt['deterministic'].get('root')
    valid, sources, reason = receipt_sources_match(receipt)
    blockers: list[str] = [] if valid else [reason or 'terminal acceptance sources are unreadable']
    goal_path = receipt_source_path(receipt, 0)
    aggregate_path = Path(receipt["sources"][1]["path"])
    if valid:
        aggregate = read_json(aggregate_path, "aggregate")
        root = resolve_path(root_value)
        if root is None:
            blockers, completion = ["terminal acceptance root is unreadable"], None
        else:
            blockers, completion = terminal_check(goal_path, root, receipt["bound_delivery"], aggregate)
    else:
        completion = None
    receipt["deterministic"] = {
        "blockers": blockers, "completion": completion, 'root': root_value,
    }
    return valid, sources


@locked_receipt
def recheck_terminal_acceptance(path: str | Path) -> Json:
    receipt = load_terminal_receipt(path)
    _valid, sources = refresh_terminal_conditions(receipt)
    blockers: list[str] = []
    audit = receipt["audit"]
    if audit.get("state") == "reserved" and not audit.get("native_child_id"):
        audit["state"] = "unknown"
        blockers.append("native audit reservation has no bound child")
    if audit.get("state") == "passed":
        result = audit.get("result")
        if (audit.get("candidate_id") != receipt["candidate_id"]
                or source_digest(sources) != audit.get("sources_sha256")):
            audit.update({"state": "failed", "reason": "sources changed after native audit"})
            blockers.append("sources changed after native audit")
        elif not isinstance(result, dict) or not isinstance(result.get("path"), str) or not result.get("sha256"):
            audit.update({"state": "failed", "reason": "native audit result is unreadable"})
            blockers.append("native audit result is unreadable")
        else:
            try:
                observed = source(result["path"], "native audit result")
            except CompletionError:
                observed = None
            if observed != result:
                audit.update({"state": "failed", "reason": "native audit result changed"})
                blockers.append("native audit result changed")
    if audit.get("state") == "unnecessary":
        blockers.append("native audit has no trusted full-predicate proof")
    if audit.get("state") not in {"passed", "unnecessary"}:
        blockers.append("native audit is not accepted")
    audit['blockers'] = blockers
    ready = not blockers and not receipt['deterministic']['blockers']
    receipt["state"] = "accepted" if ready else "candidate"
    return save_terminal_receipt(Path(path), receipt)


@locked_receipt
def retire_terminal_goal(
    path: str | Path, retire_sources: Sequence[str | Path] = (),
) -> dict[str, Any]:
    receipt = load_terminal_receipt(path)
    if receipt['state'] != 'accepted':
        raise CompletionError('only an accepted goal can be retired')
    valid, _sources, reason = receipt_sources_match(receipt)
    if not valid:
        raise CompletionError(reason)
    selected = {receipt['sources'][0]['path']}
    eligible = {recorded['path'] for recorded in receipt['sources'][2:]}
    for requested in retire_sources:
        resolved = resolve_path(requested)
        if resolved is None or str(resolved) not in eligible:
            raise CompletionError(
                'retirement requires an explicitly declared evidence artifact'
            )
        selected.add(str(resolved))
    for index, original in enumerate(receipt['sources']):
        if original['path'] in selected:
            preserved = receipt['checkpoint']['sources'][index]
            if source(preserved['path'], 'retired source checkpoint') != preserved:
                raise CompletionError('retired source checkpoint changed')
    retired = set(receipt['checkpoint']['retired_sources']) | selected
    receipt['checkpoint']['retired_sources'] = sorted(retired)
    atomic_json(Path(path), receipt)
    return receipt


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--goal", required=True)
    result.add_argument("--root", default=".")
    result.add_argument("--bound-repository")
    result.add_argument("--bound-pr", type=int)
    result.add_argument("--bound-head")
    return result


def terminal_parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    commands = result.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--goal", required=True)
    prepare.add_argument("--aggregate", required=True)
    prepare.add_argument("--owner-host", required=True)
    prepare.add_argument("--owner-session-id", required=True)
    prepare.add_argument("--root", default=".")
    prepare.add_argument("--artifact", action="append", default=[])
    prepare.add_argument("--cleanup-obligation")
    prepare.add_argument("--bound-repository")
    prepare.add_argument("--bound-pr", type=int)
    prepare.add_argument("--bound-head")
    reserve = commands.add_parser("reserve-audit")
    reserve.add_argument("--receipt", required=True)
    bind = commands.add_parser("bind-audit")
    bind.add_argument("--receipt", required=True)
    bind.add_argument("--reservation-id", required=True)
    bind.add_argument("--native-child-id", required=True)
    bind.add_argument('--reconciled', action='store_true')
    record = commands.add_parser("record-audit")
    record.add_argument("--receipt", required=True)
    record.add_argument("--reservation-id", required=True)
    record.add_argument("--result", required=True)
    recheck = commands.add_parser("recheck")
    recheck.add_argument("--receipt", required=True)
    retire = commands.add_parser('retire-goal')
    retire.add_argument('--receipt', required=True)
    retire.add_argument('--retire-source', action='append', default=[])
    return result


def terminal_binding(arguments: argparse.Namespace) -> Json | None:
    values = (arguments.bound_repository, arguments.bound_pr, arguments.bound_head)
    if any(value is not None for value in values) and not all(value is not None for value in values):
        raise CompletionError("bound delivery requires repository, pr, and head together")
    return None if not all(value is not None for value in values) else identity({
        "repository": arguments.bound_repository,
        "pr": arguments.bound_pr,
        "head": arguments.bound_head,
    }, "bound delivery")


def terminal_main(argv: list[str]) -> int:
    arguments = terminal_parser().parse_args(argv)
    dispatch_allowed = False
    if arguments.command == "prepare":
        path, receipt = prepare_terminal_acceptance(
            arguments.goal,
            arguments.aggregate,
            require_owner(arguments.owner_host, arguments.owner_session_id),
            Path(arguments.root),
            arguments.artifact,
            terminal_binding(arguments),
            arguments.cleanup_obligation,
        )
    elif arguments.command == "reserve-audit":
        path = Path(arguments.receipt)
        receipt, dispatch_allowed = reserve_terminal_audit(path)
    elif arguments.command == "bind-audit":
        path = Path(arguments.receipt)
        receipt = bind_terminal_audit(path, arguments.reservation_id, arguments.native_child_id, arguments.reconciled)
    elif arguments.command == "record-audit":
        path = Path(arguments.receipt)
        receipt = record_terminal_audit(path, arguments.reservation_id, arguments.result)
    elif arguments.command == 'retire-goal':
        path = Path(arguments.receipt)
        receipt = retire_terminal_goal(path, arguments.retire_source)
    else:
        path = Path(arguments.receipt)
        receipt = recheck_terminal_acceptance(path)
    print(json.dumps({"receipt_path": str(path.resolve()), "receipt": receipt,
                      'dispatch_allowed': dispatch_allowed}, sort_keys=True))
    return 0 if arguments.command != "recheck" or receipt["state"] == "accepted" else 1


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in {"prepare", "reserve-audit", "bind-audit", "record-audit", "recheck", 'retire-goal'}:
        return terminal_main(argv)
    arguments = parser().parse_args(argv)
    values = (arguments.bound_repository, arguments.bound_pr, arguments.bound_head)
    if any(value is not None for value in values) and not all(value is not None for value in values):
        raise CompletionError("bound delivery requires repository, pr, and head together")
    binding = None if not all(value is not None for value in values) else {
        "repository": arguments.bound_repository,
        "pr": arguments.bound_pr,
        "head": arguments.bound_head,
    }
    result = completion_check(Path(arguments.goal), binding, Path(arguments.root))
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CompletionError as error:
        print(json.dumps({"operation": "completion-check", "report_ready": False, "ready": False, "error": str(error)}))
        raise SystemExit(2) from error
