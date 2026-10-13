#!/usr/bin/env python3
"""Refresh Codex standards or run hook control for a typed terminal command."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from codex_marketplace_sync import SyncError, resolve_codex_for_sync, sync_codex_standards
from terminal_command import flush_before_cli, run_target


NON_INTERACTIVE_COMMANDS = frozenset({
    "agents", "exec", "e", "review", "login", "logout", "mcp", "plugin",
    "app-server", "remote-control", "app", "completion", "update", "doctor",
    "sandbox", "debug", "apply", "a", "queue", "archive", "delete",
    "migrate-rollouts", "unarchive", "cloud", "exec-server", "features", "help",
})
OPTIONS_WITH_VALUES = frozenset({
    "-c", "--config", "--enable", "--disable", "--remote", "--remote-auth-token-env",
    "-i", "--image", "-m", "--model", "--local-provider", "-p", "--profile",
    "-s", "--sandbox", "-C", "--cd", "--add-dir", "-a", "--ask-for-approval",
})


def without_daemon_for_interactive(arguments: list[str]) -> list[str]:
    """Avoid the Windows daemon's visible hook children for interactive sessions."""
    if sys.platform != "win32" or "--no-daemon" in arguments:
        return arguments
    if any(argument in ("--help", "-h", "--version", "-V") for argument in arguments):
        return arguments
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--":
            break
        if argument in OPTIONS_WITH_VALUES:
            index += 2
            continue
        if argument.startswith("-"):
            index += 1
            continue
        if argument in NON_INTERACTIVE_COMMANDS:
            return arguments
        break
    return ["--no-daemon", *arguments]


def hook_control(arguments: list[str]) -> int:
    script = Path(__file__).resolve().parents[3] / ".agents" / "machine" / "utility" / "hook-control" / "scripts" / "hook_control.py"
    if not script.is_file():
        print("Codex hook-control utility is not installed", file=sys.stderr)
        return 1
    try:
        return subprocess.run([sys.executable, "-I", "-B", str(script), *arguments]).returncode
    except OSError as error:
        print(f"Codex hook-control utility could not start: {error}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--hooks", action="store_true")
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    parsed = parser.parse_args(argv)
    if parsed.arguments[:1] == ["--"]:
        parsed.arguments = parsed.arguments[1:]
    if parsed.hooks:
        return hook_control(parsed.arguments)
    if not parsed.arguments or parsed.arguments[0] != "plugin":
        try:
            sync_codex_standards(resolve_codex_for_sync(parsed.target), parsed.project)
        except SyncError as error:
            print(f"standards: Codex refresh failed; this session loads installed plugins: {error}", file=sys.stderr)
    flush_before_cli()
    return run_target(parsed.target, without_daemon_for_interactive(parsed.arguments))


if __name__ == "__main__":
    raise SystemExit(main())
