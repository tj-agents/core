#!/usr/bin/env python3
"""Move repositories to another tj-agents marketplace revision and regenerate their host settings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import adopt_plugins
import lock_io
import plugin_lock
import repo_config


def bump(root: Path, revision: str, mode: str) -> str:
    root = root.expanduser().resolve()
    adopt_plugins.refuse_local_clone(root)
    lock = plugin_lock.resolve(root)
    document = lock_io.load_json(lock)
    if not plugin_lock.is_current(document):
        raise lock_io.LockError(f"{lock}: not a schema {plugin_lock.SCHEMA_VERSION} plugin lock")
    previous = plugin_lock.validate(document)[0]["revision"]
    document["marketplace"]["revision"] = revision
    plugin_lock.validate(document)
    targets = repo_config.plan(lock, root=root, scope="project", lock_document=document)
    lock_text = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    targets = {lock: lock_text, **targets}
    changed = {path: expected for path, expected in targets.items() if repo_config.text_at(path) != expected}
    drift = [path.relative_to(root).as_posix() for path in changed]
    if mode == "write":
        repo_config.write_batch(changed)
    verb = "moved" if mode == "write" else "would move"
    return f"{root}: {verb} {previous} -> {revision} ({', '.join(drift) or 'no host settings change'})"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--root", type=Path, action="append", required=True)
    parser.add_argument("--mode", choices=("preview", "write"), default="preview")
    args = parser.parse_args(argv)
    failed = 0
    for root in args.root:
        try:
            print(bump(root, args.revision, args.mode))
        except (lock_io.LockError, OSError, UnicodeError) as error:
            print(f"{root}: {error}", file=sys.stderr)
            failed += 1
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
