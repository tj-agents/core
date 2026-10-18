#!/usr/bin/env python3
"""Refresh Codex standards or run hook control for a typed terminal command."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_cli import LaunchError
try:
    from startup_binding import StartupBindingError, run_session
except Exception as _startup_import_error:
    _startup_unavailable = f"startup binding could not load ({_startup_import_error})"

    class StartupBindingError(Exception):
        pass

    def run_session(*_arguments: object, **_options: object) -> int:
        raise StartupBindingError(_startup_unavailable)
from terminal_command import command_for_target, flush_before_cli, run_target


NON_INTERACTIVE_COMMANDS = frozenset({
    "agents", "exec", "e", "review", "login", "logout", "mcp", "plugin",
    "app-server", "remote-control", "app", "completion", "update", "doctor",
    "sandbox", "debug", "apply", "a", "queue", "archive", "delete",
    "migrate-rollouts", "unarchive", "cloud", "exec-server", "features", "help",
})
REFRESH_BYPASS_COMMANDS = NON_INTERACTIVE_COMMANDS - {"exec", "e", "review"}
OPTIONS_WITH_VALUES = frozenset({
    "-c", "--config", "--enable", "--disable", "--remote", "--remote-auth-token-env",
    "-i", "--image", "-m", "--model", "--local-provider", "-p", "--profile",
    "-s", "--sandbox", "-C", "--cd", "--add-dir", "-a", "--ask-for-approval",
})


def supports_no_daemon(target: str) -> bool:
    try:
        result = subprocess.run(
            command_for_target(target, ["--help"]), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
    except (LaunchError, OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0 and "--no-daemon" in result.stdout


def without_daemon_for_interactive(arguments: list[str], target: str | None = None) -> list[str]:
    """Avoid the Windows daemon's visible hook children for interactive sessions."""
    if sys.platform != "win32" or "--no-daemon" in arguments:
        return arguments
    if any(argument in ("--help", "-h", "--version", "-V") for argument in arguments):
        return arguments
    if any(argument == "--remote" or argument.startswith("--remote=") for argument in arguments):
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
    if target is not None and not supports_no_daemon(target):
        return arguments
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


def bypasses_refresh(arguments: list[str]) -> bool:
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--":
            return False
        if argument in ("--help", "-h", "--version", "-V"):
            return True
        if argument in OPTIONS_WITH_VALUES:
            index += 2
            continue
        if argument.startswith("-"):
            index += 1
            continue
        return argument in REFRESH_BYPASS_COMMANDS
    return False


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
    if not bypasses_refresh(parsed.arguments):
        command = parsed.arguments
        started: list[bool] = []
        try:
            command = without_daemon_for_interactive(parsed.arguments, parsed.target)
            flush_before_cli()
            return run_session("codex", parsed.target, parsed.project, command,
                               on_launch=lambda: started.append(True),
                               keep_unacknowledged_session=True)
        except Exception as error:
            if started:
                print(f"standards: Codex session ended with a standards error: {error}", file=sys.stderr)
                return 1
            print(f"standards: Codex refresh failed: {error}; starting Codex without the standards refresh",
                  file=sys.stderr)
            return run_target(parsed.target, command)
    flush_before_cli()
    return run_target(parsed.target, without_daemon_for_interactive(parsed.arguments, parsed.target))


if __name__ == "__main__":
    raise SystemExit(main())
