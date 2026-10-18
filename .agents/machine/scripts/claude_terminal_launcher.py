#!/usr/bin/env python3
"""Run a typed Claude terminal command, refreshing standards when it opens a session."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from startup_binding import StartupBindingError, run_session
except Exception as _startup_import_error:
    _startup_unavailable = f"startup binding could not load ({_startup_import_error})"

    class StartupBindingError(Exception):
        pass

    def run_session(*_arguments: object, **_options: object) -> int:
        raise StartupBindingError(_startup_unavailable)
from terminal_command import (
    CLAUDE_NON_SESSION_COMMANDS,
    claude_label,
    flush_before_cli,
    native_target_for_shim,
    run_target,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    parsed = parser.parse_args(argv)
    command = parsed.arguments
    if command[:1] == ["--"]:
        command = command[1:]
    if not command or command[0] not in CLAUDE_NON_SESSION_COMMANDS:
        started: list[object] = []
        try:
            if not command:
                command = ["-n", claude_label(parsed.project)]
            flush_before_cli()
            return run_session("claude", parsed.target, parsed.project, command,
                               on_running=lambda child_pid=None: started.append(child_pid))
        except Exception as error:
            if started:
                print(f"standards: Claude session ended with a standards error: {error}", file=sys.stderr)
                return 1
            print(f"standards: Claude refresh failed: {error}; starting Claude without the standards refresh",
                  file=sys.stderr)
            return run_target(parsed.target, command)
    if not command:
        command = ["-n", claude_label(parsed.project)]
    flush_before_cli()
    return run_target(parsed.target, command)


if __name__ == "__main__":
    raise SystemExit(main())
