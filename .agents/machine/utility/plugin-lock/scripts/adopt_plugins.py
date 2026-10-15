#!/usr/bin/env python3
"""Create or extend a repository's plugin lock and generate its host settings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import lock_io
import plugin_lock
import repo_config


ROSTER = Path(__file__).resolve().parent / "plugin_roster.json"


def load_roster() -> dict:
    roster = lock_io.load_json(ROSTER)
    if roster.get("schema_version") != 1 or set(roster) != {"schema_version", "plugins", "stacks"}:
        raise lock_io.LockError(f"{ROSTER}: invalid plugin roster")
    return roster


def expand(requested: set[str], roster: dict) -> list[str]:
    known = roster["plugins"]
    pending = sorted(requested | set(plugin_lock.CORE_PLUGINS))
    selected: set[str] = set()
    while pending:
        name = pending.pop()
        if name not in known:
            raise lock_io.LockError(f"Unknown plugin: {name}")
        if name not in selected:
            selected.add(name)
            pending.extend(known[name])
    return sorted(selected)


def requested_plugins(stacks: list[str], plugins: list[str], roster: dict) -> set[str]:
    unknown = sorted(set(stacks) - set(roster["stacks"]))
    if unknown:
        raise lock_io.LockError("Unknown stack: " + ", ".join(unknown) + "; choose from " + ", ".join(sorted(roster["stacks"])))
    return set(plugins).union(*(roster["stacks"][stack] for stack in stacks))


def refuse_local_clone(root: Path) -> None:
    if (root / repo_config.LOCAL_STATE).exists():
        raise lock_io.LockError(f"{root}: adopted with --scope local; use repo_config.py --scope local for this clone")


def lock_document(root: Path, revision: str | None, requested: set[str], roster: dict) -> dict:
    lock = plugin_lock.resolve(root)
    kept: list[str] = []
    if lock.is_file():
        existing = lock_io.load_json(lock)
        if not plugin_lock.is_current(existing):
            raise lock_io.LockError(f"{lock}: not a schema {plugin_lock.SCHEMA_VERSION} plugin lock")
        if not isinstance(existing.get("plugins"), list):
            raise lock_io.LockError(f"{lock}: plugins must be a list")
        repaired = dict(existing, plugins=sorted({*existing["plugins"], *plugin_lock.CORE_PLUGINS}, key=str))
        marketplace, kept = plugin_lock.validate(repaired)
        revision = revision or marketplace["revision"]
        requested = requested | {name for name in kept if name in roster["plugins"]}
    if revision is None:
        raise lock_io.LockError("A new plugin lock needs --marketplace-revision")
    document = {
        "schema_version": plugin_lock.SCHEMA_VERSION,
        "marketplace": {"repository": plugin_lock.MARKETPLACE_REPOSITORY, "revision": revision},
        "plugins": sorted(set(expand(requested, roster)) | set(kept)),
    }
    plugin_lock.validate(document)
    return document


def plan(root: Path, revision: str | None, stacks: list[str], plugins: list[str]) -> tuple[dict[Path, str | None], Path]:
    root = root.expanduser().resolve()
    if root.exists() and not root.is_dir():
        raise lock_io.LockError(f"Repository root is not a directory: {root}")
    refuse_local_clone(root)
    roster = load_roster()
    document = lock_document(root, revision, requested_plugins(stacks, plugins, roster), roster)
    lock = root / ".agents" / plugin_lock.LOCK_NAME
    host_targets = repo_config.plan(lock, root=root, scope="project", prospective_paths=[lock], lock_document=document)
    return {lock: json.dumps(document, indent=2, ensure_ascii=False) + "\n", **host_targets}, root


def run(root: Path, revision: str | None, stacks: list[str], plugins: list[str], mode: str) -> list[str]:
    targets, root = plan(root, revision, stacks, plugins)
    changed = {path: value for path, value in targets.items() if repo_config.text_at(path) != value}
    drift = [path.relative_to(root).as_posix() for path in changed]
    if mode == "write":
        repo_config.write_batch(changed)
    return drift


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--marketplace-revision")
    parser.add_argument("--stack", action="append", default=[])
    parser.add_argument("--plugin", action="append", default=[])
    parser.add_argument("--mode", required=True, choices=("preview", "check", "write"))
    arguments = parser.parse_args(argv)
    try:
        drift = run(arguments.root, arguments.marketplace_revision, arguments.stack, arguments.plugin, arguments.mode)
    except (lock_io.LockError, OSError, UnicodeError, ValueError) as error:
        print(f"Plugin adoption failed: {error}", file=sys.stderr)
        return 1
    if drift:
        prefix = "Updated" if arguments.mode == "write" else "Would update" if arguments.mode == "preview" else "Drift in"
        print(prefix + ": " + ", ".join(drift))
    return int(arguments.mode == "check" and bool(drift))


if __name__ == "__main__":
    raise SystemExit(main())
