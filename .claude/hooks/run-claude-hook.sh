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

# A hook's stdin read can otherwise block forever if the harness's write-end pipe handle
# survives this bash -> exec hop without EOF-ing (observed on Windows/MSYS git-bash: the hook
# stays parked in json.load(sys.stdin) as an unkillable zombie, and the harness's own declared
# hook timeout does not reap it). Self-enforce a ceiling under that declared timeout so the
# process always exits.
exec timeout -k 1s 13s "$python_command" -B "$script"
