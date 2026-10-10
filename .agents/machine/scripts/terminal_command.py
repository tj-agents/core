"""Shared dispatch for terminal-profile Claude and Codex adapters."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

import agent_cli


CLAUDE_NON_SESSION_COMMANDS = frozenset({
    "agents", "attach", "auth", "auto-mode", "doctor", "gateway", "import", "install",
    "kill", "logs", "mcp", "plugin", "plugins", "project", "rm", "setup-token", "stop",
    "ultrareview", "update", "upgrade", "-h", "--help", "-v", "--version",
})


def batch_launcher_kind(target: str) -> str | None:
    """Return the supported CLI named by a Windows batch launcher, if any."""
    name = target.replace("\\", "/").rsplit("/", 1)[-1].casefold()
    if not name.endswith((".cmd", ".bat")):
        return None
    stem = name.rsplit(".", 1)[0]
    return stem if stem in {"claude", "codex"} else None


def native_target_for_batch(target: str) -> str:
    """Resolve a supported batch shim to its native executable without invoking cmd.exe."""
    kind = batch_launcher_kind(target)
    if target.replace("\\", "/").rsplit("/", 1)[-1].casefold().endswith((".cmd", ".bat")) and kind is None:
        raise OSError(f"unsupported batch launcher cannot run safely: {target}")
    if kind is None:
        return target
    try:
        if kind == "claude":
            return agent_cli.resolve_claude_executable()
        resolved, _version = agent_cli.resolve_codex_executable()
        return resolved
    except agent_cli.LaunchError as error:
        raise OSError(f"{kind} batch launcher cannot run safely: {error}") from None


def command_for_target(target: str, arguments: list[str]) -> list[str]:
    """Build the platform-required argument list without changing the typed arguments."""
    suffix = Path(target).suffix.casefold()
    if os.name == "nt" and suffix == ".ps1":
        shell = shutil.which("pwsh") or shutil.which("powershell.exe")
        if not shell:
            raise OSError("PowerShell is required to run the selected CLI launcher")
        return [shell, "-NoProfile", "-File", target, *arguments]
    if os.name == "nt" and suffix in {".cmd", ".bat"}:
        native = native_target_for_batch(target)
        return [native, *arguments]
    return [target, *arguments]


def run_target(target: str, arguments: list[str]) -> int:
    try:
        return subprocess.run(command_for_target(target, arguments)).returncode
    except OSError as error:
        print(f"terminal launcher could not start {target}: {error}", file=sys.stderr)
        return 127


def flush_before_cli() -> None:
    sys.stdout.flush()
    sys.stderr.flush()


def claude_label(project: Path) -> str:
    label = project.name
    try:
        branch = subprocess.run(
            ["git", "branch", "--show-current"], cwd=project, capture_output=True,
            text=True, encoding="utf-8", errors="replace",
        )
    except OSError:
        return label
    if branch.returncode == 0 and (name := branch.stdout.strip()):
        return f"{label}/{name}"
    return label
