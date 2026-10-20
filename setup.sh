#!/usr/bin/env bash
exec python3 -B "$(dirname "$0")/.agents/machine/scripts/setup_machine.py" "$@"
