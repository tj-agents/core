#!/usr/bin/env python3
"""Prepare verified rolling-main tj-agents plugin projections for native hosts."""

from __future__ import annotations

from contextlib import contextmanager
import copy
from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import tarfile
import signal
from typing import Iterable, Mapping


GIT_TIMEOUT_SECONDS = 90
OPERATION_TIMEOUT_SECONDS = 300
LOCK_WAIT_SECONDS = 180
LOCK_STALE_SECONDS = 900
SHA = re.compile(r"^[0-9a-f]{40}$")


class RollingPluginError(RuntimeError):
    pass


@dataclass(frozen=True)
class Selection:
    identity: str
    source_url: str
    marketplace: str

    def __post_init__(self):
        if not isinstance(self.identity, str) or self.identity.count("@") != 1:
            raise RollingPluginError("plugin selection has an invalid identity")
        name, marketplace = self.identity.rsplit("@", 1)
        _cache_component(name)
        _cache_component(marketplace)
        if self.marketplace != marketplace:
            raise RollingPluginError("plugin selection marketplace does not match its identity")

    @property
    def name(self) -> str:
        return self.identity.rsplit("@", 1)[0]


@dataclass(frozen=True)
class Package:
    identity: str
    marketplace: str
    repository: str
    revision: str
    path: str
    root: Path


@dataclass(frozen=True)
class VerifiedRoot:
    identity: str
    root: Path
    revision: str
    repository: str


@dataclass(frozen=True)
class Prepared:
    host: str
    launch_args: tuple[str, ...]
    selected_roots: tuple[VerifiedRoot, ...]
    catalog_root: Path
    environment: Mapping[str, str]
    selections: tuple[Selection, ...] = ()
    source_revisions: tuple[tuple[str, str], ...] = ()
    plugins_root: Path | None = None
    deadline: "Deadline | None" = None
    disabled: tuple[str, ...] = ()


class Deadline:
    def __init__(self, seconds: float = OPERATION_TIMEOUT_SECONDS):
        if seconds <= 0:
            raise RollingPluginError("rolling plugin deadline must be positive")
        self.ends = time.monotonic() + seconds

    def remaining(self, limit: float = GIT_TIMEOUT_SECONDS) -> float:
        value = min(limit, self.ends - time.monotonic())
        if value <= 0:
            raise RollingPluginError("rolling plugin refresh exceeded its deadline")
        return value


class Preflight:
    def __init__(self, host: str, target: Path, project: Path, arguments: Mapping[str, object] | None):
        self.host = host
        self.target = target
        self.project = project
        self.arguments = dict(arguments or {})
        self.prepared: Prepared | None = None
        self._lock = None
        self._deadline = Deadline(float(self.arguments.get("deadline_seconds", OPERATION_TIMEOUT_SECONDS)))

    def __enter__(self) -> "Preflight":
        cache = _cache_root(self.host, self.target, self.arguments)
        self._lock = exclusive(cache, deadline=self._deadline)
        self._lock.__enter__()
        try:
            self.prepared = _prepare(self.host, self.target, self.project, self.arguments, cache, self._deadline)
            if not self.prepared.selections:
                self.acknowledge_binding()
        except BaseException:
            self._lock.__exit__(*__import__("sys").exc_info())
            self._lock = None
            raise
        return self

    def acknowledge_binding(self) -> Prepared:
        if self.prepared is None:
            raise RollingPluginError("rolling plugin preflight has not prepared a package set")
        if self._lock is not None:
            self._lock.__exit__(None, None, None)
            self._lock = None
        return self.prepared

    def materialize_native(self, executable: str | Path) -> Prepared:
        if self.prepared is None:
            raise RollingPluginError("rolling plugin preflight has not prepared a package set")
        self.prepared = materialize_native(self.prepared, self.host, self.target, self.project, str(executable))
        verify_final(self.prepared, self.host, self.target, self.project, self.arguments)
        return self.prepared

    def __exit__(self, *details) -> None:
        if self._lock is not None:
            self._lock.__exit__(*details)
            self._lock = None


def _json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        raise RollingPluginError(f"cannot read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise RollingPluginError(f"{path} must contain a JSON object")
    return value


def _safe_path(value: str, allow_root: bool = False) -> str:
    raw = value.replace("\\", "/")
    if allow_root and raw == ".":
        return raw
    if not raw or raw.startswith("/") or raw.endswith("/") or "//" in raw:
        raise RollingPluginError(f"unsafe plugin path: {value!r}")
    parts = raw.split("/")
    reserved = {"con", "prn", "aux", "nul", *(f"com{value}" for value in range(1, 10)),
                *(f"lpt{value}" for value in range(1, 10))}
    if any(part in {"", ".", ".."} or ":" in part or "\x00" in part
           or part.split(".", 1)[0].casefold() in reserved for part in parts):
        raise RollingPluginError(f"unsafe plugin path: {value!r}")
    return "/".join(parts)



def _cache_component(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value) or value.endswith("."):
        raise RollingPluginError(f"unsafe plugin cache component: {value!r}")
    return _safe_path(value)


def _unlinked_ancestors(path: Path) -> None:
    if ".." in path.parts:
        raise RollingPluginError(f"cache path contains traversal: {path}")
    current = path.absolute()
    for candidate in (current, *current.parents):
        try:
            status = candidate.lstat()
        except FileNotFoundError:
            continue
        except OSError as error:
            raise RollingPluginError(f"cannot inspect cache path {candidate}: {error}") from error
        if stat.S_ISLNK(status.st_mode) or getattr(status, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise RollingPluginError(f"cache path has a linked or reparse ancestor: {candidate}")


def _github_repository(url: str) -> str | None:
    value = url.strip().replace("\\", "/")
    if value.startswith("git@github.com:"):
        value = "github.com/" + value.split(":", 1)[1]
    else:
        value = re.sub(r"^[a-z][a-z0-9+.-]*://(?:[^@/]+@)?", "", value, flags=re.IGNORECASE)
    value = value.rstrip("/")
    if value.casefold().endswith(".git"):
        value = value[:-4]
    if not value.casefold().startswith("github.com/"):
        return None
    pieces = value.split("/")
    if len(pieces) != 3 or any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", piece)
                               or piece.endswith(".") for piece in pieces[1:]):
        return None
    return "/".join(pieces[1:]).casefold()


def canonical_source(url: str) -> str | None:
    repository = _github_repository(url)
    if repository == "tomjseery/dotagents":
        return "https://github.com/tj-agents/dotnet.git"
    if repository == "tomjseery/react-agents":
        return "https://github.com/tj-agents/react.git"
    if repository is None or not repository.startswith("tj-agents/"):
        return None
    return f"https://github.com/{repository}.git"


def source_url(source: object) -> str | None:
    if not isinstance(source, dict):
        return None
    if source.get("source") == "github" and isinstance(source.get("repo"), str):
        return f"https://github.com/{source['repo']}.git"
    value = source.get("url")
    return value if isinstance(value, str) and value else None


def _claude_option_values(arguments: Iterable[str]) -> tuple[tuple[str, ...], object | None]:
    sources: tuple[str, ...] = ("user", "project", "local")
    settings: object | None = None
    values = list(arguments)
    index = 0
    while index < len(values):
        value = values[index]
        if value == "--":
            break
        if value in {"--settings", "--setting-sources"}:
            if index + 1 >= len(values):
                raise RollingPluginError(f"Claude option {value} requires a value")
            payload = values[index + 1]
            index += 2
        elif value.startswith("--settings="):
            payload = value.split("=", 1)[1]
            value = "--settings"
            index += 1
        elif value.startswith("--setting-sources="):
            payload = value.split("=", 1)[1]
            value = "--setting-sources"
            index += 1
        else:
            index += 1
            continue
        if value == "--settings":
            settings = payload
            continue
        parts = tuple(part.strip().casefold() for part in payload.replace(";", ",").split(",") if part.strip())
        if not parts or any(part not in {"user", "project", "local"} for part in parts):
            raise RollingPluginError("Claude --setting-sources must name user, project, or local sources")
        sources = tuple(source for source in ("user", "project", "local") if source in parts)
    return sources, settings


def _claude_settings_value(value: object, project: Path) -> dict[str, object]:
    if not isinstance(value, str):
        return {}
    try:
        parsed = json.loads(value)
    except ValueError:
        path = Path(value)
        if not path.is_absolute():
            path = project / path
        if not path.is_file():
            raise RollingPluginError(f"Claude --settings is neither JSON nor a settings file: {value}")
        return _json(path)
    if not isinstance(parsed, dict):
        raise RollingPluginError("Claude --settings must contain a JSON object")
    return parsed


def claude_settings(config: Path, project: Path, arguments: Iterable[str] = ()) -> tuple[dict[str, object], dict[str, object]]:
    sources, override = _claude_option_values(arguments)
    paths = {
        "user": config / "settings.json",
        "project": project / ".claude" / "settings.json",
        "local": project / ".claude" / "settings.local.json",
    }
    effective: dict[str, object] = {}
    supplied = _claude_settings_value(override, project)
    layers = [_json(paths[source]) for source in sources if paths[source].exists()]
    layers.append(supplied)
    for layer in layers:
        for key, value in layer.items():
            previous = effective.get(key)
            if key in {"enabledPlugins", "extraKnownMarketplaces"} and isinstance(previous, dict) and isinstance(value, dict):
                effective[key] = dict(previous, **value)
            else:
                effective[key] = value
    return effective, supplied


def claude_enabled(config: Path, project: Path, arguments: Iterable[str] = ()) -> dict[str, object]:
    values, _supplied = claude_settings(config, project, arguments)
    enabled = values.get("enabledPlugins")
    return dict(enabled) if isinstance(enabled, dict) else {}


def selected_claude(config: Path, plugins: Path, project: Path, arguments: Iterable[str] = ()) -> list[Selection]:
    enabled = claude_enabled(config, project, arguments)
    if not any(value is True for value in enabled.values()):
        return []
    known = _json(plugins / "known_marketplaces.json")
    selections = []
    for identity, value in sorted(enabled.items()):
        if value is not True or not isinstance(identity, str) or identity.count("@") != 1:
            continue
        name, marketplace = identity.rsplit("@", 1)
        entry = known.get(marketplace)
        source = source_url(entry.get("source")) if isinstance(entry, dict) else None
        if source is None:
            raise RollingPluginError(f"selected plugin {identity} has no registered Git marketplace source")
        authenticated = canonical_source(source)
        if authenticated is not None:
            selections.append(Selection(identity, authenticated, marketplace))
    return selections


def selected_codex(inventory: Mapping[str, object]) -> list[Selection]:
    selections: dict[str, Selection] = {}
    for group in (inventory.get("installed"), inventory.get("available")):
        if not isinstance(group, list):
            continue
        for item in group:
            if not isinstance(item, dict) or item.get("enabled") is not True:
                continue
            identity = item.get("pluginId")
            marketplace = item.get("marketplaceSource")
            if not isinstance(identity, str) or identity.count("@") != 1 or not isinstance(marketplace, dict):
                continue
            if marketplace.get("sourceType") != "git":
                continue
            source = marketplace.get("source")
            if not isinstance(source, str):
                raise RollingPluginError(f"selected plugin {identity} has no registered Git marketplace source")
            authenticated = canonical_source(source)
            if authenticated is not None:
                selections[identity] = Selection(identity, authenticated, identity.rsplit("@", 1)[1])
    return [selections[key] for key in sorted(selections)]


def supplied_selections(value: object) -> list[Selection]:
    if not isinstance(value, list):
        raise RollingPluginError("configured plugin selections must be a list")
    result = []
    for item in value:
        if not isinstance(item, Mapping):
            raise RollingPluginError("configured plugin selection must be an object")
        identity = item.get("identity")
        source = item.get("source_url")
        marketplace = item.get("marketplace")
        if not isinstance(identity, str) or identity.count("@") != 1 or not isinstance(source, str):
            raise RollingPluginError("configured plugin selection has invalid identity or source")
        name, default_marketplace = identity.rsplit("@", 1)
        if not name:
            raise RollingPluginError("configured plugin selection has invalid identity")
        authenticated = canonical_source(source)
        if authenticated is None:
            continue
        result.append(Selection(identity, authenticated, marketplace if isinstance(marketplace, str) else default_marketplace))
    return result


def _completed(command: list[str], cwd: Path | None, environment: Mapping[str, str], deadline: Deadline,
               timeout: int = GIT_TIMEOUT_SECONDS) -> subprocess.CompletedProcess:
    options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
    try:
        process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, env=dict(os.environ, **environment), **options)
    except OSError as error:
        raise RollingPluginError(f"could not run {' '.join(command[:2])}: {error}") from error
    try:
        stdout, stderr = process.communicate(timeout=deadline.remaining(timeout))
    except subprocess.TimeoutExpired as error:
        terminate_process_tree(process)
        raise RollingPluginError(f"command timed out: {' '.join(command[:3])}") from error
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def _run(command: list[str], cwd: Path | None = None, deadline: Deadline | None = None) -> str:
    environment = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    completed = _completed(command, cwd, environment, deadline or Deadline())
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).decode("utf-8", "replace").strip() or "no output"
        raise RollingPluginError(f"Git command failed: {' '.join(command)}: {detail}")
    return completed.stdout.decode("utf-8", "replace").strip()


def _cache_name(url: str) -> str:
    authenticated = canonical_source(url)
    if authenticated is None:
        raise RollingPluginError(f"source is not an authenticated tj-agents GitHub repository: {url}")
    return re.sub(r"[^a-z0-9_.-]+", "-", authenticated.casefold()).strip("-")


def _fetch_main(url: str, root: Path, deadline: Deadline | None = None) -> tuple[Path, str]:
    deadline = deadline or Deadline()
    authenticated = canonical_source(url)
    if authenticated is None:
        raise RollingPluginError(f"source is not an authenticated tj-agents GitHub repository: {url}")
    clone = root / "git" / _cache_name(authenticated)
    _unlinked_ancestors(clone)
    if clone.is_dir():
        _verified_tree(clone)
    clone.parent.mkdir(parents=True, exist_ok=True)
    if not (clone / ".git").is_dir():
        if clone.exists():
            raise RollingPluginError(f"plugin cache path is not a Git checkout: {clone}")
        _run(["git", "clone", "--no-checkout", "--depth", "1", authenticated, str(clone)], deadline=deadline)
    origin = _run(["git", "-C", str(clone), "remote", "get-url", "origin"], deadline=deadline)
    if canonical_source(origin) != authenticated:
        raise RollingPluginError(f"plugin cache origin changed for {url}")
    _run(["git", "-C", str(clone), "fetch", "--force", "--depth", "1", "origin", "refs/heads/main:refs/remotes/origin/main"], deadline=deadline)
    revision = _run(["git", "-C", str(clone), "rev-parse", "refs/remotes/origin/main"], deadline=deadline)
    if not SHA.fullmatch(revision):
        raise RollingPluginError(f"Git did not return a main commit for {url}")
    return clone, revision


def _git_text(clone: Path, revision: str, path: str, deadline: Deadline | None = None) -> bytes:
    safe = _safe_path(path)
    completed = _completed(["git", "-C", str(clone), "show", f"{revision}:{safe}"], None,
                           {"GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}, deadline or Deadline())
    if completed.returncode:
        raise RollingPluginError(f"missing required Git path {safe} at {revision[:12]}")
    return completed.stdout


def _catalog(clone: Path, revision: str, deadline: Deadline | None = None) -> dict:
    for path in (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json", "marketplace.json"):
        try:
            value = json.loads(_git_text(clone, revision, path, deadline).decode("utf-8-sig"))
        except RollingPluginError:
            continue
        except UnicodeDecodeError as error:
            raise RollingPluginError(f"catalog {path} is not UTF-8") from error
        except ValueError as error:
            raise RollingPluginError(f"catalog {path} is invalid JSON") from error
        if isinstance(value, dict) and isinstance(value.get("plugins"), list):
            return value
    raise RollingPluginError(f"no current publisher catalog found at {revision[:12]}")


def _extract_repository(clone: Path, revision: str, destination: Path, deadline: Deadline | None = None) -> None:
    _unlinked_ancestors(destination)
    archive = _completed(["git", "-C", str(clone), "archive", "--format=tar", revision], None,
                         {"GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}, deadline or Deadline())
    if archive.returncode:
        raise RollingPluginError(f"could not archive published repository {revision[:12]}")
    with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as tree:
        for entry in tree:
            if entry.isdir():
                continue
            if not entry.isfile():
                raise RollingPluginError("published repository contains an unsupported link or special entry")
            target = destination / _safe_path(entry.name)
            target.parent.mkdir(parents=True, exist_ok=True)
            handle = tree.extractfile(entry)
            if handle is None:
                raise RollingPluginError("published repository contains an unreadable entry")
            target.write_bytes(handle.read())
            if entry.mode & 0o111:
                target.chmod(target.stat().st_mode | 0o111)


def _publication_gate(clone: Path, revision: str, deadline: Deadline | None = None) -> None:
    try:
        marker = json.loads(_git_text(clone, revision, "plugins/publication.json", deadline).decode("utf-8"))
    except (RollingPluginError, UnicodeDecodeError, ValueError) as error:
        raise RollingPluginError(f"tj-agents/core main is awaiting generated publication at {revision[:12]}") from error
    expected = marker.get("source_fingerprint") if isinstance(marker, dict) else None
    if not isinstance(expected, str):
        raise RollingPluginError(f"tj-agents/core publication marker is invalid at {revision[:12]}")
    with tempfile.TemporaryDirectory(prefix="tj-agents-publication-") as temporary:
        root = Path(temporary)
        _extract_repository(clone, revision, root, deadline)
        script = root / "scripts" / "sync_plugin_packages.py"
        if not script.is_file():
            raise RollingPluginError(f"tj-agents/core publication generator is missing at {revision[:12]}")
        completed = _completed([sys.executable, "-B", str(script), "--root", str(root), "--check"],
                               root, {}, deadline or Deadline())
        if completed.returncode:
            detail = (completed.stderr or completed.stdout).decode("utf-8", "replace").strip() or "no output"
            raise RollingPluginError(
                f"tj-agents/core generated publication cannot be verified at {revision[:12]}: {detail}"
            )


def _entry(catalog: dict, name: str) -> dict:
    matches = [item for item in catalog.get("plugins", []) if isinstance(item, dict) and item.get("name") == name]
    if len(matches) != 1:
        raise RollingPluginError(f"selected package {name} is missing from the current publisher catalog")
    return matches[0]


def _entry_source(entry: dict, fallback: str) -> tuple[str, str]:
    source = entry.get("source")
    if isinstance(source, str):
        return fallback, _safe_path(source.removeprefix("./"), allow_root=True)
    if not isinstance(source, dict):
        raise RollingPluginError(f"publisher catalog entry {entry.get('name')!r} has no package source")
    kind = source.get("source")
    if kind == "local":
        value = source.get("path")
        if not isinstance(value, str):
            raise RollingPluginError(f"publisher catalog entry {entry.get('name')!r} has invalid local path")
        return fallback, _safe_path(value.removeprefix("./"), allow_root=True)
    if kind == "git-subdir":
        value = source_url(source)
        path = source.get("path")
        if not isinstance(value, str) or not isinstance(path, str):
            raise RollingPluginError(f"publisher catalog entry {entry.get('name')!r} has invalid Git subdirectory source")
        authenticated = canonical_source(value)
        if authenticated is None:
            raise RollingPluginError(f"publisher source for {entry.get('name')!r} is not authenticated tj-agents")
        return authenticated, _safe_path(path.removeprefix("./"), allow_root=True)
    raise RollingPluginError(f"publisher catalog entry {entry.get('name')!r} uses unsupported source {kind!r}")


def _tree_modes(clone: Path, revision: str, path: str, deadline: Deadline | None = None) -> dict[str, bool]:
    prefix = _safe_path(path, allow_root=True)
    completed = _completed(["git", "-C", str(clone), "ls-tree", "-r", "-z", revision, "--", prefix], None,
                           {"GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}, deadline or Deadline())
    if completed.returncode:
        raise RollingPluginError(f"missing required Git path {prefix} at {revision[:12]}")
    modes: dict[str, bool] = {}
    for item in completed.stdout.split(b"\0"):
        if not item:
            continue
        try:
            header, raw_path = item.split(b"\t", 1)
            mode, kind, _object = header.split(b" ", 2)
            tree_path = raw_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError) as error:
            raise RollingPluginError(f"invalid Git tree entry at {revision[:12]}") from error
        if kind != b"blob":
            raise RollingPluginError(f"package {prefix} contains an unsupported Git tree entry")
        if prefix != ".":
            expected = prefix + "/"
            if not tree_path.startswith(expected):
                raise RollingPluginError(f"Git tree entry escapes package {prefix}")
            tree_path = tree_path[len(expected):]
        safe = _safe_path(tree_path)
        if safe in modes:
            raise RollingPluginError(f"package {prefix} has duplicate Git path {safe}")
        try:
            modes[safe] = bool(int(mode, 8) & 0o111)
        except ValueError as error:
            raise RollingPluginError(f"package {prefix} has invalid Git file mode") from error
    return modes


def _tree_files(clone: Path, revision: str, path: str, deadline: Deadline | None = None) -> dict[str, tuple[bytes, bool]]:
    prefix = _safe_path(path, allow_root=True)
    subject = revision if prefix == "." else f"{revision}:{prefix}"
    archive = _completed(["git", "-C", str(clone), "archive", "--format=tar", subject], None,
                         {"GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}, deadline or Deadline())
    if archive.returncode:
        raise RollingPluginError(f"missing required Git path {prefix} at {revision[:12]}")
    modes = _tree_modes(clone, revision, prefix, deadline)
    files: dict[str, tuple[bytes, bool]] = {}
    names: set[str] = set()
    with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as tree:
        for entry in tree:
            if entry.isdir():
                continue
            if not entry.isfile():
                raise RollingPluginError(f"package {prefix} contains an unsupported link or special entry")
            safe = _safe_path(entry.name)
            if safe.casefold() in names:
                raise RollingPluginError(f"package {prefix} has case-colliding path {safe}")
            names.add(safe.casefold())
            handle = tree.extractfile(entry)
            if handle is None:
                raise RollingPluginError(f"package {prefix} contains an unreadable entry")
            if safe not in modes:
                raise RollingPluginError(f"Git archive contains an untracked package path {safe}")
            files[safe] = handle.read(), modes.pop(safe)
    if not files:
        raise RollingPluginError(f"current package tree is empty: {prefix}")
    if modes:
        raise RollingPluginError(f"Git archive omitted package paths at {revision[:12]}")
    return files


def _write_tree(destination: Path, files: Mapping[str, tuple[bytes, bool]]) -> None:
    staging = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    _unlinked_ancestors(destination)
    _unlinked_ancestors(staging)
    if staging.exists():
        _remove_cache_tree(staging, destination.parent)
    for relative, (content, executable) in files.items():
        target = staging / _safe_path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        if executable:
            target.chmod(target.stat().st_mode | 0o111)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        _remove_cache_tree(destination, destination.parent)
    os.replace(staging, destination)


def _verified_tree(root: Path) -> None:
    if not root.is_dir() or root.is_symlink():
        raise RollingPluginError(f"verified package root is unavailable: {root}")
    current = root
    while current.parent != current:
        if current.is_symlink():
            raise RollingPluginError(f"verified package has a linked ancestor: {current}")
        try:
            if current.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise RollingPluginError(f"verified package has a reparse ancestor: {current}")
        except AttributeError:
            pass
        current = current.parent
    for directory, names, files in os.walk(root):
        current = Path(directory)
        if current.is_symlink() or not stat.S_ISDIR(current.lstat().st_mode):
            raise RollingPluginError(f"verified package contains a link: {current}")
        for name in [*names, *files]:
            path = current / name
            if path.is_symlink():
                raise RollingPluginError(f"verified package contains a link: {path}")
            try:
                status = path.lstat()
                attributes = status.st_file_attributes
            except AttributeError:
                status = path.lstat()
                attributes = 0
            except OSError as error:
                raise RollingPluginError(f"cannot inspect verified package path {path}: {error}") from error
            if attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise RollingPluginError(f"verified package contains a reparse point: {path}")
            if name in files and not stat.S_ISREG(status.st_mode):
                raise RollingPluginError(f"verified package contains a special file: {path}")


def _linked(path: Path) -> bool:
    try:
        status = path.lstat()
    except OSError as error:
        raise RollingPluginError(f"cannot inspect cache path {path}: {error}") from error
    return path.is_symlink() or bool(getattr(status, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _remove_cache_tree(path: Path, cache: Path) -> None:
    _unlinked_ancestors(cache)
    _unlinked_ancestors(path)
    if not path.exists():
        return
    try:
        path.parent.resolve().relative_to(cache.resolve())
    except ValueError:
        raise RollingPluginError(f"cache deletion escapes its cache root: {path}") from None
    if _linked(path) or not path.is_dir():
        raise RollingPluginError(f"refusing to delete linked or non-directory cache path: {path}")
    for directory, names, _files in os.walk(path, followlinks=False):
        current = Path(directory)
        if _linked(current):
            raise RollingPluginError(f"refusing to delete linked cache path: {current}")
        for name in names:
            child = current / name
            if _linked(child):
                raise RollingPluginError(f"refusing to delete linked cache path: {child}")
    shutil.rmtree(path)


def _harness_dependencies(package: Package) -> list[tuple[str, str | None]]:
    harness = package.root / "harness.json"
    if not harness.is_file():
        return []
    value = _json(harness).get("requires")
    plugins = value.get("plugins") if isinstance(value, dict) else None
    if not isinstance(plugins, list) or not all(isinstance(item, str) and "/" in item for item in plugins):
        raise RollingPluginError(f"invalid harness dependencies in {harness}")
    sources = {}
    marketplaces = value.get("marketplaces") if isinstance(value, dict) else None
    if not isinstance(marketplaces, (list, dict)):
        raise RollingPluginError(f"invalid harness marketplaces in {harness}")
    items = marketplaces.items() if isinstance(marketplaces, dict) else ((item.get("id"), item) for item in marketplaces if isinstance(item, dict))
    for identifier, marketplace in items:
        repository = marketplace if isinstance(marketplace, str) else marketplace.get("repository") if isinstance(marketplace, Mapping) else None
        if not isinstance(identifier, str) or not isinstance(repository, str):
            raise RollingPluginError(f"invalid harness marketplace in {harness}")
        source = canonical_source(f"https://github.com/{repository}.git")
        if source is None:
            raise RollingPluginError(f"harness marketplace is not tj-agents: {repository}")
        sources[identifier] = source
    return [(dependency, sources.get(dependency.split("/", 1)[0])) for dependency in plugins]


def _package_key(package: Package) -> str:
    return f"{package.marketplace}/{package.identity.rsplit('@', 1)[0]}"


def _state(source: str, cache: Path, catalog_cache: dict[str, tuple[Path, str, dict]], published: set[tuple[str, str]],
           deadline: Deadline) -> tuple[str, Path, str, dict]:
    authenticated = canonical_source(source)
    if authenticated is None:
        raise RollingPluginError("publisher is not an authenticated tj-agents source")
    if authenticated not in catalog_cache:
        clone, revision = _fetch_main(authenticated, cache, deadline)
        if authenticated == "https://github.com/tj-agents/core.git" and (authenticated, revision) not in published:
            _publication_gate(clone, revision, deadline)
            published.add((authenticated, revision))
        catalog_cache[authenticated] = clone, revision, _catalog(clone, revision, deadline)
    clone, revision, catalog = catalog_cache[authenticated]
    return authenticated, clone, revision, catalog


def _materialize(selection: Selection, cache: Path, catalog_cache: dict[str, tuple[Path, str, dict]], published: set[tuple[str, str]],
                 deadline: Deadline) -> Package:
    source, clone, revision, catalog = _state(selection.source_url, cache, catalog_cache, published, deadline)
    visited: set[tuple[str, str]] = set()
    while True:
        marker = (source, selection.name)
        if marker in visited:
            raise RollingPluginError(f"publisher catalog source cycle includes {selection.name}")
        visited.add(marker)
        next_source, source_path = _entry_source(_entry(catalog, selection.name), source)
        if next_source == source:
            break
        source, clone, revision, catalog = _state(next_source, cache, catalog_cache, published, deadline)
    root = cache / "packages" / _cache_name(source) / revision / selection.marketplace / selection.name
    files = _tree_files(clone, revision, source_path, deadline)
    _write_tree(root, files)
    return Package(selection.identity, selection.marketplace, source, revision, source_path, root)


def resolve(selections: Iterable[Selection], cache: Path, disabled: Iterable[str] = (), deadline: Deadline | None = None,
            source_revisions: dict[str, str] | None = None) -> list[Package]:
    deadline = deadline or Deadline()
    selected = {selection.identity: selection for selection in selections}
    disabled = set(disabled)
    if not selected:
        return []
    catalog_cache: dict[str, tuple[Path, str, dict]] = {}
    published: set[tuple[str, str]] = set()
    prepared: dict[str, Package] = {}
    resolving: set[str] = set()

    def visit(selection: Selection) -> None:
        if selection.identity in prepared:
            return
        if selection.identity in resolving:
            raise RollingPluginError(f"plugin dependency cycle includes {selection.identity}")
        resolving.add(selection.identity)
        try:
            package = _materialize(selection, cache, catalog_cache, published, deadline)
            for dependency, source in _harness_dependencies(package):
                marketplace, name = dependency.split("/", 1)
                identity = f"{name}@{marketplace}"
                if identity == selection.identity:
                    continue
                if identity in disabled:
                    raise RollingPluginError(f"selected package {selection.identity} requires explicitly disabled package {identity}")
                explicit = selected.get(identity)
                if explicit is not None:
                    visit(explicit)
                elif source is None:
                    raise RollingPluginError(f"package {selection.identity} has no source for required dependency {dependency}")
                else:
                    visit(Selection(identity, source, marketplace))
            prepared[selection.identity] = package
        finally:
            resolving.remove(selection.identity)

    for selection in selected.values():
        visit(selection)
    if source_revisions is not None:
        source_revisions.update({source: revision for source, (_clone, revision, _catalog_value) in catalog_cache.items()})
    return [prepared[identity] for identity in sorted(prepared)]


def _projection(host: str, packages: Iterable[Package], cache: Path) -> tuple[Path, tuple[Path, ...]]:
    packages = list(packages)
    _unlinked_ancestors(cache)
    if not packages:
        root = cache / "catalogs" / host / "empty"
        _unlinked_ancestors(root)
        root.mkdir(parents=True, exist_ok=True)
        return root, ()
    digest = hashlib.sha256(json.dumps([
        (package.identity, package.marketplace, package.repository, package.revision, package.path)
        for package in sorted(packages, key=lambda item: item.identity)
    ], separators=(",", ":")).encode("utf-8")).hexdigest()
    root = cache / "catalogs" / host / digest
    _unlinked_ancestors(root)
    if root.exists():
        _remove_cache_tree(root, cache)
    by_market: dict[str, list[Package]] = {}
    for package in packages:
        by_market.setdefault(package.marketplace, []).append(package)
    for marketplace, members in by_market.items():
        catalog_root = root / _cache_component(marketplace)
        plugins = []
        for package in members:
            _verified_tree(package.root)
            name = _cache_component(package.identity.rsplit("@", 1)[0])
            target = catalog_root / "plugins" / name
            if target.exists():
                _remove_cache_tree(target, cache)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(package.root, target)
            relative = f"./plugins/{name}"
            plugins.append({"name": name, "source": relative if host == "claude" else {"source": "local", "path": relative}})
        catalog = {"name": marketplace, "owner": {"name": marketplace}, "plugins": plugins}
        catalog_path = catalog_root / (".claude-plugin" if host == "claude" else ".agents/plugins") / "marketplace.json"
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    catalog_base = cache / "catalogs" / host
    for candidate in catalog_base.iterdir():
        if candidate != root and candidate.is_dir():
            _remove_cache_tree(candidate, cache)
    return root, tuple(package.root for package in packages)


@contextmanager
def exclusive(cache: Path, wait: float = LOCK_WAIT_SECONDS, deadline: Deadline | None = None):
    lock = cache / "rolling-plugins.lock"
    _unlinked_ancestors(lock)
    cache.mkdir(parents=True, exist_ok=True)
    until = deadline or Deadline(wait if wait > 0 else 0.001)
    handle = lock.open("a+b")
    while True:
        try:
            if os.name == "nt":
                import msvcrt
                handle.seek(0)
                if handle.tell() == 0:
                    handle.write(b"0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except OSError:
            try:
                until.remaining(0.1)
            except RollingPluginError:
                handle.close()
                raise RollingPluginError("another launch is preparing rolling plugins") from None
            time.sleep(0.1)
    try:
        handle.seek(0)
        handle.write(str(os.getpid()).encode("ascii")[:1])
        handle.flush()
        yield
    finally:
        try:
            if os.name == "nt":
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def _cache_root(host: str, target: Path, arguments: Mapping[str, object]) -> Path:
    root = Path(arguments.get("cache_root") or target / "plugins" / "cache" / ".tj-agents-rolling" / host)
    _unlinked_ancestors(root)
    _unlinked_ancestors(target / "plugins" / "cache")
    expected = (target / "plugins" / "cache").resolve()
    try:
        root.resolve().relative_to(expected)
    except ValueError:
        raise RollingPluginError(f"rolling cache must remain under the host plugin cache: {root}") from None
    return root


def _selection_state(host: str, target: Path, project: Path, arguments: Mapping[str, object]) -> tuple[list[Selection], set[str]]:
    if host == "claude":
        argv = arguments.get("argv") or ()
        return (
            selected_claude(target, Path(arguments.get("plugins_root") or target / "plugins"), project, argv),
            {identity for identity, value in claude_enabled(target, project, argv).items() if value is False},
        )
    reader = arguments.get("selection_reader")
    if not callable(reader):
        raise RollingPluginError("Codex rolling preflight requires an effective configuration reader")
    value = reader()
    disabled = set()
    if isinstance(value, Mapping):
        raw_disabled = value.get("disabled")
        if raw_disabled is not None:
            if not isinstance(raw_disabled, list) or not all(isinstance(identity, str) and identity.count("@") == 1 for identity in raw_disabled):
                raise RollingPluginError("Codex effective configuration has invalid disabled plugin identities")
            disabled = set(raw_disabled)
        value = value.get("selections")
    return supplied_selections(value), disabled


def _read_selections(host: str, target: Path, project: Path, arguments: Mapping[str, object]) -> list[Selection]:
    return _selection_state(host, target, project, arguments)[0]


def _prepare(host: str, target: Path, project: Path, arguments: Mapping[str, object], cache: Path,
             deadline: Deadline | None = None) -> Prepared:
    deadline = deadline or Deadline()
    if host not in {"claude", "codex"}:
        raise RollingPluginError(f"unsupported host: {host}")
    if host == "claude":
        plugins = Path(arguments.get("plugins_root") or target / "plugins")
        argv = arguments.get("argv") or ()
        selections = selected_claude(target, plugins, project, argv)
        disabled = {identity for identity, value in claude_enabled(target, project, argv).items() if value is False}
    else:
        plugins = target / "plugins"
        inventory = arguments.get("inventory")
        supplied = arguments.get("selections")
        if supplied is not None:
            selections = supplied_selections(supplied)
        else:
            if not isinstance(inventory, Mapping):
                raise RollingPluginError("Codex rolling preparation requires native plugin inventory")
            selections = selected_codex(inventory)
        disabled = set(arguments.get("disabled") or ())
    revisions: dict[str, str] = {}
    packages = resolve(selections, cache, disabled, deadline, revisions)
    catalog, roots = _projection(host, packages, cache)
    final, final_disabled = _selection_state(host, target, project, arguments)
    if {(item.identity, item.source_url) for item in final} != {(item.identity, item.source_url) for item in selections}:
        raise RollingPluginError("plugin selection changed while preparing the rolling package set")
    if final_disabled != disabled:
        raise RollingPluginError("plugin disablement changed while preparing the rolling package set")
    verified = tuple(VerifiedRoot(package.identity, package.root, package.revision, package.repository) for package in packages)
    if host == "codex":
        launch_args = []
        for marketplace in sorted({package.marketplace for package in packages}):
            market_catalog = catalog / marketplace
            launch_args.extend(("-c", f'marketplaces.{marketplace}.source_type="local"', "-c",
                                f'marketplaces.{marketplace}.source="{market_catalog}"'))
        for package in packages:
            launch_args.extend(("-c", f"plugins.{package.identity}.enabled=true"))
        return Prepared(host, tuple(launch_args), verified, catalog, {}, tuple(selections),
                        tuple(sorted(revisions.items())), plugins, deadline, tuple(sorted(disabled)))
    environment = {} if plugins == target / "plugins" else {"CLAUDE_CODE_PLUGIN_CACHE_DIR": str(plugins)}
    if not packages:
        return Prepared(host, (), verified, catalog, environment, tuple(selections), tuple(sorted(revisions.items())), plugins,
                        deadline, tuple(sorted(disabled)))
    effective, supplied = claude_settings(target, project, arguments.get("argv") or ())
    settings = dict(supplied)
    enabled = effective.get("enabledPlugins")
    enabled = dict(enabled) if isinstance(enabled, dict) else {}
    enabled.update({package.identity: True for package in packages})
    settings["enabledPlugins"] = enabled
    marketplaces = settings.get("extraKnownMarketplaces")
    marketplaces = dict(marketplaces) if isinstance(marketplaces, dict) else {}
    known = _json(plugins / "known_marketplaces.json")
    effective_marketplaces = effective.get("extraKnownMarketplaces")
    effective_marketplaces = effective_marketplaces if isinstance(effective_marketplaces, dict) else {}
    for marketplace in {package.marketplace for package in packages}:
        configured = effective_marketplaces.get(marketplace)
        configured = dict(configured) if isinstance(configured, dict) else {}
        if "source" not in configured:
            registered = known.get(marketplace)
            if isinstance(registered, Mapping) and isinstance(registered.get("source"), Mapping):
                configured["source"] = dict(registered["source"])
        configured["autoUpdate"] = False
        marketplaces[marketplace] = configured
    settings["extraKnownMarketplaces"] = marketplaces
    launch_args = ("--settings", json.dumps(settings, separators=(",", ":")))
    return Prepared(host, launch_args, verified, catalog, environment, tuple(selections), tuple(sorted(revisions.items())), plugins,
                    deadline, tuple(sorted(disabled)))


def _native(command: list[str], cwd: Path, environment: Mapping[str, str], deadline: Deadline | None = None,
            json_output: bool = False) -> object:
    completed = _completed(command, cwd, environment, deadline or Deadline())
    if completed.returncode:
        raise RollingPluginError((completed.stderr or completed.stdout or b"native plugin command failed").decode("utf-8", "replace").strip())
    output = completed.stdout.decode("utf-8", "replace")
    if not json_output:
        return output
    try:
        value = json.loads(output)
    except ValueError as error:
        raise RollingPluginError("native plugin command did not return JSON") from error
    return value


def _promote(source: Path, destination: Path, expected: Path, cache: Path, root: VerifiedRoot,
             allow_adopt: bool = False) -> Path:
    _verified_tree(source)
    if _tree_bytes(source) != _tree_bytes(expected):
        raise RollingPluginError(f"native package differs from verified Git package: {source}")
    try:
        destination.parent.resolve().relative_to(cache.resolve())
    except ValueError:
        raise RollingPluginError(f"native plugin cache destination escapes cache: {destination}") from None
    _unlinked_ancestors(cache)
    _unlinked_ancestors(destination)
    if destination.exists():
        marker = destination.parent / ".tj-agents-rolling.json"
        owned = _json(marker) if marker.exists() else None
        if owned and (owned.get("identity") != root.identity or owned.get("repository") != root.repository):
            raise RollingPluginError(f"refusing to replace unowned native plugin cache root {destination}")
        if not owned:
            if not allow_adopt:
                raise RollingPluginError(f"refusing to replace unowned native plugin cache root {destination}")
            _verified_tree(destination)
        _remove_cache_tree(destination, cache)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)
    _verified_tree(destination)
    _write_json(destination.parent / ".tj-agents-rolling.json", {
        "schema_version": 1, "identity": root.identity, "repository": root.repository, "revision": root.revision,
    })
    return destination


def _tree_bytes(root: Path) -> dict[str, tuple[bytes, bool]]:
    _verified_tree(root)
    result = {}
    for directory, _names, files in os.walk(root):
        current = Path(directory)
        for name in files:
            path = current / name
            result[path.relative_to(root).as_posix()] = (path.read_bytes(), bool(path.stat().st_mode & 0o111))
    return result


def _within(child: Path, parent: Path) -> bool:
    child_key = os.path.normcase(str(child.resolve())).rstrip("\\/")
    parent_key = os.path.normcase(str(parent.resolve())).rstrip("\\/")
    return child_key == parent_key or child_key.startswith(parent_key + os.sep)


def _claude_install_targets(registry: Mapping[str, object], identity: str, project: Path) -> list[tuple[str, Path]]:
    targets: set[tuple[str, Path]] = set()
    records = registry.get(identity)
    for record in records if isinstance(records, list) else ():
        if not isinstance(record, dict):
            continue
        scope = record.get("scope")
        if scope in {"user", "managed"}:
            targets.add((scope, project))
        elif scope in {"project", "local"} and isinstance(record.get("projectPath"), str):
            owner = Path(record["projectPath"])
            if _within(project, owner):
                targets.add((scope, owner))
    return sorted(targets) or [("user", project)]


def _registry_paths(value: object) -> set[Path]:
    result: set[Path] = set()
    if isinstance(value, Mapping):
        candidate = value.get("installPath")
        if isinstance(candidate, str) and candidate:
            result.add(Path(candidate))
        for child in value.values():
            result.update(_registry_paths(child))
    elif isinstance(value, list):
        for child in value:
            result.update(_registry_paths(child))
    return result


def _claude_pinned_paths() -> set[Path]:
    state = Path(os.environ.get("AGENT_STATE_DIRECTORY") or Path.home() / ".agents-state")
    pins = state / "plugin-pins"
    protected: set[Path] = set()
    try:
        candidates = tuple(pins.glob("*.json"))
    except OSError:
        return protected
    for candidate in candidates:
        if _linked(candidate):
            raise RollingPluginError(f"Claude plugin pin is linked: {candidate}")
        try:
            document = _json(candidate)
        except RollingPluginError:
            continue
        protected.update(_registry_paths(document))
        values = document.get("paths")
        if isinstance(values, list):
            protected.update(Path(value) for value in values if isinstance(value, str) and value)
    return protected


def _pin_claude_cache(config: Path, deadline: Deadline) -> None:
    script = Path(__file__).with_name("prune_plugin_cache.py")
    if not script.is_file():
        raise RollingPluginError("Claude plugin cache pin helper is unavailable")
    completed = _completed([sys.executable, "-B", str(script), "--config-dir", str(config), "--pin"],
                           config, {}, deadline)
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).decode("utf-8", "replace").strip() or "no output"
        raise RollingPluginError(f"could not pin the Claude plugin cache: {detail}")


def _prune_native_cache(cache: Path, active: Iterable[Path], roots: Iterable[VerifiedRoot]) -> None:
    roots = tuple(roots)
    protected = {path.resolve() for path in active if path.exists()}
    protected.update(root.root.resolve() for root in roots if root.root.exists())
    expected = {root.identity: root.repository for root in roots}
    if not cache.is_dir():
        return
    for marker in cache.rglob(".tj-agents-rolling.json"):
        parent = marker.parent
        if _linked(marker) or _linked(parent):
            raise RollingPluginError(f"rolling cache contains a linked ownership marker: {marker}")
        value = _json(marker)
        identity = value.get("identity")
        repository = value.get("repository")
        if expected.get(identity) != repository:
            continue
        for candidate in parent.iterdir():
            if candidate == marker:
                continue
            if _linked(candidate):
                raise RollingPluginError(f"rolling cache contains a linked package root: {candidate}")
            if not candidate.is_dir():
                continue
            resolved = candidate.resolve()
            if any(resolved == path or _within(path, resolved) or _within(resolved, path) for path in protected):
                continue
            _verified_tree(candidate)
            _remove_cache_tree(candidate, cache)


def _write_json(path: Path, value: object) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    _unlinked_ancestors(path)
    _unlinked_ancestors(temporary)
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _codex_inventory_selects(entries: object, identity: str) -> bool:
    if not isinstance(entries, list):
        return False
    name, marketplace = identity.rsplit("@", 1)
    return any(
        isinstance(entry, Mapping)
        and entry.get("pluginId") == identity
        and entry.get("enabled") is True
        and entry.get("marketplaceName", marketplace) == marketplace
        and entry.get("name", name) == name
        for entry in entries
    )


def _codex_inventory_entries(inventory: object) -> list[object]:
    if not isinstance(inventory, Mapping):
        raise RollingPluginError("Codex did not return its installed native inventory")
    entries = inventory.get("installed")
    if entries is None:
        entries = inventory.get("plugins")
    if not isinstance(entries, list):
        raise RollingPluginError("Codex did not return its installed native inventory")
    return entries


def _claude_registry_authenticates(registry: Mapping[str, object], known: Mapping[str, object], identity: str) -> bool:
    marketplace = identity.rsplit("@", 1)[1]
    entry = known.get(marketplace)
    source = source_url(entry.get("source")) if isinstance(entry, Mapping) else None
    if canonical_source(source or "") is None:
        return False
    records = registry.get(identity)
    return isinstance(records, list) and any(isinstance(record, Mapping) for record in records)


def materialize_native(prepared: Prepared, host: str, target: Path, project: Path, executable: str) -> Prepared:
    if not prepared.selected_roots:
        return prepared
    packages = {root.identity: root for root in prepared.selected_roots}
    plugins = prepared.plugins_root or target / "plugins"
    actual_cache = plugins / "cache"
    _unlinked_ancestors(actual_cache)
    deadline = prepared.deadline or Deadline()
    with tempfile.TemporaryDirectory(prefix=f"tj-agents-{host}-") as temporary:
        temporary_root = Path(temporary)
        roots = []
        if host == "codex":
            environment = {"CODEX_HOME": str(temporary_root)}
            inventory = _native([executable, *prepared.launch_args, "plugin", "list", "--json"], project,
                                prepared.environment, deadline, True)
            entries = _codex_inventory_entries(inventory)
            for identity, expected in packages.items():
                response = _native([executable, *prepared.launch_args, "plugin", "add", identity, "--json"], project, environment, deadline, True)
                raw_path = response.get("installedPath") if isinstance(response, Mapping) else None
                if not isinstance(raw_path, str):
                    raise RollingPluginError(f"Codex did not report an installed path for {identity}")
                name, marketplace = identity.rsplit("@", 1)
                destination = actual_cache / marketplace / name / "local"
                root = _promote(Path(raw_path), destination, expected.root, actual_cache, expected,
                                allow_adopt=_codex_inventory_selects(entries, identity))
                roots.append(VerifiedRoot(identity, root, expected.revision, expected.repository))
            inventory = _native([executable, *prepared.launch_args, "plugin", "list", "--json"], project,
                                prepared.environment, deadline, True)
            entries = _codex_inventory_entries(inventory)
            for root in roots:
                name, marketplace = root.identity.rsplit("@", 1)
                matching = [entry for entry in entries if isinstance(entry, Mapping) and entry.get("pluginId") == root.identity]
                if not matching:
                    raise RollingPluginError(f"Codex did not retain {root.identity} in its native inventory")
                expected_path = actual_cache / marketplace / name / "local"
                versions = {entry.get("version") for entry in matching}
                if "local" not in versions or not expected_path.is_dir() or expected_path != root.root or not _codex_inventory_selects(matching, root.identity):
                    raise RollingPluginError(f"Codex native inventory did not select the promoted root for {root.identity}")
            _prune_native_cache(actual_cache, [root.root for root in roots], roots)
        elif host == "claude":
            config = temporary_root / "config"
            plugin_root = temporary_root / "plugins"
            known = _json(plugins / "known_marketplaces.json")
            entries = {}
            last_updated = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            for identity, expected in packages.items():
                marketplace = identity.rsplit("@", 1)[1]
                original = known.get(marketplace)
                if not isinstance(original, dict):
                    raise RollingPluginError(f"selected marketplace is no longer registered: {marketplace}")
                catalog = prepared.catalog_root / marketplace
                entries[marketplace] = {
                    "source": {"source": "directory", "path": str(catalog)},
                    "installLocation": str(catalog),
                    "autoUpdate": False,
                    "lastUpdated": last_updated,
                }
            (config / "plugins").mkdir(parents=True)
            (config / "plugins" / "known_marketplaces.json").write_text(json.dumps(entries), encoding="utf-8")
            plugin_root.mkdir(parents=True)
            (plugin_root / "known_marketplaces.json").write_text(json.dumps(entries), encoding="utf-8")
            (config / "settings.json").write_text(json.dumps({"enabledPlugins": {identity: True for identity in packages}}), encoding="utf-8")
            environment = {"CLAUDE_CONFIG_DIR": str(config), "CLAUDE_CODE_PLUGIN_CACHE_DIR": str(plugin_root)}
            registry_path = plugins / "installed_plugins.json"
            if registry_path.exists():
                before_document = _json(registry_path)
            else:
                before_document = {"version": 2, "plugins": {}}
            before = before_document.get("plugins")
            if not isinstance(before, dict):
                raise RollingPluginError("Claude installed plugin registry has invalid plugins")
            for identity in packages:
                _native([executable, "plugin", "install", identity, "--scope", "user"], project, environment, deadline)
            maintenance = _json(plugin_root / "installed_plugins.json")
            installed = maintenance.get("plugins")
            if not isinstance(installed, dict):
                raise RollingPluginError("Claude did not write a disposable plugin registry")
            document = copy.deepcopy(before_document)
            registry = document.setdefault("plugins", {})
            if not isinstance(registry, dict):
                raise RollingPluginError("Claude did not write an installed plugin registry")
            for identity, expected in packages.items():
                records = installed.get(identity)
                user_path = next((item.get("installPath") for item in records or [] if isinstance(item, dict)
                                  and item.get("scope") == "user" and isinstance(item.get("installPath"), str)), None)
                if not isinstance(user_path, str):
                    raise RollingPluginError(f"Claude did not install {identity}")
                name, marketplace = identity.rsplit("@", 1)
                destination = actual_cache / marketplace / name / expected.revision
                promoted = _promote(
                    Path(user_path), destination, expected.root, actual_cache, expected,
                    allow_adopt=_claude_registry_authenticates(before, known, identity),
                )
                targets = _claude_install_targets(before, identity, project)
                existing = registry.get(identity)
                existing = existing if isinstance(existing, list) else []
                if not existing:
                    existing = [{"scope": "user"}]
                    registry[identity] = existing
                paths = []
                for item in existing:
                    if not isinstance(item, dict):
                        continue
                    scope = item.get("scope")
                    owner = item.get("projectPath")
                    key = (scope, Path(owner)) if isinstance(owner, str) else (scope, project)
                    if (scope in {"user", "managed"} and any(target_scope == scope for target_scope, _owner in targets)) or (
                            scope in {"project", "local"} and isinstance(owner, str) and any(target_scope == scope and _within(project, target_owner) and _within(Path(owner), target_owner) for target_scope, target_owner in targets)):
                        item["installPath"] = str(promoted)
                        paths.append(promoted)
                if not paths:
                    existing.append({"scope": "user", "installPath": str(promoted)})
                    paths.append(promoted)
                if any(path != promoted for path in paths):
                    raise RollingPluginError(f"Claude did not repoint every selected install for {identity}")
                for root in paths:
                    _verified_tree(root)
                    if _tree_bytes(root) != _tree_bytes(expected.root):
                        raise RollingPluginError(f"Claude installed package differs from verified Git package: {identity}")
                roots.append(VerifiedRoot(identity, promoted, expected.revision, expected.repository))
            registry_written = False
            try:
                _write_json(registry_path, document)
                registry_written = True
                inventory = _native([executable, *prepared.launch_args, "plugin", "list", "--json"], project,
                                    prepared.environment, deadline, True)
                if not isinstance(inventory, list):
                    raise RollingPluginError("Claude did not return its native plugin inventory")
                for root in roots:
                    entries = [entry for entry in inventory if isinstance(entry, Mapping) and entry.get("id") == root.identity]
                    if not any(entry.get("enabled") is True and entry.get("installPath") == str(root.root) for entry in entries):
                        raise RollingPluginError(f"Claude native inventory did not select the promoted root for {root.identity}")
                if plugins == target / "plugins":
                    _pin_claude_cache(target, deadline)
                    _prune_native_cache(actual_cache, _registry_paths(document) | _claude_pinned_paths(), roots)
            except BaseException:
                if registry_written:
                    try:
                        _write_json(registry_path, before_document)
                    except OSError:
                        pass
                raise
        else:
            raise RollingPluginError(f"unsupported host: {host}")
    return Prepared(prepared.host, prepared.launch_args, tuple(roots), prepared.catalog_root, prepared.environment,
                    prepared.selections, prepared.source_revisions, prepared.plugins_root, deadline, prepared.disabled)


def hook_trust_arguments(prepared: Prepared) -> tuple[str, ...]:
    return prepared.launch_args


def verify_final(prepared: Prepared, host: str, target: Path, project: Path, arguments: Mapping[str, object]) -> None:
    current, disabled = _selection_state(host, target, project, arguments)
    expected = {(selection.identity, selection.source_url) for selection in prepared.selections}
    actual = {(selection.identity, selection.source_url) for selection in current}
    if expected != actual:
        raise RollingPluginError("plugin selection changed while materializing native packages")
    if tuple(sorted(disabled)) != prepared.disabled:
        raise RollingPluginError("plugin disablement changed while materializing native packages")
    cache = _cache_root(host, target, arguments)
    for source, expected_revision in prepared.source_revisions:
        _clone, revision = _fetch_main(source, cache, prepared.deadline)
        if revision != expected_revision:
            raise RollingPluginError(f"publisher main advanced while materializing {source}")


def terminate_process_tree(process: subprocess.Popen, timeout: float = 5) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/pid", str(process.pid), "/t", "/f"], stdin=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        except OSError:
            process.terminate()
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        if os.name != "nt":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except OSError:
                process.kill()
        process.wait()


def preflight(host: str, target: Path, project: Path, arguments: Mapping[str, object] | None = None) -> Preflight:
    return Preflight(host, target.absolute(), project.resolve(), arguments)


def prepare(host: str, target: Path, project: Path, arguments: Mapping[str, object] | None = None) -> Prepared:
    with preflight(host, target, project, arguments) as active:
        return active.acknowledge_binding()
