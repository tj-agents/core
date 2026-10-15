#!/usr/bin/env python3
"""Create or extend a repository's plugin selection and generate host settings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import lock_io
import plugin_selection
import repo_config


ROSTER = Path(__file__).resolve().parent / "plugin_roster.json"


def load_roster() -> dict:
    roster = lock_io.load_json(ROSTER)
    if roster.get("schema_version") != 1 or set(roster) != {"schema_version", "plugins", "stacks"}:
        raise lock_io.LockError(f"{ROSTER}: invalid plugin roster")
    return roster


def expand(requested: set[str], roster: dict) -> list[str]:
    known = roster["plugins"]
    pending = sorted(requested)
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


def selection_document(root: Path, requested: set[str], roster: dict) -> dict:
    selection = plugin_selection.resolve(root)
    kept: list[str] = []
    legacy = root / ".agents" / "plugins.lock.json"
    if selection.is_file() and legacy.is_file():
        raise lock_io.LockError("Repository has both plugins.json and plugins.lock.json; remove the old lock after migration")
    if selection.is_file() or legacy.is_file():
        existing = lock_io.load_json(selection if selection.is_file() else legacy)
        document = existing if plugin_selection.is_current(existing) else plugin_selection.migrate(existing)
        _, kept = plugin_selection.validate(document)
        requested = requested | {name for name in kept if name in roster["plugins"]}
    elif not requested:
        requested = set(plugin_selection.CORE_PLUGINS)
    document = {
        "schema_version": plugin_selection.SCHEMA_VERSION,
        "marketplace": {"repository": plugin_selection.MARKETPLACE_REPOSITORY},
        "plugins": sorted(set(expand(requested, roster)) | set(kept)),
    }
    plugin_selection.validate(document)
    return document


def plan(root: Path, stacks: list[str], plugins: list[str], scope: str) -> tuple[dict[Path, str | None], Path]:
    root = root.expanduser().resolve()
    if root.exists() and not root.is_dir():
        raise lock_io.LockError(f"Repository root is not a directory: {root}")
    roster = load_roster()
    document = selection_document(root, requested_plugins(stacks, plugins, roster), roster)
    selection = root / ".agents" / plugin_selection.SELECTION_NAME
    host_targets = repo_config.plan(selection, root=root, scope=scope, prospective_paths=[selection], lock_document=document)
    targets = {selection: json.dumps(document, indent=2, ensure_ascii=False) + "\n", **host_targets}
    legacy = root / ".agents" / "plugins.lock.json"
    if legacy.is_file() and not selection.is_file():
        targets[legacy] = None
    return targets, root


def run(root: Path, stacks: list[str], plugins: list[str], mode: str, scope: str = "project") -> list[str]:
    targets, root = plan(root, stacks, plugins, scope)
    changed = {path: value for path, value in targets.items() if repo_config.text_at(path) != value}
    drift = [path.relative_to(root).as_posix() for path in changed]
    if mode == "write":
        repo_config.write_batch(changed)
    return drift


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--stack", action="append", default=[])
    parser.add_argument("--plugin", action="append", default=[])
    parser.add_argument("--scope", choices=("project", "local"), default="project")
    parser.add_argument("--mode", required=True, choices=("preview", "check", "write"))
    arguments = parser.parse_args(argv)
    try:
        drift = run(arguments.root, arguments.stack, arguments.plugin, arguments.mode, arguments.scope)
    except (lock_io.LockError, OSError, UnicodeError, ValueError) as error:
        print(f"Plugin adoption failed: {error}", file=sys.stderr)
        return 1
    if drift:
        prefix = "Updated" if arguments.mode == "write" else "Would update" if arguments.mode == "preview" else "Drift in"
        print(prefix + ": " + ", ".join(drift))
    return int(arguments.mode == "check" and bool(drift))


if __name__ == "__main__":
    raise SystemExit(main())
