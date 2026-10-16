#!/usr/bin/env python3
"""Converge owned Codex agents from an authenticated engineering package."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


class ConvergenceError(RuntimeError):
    pass


MANIFEST = ".base-agents-delivery.json"
PENDING = ".base-agents-delivery.pending.json"
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*\.toml$")
DIGEST = re.compile(r"^[0-9A-F]{64}$")
CANONICAL_CORE = "https://github.com/tj-agents/core.git"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _normalized_digest(path: Path) -> str:
    return hashlib.sha256(path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")).hexdigest().upper()


def _reparse(path: Path) -> bool:
    try:
        attributes = path.lstat().st_file_attributes
    except AttributeError:
        return path.is_symlink()
    return path.is_symlink() or bool(attributes & 0x400)


def _safe(path: Path) -> None:
    absolute = path.absolute()
    parts = absolute.parts
    current = Path(parts[0])
    for part in parts[1:]:
        current /= part
        if not current.exists() and not current.is_symlink():
            continue
        if _reparse(current):
            raise ConvergenceError(f"refusing a reparse-point delivery path: {current}")


def _atomic(path: Path, text: str) -> None:
    _safe(path.parent)
    path.parent.mkdir(parents=True, exist_ok=True)
    _safe(path.parent)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        _safe(path)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _load(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ConvergenceError(f"{label}: cannot read JSON ({error})") from error
    if not isinstance(value, dict):
        raise ConvergenceError(f"{label}: expected an object")
    return value


def _name(value: object, label: str) -> str:
    if not isinstance(value, str) or not NAME.fullmatch(value):
        raise ConvergenceError(f"invalid {label} agent name: {value}")
    return value


def _manifest(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    _safe(path)
    value = _load(path, str(path))
    if value.get("schema_version") != 1 or value.get("owner") != "base-agents" or not isinstance(value.get("files"), list):
        raise ConvergenceError(f"unsupported base-agents ownership state: {path}")
    result = {}
    for entry in value["files"]:
        if not isinstance(entry, dict):
            raise ConvergenceError(f"invalid base-agents ownership entry in {path}")
        name = _name(entry.get("name"), "owned")
        digest = entry.get("sha256")
        if not isinstance(digest, str) or not DIGEST.fullmatch(digest.upper()) or name in result:
            raise ConvergenceError(f"invalid base-agents ownership entry in {path}")
        result[name] = digest.upper()
    return result


def _write_manifest(path: Path, files: dict[str, str]) -> None:
    if not files:
        if path.exists():
            _safe(path)
            path.unlink()
        return
    value = {"schema_version": 1, "owner": "base-agents", "files": [{"name": name, "sha256": files[name]} for name in sorted(files)]}
    _atomic(path, json.dumps(value, indent=2) + "\n")


def _payload_digest(root: Path) -> str:
    paths = [root / "workflows" / "hosts" / "agent-delivery.json"]
    source = root / "codex-agents"
    _safe(source)
    if not source.is_dir():
        raise ConvergenceError("authenticated engineering package has no codex-agents directory")
    paths.extend(source.rglob("*"))
    digest = hashlib.sha256()
    for path in sorted(paths):
        _safe(path)
        if path.is_dir():
            continue
        if not path.is_file():
            raise ConvergenceError(f"invalid Codex agent payload entry: {path}")
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def _engineering(verified_roots) -> Path | None:
    found = []
    for root in verified_roots:
        if getattr(root, "identity", None) not in {"engineering@base-agents", "engineering@tj-agents"}:
            continue
        if getattr(root, "repository", "").casefold() != CANONICAL_CORE:
            raise ConvergenceError("engineering root was not authenticated from tj-agents/core")
        path = getattr(root, "root", None)
        if not isinstance(path, Path) or not path.is_dir() or path.is_symlink():
            raise ConvergenceError("authenticated engineering root is unavailable or a symlink")
        _safe(path)
        resolved = path.resolve(strict=True)
        _safe(resolved)
        revision = getattr(root, "revision", None)
        if not isinstance(revision, str) or not revision:
            raise ConvergenceError("authenticated engineering root has no source revision")
        found.append((revision, resolved))
    if not found:
        return None
    revisions = {revision for revision, _root in found}
    payloads = {_payload_digest(root) for _revision, root in found}
    if len(revisions) != 1 or len(payloads) != 1:
        raise ConvergenceError("authenticated engineering roots disagree on generation or agent payload")
    return sorted(root for _revision, root in found)[0]


def _delivery(root: Path) -> tuple[dict[str, Path], set[str], dict[str, set[str]]]:
    config = _load(root / "workflows" / "hosts" / "agent-delivery.json", "Codex agent delivery config")
    patterns = config.get("generated_agent_patterns")
    former = config.get("former_managed_agents")
    known = config.get("project_managed_agent_sha256", {})
    if not isinstance(patterns, list) or not patterns or not all(isinstance(value, str) and value != "*.toml" for value in patterns):
        raise ConvergenceError("invalid generated Codex agent patterns")
    if not isinstance(former, list) or not isinstance(known, dict):
        raise ConvergenceError("invalid Codex agent delivery config")
    source = root / "codex-agents"
    _safe(source)
    if not source.is_dir():
        raise ConvergenceError("authenticated engineering package has no codex-agents directory")
    files = {}
    for path in source.iterdir():
        if not path.is_file() or path.is_symlink() or not any(fnmatch.fnmatchcase(path.name, pattern) for pattern in patterns):
            continue
        files[_name(path.name, "generated")] = path
    if not files:
        raise ConvergenceError("authenticated engineering package has no generated Codex agents")
    former_names = {_name(value, "former managed") for value in former}
    known_digests = {}
    for name, values in known.items():
        name = _name(name, "project managed")
        if not isinstance(values, list) or not values or not all(isinstance(value, str) and DIGEST.fullmatch(value.upper()) for value in values):
            raise ConvergenceError(f"invalid project agent digest inventory for {name}")
        known_digests[name] = {value.upper() for value in values}
    for name, path in files.items():
        known_digests.setdefault(name, set()).add(_normalized_digest(path))
    return files, former_names, known_digests


def _recover(target: Path, owned: dict[str, str], pending: dict[str, str]) -> None:
    for name, digest in pending.items():
        destination = target / name
        _safe(destination)
        if not destination.exists():
            continue
        if not destination.is_file() or _digest(destination) not in {digest, owned.get(name)}:
            raise ConvergenceError(f"interrupted profile install has an unexpected agent state: {destination}")
        if _digest(destination) == digest:
            owned[name] = digest


def _copy(source: Path, destination: Path, digest: str) -> None:
    _safe(destination)
    descriptor, temporary = tempfile.mkstemp(prefix=".base-agents-delivery.", dir=str(destination.parent))
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(source.read_bytes())
        if _digest(Path(temporary)) != digest:
            raise ConvergenceError(f"staged profile agent differs from its source: {source}")
        _safe(destination)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _migrate_project(project: Path | None, names: set[str], known: dict[str, set[str]]) -> None:
    if project is None:
        return
    target = project / ".codex" / "agents"
    if not target.exists():
        return
    _safe(target)
    for name in names:
        path = target / name
        if not path.exists():
            continue
        _safe(path)
        if path.is_file() and _normalized_digest(path) in known.get(name, set()):
            path.unlink()
    if target.exists() and target.is_dir() and not any(target.iterdir()):
        target.rmdir()


def converge(environ: dict, project: Path | None, verified_roots) -> None:
    root = _engineering(verified_roots)
    if root is None:
        return
    files, former, known = _delivery(root)
    target = Path(environ.get("CODEX_HOME") or Path.home() / ".codex") / "agents"
    _safe(target)
    owned_path = target / MANIFEST
    pending_path = target / PENDING
    owned = _manifest(owned_path)
    pending = _manifest(pending_path)
    _recover(target, owned, pending)
    source_names = set(files)
    actions = []
    for name, source in sorted(files.items()):
        destination = target / name
        digest = _digest(source)
        _safe(destination)
        if not destination.exists():
            actions.append(("add", source, destination, digest))
        elif not destination.is_file():
            raise ConvergenceError(f"Codex profile agent is not a file: {destination}")
        elif _digest(destination) == digest:
            actions.append(("unchanged", source, destination, digest))
        elif owned.get(name) == _digest(destination):
            actions.append(("replace", source, destination, digest))
        else:
            raise ConvergenceError(f"refusing to overwrite an unowned or modified profile agent: {destination}")
    retired = []
    for name, digest in owned.items():
        if name in source_names:
            continue
        destination = target / name
        _safe(destination)
        if destination.exists():
            if not destination.is_file() or _digest(destination) != digest:
                raise ConvergenceError(f"refusing to remove a modified retired profile agent: {destination}")
            retired.append(destination)
    new_owned = {name: digest for name, digest in owned.items() if name in source_names}
    for state, _source, _destination, digest in actions:
        if state != "unchanged" or _destination.name in owned:
            new_owned[_destination.name] = digest
    if actions or retired or pending:
        _write_manifest(pending_path, new_owned)
    target.mkdir(parents=True, exist_ok=True)
    for state, source, destination, digest in actions:
        if state != "unchanged":
            _copy(source, destination, digest)
    for destination in retired:
        destination.unlink()
    _write_manifest(owned_path, new_owned)
    _write_manifest(pending_path, {})
    _migrate_project(project.resolve() if project is not None else None, source_names | former, known)
