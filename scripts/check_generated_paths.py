#!/usr/bin/env python3
"""Reject pull requests that modify generated distribution output, including catalog digests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ".agents/catalog/catalog.json"


def git(*args: str, root: Path = ROOT) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def generated_roots(merge_base: str, root: Path = ROOT) -> list[str]:
    # Read from the merge base, not the PR's tree: a PR editing sources.json
    # must not be able to exempt its own paths from this guard.
    config = json.loads(git("show", f"{merge_base}:.agents/plugins/sources.json", root=root))
    return list(config["generated_roots"])


def catalog_digests(revision: str, root: Path = ROOT) -> dict[str, str]:
    try:
        catalog = json.loads(git("show", f"{revision}:{CATALOG}", root=root))
    except subprocess.CalledProcessError:
        return {}
    return {
        plugin["id"]: plugin.get("digest")
        for release in catalog.get("releases", [])
        for plugin in release.get("plugins", [])
    }


# The catalog itself is authored, but its digests are written by the same post-merge job as plugins/*.
# A PR that commits them collides with that job's commit on main, and every other open PR touching the
# same package then conflicts on the digest line.
def changed_digests(merge_base: str, root: Path = ROOT) -> list[str]:
    before, after = catalog_digests(merge_base, root), catalog_digests("HEAD", root)
    return sorted(
        f"{CATALOG} digest of {plugin_id}"
        for plugin_id in before.keys() & after.keys()
        if before[plugin_id] != after[plugin_id]
    )


def offending_paths(base: str, root: Path = ROOT) -> list[str]:
    merge_base = git("merge-base", base, "HEAD", root=root)
    roots = generated_roots(merge_base, root)
    changed = git("diff", "--name-only", f"{merge_base}..HEAD", root=root).splitlines()
    return sorted(
        path
        for path in changed
        if any(path == generated or path.startswith(generated + "/") for generated in roots)
    ) + changed_digests(merge_base, root)


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
            " must not change in a pull request. Restore it from the base and keep any"
            " local regeneration uncommitted:",
            file=sys.stderr,
        )
        for path in offending:
            print(f"  {path}", file=sys.stderr)
        return 1
    print("No generated paths changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
