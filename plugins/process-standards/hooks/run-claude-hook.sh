#!/usr/bin/env bash

set -u

if [ "$#" -ne 1 ]; then
    echo "Usage: run-claude-hook.sh <hook.py>" >&2
    exit 1
fi

script=$1
case "$(uname -s)" in
    CYGWIN*|MINGW*|MSYS*)
        python_command=python
        script="$(cygpath -w "$script")"
        ;;
    *) python_command=python3 ;;
esac

exec "$python_command" -B "$script"
