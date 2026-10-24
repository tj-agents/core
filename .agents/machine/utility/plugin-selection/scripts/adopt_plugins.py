#!/usr/bin/env python3
"""Create or extend a repository's plugin selection and generate host settings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import urllib.request

import lock_io
import plugin_selection
import repo_config


CATALOG_URL = "https://raw.githubusercontent.com/{repository}/HEAD/.claude-plugin/marketplace.json"


def marketplace_catalog(repository: str) -> dict[str, list[str]]:
    try:
        with urllib.request.urlopen(CATALOG_URL.format(repository=repository), timeout=30) as response:
            manifest = json.load(response)
    except (OSError, ValueError) as error:
        raise lock_io.LockError(f"Cannot read the {repository} marketplace catalog: {error}") from error
    entries = manifest.get("plugins") if isinstance(manifest, dict) else None
    if not isinstance(entries, list):
        raise lock_io.LockError(f"The {repository} marketplace catalog has no plugin list")
    catalog = {}
    for entry in entries:
        name = entry.get("name") if isinstance(entry, dict) else None
        dependencies = entry.get("dependencies", []) if isinstance(entry, dict) else None
        if (not isinstance(name, str) or not isinstance(dependencies, list)
                or any(not isinstance(dependency, str) or "@" in dependency for dependency in dependencies)):
            raise lock_io.LockError(f"The {repository} marketplace catalog has an invalid plugin entry: {entry!r}")
        catalog[name] = dependencies
    return catalog


def expand(requested: set[str], catalog: dict[str, list[str]]) -> list[str]:
    pending = sorted(requested)
    selected: set[str] = set()
    while pending:
        name = pending.pop()
        if name not in catalog:
            raise lock_io.LockError(f"Unknown plugin: {name}")
        if name not in selected:
            selected.add(name)
            pending.extend(catalog[name])
    return sorted(selected)


def requested_plugins(plugins: list[str]) -> tuple[set[str], set[str]]:
    names = set()
    foreign = set()
    for plugin in plugins:
        identity = plugin if "@" in plugin else plugin_selection.plugin_id(plugin)
        if not plugin_selection.valid_identity(identity):
            raise lock_io.LockError(f"--plugin must be <plugin> or <plugin>@<marketplace>: {plugin}")
        name, marketplace = plugin_selection.split(identity)
        if marketplace == plugin_selection.MARKETPLACE_NAME:
            names.add(name)
        else:
            foreign.add(identity)
    return names, foreign


def parse_marketplace(value: str) -> tuple[str, dict]:
    name, separator, repository = value.partition("=")
    if not separator:
        raise lock_io.LockError(f"--marketplace must be <name>=<owner>/<repository>: {value}")
    source = {"repository": repository}
    plugin_selection.validate_marketplace(name, source)
    return name, source


def selection_document(root: Path, requested: set[str], foreign: set[str], declared: dict) -> dict:
    selection = plugin_selection.resolve(root)
    kept: list[str] = []
    marketplaces = {}
    legacy = root / ".agents" / "plugins.lock.json"
    if selection.is_file() and legacy.is_file():
        raise lock_io.LockError("Repository has both plugins.json and plugins.lock.json; remove the old lock after migration")
    if selection.is_file() or legacy.is_file():
        existing = lock_io.load_json(selection if selection.is_file() else legacy)
        document = existing if plugin_selection.is_current(existing) else plugin_selection.migrate(existing)
        marketplaces, kept = plugin_selection.validate(document)
    else:
        requested |= set(plugin_selection.CORE_PLUGINS)
    own = {plugin_selection.split(identity)[0] for identity in kept
           if plugin_selection.split(identity)[1] == plugin_selection.MARKETPLACE_NAME}
    if requested or own:
        catalog = marketplace_catalog(plugin_selection.MARKETPLACE_REPOSITORY)
        requested |= own & set(catalog)
    if requested:
        marketplaces.setdefault(plugin_selection.MARKETPLACE_NAME, {"repository": plugin_selection.MARKETPLACE_REPOSITORY})
    marketplaces.update(declared)
    selected = {plugin_selection.plugin_id(name) for name in expand(requested, catalog)} if requested else set()
    document = {
        "schema_version": plugin_selection.SCHEMA_VERSION,
        "marketplaces": dict(sorted(marketplaces.items())),
        "plugins": sorted(selected | set(kept) | foreign),
    }
    plugin_selection.validate(document)
    return document


def plan(root: Path, plugins: list[str], scope: str | None, marketplaces: list[str] = ()) -> tuple[dict[Path, str | None], Path]:
    root = root.expanduser().resolve()
    if root.exists() and not root.is_dir():
        raise lock_io.LockError(f"Repository root is not a directory: {root}")
    names, foreign = requested_plugins(plugins)
    declared = {}
    for value in marketplaces:
        name, source = parse_marketplace(value)
        if name in declared:
            raise lock_io.LockError(f"--marketplace {name} is given more than once")
        declared[name] = source
    document = selection_document(root, names, foreign, declared)
    selection = root / ".agents" / plugin_selection.SELECTION_NAME
    host_targets = repo_config.plan(selection, root=root, scope=scope, prospective_paths=[selection], lock_document=document)
    targets = {selection: json.dumps(document, indent=2, ensure_ascii=False) + "\n", **host_targets}
    legacy = root / ".agents" / "plugins.lock.json"
    if legacy.is_file() and not selection.is_file():
        targets[legacy] = None
    return targets, root


def run(root: Path, plugins: list[str], mode: str, scope: str | None = None, marketplaces: list[str] = ()) -> list[str]:
    targets, root = plan(root, plugins, scope, marketplaces)
    changed = {path: value for path, value in targets.items() if repo_config.text_at(path) != value}
    drift = [path.relative_to(root).as_posix() for path in changed]
    if mode == "write":
        repo_config.write_batch(changed)
    return drift


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--marketplace", action="append", default=[], metavar="NAME=OWNER/REPO")
    parser.add_argument("--plugin", action="append", default=[])
    parser.add_argument("--scope", choices=("project", "local"))
    parser.add_argument("--mode", required=True, choices=("preview", "check", "write"))
    arguments = parser.parse_args(argv)
    try:
        drift = run(arguments.root, arguments.plugin, arguments.mode, arguments.scope, arguments.marketplace)
    except (lock_io.LockError, OSError, UnicodeError, ValueError) as error:
        print(f"Plugin adoption failed: {error}", file=sys.stderr)
        return 1
    if drift:
        prefix = "Updated" if arguments.mode == "write" else "Would update" if arguments.mode == "preview" else "Drift in"
        print(prefix + ": " + ", ".join(drift))
    return int(arguments.mode == "check" and bool(drift))


if __name__ == "__main__":
    raise SystemExit(main())
