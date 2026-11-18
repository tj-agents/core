#!/usr/bin/env python3
"""Refresh Claude and Codex tj-agents plugins to current main and verify what each host will load.

The default fast path asks each owned source repository for its main revision and runs Claude's native
`plugin update` only for installs behind it. `--full` runs the slower verified refresh and repair.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Callable, Iterable, Mapping, Sequence

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import agent_cli  # noqa: E402
from codex_marketplace_sync import SyncError, _marketplace_source, codex_config_selection  # noqa: E402
from generation_record import generations_path  # noqa: E402
import rolling_plugins  # noqa: E402
from startup_binding import StartupBindingError, run_session  # noqa: E402

HOSTS = ("claude", "codex")
OWNER = "tj-agents"
MARKER = ".tj-agents-rolling.json"
MARKETPLACE_TIMEOUT_SECONDS = 180
REMOTE_TIMEOUT_SECONDS = 30
UPDATE_TIMEOUT_SECONDS = 180
LOCK_WAIT_SECONDS = 300
UPDATABLE_SCOPES = ("user", "project", "local")
GITHUB_REPOSITORY = re.compile(r"github\.com[/:](?P<repository>[^/]+/[^/]+?)(?:\.git)?/?$", re.IGNORECASE)


class RefreshError(RuntimeError):
    pass


@dataclass(frozen=True)
class Install:
    identity: str
    scope: str
    owner: Path
    repository: str
    revision: str | None


def progress(message: str) -> None:
    print(f"refresh-cli: {message}", file=sys.stderr, flush=True)


def configuration_root(host: str, environ: Mapping[str, str] = os.environ) -> Path:
    if host == "claude":
        return Path(environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    return Path(environ.get("CODEX_HOME") or Path.home() / ".codex")


def plugins_root(host: str, environ: Mapping[str, str] = os.environ) -> Path:
    if host == "claude" and environ.get("CLAUDE_CODE_PLUGIN_CACHE_DIR"):
        return Path(environ["CLAUDE_CODE_PLUGIN_CACHE_DIR"])
    return configuration_root(host, environ) / "plugins"


def repository_name(source: object) -> str | None:
    if isinstance(source, Mapping):
        if source.get("source") == "github" and isinstance(source.get("repo"), str):
            return source["repo"].strip("/")
        source = source.get("url") or source.get("source")
    if not isinstance(source, str):
        return None
    match = GITHUB_REPOSITORY.search(source.strip())
    return match.group("repository") if match else None


def owned(repository: str | None) -> bool:
    return bool(repository) and repository.split("/", 1)[0].casefold() == OWNER


def claude_marketplaces(environ: Mapping[str, str] = os.environ) -> list[str]:
    path = plugins_root("claude", environ) / "known_marketplaces.json"
    try:
        known = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise RefreshError(f"Claude marketplace registry could not be read: {path}: {error}") from None
    if not isinstance(known, Mapping):
        raise RefreshError(f"Claude marketplace registry is not an object: {path}")
    return sorted(name for name, entry in known.items()
                  if isinstance(entry, Mapping) and owned(repository_name(entry.get("source"))))


def codex_marketplaces(selection: Mapping[str, object]) -> list[str]:
    configured = selection.get("effective_marketplace_configuration") or {}
    return sorted(name for name, entry in configured.items() if owned(repository_name(_marketplace_source(entry))))


def run(command: Sequence[str], cwd: Path, timeout: float) -> None:
    try:
        result = subprocess.run(list(command), cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=timeout)
    except (OSError, subprocess.SubprocessError) as error:
        raise RefreshError(f"{' '.join(command[1:4])} could not run: {error}") from None
    if result.returncode:
        detail = (result.stderr or result.stdout).strip().splitlines()
        raise RefreshError(f"{' '.join(command[1:4])} failed: {detail[-1] if detail else result.returncode}")


def main_revision(repository: str) -> str:
    try:
        result = subprocess.run(["git", "ls-remote", f"https://github.com/{repository}.git", "refs/heads/main"],
                                capture_output=True, text=True, encoding="utf-8", timeout=REMOTE_TIMEOUT_SECONDS)
    except (OSError, subprocess.SubprocessError) as error:
        raise RefreshError(f"main of {repository} could not be resolved: {error}") from None
    revision = result.stdout.split()[0] if result.returncode == 0 and result.stdout.strip() else ""
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise RefreshError(f"main of {repository} could not be resolved: {result.stderr.strip()}")
    return revision


def installed_packages(host: str, environ: Mapping[str, str] = os.environ) -> list[dict[str, object]]:
    cache = plugins_root(host, environ) / "cache"
    packages = []
    for marker in sorted(cache.glob(f"*/*/{MARKER}")):
        try:
            value = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(value, Mapping) and isinstance(value.get("identity"), str):
            packages.append({"identity": value["identity"], "repository": value.get("repository"),
                             "revision": value.get("revision"), "directory": str(marker.parent)})
    return packages


def claude_enabled(project: Path, environ: Mapping[str, str] = os.environ) -> set[str]:
    enabled: dict[str, bool] = {}
    for path in (configuration_root("claude", environ) / "settings.json", project / ".claude" / "settings.json",
                 project / ".claude" / "settings.local.json"):
        try:
            value = json.loads(path.read_text(encoding="utf-8")).get("enabledPlugins")
        except (OSError, ValueError, AttributeError):
            continue
        if isinstance(value, Mapping):
            enabled.update({identity: flag is True for identity, flag in value.items()})
    return {identity for identity, flag in enabled.items() if flag}


def codex_enabled(selection: Mapping[str, object]) -> set[str]:
    return {entry["identity"] for entry in selection.get("selections") or ()
            if isinstance(entry, Mapping) and isinstance(entry.get("identity"), str)}


def _applies(record: Mapping[str, object], project: Path) -> bool:
    scope = record.get("scope")
    if scope in {"user", "managed"}:
        return True
    owner = record.get("projectPath")
    if scope not in {"project", "local"} or not isinstance(owner, str):
        return False
    try:
        project.resolve().relative_to(Path(owner).resolve())
    except (OSError, ValueError):
        return False
    return True


def _plugin_repository(known: Mapping[str, object], identity: str) -> str | None:
    name, marketplace = identity.rsplit("@", 1)
    entry = known.get(marketplace)
    if not isinstance(entry, Mapping):
        return None
    marketplace_source = rolling_plugins.source_url(entry.get("source"))
    location = entry.get("installLocation")
    try:
        catalog = json.loads((Path(location) / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        catalog = {}
    plugins = catalog.get("plugins") if isinstance(catalog, Mapping) else None
    listed = next((item for item in plugins or () if isinstance(item, Mapping) and item.get("name") == name), None)
    source = listed.get("source") if isinstance(listed, Mapping) else None
    url = rolling_plugins.source_url(source) if isinstance(source, Mapping) else marketplace_source
    return rolling_plugins.canonical_source(url or "")


def _install_owner(record: Mapping[str, object], project: Path) -> Path:
    owner = record.get("projectPath")
    return Path(owner) if record.get("scope") in {"project", "local"} and isinstance(owner, str) else project


def claude_installs(enabled: set[str], project: Path,
                    environ: Mapping[str, str] = os.environ) -> tuple[list[Install], list[str]]:
    root = plugins_root("claude", environ)
    try:
        registry = json.loads((root / "installed_plugins.json").read_text(encoding="utf-8")).get("plugins", {})
        known = json.loads((root / "known_marketplaces.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, AttributeError) as error:
        return [], [f"Claude plugin registry could not be read: {error}"]
    installs, problems = [], []
    marketplaces = set(claude_marketplaces(environ))
    for identity, records in sorted(registry.items()) if isinstance(registry, Mapping) else ():
        if identity not in enabled or identity.rsplit("@", 1)[-1] not in marketplaces:
            continue
        repository = _plugin_repository(known, identity)
        if repository is None or not owned(repository_name(repository)):
            continue
        for record in records if isinstance(records, list) else ():
            if not isinstance(record, Mapping) or not _applies(record, project):
                continue
            install, scope = record.get("installPath"), record.get("scope")
            revision = record.get("gitCommitSha")
            if not isinstance(install, str) or not Path(install).is_dir():
                problems.append(f"{identity} ({scope}): its install {install!r} is missing")
                revision = None
            elif record.get("version") != Path(install).name:
                problems.append(f"{identity} ({scope}): registry version {record.get('version')!r} does not name "
                                f"its install directory {Path(install).name!r}, so Claude loads another copy")
            elif not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
                problems.append(f"{identity} ({scope}): {install!r} records no source revision")
                revision = None
            installs.append(Install(identity, str(scope), _install_owner(record, project), repository, revision))
    return installs, problems


def main_revisions(repositories: Iterable[str], resolve: Callable[[str], str] = main_revision) -> dict[str, str]:
    names = sorted(set(repositories))
    with ThreadPoolExecutor(max_workers=max(1, len(names))) as pool:
        return dict(zip(names, pool.map(resolve, names)))


def verify_claude(enabled: set[str], project: Path, repositories: Callable[[str], str] = main_revision,
                  environ: Mapping[str, str] = os.environ) -> dict[str, object]:
    installs, problems = claude_installs(enabled, project, environ)
    heads = main_revisions((repository_name(install.repository) for install in installs), repositories)
    packages = []
    for install in installs:
        head = heads[repository_name(install.repository)]
        packages.append({"identity": install.identity, "scope": install.scope, "repository": install.repository,
                         "revision": install.revision, "main": head, "current": install.revision == head})
        if install.revision and install.revision != head:
            problems.append(f"{install.identity} ({install.scope}) is at {install.revision}, main is {head}")
    if not packages:
        problems.append("no tj-agents package is installed for claude")
    return {"host": "claude", "packages": packages, "problems": problems}


def verify(host: str, enabled: set[str], project: Path, repositories: Callable[[str], str] = main_revision,
           environ: Mapping[str, str] = os.environ) -> dict[str, object]:
    if host == "claude":
        return verify_claude(enabled, project, repositories, environ)
    heads: dict[str, str] = {}
    packages = []
    unused_stale = []
    problems = []
    for package in installed_packages(host, environ):
        repository = repository_name(package["repository"])
        if package["identity"] not in enabled or not owned(repository):
            continue
        if repository not in heads:
            heads[repository] = repositories(repository)
        current = package["revision"] == heads[repository]
        packages.append({**package, "main": heads[repository], "current": current})
        if current:
            continue
        if host == "codex" and not package["identity"].startswith("machine@"):
            unused_stale.append(package["identity"])
        else:
            problems.append(f"{package['identity']} is at {package['revision']}, main is {heads[repository]}")
    if not packages:
        problems.append(f"no rolling tj-agents package is installed for {host}")
    report = {"host": host, "packages": packages, "problems": problems}
    if unused_stale:
        report["unused_stale_cache"] = unused_stale
    return report


def codex_selection(executable: str, project: Path) -> Mapping[str, object]:
    try:
        return codex_config_selection(executable, project, timeout=MARKETPLACE_TIMEOUT_SECONDS)
    except SyncError as error:
        raise RefreshError(str(error)) from None


def refresh(host: str, project: Path, verify_only: bool = False, environ: Mapping[str, str] = os.environ,
            launch: Callable[..., int] = run_session) -> set[str]:
    if host == "claude":
        executable = agent_cli.resolve_claude_executable()
        names = claude_marketplaces(environ)
        command = "update"
    else:
        executable, _version = agent_cli.resolve_codex_executable()
        selection = codex_selection(executable, project)
        names = codex_marketplaces(selection)
        command = "upgrade"
    if not verify_only:
        for name in names:
            progress(f"{host}: updating marketplace {name}")
            run([executable, "plugin", "marketplace", command, name], project, MARKETPLACE_TIMEOUT_SECONDS)
        progress(f"{host}: running the verified rolling refresh")
        try:
            status = launch(host, executable, project, ["--version"])
        except StartupBindingError as error:
            raise RefreshError(f"{host} rolling refresh failed: {error}") from None
        if status:
            raise RefreshError(f"{host} rolling refresh exited {status}")
    progress(f"{host}: comparing installs with main")
    return claude_enabled(project, environ) if host == "claude" else codex_enabled(selection)


def _stale(installs: Iterable[Install], heads: Mapping[str, str]) -> list[Install]:
    return [install for install in installs if install.scope in UPDATABLE_SCOPES
            and repository_name(install.repository) in heads
            and install.revision != heads[repository_name(install.repository)]]


def fast_claude(project: Path, environ: Mapping[str, str] = os.environ, repositories: Callable[[str], str] = main_revision,
                lock_wait: float = LOCK_WAIT_SECONDS, update: Callable[..., None] = run) -> dict[str, object]:
    enabled = claude_enabled(project, environ)
    installs, _problems = claude_installs(enabled, project, environ)
    progress(f"claude: resolving main for {len({install.repository for install in installs})} source repositories")
    heads = main_revisions((repository_name(install.repository) for install in installs), repositories)
    stale = _stale(installs, heads)
    if stale:
        executable = agent_cli.resolve_claude_executable()
        cache = plugins_root("claude", environ) / "cache" / ".tj-agents-rolling" / "claude"
        progress("claude: waiting for the plugin lock")
        try:
            with rolling_plugins.exclusive(cache, lock_wait):
                stale = _stale(claude_installs(enabled, project, environ)[0], heads)
                for install in stale:
                    head = heads[repository_name(install.repository)]
                    progress(f"claude: updating {install.identity} ({install.scope}) "
                             f"{(install.revision or 'unknown')[:12]} -> {head[:12]}")
                    try:
                        update([executable, "plugin", "update", install.identity, "--scope", install.scope, "--json"],
                               install.owner, UPDATE_TIMEOUT_SECONDS)
                    except RefreshError as error:
                        progress(f"claude: {install.identity} was not updated: {error}")
                current = claude_installs(enabled, project, environ)[0]
                recorded = {(install.repository, install.revision) for install in current
                            if install.revision and install.revision == heads.get(repository_name(install.repository))}
                rolling_plugins.record_generations(generations_path(plugins_root("claude", environ), "claude"), recorded)
        except rolling_plugins.RollingPluginError as error:
            raise RefreshError(f"Claude plugins are locked: {error}") from None
    report = verify_claude(enabled, project, lambda repository: heads.get(repository) or repositories(repository),
                           environ)
    if stale and not report["problems"]:
        progress("claude: updated. Run /reload-plugins in each open Claude session to load it.")
    elif not stale:
        progress("claude: already current")
    return report


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=(*HOSTS, "both"), default="both")
    parser.add_argument("--project", type=Path, default=Path.cwd())
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--full", action="store_true", help="update marketplaces and run the verified rolling refresh")
    mode.add_argument("--verify-only", action="store_true")
    arguments = parser.parse_args(list(argv) if argv is not None else None)
    hosts = HOSTS if arguments.host == "both" else (arguments.host,)
    project = arguments.project.resolve()
    reports = []
    failed = False
    for host in hosts:
        try:
            if host == "claude" and not (arguments.full or arguments.verify_only):
                report = fast_claude(project)
            elif host == "codex" and not (arguments.full or arguments.verify_only):
                progress("codex: each launch binds current main; pass --full to also refresh its shared cache")
                continue
            else:
                report = verify(host, refresh(host, project, arguments.verify_only), project)
        except (RefreshError, agent_cli.LaunchError, OSError) as error:
            report = {"host": host, "packages": [], "problems": [str(error)]}
        failed = failed or bool(report["problems"])
        reports.append(report)
    print(json.dumps(reports, indent=2))
    if arguments.full and "claude" in hosts and not failed:
        progress("Claude: run /reload-plugins in each open session. Codex: new sessions load the refreshed packages.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
