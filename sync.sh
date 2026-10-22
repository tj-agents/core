#!/usr/bin/env bash
exec python3 -B "$(dirname "$0")/.agents/machine/scripts/reload_plugins.py" --project "$PWD" "$@"
