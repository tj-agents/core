#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null; then
    python=$candidate
    break
  fi
done
if [[ -z ${python:-} ]]; then
  echo "open.sh: Python 3.9 or newer is required" >&2
  exit 1
fi

page=$("$python" guide/build.py --print-output)
"$python" guide/build.py

if [[ ${1:-} != --build-only ]]; then
  "$python" -c 'import pathlib, sys, webbrowser; webbrowser.open(pathlib.Path(sys.argv[1]).resolve().as_uri())' "$page"
fi
