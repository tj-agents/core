#!/usr/bin/env bash
root="$(dirname "$0")"
runtime_source_args=()
for argument in "$@"; do
  [[ "$argument" == "--check" ]] && runtime_source_args+=(--check)
done
python3 -B "$root/scripts/runtime_sources.py" "${runtime_source_args[@]}" || exit $?
exec python3 -B "$root/.agents/machine/scripts/setup_machine.py" "$@"
