"""Require every repository-selected plugin in the active native host (Python 3.9+)."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess


IDENTITY = re.compile(r"[a-z][a-z0-9-]*@[a-z][a-z0-9-]*\Z")
INVENTORY_TIMEOUT_SECONDS = 3
MAINTENANCE_COMMANDS = frozenset({
    "plugin", "plugins", "login", "logout", "doctor", "help", "completion", "update",
    "mcp", "features", "--help", "-h", "--version", "-V",
})


class RequiredPluginsError(RuntimeError):
    pass


def project_root(project: Path) -> Path:
    project = project.resolve()
    for directory in (project, *project.parents):
        if (directory / ".agents/plugins.json").exists() or (directory / ".git").exists():
            return directory
    return project


def check_launch(project: Path, host: str, executable: str | None, arguments) -> None:
    if arguments and arguments[0] in MAINTENANCE_COMMANDS:
        return
    for index, argument in enumerate(arguments):
        if argument == "--":
            break
        if argument in ("-C", "--cd"):
            if index + 1 >= len(arguments):
                raise RequiredPluginsError(f"{argument} requires a project directory")
            project = project / arguments[index + 1]
        elif argument.startswith("--cd="):
            project = project / argument.partition("=")[2]
    check(project, host, executable)


def selected(project: Path) -> tuple[str, ...]:
    path = project / ".agents" / "plugins.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return ()
    except (OSError, ValueError) as error:
        raise RequiredPluginsError(f"Cannot read required plugin selection {path}: {error}") from error
    plugins = document.get("plugins") if isinstance(document, dict) and document.get("schema_version") == 1 else None
    if (not isinstance(plugins, list) or not plugins
            or any(not isinstance(value, str) or not IDENTITY.fullmatch(value) for value in plugins)):
        raise RequiredPluginsError(f"{path}: plugins must list required <plugin>@<marketplace> identities")
    return tuple(sorted(set(plugins)))


def enabled_roots(host: str, project: Path, entries: list) -> dict[str, Path]:
    roots = {}
    profile = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("enabled") is not True:
            continue
        if entry.get("installed") is False or entry.get("error") or entry.get("errors"):
            continue
        owner = entry.get("projectPath")
        if entry.get("scope") in ("project", "local") and not owner:
            continue
        if owner and not isinstance(owner, str):
            continue
        if owner and entry.get("scope") not in ("user", "managed"):
            if not project.resolve().is_relative_to(Path(owner).resolve()):
                continue
        if host == "codex":
            name, marketplace, version = (entry.get(key) for key in ("name", "marketplaceName", "version"))
            if not all(isinstance(value, str) and value for value in (name, marketplace, version)):
                continue
            identity = f"{name}@{marketplace}"
            if (not IDENTITY.fullmatch(identity) or version in (".", "..")
                    or "/" in version or "\\" in version):
                continue
            path = profile / "plugins" / "cache" / marketplace / name / version
        else:
            identity, location = entry.get("id"), entry.get("installPath")
            if not isinstance(identity, str) or not IDENTITY.fullmatch(identity) or not isinstance(location, str):
                continue
            path = Path(location)
        if path.is_dir():
            roots[identity] = path
    return roots


def check(project: Path, host: str, executable: str | None = None) -> tuple[Path, ...] | None:
    project = project_root(project)
    required = selected(project)
    if not required:
        return None
    binary = executable or shutil.which(host)
    if not binary:
        raise RequiredPluginsError(f"Required standards cannot be verified: {host} executable is unavailable")
    try:
        command = [binary, "plugin", "list", "--json"]
        if os.name == "nt" and Path(binary).suffix.casefold() == ".ps1":
            command = ["powershell.exe", "-NoProfile", "-NonInteractive", "-File", *command]
        result = subprocess.run(
            command, cwd=project, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=INVENTORY_TIMEOUT_SECONDS,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise RequiredPluginsError(f"Required {host} plugin inventory could not run: {error}") from error
    if result.returncode:
        raise RequiredPluginsError(
            f"Required {host} plugin inventory failed: {(result.stderr or result.stdout).strip()[:1024]}"
        )
    try:
        data = json.loads(result.stdout)
    except ValueError as error:
        raise RequiredPluginsError(f"Required {host} plugin inventory returned invalid JSON") from error
    entries = data.get("installed") if host == "codex" and isinstance(data, dict) else data
    if not isinstance(entries, list):
        raise RequiredPluginsError(f"Required {host} plugin inventory returned an invalid roster")
    roots = enabled_roots(host, project, entries)
    missing = sorted(set(required) - roots.keys())
    if missing:
        raise RequiredPluginsError(
            f"Required standards unavailable for {host} in {project}: {', '.join(missing)}. "
            "Repair repository selection/native installation, then start a fresh session. "
            "Cached files from another host do not establish activation."
        )
    return tuple(roots.values())
