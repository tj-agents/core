#!/usr/bin/env bash
root="$(dirname "$0")"
python3 -B "$root/scripts/runtime_sources.py" || exit $?
exec python3 -B "$root/.agents/dependencies/agent/.agents/agent/runtime/reload_plugins.py" --project "$PWD" "$@"
