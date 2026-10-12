#!/usr/bin/env python3
"""Run a typed Claude terminal command, refreshing standards when it opens a session."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_cli import sync_claude_standards
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
        try:
            sync_claude_standards(parsed.project, claude=native_target_for_shim(parsed.target))
        except OSError as error:
            print(f"standards: Claude refresh failed; this session loads installed plugins: {error}", file=sys.stderr)
    if not command:
        command = ["-n", claude_label(parsed.project)]
    flush_before_cli()
    return run_target(parsed.target, command)


if __name__ == "__main__":
    raise SystemExit(main())
