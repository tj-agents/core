"""Require every repository-selected plugin in the active native host (Python 3.9+)."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess


IDENTITY = re.compile(r"[a-z][a-z0-9-]*@[a-z][a-z0-9-]*\Z")
INVENTORY_TIMEOUT_SECONDS = 5
MAINTENANCE_COMMANDS = {
    "codex": frozenset({"plugin", "login", "logout", "doctor", "help", "completion", "update", "mcp", "features"}),
    "claude": frozenset({"plugin", "plugins", "auth", "doctor", "install", "setup-token", "update", "upgrade", "mcp"}),
}
MODEL_CONFIG_KEYS = frozenset({
    "model", "model_provider", "model_reasoning_effort", "model_reasoning_summary",
    "model_verbosity", "service_tier", "personality",
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
    original_project = project
    value_options = {
        "-C", "--cd", "-c", "--config", "-m", "--model", "-p", "--profile",
        "-s", "--sandbox", "-a", "--ask-for-approval", "--add-dir", "--enable", "--disable",
        "--remote", "--remote-auth-token-env", "-i", "--image", "--local-provider",
    } if host == "codex" else {
        "--model", "--permission-mode", "--settings", "--setting-sources", "--plugin-dir", "--plugin-url",
    }
    configuration_options = {"-c", "--config", "-p", "--profile", "--enable", "--disable"} if host == "codex" else {
        "--settings", "--setting-sources", "--plugin-dir", "--plugin-url",
    }
    inventory_options = []
    flag_options = {
        "--no-alt-screen", "--search", "--full-auto", "--dangerously-bypass-approvals-and-sandbox",
        "--no-daemon", "--strict-config", "--oss", "--approve-for-me",
        "--dangerously-bypass-hook-trust", "--worktree",
    } if host == "codex" else set()
    command_seen = False
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--":
            break
        if argument in ("--help", "-h", "--version", "-V" if host == "codex" else "-v"):
            return
        if not command_seen and argument in MAINTENANCE_COMMANDS[host]:
            return
        option, separator, value = argument.partition("=")
        if host == "codex" and len(argument) > 2 and argument[:2] in value_options:
            option, separator, value = argument[:2], "=", argument[2:].removeprefix("=")
        if option in value_options:
            if not separator:
                index += 1
                if index >= len(arguments):
                    raise RequiredPluginsError(f"{option} requires a value")
                value = arguments[index]
            if host == "codex" and option in ("-C", "--cd"):
                project = original_project / value
            if option in configuration_options:
                inventory_options.extend((option, value))
        elif argument not in flag_options:
            command_seen = True
        index += 1
    if inventory_options:
        check(project, host, executable, inventory_options=tuple(inventory_options))
    else:
        check(project, host, executable)


def readable_payload(path: Path, host: str, name: str) -> bool:
    manifest = path / f".{host}-plugin" / "plugin.json"
    try:
        document = json.loads(manifest.read_text(encoding="utf-8-sig"))
        if not isinstance(document, dict) or document.get("name") != name:
            return False
        for field in ("skills", "hooks", "agents", "commands"):
            values = document.get(field, [])
            if isinstance(values, str):
                values = [values]
            if field == "hooks" and isinstance(values, dict):
                continue
            if not isinstance(values, list):
                return False
            for value in values:
                if not isinstance(value, str):
                    return False
                target = (path / value).resolve()
                if not target.is_relative_to(path.resolve()) or not target.exists():
                    return False
                if target.is_file():
                    target.read_bytes()
                else:
                    next(target.iterdir(), None)
        return True
    except (OSError, ValueError):
        return False


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
        if readable_payload(path, host, identity.split("@", 1)[0]):
            roots[identity] = path
    return roots


def check(project: Path, host: str, executable: str | None = None,
          inventory_options: tuple[str, ...] = ()) -> tuple[Path, ...] | None:
    project = project_root(project)
    required = selected(project)
    if not required:
        return None
    if host == "codex":
        for option, value in zip(inventory_options[::2], inventory_options[1::2]):
            key = value.partition("=")[0].strip().strip("\"'")
            if option not in ("-c", "--config") or key not in MODEL_CONFIG_KEYS:
                raise RequiredPluginsError(
                    f"Cannot verify required Codex plugins with launch override {option}: native plugin "
                    "inventory does not apply session activation overrides. Use the persisted repository "
                    "configuration for plugin, profile and feature settings, then relaunch. "
                    "Model and reasoning overrides remain available."
                )
    binary = executable or shutil.which(host)
    if not binary:
        raise RequiredPluginsError(f"Required standards cannot be verified: {host} executable is unavailable")
    try:
        command = [binary, *inventory_options, "plugin", "list", "--json"]
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
