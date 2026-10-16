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
    """Expand tj-agents plugin names with their roster dependencies and the core plugins."""
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


def requested_plugins(stacks: list[str], plugins: list[str], roster: dict) -> tuple[set[str], set[str]]:
    """Split the request into tj-agents roster names and foreign `<plugin>@<marketplace>` selections."""
    unknown = sorted(set(stacks) - set(roster["stacks"]))
    if unknown:
        raise lock_io.LockError("Unknown stack: " + ", ".join(unknown) + "; choose from " + ", ".join(sorted(roster["stacks"])))
    names = set().union(*(roster["stacks"][stack] for stack in stacks))
    foreign = set()
    for plugin in plugins:
        identity = plugin if "@" in plugin else plugin_lock.plugin_id(plugin)
        if not plugin_lock.valid_identity(identity):
            raise lock_io.LockError(f"--plugin must be <plugin> or <plugin>@<marketplace>: {plugin}")
        name, marketplace = plugin_lock.split(identity)
        if marketplace == plugin_lock.MARKETPLACE_NAME:
            names.add(name)
        else:
            foreign.add(identity)
    return names, foreign


def parse_marketplace(value: str) -> tuple[str, dict]:
    name, separator, rest = value.partition("=")
    repository, at, revision = rest.rpartition("@")
    if not separator or not at:
        raise lock_io.LockError(f"--marketplace must be <name>=<owner>/<repository>@<revision>: {value}")
    pin = {"repository": repository, "revision": revision}
    plugin_lock.validate_marketplace(name, pin)
    return name, pin


def lock_document(root: Path, revision: str | None, names: set[str], foreign: set[str], declared: dict, roster: dict, core_marketplace: str | None = None) -> dict:
    lock = plugin_lock.resolve(root)
    marketplaces: dict = {}
    kept: list[str] = []
    existing_core = plugin_lock.MARKETPLACE_NAME
    if lock.is_file():
        existing = lock_io.load_json(lock)
        if not plugin_lock.is_current(existing):
            raise lock_io.LockError(f"{lock}: not a schema {plugin_lock.SCHEMA_VERSION} plugin lock")
        identities = existing.get("plugins")
        if not isinstance(identities, list) or any(not isinstance(item, str) for item in identities) or len(set(identities)) != len(identities):
            raise lock_io.LockError(f"{lock}: plugins must be a list of unique plugin names")
        existing_core = plugin_lock.core_marketplace(identities)
        core = [plugin_lock.plugin_id(name, existing_core) for name in plugin_lock.CORE_PLUGINS]
        repaired = dict(existing, plugins=sorted({*identities, *core}))
        marketplaces, kept = plugin_lock.validate(repaired)
    chosen_core = core_marketplace or existing_core
    if chosen_core not in {plugin_lock.MARKETPLACE_NAME, plugin_lock.CORE_MARKETPLACE}:
        raise lock_io.LockError("Unsupported Core marketplace")
    kept = [plugin_lock.plugin_id(name, chosen_core) if name in plugin_lock.CORE_PLUGINS and marketplace == existing_core else identity
            for identity in kept for name, marketplace in [plugin_lock.split(identity)]]
    for identity in kept:
        name, marketplace = plugin_lock.split(identity)
        if marketplace == plugin_lock.MARKETPLACE_NAME and name in roster["plugins"]:
            names.add(name)
    marketplaces.update(declared)
    if revision is not None:
        marketplaces[plugin_lock.MARKETPLACE_NAME] = {"repository": plugin_lock.MARKETPLACE_REPOSITORY, "revision": revision}
    if chosen_core not in marketplaces:
        required = "--marketplace-revision" if chosen_core == plugin_lock.MARKETPLACE_NAME else "--marketplace base-agents=tj-agents/core@<revision>"
        raise lock_io.LockError("A new plugin lock needs " + required)
    for identity in foreign:
        if plugin_lock.split(identity)[1] not in marketplaces:
            raise lock_io.LockError(f"{identity} needs its marketplace declared with --marketplace")
    selected = {plugin_lock.plugin_id(name, chosen_core if name in plugin_lock.CORE_PLUGINS else plugin_lock.MARKETPLACE_NAME)
                for name in expand(names, roster)} | set(kept) | foreign
    if chosen_core != existing_core and existing_core not in {plugin_lock.split(identity)[1] for identity in selected}:
        marketplaces.pop(existing_core, None)
    document = {
        "schema_version": plugin_lock.SCHEMA_VERSION,
        "marketplaces": dict(sorted(marketplaces.items())),
        "plugins": sorted(selected),
    }
    plugin_lock.validate(document)
    return document


def plan(root: Path, revision: str | None, stacks: list[str], plugins: list[str], marketplaces: list[str] = (), core_marketplace: str | None = None) -> tuple[dict[Path, str | None], Path]:
    root = root.expanduser().resolve()
    if root.exists() and not root.is_dir():
        raise lock_io.LockError(f"Repository root is not a directory: {root}")
    repo_config.refuse_local_clone(root)
    roster = load_roster()
    names, foreign = requested_plugins(stacks, plugins, roster)
    declared: dict = {}
    for value in marketplaces:
        name, pin = parse_marketplace(value)
        if name in declared:
            raise lock_io.LockError(f"--marketplace {name} is given more than once")
        declared[name] = pin
    if revision is not None and plugin_lock.MARKETPLACE_NAME in declared:
        raise lock_io.LockError(f"Use either --marketplace-revision or --marketplace {plugin_lock.MARKETPLACE_NAME}=..., not both")
    document = lock_document(root, revision, names, foreign, declared, roster, core_marketplace)
    lock = root / ".agents" / plugin_lock.LOCK_NAME
    host_targets = repo_config.plan(lock, root=root, scope="project", prospective_paths=[lock], lock_document=document)
    return {lock: json.dumps(document, indent=2, ensure_ascii=False) + "\n", **host_targets}, root


def run(root: Path, revision: str | None, stacks: list[str], plugins: list[str], mode: str, marketplaces: list[str] = (), core_marketplace: str | None = None) -> list[str]:
    targets, root = plan(root, revision, stacks, plugins, marketplaces, core_marketplace)
    changed = {path: value for path, value in targets.items() if repo_config.text_at(path) != value}
    drift = [path.relative_to(root).as_posix() for path in changed]
    if mode == "write":
        repo_config.write_batch(changed)
    return drift


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--marketplace-revision")
    parser.add_argument("--core-marketplace", choices=(plugin_lock.MARKETPLACE_NAME, plugin_lock.CORE_MARKETPLACE))
    parser.add_argument("--marketplace", action="append", default=[], metavar="NAME=OWNER/REPO@REVISION")
    parser.add_argument("--stack", action="append", default=[])
    parser.add_argument("--plugin", action="append", default=[])
    parser.add_argument("--mode", required=True, choices=("preview", "check", "write"))
    arguments = parser.parse_args(argv)
    try:
        drift = run(arguments.root, arguments.marketplace_revision, arguments.stack, arguments.plugin, arguments.mode, arguments.marketplace, arguments.core_marketplace)
    except (lock_io.LockError, OSError, UnicodeError, ValueError) as error:
        print(f"Plugin adoption failed: {error}", file=sys.stderr)
        return 1
    if drift:
        prefix = "Updated" if arguments.mode == "write" else "Would update" if arguments.mode == "preview" else "Drift in"
        print(prefix + ": " + ", ".join(drift))
    return int(arguments.mode == "check" and bool(drift))


if __name__ == "__main__":
    raise SystemExit(main())
