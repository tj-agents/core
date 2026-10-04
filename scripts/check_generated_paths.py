#!/usr/bin/env python3
"""Reject pull requests that modify generated distribution output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def generated_roots(merge_base: str) -> list[str]:
    # Read from the merge base, not the PR's tree: a PR editing sources.json
    # must not be able to exempt its own paths from this guard.
    config = json.loads(git("show", f"{merge_base}:.agents/plugins/sources.json"))
    return list(config["generated_roots"])


def offending_paths(base: str) -> list[str]:
    merge_base = git("merge-base", base, "HEAD")
    roots = generated_roots(merge_base)
    changed = git("diff", "--name-only", f"{merge_base}..HEAD").splitlines()
    return sorted(
        path
        for path in changed
        if any(path == root or path.startswith(root + "/") for root in roots)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="base ref the pull request targets")
    args = parser.parse_args(argv)
    try:
        offending = offending_paths(args.base)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"Generated-path guard failed to run: {error}", file=sys.stderr)
        return 1
    if offending:
        print(
            "Generated output is owned by the post-merge regeneration job on main and"
            " must not change in a pull request:",
            file=sys.stderr,
        )
        for path in offending:
            print(f"  {path}", file=sys.stderr)
        return 1
    print("No generated paths changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
