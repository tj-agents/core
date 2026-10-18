#!/usr/bin/env python3
"""Refresh Claude and Codex tj-agents plugins to current main and verify what each host will load."""

from __future__ import annotations

import argparse
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
from startup_binding import StartupBindingError, run_session  # noqa: E402

HOSTS = ("claude", "codex")
OWNER = "tj-agents"
MARKER = ".tj-agents-rolling.json"
MARKETPLACE_TIMEOUT_SECONDS = 180
REMOTE_TIMEOUT_SECONDS = 30
GITHUB_REPOSITORY = re.compile(r"github\.com[/:](?P<repository>[^/]+/[^/]+?)(?:\.git)?/?$", re.IGNORECASE)


class RefreshError(RuntimeError):
    pass


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


def claude_registry_problems(enabled: set[str], project: Path, environ: Mapping[str, str] = os.environ) -> list[str]:
    path = plugins_root("claude", environ) / "installed_plugins.json"
    try:
        registry = json.loads(path.read_text(encoding="utf-8")).get("plugins", {})
    except (OSError, ValueError, AttributeError) as error:
        return [f"Claude plugin registry could not be read: {error}"]
    problems = []
    marketplaces = set(claude_marketplaces(environ))
    for identity, records in registry.items() if isinstance(registry, Mapping) else ():
        if identity not in enabled or identity.rsplit("@", 1)[-1] not in marketplaces:
            continue
        for record in records if isinstance(records, list) else ():
            if not isinstance(record, Mapping) or not _applies(record, project):
                continue
            install = record.get("installPath")
            scope = record.get("scope")
            marker = Path(install).parent / MARKER if isinstance(install, str) else None
            if marker is None or not marker.is_file():
                problems.append(f"{identity} ({scope}): {install!r} is not a rolling install, so Claude loads "
                                f"an unrefreshed copy")
                continue
            try:
                revision = json.loads(marker.read_text(encoding="utf-8")).get("revision")
            except (OSError, ValueError, AttributeError):
                revision = None
            if Path(install).name != revision:
                problems.append(f"{identity} ({scope}): Claude loads {Path(install).name!r}, but the refreshed "
                                f"install is {revision!r}")
            elif record.get("version") != Path(install).name:
                problems.append(f"{identity} ({scope}): registry version {record.get('version')!r} does not name "
                                f"its install directory {Path(install).name!r}, so Claude loads another copy")
    return problems


def verify(host: str, enabled: set[str], project: Path, repositories: Callable[[str], str] = main_revision,
           environ: Mapping[str, str] = os.environ) -> dict[str, object]:
    heads: dict[str, str] = {}
    packages = []
    unused_stale = []
    problems = claude_registry_problems(enabled, project, environ) if host == "claude" else []
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
            run([executable, "plugin", "marketplace", command, name], project, MARKETPLACE_TIMEOUT_SECONDS)
        try:
            status = launch(host, executable, project, ["--version"])
        except StartupBindingError as error:
            raise RefreshError(f"{host} rolling refresh failed: {error}") from None
        if status:
            raise RefreshError(f"{host} rolling refresh exited {status}")
    return claude_enabled(project, environ) if host == "claude" else codex_enabled(selection)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=(*HOSTS, "both"), default="both")
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--verify-only", action="store_true")
    arguments = parser.parse_args(list(argv) if argv is not None else None)
    hosts = HOSTS if arguments.host == "both" else (arguments.host,)
    project = arguments.project.resolve()
    reports = []
    failed = False
    for host in hosts:
        try:
            report = verify(host, refresh(host, project, arguments.verify_only), project)
        except (RefreshError, agent_cli.LaunchError, OSError) as error:
            report = {"host": host, "packages": [], "problems": [str(error)]}
        failed = failed or bool(report["problems"])
        reports.append(report)
    print(json.dumps(reports, indent=2))
    if "claude" in hosts and not failed:
        print("Claude: run /reload-plugins in each open session. Codex: new sessions load the refreshed packages.",
              file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
