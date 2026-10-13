#!/usr/bin/env python3
"""Refresh enabled Claude plugins from their registered marketplaces before a session loads them."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

STATE_DIRECTORY_ENV = "AGENT_STATE_DIRECTORY"
STATE_FILE = "claude-standards-sync.json"
LOCK_FILE = "claude-standards-sync.lock"
REMOTE_TIMEOUT_SECONDS = 20
MARKETPLACE_TIMEOUT_SECONDS = 180
PLUGIN_TIMEOUT_SECONDS = 120
LOCK_WAIT_SECONDS = 180
STALE_LOCK_SECONDS = 900
GIT_SOURCES = {"github", "git"}
FULL_SHA = re.compile(r"[0-9a-f]{40}")
PLUGIN_ROOT_PATH = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s\"']+?\.py)(?:@[A-Za-z|]+)?(?=[\s\"']|$)")
PROFILE_ALIASES = {
    "base@tj-agents": ("base@base-agents",),
    "engineering@tj-agents": ("engineering@base-agents",),
    "machine@tj-agents": ("machine@base-agents",),
    "cpp@tj-agents": ("cpp@cpp-agents",),
    "msvc@tj-agents": ("msvc@cpp-agents",),
    "win32@tj-agents": ("win32@cpp-agents",),
    "dotnet@tj-agents": ("dotnet@dotagents", "dotnet@dotnet"),
    "react@tj-agents": ("react@react-agents", "react@react"),
}
STALE_PROFILE_ALIASES = {"dotnet@dotnet", "react@react"}
PROFILE_REPOSITORIES = {
    "base": "tj-agents/core",
    "engineering": "tj-agents/core",
    "machine": "tj-agents/core",
    "cpp": "tj-agents/cpp",
    "msvc": "tj-agents/cpp",
    "win32": "tj-agents/cpp",
    "dotnet": "tj-agents/dotnet",
    "react": "tj-agents/react",
}


@dataclass(frozen=True)
class Install:
    identity: str
    scope: str
    project: Path | None
    version: str
    installed_path: Path | None = None
    git_commit_sha: str | None = None
    strict: bool = True

    @property
    def name(self) -> str:
        return self.identity.rsplit("@", 1)[0]

    @property
    def marketplace(self) -> str:
        return self.identity.rsplit("@", 1)[1]

    @property
    def key(self) -> str:
        return "|".join((self.identity, self.scope, comparable(self.project) if self.project else ""))


@dataclass
class Marketplace:
    name: str
    checkout: Path | None
    url: str | None
    ref: str | None
    installs: list[Install] = field(default_factory=list)
    owned: bool = True


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def read_json_object(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def comparable(path: Path) -> str:
    return os.path.normcase(os.path.abspath(str(path))).rstrip("\\/")


def within(child: Path, parent: Path) -> bool:
    child_key, parent_key = comparable(child), comparable(parent)
    return child_key == parent_key or child_key.startswith(parent_key + os.sep)


def config_root(environ) -> Path:
    configured = environ.get("CLAUDE_CONFIG_DIR")
    return Path(configured) if configured else Path.home() / ".claude"


def plugins_root(config: Path, environ) -> Path:
    configured = environ.get("CLAUDE_CODE_PLUGIN_CACHE_DIR")
    return Path(configured) if configured else config / "plugins"


def state_root(environ) -> Path:
    configured = environ.get(STATE_DIRECTORY_ENV)
    return Path(configured) if configured else Path.home() / ".agents-state"


def enabled_plugins(config: Path, project: Path) -> set[str]:
    merged: dict = {}
    for path in (
        config / "settings.json",
        project / ".claude" / "settings.json",
        project / ".claude" / "settings.local.json",
    ):
        values = read_json(path).get("enabledPlugins")
        if isinstance(values, dict):
            merged.update(values)
    return {identity for identity, enabled in merged.items() if enabled is True}


def installs(plugins: Path, project: Path, enabled: set[str]) -> list[Install]:
    records = read_json(plugins / "installed_plugins.json").get("plugins")
    found = []
    for identity, entries in records.items() if isinstance(records, dict) else ():
        if identity not in enabled or "@" not in identity or not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            scope = entry.get("scope")
            version = str(entry.get("version") or "unknown")
            owner = entry.get("projectPath")
            install_path = entry.get("installPath")
            commit = entry.get("gitCommitSha")
            path = Path(install_path) if isinstance(install_path, str) and install_path else None
            sha = commit if isinstance(commit, str) and FULL_SHA.fullmatch(commit) else None
            if scope in ("user", "managed"):
                found.append(Install(identity, scope, None, version, path, sha))
            elif scope in ("project", "local") and isinstance(owner, str) and owner and within(project, Path(owner)):
                found.append(Install(identity, scope, Path(owner), version, path, sha))
    return found


def source_url(source: dict) -> str | None:
    if source.get("source") == "github" and isinstance(source.get("repo"), str):
        return f"https://github.com/{source['repo']}.git"
    url = source.get("url")
    return url if isinstance(url, str) and url else None


def marketplaces(plugins: Path, found: list[Install]) -> list[Marketplace]:
    known = read_json(plugins / "known_marketplaces.json")
    grouped: dict[str, list[Install]] = {}
    for install in found:
        grouped.setdefault(install.marketplace, []).append(install)
    selected = []
    for name, members in sorted(grouped.items()):
        entry = known.get(name)
        source = entry.get("source") if isinstance(entry, dict) else None
        if not isinstance(source, dict) or source.get("source") not in GIT_SOURCES:
            continue
        location = entry.get("installLocation")
        checkout = Path(location) if isinstance(location, str) and location else None
        if checkout is not None and checkout.exists() and not is_checkout(checkout):
            continue
        ref = source.get("ref")
        entries = plugin_entries(checkout)
        members = [replace(install, strict=entries.get(install.name, {}).get("strict") is not False) for install in members]
        selected.append(Marketplace(name, checkout, source_url(source), ref if isinstance(ref, str) and ref else None, members))
    return selected


def plugin_entries(checkout: Path | None) -> dict[str, dict]:
    if checkout is None:
        return {}
    entries = read_json(checkout / ".claude-plugin" / "marketplace.json").get("plugins")
    found = {}
    if isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, dict) and isinstance(entry.get("name"), str):
                found[entry["name"]] = entry
    return found


def plugin_entry_sources(checkout: Path | None) -> dict[str, dict]:
    return {
        name: entry["source"] for name, entry in plugin_entries(checkout).items()
        if isinstance(entry.get("source"), dict)
    }


def repo_label(url: str) -> str:
    stripped = url[:-4] if url.endswith(".git") else url
    segments = [segment for segment in re.split(r"[\\/]+", stripped) if segment]
    return "/".join(segments[-2:]) if len(segments) >= 2 else (segments[-1] if segments else stripped)


def normalize_url(url: str) -> str:
    stripped = url.strip()
    if "://" in stripped:
        stripped = re.sub(r"^[a-z][a-z0-9+.-]*://", "", stripped, flags=re.IGNORECASE)
    else:
        scp = re.match(r"^[^/@]+@([^:/]+):(.+)$", stripped)
        if scp:
            stripped = f"{scp.group(1)}/{scp.group(2)}"
    stripped = stripped.rstrip("/")
    if stripped.lower().endswith(".git"):
        stripped = stripped[:-4]
    host, separator, rest = stripped.partition("/")
    return host.rsplit("@", 1)[-1].lower() + separator + rest


def external_groups(markets: list[Marketplace]) -> list[Marketplace]:
    grouped: dict[tuple[str, str | None], tuple[str, list[Install]]] = {}
    for market in markets:
        sources = plugin_entry_sources(market.checkout)
        own = normalize_url(market.url) if market.url else None
        native = []
        for install in market.installs:
            override = sources.get(install.name)
            resolved = source_url(override) if isinstance(override, dict) else None
            ref = override.get("ref") if isinstance(override, dict) else None
            separate_ref = isinstance(override, dict) and override.get("source") == "git-subdir" and isinstance(ref, str) and ref
            if resolved and (normalize_url(resolved) != own or separate_ref):
                key = (normalize_url(resolved), ref if isinstance(ref, str) and ref else None)
                raw_url, members = grouped.get(key, (resolved, []))
                members.append(install)
                grouped[key] = (raw_url, members)
            else:
                native.append(install)
        market.installs = native
    ordered = sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1] or ""))
    return [Marketplace(repo_label(raw_url), None, raw_url, ref, members, owned=False) for (_, ref), (raw_url, members) in ordered]


def run(command: list[str], cwd: Path | None = None, timeout: float = REMOTE_TIMEOUT_SECONDS) -> tuple[int | None, str, str]:
    environment = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            **options,
        )
    except subprocess.TimeoutExpired:
        return None, "", f"timed out after {timeout:g}s"
    except OSError as error:
        return None, "", str(error)
    return completed.returncode, completed.stdout, completed.stderr


def last_line(*texts: str) -> str:
    for text in texts:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if lines:
            return lines[-1]
    return "no output"


def git(checkout: Path, *arguments: str) -> str | None:
    code, output, _ = run(["git", "-C", str(checkout), *arguments])
    return output.strip() or None if code == 0 else None


def is_checkout(path: Path) -> bool:
    return path.is_dir() and (path / ".git").exists()


def checkout_head(market: Marketplace) -> str | None:
    if market.checkout is None or not is_checkout(market.checkout):
        return None
    return git(market.checkout, "rev-parse", "HEAD")


def remote_commit(market: Marketplace) -> tuple[str | None, str | None]:
    if market.ref and FULL_SHA.fullmatch(market.ref):
        return market.ref, None
    present = market.checkout is not None and is_checkout(market.checkout)
    url = (git(market.checkout, "remote", "get-url", "origin") if present else None) or market.url
    if not url:
        return None, "no remote URL"
    wanted = market.ref or (git(market.checkout, "symbolic-ref", "--quiet", "--short", "HEAD") if present else None)
    patterns = [wanted or "HEAD"]
    if wanted:
        patterns.extend((f"{wanted}^{{}}", f"refs/tags/{wanted}", f"refs/tags/{wanted}^{{}}", f"refs/heads/{wanted}"))
    code, output, error = run(["git", "ls-remote", url, *patterns])
    if code != 0:
        return None, last_line(error, output)
    refs = {}
    for line in output.splitlines():
        commit, _, name = line.partition("\t")
        if FULL_SHA.fullmatch(commit.strip()):
            refs[name.strip()] = commit.strip()
    names = (
        f"refs/tags/{wanted}^{{}}", f"{wanted}^{{}}", f"refs/heads/{wanted}", f"refs/tags/{wanted}", wanted
    ) if wanted else ("HEAD",)
    for name in names:
        if name in refs:
            return refs[name], None
    return None, f"{wanted or 'HEAD'} not found"


def probe(market: Marketplace) -> tuple[str | None, str | None, str | None]:
    remote, error = remote_commit(market)
    return remote, checkout_head(market), error


def load_state(root: Path) -> dict[str, str]:
    recorded = read_json(root / STATE_FILE).get("installs")
    if not isinstance(recorded, dict):
        return {}
    return {key: value for key, value in recorded.items() if isinstance(key, str) and isinstance(value, str)}


def save_state(root: Path, state: dict[str, str]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    temporary = root / f".{STATE_FILE}.{os.getpid()}.tmp"
    temporary.write_text(json.dumps({"schema_version": 1, "installs": dict(sorted(state.items()))}, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, root / STATE_FILE)


def save_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


@contextmanager
def exclusive(root: Path, wait: float):
    root.mkdir(parents=True, exist_ok=True)
    path = root / LOCK_FILE
    deadline = time.monotonic() + wait
    while True:
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            try:
                if time.time() - path.stat().st_mtime > STALE_LOCK_SECONDS:
                    path.unlink()
                    continue
            except FileNotFoundError:
                continue
            if time.monotonic() >= deadline:
                raise TimeoutError("another launch is still updating plugins") from None
            time.sleep(0.25)
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        os.close(descriptor)
        yield lambda: os.utime(path)
    finally:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def claude(executable: str, arguments: list[str], cwd: Path, timeout: float) -> tuple[bool, str]:
    code, output, error = run([executable, *arguments], cwd=cwd, timeout=timeout)
    lines = [line for line in output.splitlines() if line.strip()]
    if lines:
        try:
            result = json.loads(lines[-1])
        except ValueError:
            result = None
        if isinstance(result, dict) and "outcome" in result:
            return result["outcome"] == "ok", str(result.get("message") or "")
    return code == 0, last_line(error, output)


def short(commit: str | None) -> str:
    return commit[:12] if commit else "none"


def describe(members: list[Install]) -> str:
    return ", ".join(
        f"{install.name} {install.version}" + ("" if install.scope == "user" else f" ({install.scope})")
        for install in members
    )


def hook_paths(value) -> set[str]:
    if isinstance(value, dict):
        return set().union(*(hook_paths(item) for item in value.values())) if value else set()
    if isinstance(value, list):
        return set().union(*(hook_paths(item) for item in value)) if value else set()
    if not isinstance(value, str):
        return set()
    return {match.group(1) for match in PLUGIN_ROOT_PATH.finditer(value)}


def package_path(root: Path, relative: str) -> Path | None:
    candidate = (root / relative).resolve()
    return candidate if within(candidate, root.resolve()) else None


def declared_skills_complete(root: Path, value) -> bool:
    values = [value] if isinstance(value, str) else value
    if not isinstance(values, list) or not values or not all(isinstance(item, str) for item in values):
        return False
    for relative in values:
        path = package_path(root, relative)
        if path is None:
            return False
        if path.is_dir() and any(path.rglob("SKILL.md")):
            continue
        if path.is_file() and path.name == "SKILL.md":
            continue
        return False
    return True


def package_complete(install: Install) -> bool:
    root = install.installed_path
    if root is None or not root.is_dir():
        return False
    manifest_path = root / ".claude-plugin" / "plugin.json"
    if not manifest_path.exists():
        return not install.strict
    manifest = read_json(manifest_path)
    if manifest.get("name") != install.name:
        return False
    if "skills" in manifest and not declared_skills_complete(root, manifest["skills"]):
        return False
    if "hooks" in manifest:
        if not isinstance(manifest["hooks"], str):
            return False
        hooks_path = package_path(root, manifest["hooks"])
        hooks_manifest = read_json(hooks_path) if hooks_path is not None else {}
        if not hooks_manifest or any(package_path(root, path) is None or not package_path(root, path).is_file()
                                     for path in hook_paths(hooks_manifest)):
            return False
    harness_path = root / "harness.json"
    if not harness_path.exists():
        return True
    harness = read_json(harness_path)
    required = harness.get("requires") if isinstance(harness, dict) else None
    hooks = required.get("hooks") if isinstance(required, dict) else None
    return isinstance(hooks, list) and all(
        not isinstance(hook, dict)
        or "claude" not in hook.get("hosts", [])
        or isinstance(hook.get("path"), str)
        and (path := package_path(root, hook["path"])) is not None
        and path.is_file()
        for hook in hooks
    )


def installed_at(install: Install, remote: str) -> bool:
    if not package_complete(install):
        return False
    return install.git_commit_sha == remote if install.git_commit_sha else bool(re.search(
        rf"(?:^|-){re.escape(remote[:12])}$", install.version
    ))


def current(install: Install, remote: str, state: dict[str, str]) -> bool:
    if not package_complete(install) or install.git_commit_sha and install.git_commit_sha != remote:
        return False
    return state.get(install.key) == remote or installed_at(install, remote)


def registered_installs(plugins: Path) -> dict[str, list[Install]]:
    records = read_json(plugins / "installed_plugins.json").get("plugins")
    found: dict[str, list[Install]] = {}
    for identity, entries in records.items() if isinstance(records, dict) else ():
        if not isinstance(identity, str) or "@" not in identity or not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict) or entry.get("scope") not in ("user", "managed", "project", "local"):
                continue
            owner = entry.get("projectPath")
            path = entry.get("installPath")
            commit = entry.get("gitCommitSha")
            found.setdefault(identity, []).append(Install(
                identity,
                entry["scope"],
                Path(owner) if isinstance(owner, str) and owner else None,
                str(entry.get("version") or "unknown"),
                Path(path) if isinstance(path, str) and path else None,
                commit if isinstance(commit, str) and FULL_SHA.fullmatch(commit) else None,
            ))
    return found


def source_matches_repository(source: dict, repository: str) -> bool:
    if source.get("source") == "github":
        return source.get("repo") == repository
    url = source_url(source)
    if not isinstance(url, str) or not (
        re.fullmatch(r"https://github\.com/.+", url, re.IGNORECASE)
        or re.fullmatch(r"ssh://(?:git@)?github\.com/.+", url, re.IGNORECASE)
        or re.fullmatch(r"[^/@]+@github\.com:.+", url, re.IGNORECASE)
    ):
        return False
    return normalize_url(url).lower() == "github.com/" + repository.lower()


def marketplace_is_authenticated(plugins: Path, identity: str) -> bool:
    entry = read_json(plugins / "known_marketplaces.json").get("tj-agents")
    source = entry.get("source") if isinstance(entry, dict) else None
    location = entry.get("installLocation") if isinstance(entry, dict) else None
    if not isinstance(source, dict) or not source_matches_repository(source, "tj-agents/marketplace"):
        return False
    sources = plugin_entry_sources(Path(location)) if isinstance(location, str) else {}
    declared = sources.get(identity.rsplit("@", 1)[0])
    expected = PROFILE_REPOSITORIES.get(identity.rsplit("@", 1)[0])
    return isinstance(declared, dict) and isinstance(expected, str) and source_matches_repository(declared, expected)


def legacy_install_is_authenticated(plugins: Path, identity: str, records: dict[str, list[Install]]) -> bool:
    if not records.get(identity):
        return False
    name, marketplace = identity.rsplit("@", 1)
    entry = read_json(plugins / "known_marketplaces.json").get(marketplace)
    source = entry.get("source") if isinstance(entry, dict) else None
    expected = PROFILE_REPOSITORIES.get(name)
    return isinstance(source, dict) and isinstance(expected, str) and source_matches_repository(source, expected)


def scoped_roots(records: dict[str, list[Install]], project: Path, initial: set[Path] | None = None) -> set[Path]:
    return {project, *(initial or ()), *(install.project for installs in records.values() for install in installs
                                       if install.scope in ("project", "local") and install.project is not None)}


def scoped_profiles_valid(records: dict[str, list[Install]], project: Path, initial: set[Path] | None = None) -> bool:
    return all(
        read_json_object(path) is not None
        for root in scoped_roots(records, project, initial)
        for path in (root / ".claude" / "settings.json", root / ".claude" / "settings.local.json")
        if path.exists()
    )


def scoped_alias_conflict(records: dict[str, list[Install]], project: Path, canonical: str, aliases: tuple[str, ...], selected: bool,
                          initial: set[Path] | None = None) -> bool:
    if not selected:
        return False
    for root in scoped_roots(records, project, initial):
        for path in (root / ".claude" / "settings.json", root / ".claude" / "settings.local.json"):
            scoped = read_json(path).get("enabledPlugins")
            if not isinstance(scoped, dict) or scoped.get(canonical) is False:
                continue
            if any(scoped.get(alias) is False for alias in aliases):
                return True
    return False


def profile_plan(plugins: Path, settings: dict, project: Path) -> tuple[dict, list[tuple[str, tuple[str, ...], bool]], list[str]]:
    enabled = settings.get("enabledPlugins")
    if not isinstance(enabled, dict):
        return settings, [], []
    updated = dict(settings)
    migrated = dict(enabled)
    records = registered_installs(plugins)
    selected = []
    deferred = []
    for canonical, aliases in PROFILE_ALIASES.items():
        present = [identity for identity in aliases if isinstance(migrated.get(identity), bool)]
        if not present:
            continue
        authentication_identities = [
            identity if identity not in STALE_PROFILE_ALIASES or records.get(identity) else next(
                (candidate for candidate in aliases if candidate not in STALE_PROFILE_ALIASES and records.get(candidate)), identity
            )
            for identity in present
        ]
        if not marketplace_is_authenticated(plugins, canonical) or any(
            not legacy_install_is_authenticated(plugins, identity, records) for identity in authentication_identities
        ):
            deferred.append(canonical)
            continue
        values = [migrated[identity] for identity in (canonical, *present) if isinstance(migrated.get(identity), bool)]
        selected_value = False if False in values else True
        if scoped_alias_conflict(records, project, canonical, aliases, selected_value):
            deferred.append(canonical)
            continue
        migrated[canonical] = selected_value
        for identity in present:
            migrated.pop(identity)
        selected.append((canonical, tuple(present), selected_value))
    if migrated != enabled:
        updated["enabledPlugins"] = migrated
    return updated, selected, deferred


def migrate_profile(config: Path, plugins: Path, project: Path, executable: str | None, check: bool, out) -> int:
    path = config / "settings.json"
    settings = read_json_object(path) if path.exists() else {}
    registry_path = plugins / "installed_plugins.json"
    known_path = plugins / "known_marketplaces.json"
    if settings is None or registry_path.exists() and read_json_object(registry_path) is None or known_path.exists() and read_json_object(known_path) is None:
        print("standards: profile migration deferred because a profile registry is malformed", file=out)
        return 1
    records = registered_installs(plugins)
    initial_roots = scoped_roots(records, project)
    if not scoped_profiles_valid(records, project, initial_roots):
        print("standards: profile migration deferred because a scoped profile is malformed", file=out)
        return 1
    updated, selected, deferred = profile_plan(plugins, settings, project)
    for identity in deferred:
        print(f"standards: profile migration deferred for {identity} because a scoped legacy selection would change", file=out)
    if updated == settings:
        return int(bool(deferred))
    if check:
        for canonical, aliases, _ in selected:
            print(f"standards: profile migration would select {canonical} ({', '.join(aliases)})", file=out)
        return 1
    problems = int(bool(deferred))
    candidates = []
    for selection in selected:
        canonical, _, enabled = selection
        if enabled and not executable:
            print(f"standards: profile migration deferred for {canonical} because the claude executable was not found", file=out)
            problems += 1
            continue
        candidates.append(selection)
    initial_enabled = settings.get("enabledPlugins")
    initial_enabled = dict(initial_enabled) if isinstance(initial_enabled, dict) else {}
    snapshots = {
        canonical: {identity: initial_enabled.get(identity) for identity in (canonical, *PROFILE_ALIASES[canonical])}
        for canonical, _, _ in candidates
    }
    installed = set()
    for canonical, aliases, enabled in candidates:
        if not enabled:
            continue
        existing = [install for install in registered_installs(plugins).get(canonical, []) if install.scope == "user"]
        if any(package_complete(install) for install in existing):
            continue
        if not marketplace_is_authenticated(plugins, canonical):
            print(f"standards: profile migration could not verify {canonical}; aliases were preserved", file=out)
            return 1
        ok, detail = claude(executable, ["plugin", "install", canonical, "--scope", "user"], project, PLUGIN_TIMEOUT_SECONDS)
        refreshed = [install for install in registered_installs(plugins).get(canonical, []) if install.scope == "user"]
        if not ok or not any(package_complete(install) for install in refreshed):
            print(f"standards: profile migration could not install {canonical} ({detail}); aliases were preserved", file=out)
            return 1
        installed.add(canonical)
    saved = read_json_object(path)
    if saved is None:
        print("standards: profile migration deferred because the user profile changed", file=out)
        return 1
    saved_enabled = saved.get("enabledPlugins")
    saved_enabled = dict(saved_enabled) if isinstance(saved_enabled, dict) else {}
    current_records = registered_installs(plugins)
    scopes_valid = scoped_profiles_valid(current_records, project, initial_roots)
    if not scopes_valid:
        print("standards: profile migration deferred because a scoped profile changed or is malformed", file=out)
        problems += 1
    apply = []
    rollback = []
    for canonical, aliases, enabled in candidates:
        snapshot = snapshots[canonical]
        configured_aliases = PROFILE_ALIASES[canonical]
        aliases_unchanged = all(saved_enabled.get(alias) == snapshot[alias] for alias in configured_aliases)
        canonical_value = saved_enabled.get(canonical)
        expected = snapshot[canonical]
        canonical_unchanged = canonical_value == expected or canonical in installed and expected is None and canonical_value is True
        if not scopes_valid:
            if canonical in installed and expected is None and canonical_value is True:
                rollback.append(canonical)
        elif scoped_alias_conflict(current_records, project, canonical, configured_aliases, enabled, initial_roots):
            problems += 1
            if canonical in installed and expected is None and canonical_value is True:
                rollback.append(canonical)
            print(f"standards: profile migration deferred for {canonical} because a scoped legacy selection would change", file=out)
        elif aliases_unchanged and canonical_unchanged:
            apply.append((canonical, aliases, enabled))
        else:
            problems += 1
            if canonical in installed and expected is None and canonical_value is True:
                rollback.append(canonical)
            print(f"standards: profile migration deferred for {canonical} because affected preferences changed", file=out)
    if not apply and not rollback:
        return int(bool(problems))
    merged_enabled = dict(saved_enabled)
    for canonical in rollback:
        merged_enabled.pop(canonical, None)
    for canonical, aliases, enabled in apply:
        merged_enabled[canonical] = enabled
        for alias in aliases:
            merged_enabled.pop(alias, None)
    saved["enabledPlugins"] = merged_enabled
    save_json(path, saved)
    for canonical, aliases, enabled in apply:
        if not enabled:
            continue
        for alias in aliases:
            for install in registered_installs(plugins).get(alias, []):
                if install.scope != "user":
                    continue
                ok, detail = claude(executable, ["plugin", "uninstall", alias, "--scope", "user", "--keep-data"], project, PLUGIN_TIMEOUT_SECONDS)
                if not ok:
                    problems += 1
                    print(f"standards: profile migration could not uninstall {alias} ({detail})", file=out)
    return int(bool(problems))


def default_claude() -> str | None:
    native = Path.home() / ".local" / "bin" / ("claude.exe" if os.name == "nt" else "claude")
    return str(native) if native.is_file() else shutil.which("claude")


def update(market: Marketplace, remote: str, executable: str, project: Path, plugins: Path, state: dict[str, str],
           renew, out) -> int:
    pending = [install for install in market.installs if not current(install, remote, state)]
    before = checkout_head(market)
    print(f"standards: updating {market.name} to {short(remote)} (installed: {describe(pending or market.installs)})", file=out, flush=True)
    if market.owned and before != remote:
        renew()
        ok, detail = claude(executable, ["plugin", "marketplace", "update", market.name], project, MARKETPLACE_TIMEOUT_SECONDS)
        if not ok:
            print(f"standards: {market.name} was not refreshed ({detail}); this session loads {describe(market.installs)}", file=out)
            return 1
    reached = checkout_head(market) or remote
    failed = []
    for install in market.installs:
        if current(install, reached, state):
            state[install.key] = reached
            continue
        repair = not package_complete(install) and (
            state.get(install.key) == reached or install.git_commit_sha == reached or install.version == reached[:12]
        )
        cwd = install.project or project
        if repair:
            renew()
            ok, detail = claude(
                executable,
                ["plugin", "uninstall", install.identity, "--scope", install.scope, "--keep-data"],
                cwd,
                PLUGIN_TIMEOUT_SECONDS,
            )
            if ok:
                renew()
                ok, detail = claude(
                    executable,
                    ["plugin", "install", install.identity, "--scope", install.scope],
                    cwd,
                    PLUGIN_TIMEOUT_SECONDS,
                )
        else:
            renew()
            ok, detail = claude(
                executable,
                ["plugin", "update", install.identity, "--scope", install.scope, "--json"],
                cwd,
                PLUGIN_TIMEOUT_SECONDS,
            )
        refreshed = {candidate.key: candidate for candidate in installs(
            plugins, project, {candidate.identity for candidate in market.installs}
        )}
        reloaded = refreshed.get(install.key)
        if ok and reloaded is not None and installed_at(reloaded, reached):
            state[install.key] = reached
        else:
            failed.append((install, detail if not ok else "installed package is incomplete"))
    refreshed = {install.key: install for install in installs(plugins, project, {install.identity for install in market.installs})}
    print(f"standards: {market.name} at {short(reached)}: {describe([refreshed.get(install.key, install) for install in market.installs])}", file=out)
    for install, detail in failed:
        print(f"standards: {install.identity} ({install.scope}) was not updated ({detail}); this session loads {install.version}", file=out)
    return len(failed)


def synchronize(config: Path, plugins: Path, project: Path, state_dir: Path, executable: str | None,
                check: bool = False, out=sys.stdout, lock_wait: float = LOCK_WAIT_SECONDS,
                migrate_profile_settings: bool = False) -> int:
    migration_problems = migrate_profile(config, plugins, project, executable, check, out) if migrate_profile_settings else 0
    owned = marketplaces(plugins, installs(plugins, project, enabled_plugins(config, project)))
    groups = external_groups(owned)
    markets = [market for market in owned if market.installs] + groups
    if not markets:
        return migration_problems
    with ThreadPoolExecutor(max_workers=min(8, len(markets))) as pool:
        probes = list(pool.map(probe, markets))
    state = load_state(state_dir)
    problems = migration_problems
    stale = []
    for market, (remote, head, error) in zip(markets, probes):
        if remote is None:
            print(f"standards: could not check {market.name} ({error}); this session loads {describe(market.installs)}", file=out)
            problems += 1
        elif (market.owned and head != remote) or not all(current(install, remote, state) for install in market.installs):
            stale.append((market, remote))
    if check:
        for market, remote in stale:
            print(f"standards: {market.name} needs a refresh to {short(remote)} (installed: {describe(market.installs)})", file=out)
        return int(bool(problems or stale))
    if not stale:
        return int(bool(problems))
    if not executable:
        print("standards: the claude executable was not found; this session loads the installed plugins", file=out)
        return 1
    try:
        with exclusive(state_dir, lock_wait) as renew:
            state = load_state(state_dir)
            for market, remote in stale:
                problems += update(market, remote, executable, project, plugins, state, renew, out)
                save_state(state_dir, state)
    except TimeoutError as error:
        print(f"standards: {error}; this session loads the installed plugins", file=out)
        return 1
    return int(bool(problems))


def apply_harness_permissions(project: Path | None = None, run=subprocess.run) -> None:
    """Converge this machine's declared harness permissions. Fire-and-forget: any failure here is
    swallowed rather than turned into a sync failure, because a permissions converge is strictly
    additional to a standards refresh. `run` defaults to the real `subprocess.run` but is accepted so a
    caller -- this module's own `main`, or codex_marketplace_sync.py's own sync, which imports this
    function rather than duplicating it -- can supply a fake for its own tests.
    """
    package_root = Path(__file__).resolve().parents[3]
    script = package_root / ".agents" / "machine" / "utility" / "bootstrap-capabilities" / "scripts" / "harness_permissions_sync.py"
    if not script.is_file():
        return
    try:
        run(
            [sys.executable, "-I", "-B", str(script), "--apply", "--project", str((project or Path.cwd()).resolve())],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30,
        )
    except Exception:  # noqa: BLE001
        pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--claude")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--migrate-profile", action="store_true")
    arguments = parser.parse_args(argv)
    config = config_root(os.environ)
    try:
        code = synchronize(
            config,
            plugins_root(config, os.environ),
            arguments.project.resolve(),
            state_root(os.environ),
            arguments.claude or default_claude(),
            arguments.check,
            migrate_profile_settings=arguments.migrate_profile,
        )
    except Exception as error:  # noqa: BLE001
        print(f"standards: sync failed ({error}); this session loads the installed plugins")
        code = 1
    if not arguments.check:
        apply_harness_permissions(arguments.project.resolve())
    return code


if __name__ == "__main__":
    sys.exit(main())
