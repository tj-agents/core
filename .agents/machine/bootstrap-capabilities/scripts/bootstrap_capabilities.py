#!/usr/bin/env python3
"""Install or verify an exact project capability lock through a native host CLI."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
from typing import Any, Iterable


LOCK_NAME = "capabilities.lock.json"
STATE_DIRECTORY = "capability-bootstrap"
HEX_COMMIT = re.compile(r"^[0-9a-f]{40}$")
SAFE_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class BootstrapError(RuntimeError):
    """A user-visible validation or installation failure."""


class BootstrapRunError(BootstrapError):
    """A failure carrying the operations completed before it stopped."""

    def __init__(self, report: dict[str, Any]):
        super().__init__(report["errors"][-1])
        self.report = report


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise BootstrapError(f"Cannot read JSON at {path}: {error}") from error
    if not isinstance(value, dict):
        raise BootstrapError(f"Expected a JSON object at {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def find_catalog(script: Path) -> Path:
    override = os.environ.get("AGENT_CAPABILITY_CATALOG")
    if override:
        candidate = Path(override).expanduser().resolve()
        if candidate.is_file():
            return candidate
        raise BootstrapError(f"AGENT_CAPABILITY_CATALOG does not name a file: {candidate}")
    for parent in (script.parent, *script.parents):
        for relative in ("catalog/catalog.json", ".agents/catalog/catalog.json"):
            candidate = parent / relative
            if candidate.is_file():
                return candidate.resolve()
    raise BootstrapError("The packaged catalog/catalog.json could not be found beside this bootstrap.")


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise BootstrapError(f"{label} must be a non-empty string")
    return value


def require_string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise BootstrapError(f"{label} must be a list of non-empty strings")
    if len(value) != len(set(value)):
        raise BootstrapError(f"{label} contains duplicates")
    return value


def catalog_index(catalog: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    if catalog.get("schema_version") != 1 or catalog.get("digest_format") != "sha256-tree-v1":
        raise BootstrapError("Unsupported capability catalog schema or digest format")
    releases: dict[str, dict[str, Any]] = {}
    plugins: dict[str, dict[str, Any]] = {}
    values = catalog.get("releases")
    if not isinstance(values, list) or not values:
        raise BootstrapError("Catalog releases must be a non-empty list")
    for release in values:
        if not isinstance(release, dict):
            raise BootstrapError("Each catalog release must be an object")
        release_id = require_string(release.get("id"), "release.id")
        if release_id in releases:
            raise BootstrapError(f"Duplicate release id: {release_id}")
        marketplace = require_string(release.get("marketplace"), f"{release_id}.marketplace")
        version = require_string(release.get("version"), f"{release_id}.version")
        revision = require_string(release.get("revision"), f"{release_id}.revision")
        require_string(release.get("owner_repository"), f"{release_id}.owner_repository")
        require_string(release.get("source"), f"{release_id}.source")
        if not SAFE_NAME.fullmatch(marketplace):
            raise BootstrapError(f"Unsafe marketplace name: {marketplace}")
        if release_id != f"{marketplace}@{version}":
            raise BootstrapError(f"Release id must match marketplace and version: {release_id}")
        if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", revision):
            raise BootstrapError(f"Release revision must be an immutable semantic tag: {release_id}")
        release_plugins = release.get("plugins")
        if not isinstance(release_plugins, list) or not release_plugins:
            raise BootstrapError(f"{release_id}.plugins must be a non-empty list")
        releases[release_id] = release
        for plugin in release_plugins:
            if not isinstance(plugin, dict):
                raise BootstrapError(f"{release_id}.plugins must contain objects")
            plugin_id = require_string(plugin.get("id"), f"{release_id}.plugin.id")
            name = require_string(plugin.get("name"), plugin_id + ".name")
            expected_id = f"{marketplace}/{name}"
            if plugin_id != expected_id:
                raise BootstrapError(f"{plugin_id} must equal {expected_id}")
            if plugin_id in plugins:
                raise BootstrapError(f"Duplicate plugin id: {plugin_id}")
            package_path = PurePosixPath(require_string(plugin.get("package_path"), f"{plugin_id}.package_path"))
            if package_path.is_absolute() or ".." in package_path.parts or package_path.as_posix() != f"plugins/{name}":
                raise BootstrapError(f"Unsafe or mismatched package path for {plugin_id}")
            platforms = require_string_list(plugin.get("platforms"), f"{plugin_id}.platforms")
            if not platforms:
                raise BootstrapError(f"{plugin_id}.platforms must not be empty")
            status = require_string(plugin.get("status"), f"{plugin_id}.status")
            if status not in {"current", "deprecated"}:
                raise BootstrapError(f"Invalid status for {plugin_id}: {status}")
            require_string(plugin.get("version"), f"{plugin_id}.version")
            require_string(plugin.get("description"), f"{plugin_id}.description")
            require_string_list(plugin.get("skills"), f"{plugin_id}.skills")
            excludes = require_string_list(plugin.get("digest_excludes", []), f"{plugin_id}.digest_excludes")
            for excluded in excludes:
                path = PurePosixPath(excluded)
                if path.is_absolute() or ".." in path.parts:
                    raise BootstrapError(f"Unsafe digest exclusion for {plugin_id}: {excluded}")
            dependencies = plugin.get("dependencies")
            if not isinstance(dependencies, dict):
                raise BootstrapError(f"{plugin_id}.dependencies must be an object")
            require_string_list(dependencies.get("required"), f"{plugin_id}.dependencies.required")
            require_string_list(dependencies.get("optional"), f"{plugin_id}.dependencies.optional")
            external = plugin.get("external_prerequisites")
            if not isinstance(external, dict):
                raise BootstrapError(f"{plugin_id}.external_prerequisites must be an object")
            require_string_list(external.get("required"), f"{plugin_id}.external_prerequisites.required")
            require_string_list(external.get("optional"), f"{plugin_id}.external_prerequisites.optional")
            digest = require_string(plugin.get("digest"), f"{plugin_id}.digest")
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
                raise BootstrapError(f"Invalid digest for {plugin_id}")
            plugin["_release"] = release
            plugins[plugin_id] = plugin
    for plugin_id, plugin in plugins.items():
        for dependency in plugin["dependencies"]["required"] + plugin["dependencies"]["optional"]:
            if dependency not in plugins:
                raise BootstrapError(f"{plugin_id} names unknown dependency {dependency}")
    detect_cycles(plugins)
    return releases, plugins


def detect_cycles(plugins: dict[str, dict[str, Any]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(plugin_id: str) -> None:
        if plugin_id in visiting:
            raise BootstrapError(f"Plugin dependency cycle includes {plugin_id}")
        if plugin_id in visited:
            return
        visiting.add(plugin_id)
        for dependency in plugins[plugin_id]["dependencies"]["required"]:
            visit(dependency)
        visiting.remove(plugin_id)
        visited.add(plugin_id)

    for plugin_id in plugins:
        visit(plugin_id)


def platform_name() -> str:
    if sys.platform == "win32":
        return "windows"
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform == "darwin":
        return "macos"
    return sys.platform


def check_required_prerequisites(selections: list[dict[str, Any]], plugins: dict[str, dict[str, Any]]) -> list[str]:
    checks: list[str] = []
    current_platform = platform_name()
    for selection in selections:
        plugin = plugins[selection["id"]]
        if current_platform not in plugin["platforms"]:
            raise BootstrapError(
                f"{selection['id']} supports {', '.join(plugin['platforms'])}, not {current_platform}"
            )
        checks.append(f"platform:{selection['id']}:{current_platform}")
        for prerequisite in plugin["external_prerequisites"]["required"]:
            if prerequisite == "python>=3.9":
                if sys.version_info < (3, 9):
                    raise BootstrapError("Python 3.9 or newer is required")
            elif prerequisite.startswith("exe:"):
                name = prerequisite.removeprefix("exe:")
                if not name or shutil.which(name) is None:
                    raise BootstrapError(f"{selection['id']} requires executable on PATH: {name}")
            elif prerequisite.startswith("platform:"):
                expected = prerequisite.removeprefix("platform:")
                if expected != current_platform:
                    raise BootstrapError(f"{selection['id']} requires platform {expected}")
            else:
                raise BootstrapError(
                    f"{selection['id']} has an unsupported required-prerequisite check: {prerequisite}"
                )
            checks.append(f"prerequisite:{selection['id']}:{prerequisite}")
    return checks


def validate_lock(
    lock: dict[str, Any], releases: dict[str, dict[str, Any]], plugins: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    if lock.get("schema_version") != 1:
        raise BootstrapError("Unsupported capability lock schema")
    selections = lock.get("plugins")
    if not isinstance(selections, list) or not selections:
        raise BootstrapError("Lock plugins must be a non-empty list")
    selected: dict[str, dict[str, Any]] = {}
    release_commits: dict[str, str] = {}
    for selection in selections:
        if not isinstance(selection, dict):
            raise BootstrapError("Each lock selection must be an object")
        plugin_id = require_string(selection.get("id"), "lock plugin id")
        release_id = require_string(selection.get("release"), f"{plugin_id}.release")
        commit = require_string(selection.get("commit"), f"{plugin_id}.commit")
        if not HEX_COMMIT.fullmatch(commit):
            raise BootstrapError(f"{plugin_id}.commit must be a full lowercase Git commit")
        if plugin_id in selected:
            raise BootstrapError(f"Duplicate lock selection: {plugin_id}")
        if plugin_id not in plugins:
            raise BootstrapError(f"Lock selects unknown plugin: {plugin_id}")
        if release_id not in releases or plugins[plugin_id]["_release"]["id"] != release_id:
            raise BootstrapError(f"{plugin_id} does not belong to catalog release {release_id}")
        prior = release_commits.setdefault(release_id, commit)
        if prior != commit:
            raise BootstrapError(f"Selections from {release_id} disagree on the exact commit")
        required_skills = require_string_list(selection.get("required_skills"), f"{plugin_id}.required_skills")
        unknown_skills = sorted(set(required_skills) - set(plugins[plugin_id]["skills"]))
        if unknown_skills:
            raise BootstrapError(f"{plugin_id} requires unknown skills: {', '.join(unknown_skills)}")
        scopes = selection.get("path_scopes")
        if not isinstance(scopes, list):
            raise BootstrapError(f"{plugin_id}.path_scopes must be a list")
        for scope in scopes:
            if not isinstance(scope, dict) or not isinstance(scope.get("path"), str) or not scope["path"]:
                raise BootstrapError(f"{plugin_id}.path_scopes contains an invalid path")
            scope_path = PurePosixPath(scope["path"].replace("\\", "/"))
            if scope_path.is_absolute() or ".." in scope_path.parts or re.match(r"^[A-Za-z]:", scope["path"]):
                raise BootstrapError(f"{plugin_id}.path_scopes must stay inside the project: {scope['path']}")
            scope_skills = require_string_list(scope.get("skills"), f"{plugin_id}.path_scopes.skills")
            unknown = sorted(set(scope_skills) - set(plugins[plugin_id]["skills"]))
            if unknown:
                raise BootstrapError(f"{plugin_id} path scope requires unknown skills: {', '.join(unknown)}")
        require_string_list(selection.get("exceptions"), f"{plugin_id}.exceptions")
        selected[plugin_id] = selection
    for plugin_id in selected:
        missing = sorted(set(plugins[plugin_id]["dependencies"]["required"]) - set(selected))
        if missing:
            raise BootstrapError(f"{plugin_id} is missing required plugin selections: {', '.join(missing)}")
    return [selected[plugin_id] for plugin_id in sorted(selected)]


def tree_digest(root: Path, excluded: Iterable[str]) -> str:
    excluded_paths = {PurePosixPath(value).as_posix() for value in excluded}
    if not root.is_dir():
        raise BootstrapError(f"Package directory does not exist: {root}")
    files: list[tuple[str, Path]] = []
    for path in root.rglob("*"):
        if path.is_symlink():
            raise BootstrapError(f"Package digest rejects symlinks: {path}")
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            if relative not in excluded_paths:
                files.append((relative, path))
    digest = hashlib.sha256()
    for relative, path in sorted(files):
        data = path.read_bytes()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(len(data)).encode("ascii"))
        digest.update(b"\0")
        digest.update(data)
    return "sha256:" + digest.hexdigest()


def executable(name: str) -> str:
    located = shutil.which(name)
    if not located:
        raise BootstrapError(f"Required executable was not found on PATH: {name}")
    return located


class NativeHost:
    def __init__(self, harness: str, profile: Path, run):
        self.harness = harness
        self.profile = profile
        self.command = executable(harness)
        self.run = run
        self.environment = os.environ.copy()
        self.environment["CODEX_HOME" if harness == "codex" else "CLAUDE_CONFIG_DIR"] = str(profile)

    def invoke(self, arguments: list[str], json_output: bool = False) -> Any:
        completed = self.run(
            [self.command, *arguments],
            env=self.environment,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise BootstrapError(f"{self.harness} {' '.join(arguments)} failed: {detail}")
        if not json_output:
            return completed.stdout
        try:
            return json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            raise BootstrapError(f"{self.harness} returned invalid JSON for {' '.join(arguments)}") from error

    def marketplaces(self) -> dict[str, str | None]:
        if self.harness == "codex":
            value = self.invoke(["plugin", "marketplace", "list", "--json"], True)
            return {
                item["name"]: item.get("root")
                for item in value.get("marketplaces", [])
                if isinstance(item, dict) and item.get("name")
            }
        output = self.invoke(["plugin", "marketplace", "list"])
        marketplaces: dict[str, str | None] = {}
        current: str | None = None
        for raw_line in output.splitlines():
            line = raw_line.strip()
            if current and line.startswith("Source: Directory (") and line.endswith(")"):
                marketplaces[current] = line[len("Source: Directory ("):-1]
            elif line and not line.startswith("Source:"):
                candidate = line.split()[-1]
                if SAFE_NAME.fullmatch(candidate):
                    current = candidate
                    marketplaces[current] = None
        return marketplaces

    def installed(self) -> dict[str, dict[str, Any]]:
        if self.harness == "codex":
            value = self.invoke(["plugin", "list", "--json"], True)
            return {
                item["pluginId"]: {
                    "enabled": bool(item.get("installed") and item.get("enabled")),
                    "version": item.get("version"),
                    "path": (item.get("source") or {}).get("path") if isinstance(item.get("source"), dict) else None,
                }
                for item in value.get("installed", [])
                if isinstance(item, dict) and item.get("pluginId")
            }
        value = self.invoke(["plugin", "list", "--json"], True)
        return {
            item["id"]: {
                "enabled": bool(item.get("enabled")),
                "version": item.get("version"),
                "path": item.get("installPath"),
            }
            for item in value
            if isinstance(item, dict) and item.get("id") and item.get("scope") == "user"
        }

    def add_marketplace(self, checkout: Path) -> None:
        arguments = ["plugin", "marketplace", "add", str(checkout)]
        if self.harness == "claude":
            arguments += ["--scope", "user"]
        self.invoke(arguments)

    def install(self, identity: str) -> None:
        if self.harness == "codex":
            self.invoke(["plugin", "add", identity])
        else:
            self.invoke(["plugin", "install", identity, "--scope", "user", "--yes"])

    def enable(self, identity: str) -> None:
        if self.harness == "claude":
            self.invoke(["plugin", "enable", identity, "--scope", "user"])
        else:
            self.install(identity)

    def refresh(self, identity: str) -> None:
        if self.harness == "codex":
            self.install(identity)
        else:
            self.invoke(["plugin", "update", identity, "--scope", "user", "--yes"])


def git(run, arguments: list[str], cwd: Path | None = None) -> str:
    command = executable("git")
    completed = run(
        [command, *arguments], cwd=cwd, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise BootstrapError(f"git {' '.join(arguments)} failed: {detail}")
    return completed.stdout.strip()


def normalize_source(source: str) -> str:
    return source.rstrip("/").removesuffix(".git")


def release_state(release: dict[str, Any], commit: str, destination: Path) -> dict[str, str]:
    source = require_string(release.get("source"), f"{release['id']}.source")
    revision = require_string(release.get("revision"), f"{release['id']}.revision")
    return {
        "checkout": str(destination),
        "release": release["id"],
        "commit": commit,
        "source": normalize_source(source),
        "revision": revision,
    }


def validate_state_record(
    record: dict[str, Any], destination: Path, label: str, require_identity: bool = True
) -> None:
    expected_checkout = record.get("checkout")
    expected_release = record.get("release")
    expected_commit = record.get("commit")
    expected_source = record.get("source")
    expected_revision = record.get("revision")
    if (
        not isinstance(expected_checkout, str)
        or Path(expected_checkout).resolve() != destination.resolve()
        or not isinstance(expected_release, str)
        or "@" not in expected_release
        or not isinstance(expected_commit, str)
        or not HEX_COMMIT.fullmatch(expected_commit)
        or (expected_source is not None and (not isinstance(expected_source, str) or not expected_source))
        or (expected_revision is not None and (not isinstance(expected_revision, str) or not expected_revision))
        or (require_identity and (expected_source is None or expected_revision is None))
    ):
        raise BootstrapError(f"{label} is invalid for checkout: {destination}")


def state_revision(record: dict[str, Any]) -> str:
    if isinstance(record.get("revision"), str):
        return record["revision"]
    return f"v{record['release'].rsplit('@', 1)[1]}"


def validate_checkout_at(
    run,
    record: dict[str, Any],
    revision: str,
    destination: Path,
    label: str,
    allowed_sources: set[str] | None = None,
    require_identity: bool = True,
) -> None:
    validate_state_record(record, destination, label, require_identity)
    if not (destination / ".git").exists():
        raise BootstrapError(f"Managed checkout is missing: {destination}")
    if git(run, ["status", "--porcelain"], destination):
        raise BootstrapError(f"Managed checkout has local changes: {destination}")
    actual_commit = git(run, ["rev-parse", "HEAD"], destination)
    expected_commit = record["commit"]
    if actual_commit != expected_commit:
        raise BootstrapError(
            f"Managed checkout is {actual_commit}, {label} requires {expected_commit}: {destination}"
        )
    tag_ref = f"refs/tags/{revision}"
    tag_commit = git(run, ["rev-parse", f"{tag_ref}^{{commit}}"], destination)
    if tag_commit != expected_commit:
        raise BootstrapError(
            f"Managed checkout local tag {tag_ref} is {tag_commit}, {label} requires {expected_commit}"
        )
    if allowed_sources is not None:
        actual_source = normalize_source(git(run, ["remote", "get-url", "origin"], destination))
        if actual_source not in allowed_sources:
            expected_sources = ", ".join(sorted(allowed_sources))
            raise BootstrapError(
                f"Managed checkout origin is {actual_source}, {label} requires {expected_sources}: {destination}"
            )


def validate_managed_checkout(
    run, managed: dict[str, Any], destination: Path
) -> dict[str, str]:
    revision = state_revision(managed)
    validate_checkout_at(
        run, managed, revision, destination, "recorded state", require_identity=False
    )
    actual_source = normalize_source(git(run, ["remote", "get-url", "origin"], destination))
    recorded_source = managed.get("source")
    normalized = {
        **managed,
        "source": normalize_source(recorded_source) if isinstance(recorded_source, str) else actual_source,
        "revision": revision,
    }
    validate_checkout_at(
        run,
        normalized,
        revision,
        destination,
        "recorded state",
        {normalized["source"]},
    )
    return normalized


def validate_pending_transition(
    pending: dict[str, Any], managed: dict[str, Any], expected: dict[str, str], release: dict[str, Any]
) -> None:
    wanted = {
        "from": managed,
        "to": expected,
        "source": expected["source"],
        "revision": expected["revision"],
    }
    if pending != wanted:
        raise BootstrapError(f"Pending marketplace transition disagrees with the lock: {release['marketplace']}")


def validate_transition_checkout(
    run, pending: dict[str, Any], destination: Path
) -> None:
    prior = pending["from"]
    target = pending["to"]
    validate_state_record(prior, destination, "pending transition source")
    validate_state_record(target, destination, "pending transition target")
    if not (destination / ".git").exists():
        raise BootstrapError(f"Managed checkout is missing: {destination}")
    if git(run, ["status", "--porcelain"], destination):
        raise BootstrapError(f"Managed checkout has local changes: {destination}")
    actual_commit = git(run, ["rev-parse", "HEAD"], destination)
    allowed_sources = {prior["source"], target["source"]}
    if actual_commit == prior["commit"]:
        validate_checkout_at(
            run,
            prior,
            state_revision(prior),
            destination,
            "pending transition source",
            allowed_sources,
        )
    elif actual_commit == target["commit"]:
        validate_checkout_at(
            run,
            target,
            target["revision"],
            destination,
            "pending transition target",
            allowed_sources,
        )
    else:
        raise BootstrapError(
            f"Managed checkout is {actual_commit}, pending transition allows only "
            f"{prior['commit']} or {target['commit']}: {destination}"
        )


def checkout_release(
    run,
    release: dict[str, Any],
    commit: str,
    destination: Path,
    managed: dict[str, Any] | None = None,
    pending: dict[str, Any] | None = None,
) -> None:
    source = require_string(release.get("source"), f"{release['id']}.source")
    revision = require_string(release.get("revision"), f"{release['id']}.revision")
    if destination.exists():
        if not (destination / ".git").exists():
            raise BootstrapError(f"Managed checkout path is not a Git checkout: {destination}")
        if pending is not None:
            validate_transition_checkout(run, pending, destination)
        elif managed is not None:
            validate_managed_checkout(run, managed, destination)
        elif git(run, ["status", "--porcelain"], destination):
            raise BootstrapError(f"Managed checkout has local changes: {destination}")
        remote = git(run, ["remote", "get-url", "origin"], destination)
        if normalize_source(remote) != normalize_source(source):
            if managed is None:
                raise BootstrapError(f"Managed checkout origin disagrees with the catalog: {destination}")
            git(run, ["remote", "set-url", "origin", source], destination)
    else:
        if managed is not None:
            raise BootstrapError(f"Managed checkout is missing: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        git(run, ["clone", "--no-checkout", "-c", "core.autocrlf=false", source, str(destination)])
    tag_ref = f"refs/tags/{revision}"
    git(run, ["fetch", "--force", "origin", f"{tag_ref}:{tag_ref}"], destination)
    resolved = git(run, ["rev-parse", f"{tag_ref}^{{commit}}"], destination)
    if resolved != commit:
        raise BootstrapError(f"{release['id']} tag {revision} resolves to {resolved}, lock requires {commit}")
    git(run, ["checkout", "--detach", "--force", commit], destination)


def checkout_path(profile: Path, marketplace: str) -> Path:
    if not SAFE_NAME.fullmatch(marketplace):
        raise BootstrapError(f"Unsafe marketplace name: {marketplace}")
    return profile / STATE_DIRECTORY / "checkouts" / marketplace


def state_path(profile: Path) -> Path:
    return profile / STATE_DIRECTORY / "managed.json"


def load_state(profile: Path) -> dict[str, Any]:
    path = state_path(profile)
    if not path.exists():
        return {"schema_version": 1, "marketplaces": {}, "transitions": {}}
    state = load_json(path)
    if state.get("schema_version") != 1 or not isinstance(state.get("marketplaces"), dict):
        raise BootstrapError(f"Unsupported managed-state schema at {path}")
    if "transitions" not in state:
        state["transitions"] = {}
    if not isinstance(state["transitions"], dict):
        raise BootstrapError(f"Unsupported managed-state transitions at {path}")
    return state


def record_marketplace(profile: Path, state: dict[str, Any], release: dict[str, Any], commit: str, checkout: Path) -> None:
    state["marketplaces"][release["marketplace"]] = release_state(release, commit, checkout)
    write_json(state_path(profile), state)


def start_transition(
    profile: Path,
    state: dict[str, Any],
    release: dict[str, Any],
    managed: dict[str, Any],
    expected: dict[str, str],
) -> dict[str, Any]:
    pending = {
        "from": managed,
        "to": expected,
        "source": expected["source"],
        "revision": expected["revision"],
    }
    state["transitions"][release["marketplace"]] = pending
    write_json(state_path(profile), state)
    return pending


def finish_transition(
    profile: Path, state: dict[str, Any], marketplace: str, expected: dict[str, str]
) -> None:
    state["marketplaces"][marketplace] = expected
    state["transitions"].pop(marketplace, None)
    write_json(state_path(profile), state)


def verify_checkout(
    run, profile: Path, release: dict[str, Any], commit: str, selected: list[dict[str, Any]], plugins: dict[str, dict[str, Any]]
) -> list[str]:
    marketplace = release["marketplace"]
    checkout = checkout_path(profile, marketplace)
    if not (checkout / ".git").exists():
        raise BootstrapError(f"Managed checkout is missing: {checkout}")
    actual_commit = git(run, ["rev-parse", "HEAD"], checkout)
    if actual_commit != commit:
        raise BootstrapError(f"{marketplace} checkout is {actual_commit}, expected {commit}")
    tag_commit = git(run, ["rev-parse", f"refs/tags/{release['revision']}^{{commit}}"], checkout)
    if tag_commit != commit:
        raise BootstrapError(
            f"{marketplace} local tag {release['revision']} is {tag_commit}, expected {commit}"
        )
    if git(run, ["status", "--porcelain"], checkout):
        raise BootstrapError(f"Managed checkout has local changes: {checkout}")
    expected_source = normalize_source(
        require_string(release.get("source"), f"{release['id']}.source")
    )
    actual_source = normalize_source(git(run, ["remote", "get-url", "origin"], checkout))
    if actual_source != expected_source:
        raise BootstrapError(f"Managed checkout origin is {actual_source}, expected {expected_source}: {checkout}")
    checks: list[str] = []
    for selection in selected:
        plugin = plugins[selection["id"]]
        package = checkout / PurePosixPath(plugin["package_path"])
        actual_digest = tree_digest(package, plugin.get("digest_excludes", []))
        if actual_digest != plugin["digest"]:
            raise BootstrapError(f"{selection['id']} digest is {actual_digest}, expected {plugin['digest']}")
        checks.append(f"digest:{selection['id']}")
    return checks


def verify_installed_plugin(
    harness: str,
    identity: str,
    installed: dict[str, dict[str, Any]],
    plugin: dict[str, Any],
    commit: str,
) -> list[str]:
    record = installed.get(identity)
    if not record or not record.get("enabled"):
        raise BootstrapError(f"Plugin is not installed and enabled: {identity}")
    actual_version = record.get("version")
    if harness == "codex":
        expected_version = plugin["version"]
        if actual_version != expected_version:
            raise BootstrapError(
                f"Installed plugin version is {actual_version}, expected {expected_version}: {identity}"
            )
    elif not isinstance(actual_version, str) or len(actual_version) < 7 or not commit.startswith(actual_version):
        raise BootstrapError(
            f"Installed plugin revision is {actual_version}, expected commit {commit}: {identity}"
        )
    install_path = record.get("path")
    if not isinstance(install_path, str) or not install_path:
        raise BootstrapError(f"Installed plugin path is unavailable: {identity}")
    actual_digest = tree_digest(Path(install_path), plugin.get("digest_excludes", []))
    if actual_digest != plugin["digest"]:
        raise BootstrapError(f"Installed plugin digest is {actual_digest}, expected {plugin['digest']}: {identity}")
    return [f"enabled:{identity}", f"installed-digest:{identity}"]


def installed_plugin_is_exact(
    harness: str,
    identity: str,
    installed: dict[str, dict[str, Any]],
    plugin: dict[str, Any],
    commit: str,
) -> bool:
    try:
        verify_installed_plugin(harness, identity, installed, plugin, commit)
    except BootstrapError:
        return False
    return True


def release_groups(selections: list[dict[str, Any]], plugins: dict[str, dict[str, Any]]) -> list[tuple[dict[str, Any], str, list[dict[str, Any]]]]:
    groups: dict[str, tuple[dict[str, Any], str, list[dict[str, Any]]]] = {}
    for selection in selections:
        release = plugins[selection["id"]]["_release"]
        group = groups.get(release["id"])
        if group is None:
            groups[release["id"]] = (release, selection["commit"], [selection])
        else:
            group[2].append(selection)
    return [groups[key] for key in sorted(groups)]


def plan_operations(selections: list[dict[str, Any]], plugins: dict[str, dict[str, Any]], profile: Path) -> list[str]:
    operations: list[str] = []
    for release, commit, members in release_groups(selections, plugins):
        checkout = checkout_path(profile, release["marketplace"])
        operations.append(f"checkout {release['source']} {release['revision']} ({commit}) at {checkout}")
        operations.append(f"register marketplace {release['marketplace']} from {checkout}")
        operations.extend(f"install {plugins[item['id']]['name']}@{release['marketplace']}" for item in members)
    return operations


def execute(arguments: argparse.Namespace, run=subprocess.run) -> dict[str, Any]:
    lock_path = arguments.lock.expanduser().resolve()
    profile = arguments.profile.expanduser().resolve()
    catalog_path = arguments.catalog.expanduser().resolve() if arguments.catalog else find_catalog(Path(__file__).resolve())
    catalog = load_json(catalog_path)
    releases, plugins = catalog_index(catalog)
    selections = validate_lock(load_json(lock_path), releases, plugins)
    prerequisite_checks = check_required_prerequisites(selections, plugins)
    report: dict[str, Any] = {
        "schema_version": 1,
        "mode": arguments.mode,
        "harness": arguments.harness,
        "profile": str(profile),
        "lock": str(lock_path),
        "catalog": str(catalog_path),
        "status": "planned" if arguments.mode == "preview" else "in_progress",
        "planned": plan_operations(selections, plugins, profile),
        "applied": [],
        "checks": ["catalog", "lock", "dependency-closure", *prerequisite_checks],
        "external_prerequisites": {
            selection["id"]: plugins[selection["id"]]["external_prerequisites"]
            for selection in selections
        },
        "errors": [],
    }
    if arguments.mode == "preview":
        return report
    try:
        host = NativeHost(arguments.harness, profile, run)
        groups = release_groups(selections, plugins)
        state = load_state(profile)
        if arguments.mode == "apply":
            for release, commit, members in groups:
                checkout = checkout_path(profile, release["marketplace"])
                configured = host.marketplaces()
                marketplace = release["marketplace"]
                managed = state["marketplaces"].get(marketplace)
                expected = release_state(release, commit, checkout)
                pending = state["transitions"].get(marketplace)
                if managed is not None and pending is None:
                    normalized = validate_managed_checkout(run, managed, checkout)
                    if normalized != managed:
                        state["marketplaces"][marketplace] = normalized
                        write_json(state_path(profile), state)
                    managed = normalized
                registered = configured.get(marketplace)
                if marketplace in configured:
                    if not managed:
                        raise BootstrapError(
                            f"Marketplace name is already registered outside this bootstrap: {marketplace}"
                        )
                    if not registered or Path(registered).resolve() != checkout.resolve():
                        raise BootstrapError(
                            f"Registered marketplace source disagrees with managed checkout: {marketplace}"
                        )
                if pending is not None:
                    if managed is None or managed == expected:
                        raise BootstrapError(f"Orphaned marketplace transition: {marketplace}")
                    validate_pending_transition(pending, managed, expected, release)
                elif managed is not None and managed != expected:
                    validate_managed_checkout(run, managed, checkout)
                    pending = start_transition(profile, state, release, managed, expected)
                    report["applied"].append(f"transition:{marketplace}:{managed['commit']}->{commit}")
                checkout_release(run, release, commit, checkout, managed, pending)
                report["applied"].append(f"checkout:{marketplace}@{commit}")
                if managed is None:
                    record_marketplace(profile, state, release, commit, checkout)
                    report["applied"].append(f"managed-state:{marketplace}@{commit}")
                if marketplace not in configured:
                    host.add_marketplace(checkout)
                    report["applied"].append(f"marketplace:{marketplace}")
                installed = host.installed()
                for selection in members:
                    plugin = plugins[selection["id"]]
                    identity = f"{plugin['name']}@{release['marketplace']}"
                    if identity not in installed:
                        host.install(identity)
                        report["applied"].append(f"plugin:{identity}")
                    elif pending is not None or not installed_plugin_is_exact(
                        arguments.harness, identity, installed, plugin, commit
                    ):
                        host.refresh(identity)
                        report["applied"].append(f"refreshed:{identity}")
                current = host.installed()
                for selection in members:
                    plugin = plugins[selection["id"]]
                    identity = f"{plugin['name']}@{release['marketplace']}"
                    if identity in current and not current[identity].get("enabled"):
                        host.enable(identity)
                        report["applied"].append(f"enabled:{identity}")
                refreshed = host.installed()
                for selection in members:
                    plugin = plugins[selection["id"]]
                    identity = f"{plugin['name']}@{marketplace}"
                    report["checks"].extend(
                        verify_installed_plugin(arguments.harness, identity, refreshed, plugin, commit)
                    )
                if pending is not None:
                    finish_transition(profile, state, marketplace, expected)
                    report["applied"].append(f"managed-state:{marketplace}@{commit}")
        for release, commit, members in groups:
            marketplace = release["marketplace"]
            checkout = checkout_path(profile, marketplace)
            expected = release_state(release, commit, checkout)
            if state["transitions"].get(marketplace) is not None:
                raise BootstrapError(f"Marketplace transition is incomplete: {marketplace}")
            managed = state["marketplaces"].get(marketplace)
            if managed is not None:
                managed = validate_managed_checkout(run, managed, checkout)
                state["marketplaces"][marketplace] = managed
            if managed != expected:
                raise BootstrapError(f"Managed marketplace state disagrees with the lock: {marketplace}")
            report["checks"].extend(verify_checkout(run, profile, release, commit, members, plugins))
        configured = host.marketplaces()
        installed = host.installed()
        for selection in selections:
            plugin = plugins[selection["id"]]
            release = plugin["_release"]
            registered = configured.get(release["marketplace"])
            checkout = checkout_path(profile, release["marketplace"])
            if not registered:
                raise BootstrapError(f"Marketplace is not registered: {release['marketplace']}")
            if Path(registered).resolve() != checkout.resolve():
                raise BootstrapError(
                    f"Registered marketplace source disagrees with managed checkout: {release['marketplace']}"
                )
            report["checks"].append(f"marketplace-source:{release['marketplace']}")
            identity = f"{plugin['name']}@{release['marketplace']}"
            report["checks"].extend(
                verify_installed_plugin(arguments.harness, identity, installed, plugin, selection["commit"])
            )
        report["status"] = "applied" if arguments.mode == "apply" else "verified"
        return report
    except BootstrapError as error:
        report["status"] = "partial" if report["applied"] or (profile / STATE_DIRECTORY).exists() else "failed"
        report["errors"].append(str(error))
        raise BootstrapRunError(report) from error


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--harness", choices=("codex", "claude"), required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--mode", choices=("preview", "apply", "verify"), required=True)
    parser.add_argument("--catalog", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--report", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_arguments(argv)
    try:
        report = execute(arguments)
    except BootstrapRunError as error:
        report = error.report
        if arguments.report:
            write_json(arguments.report.expanduser().resolve(), report)
        print(json.dumps(report, indent=2), file=sys.stderr)
        return 1
    except BootstrapError as error:
        report = {
            "schema_version": 1,
            "mode": arguments.mode,
            "harness": arguments.harness,
            "profile": str(arguments.profile.expanduser().resolve()),
            "status": "failed",
            "planned": [],
            "applied": [],
            "checks": [],
            "errors": [str(error)],
        }
        if arguments.report:
            write_json(arguments.report.expanduser().resolve(), report)
        print(json.dumps(report, indent=2), file=sys.stderr)
        return 1
    if arguments.report:
        write_json(arguments.report.expanduser().resolve(), report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
