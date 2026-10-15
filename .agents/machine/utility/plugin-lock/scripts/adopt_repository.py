#!/usr/bin/env python3
"""Compose and adopt immutable capability snapshots for one repository."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys

import bootstrap_capabilities as bootstrap
import compose_catalog
import repo_config


LOCK = Path(".agents/capabilities.lock.json")
CATALOG = Path(".agents/catalog/catalog.json")
CORE = repo_config.CORE_PLUGINS


def rendered(document: dict) -> str:
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def load_existing(lock_path: Path, catalog_path: Path) -> tuple[dict | None, dict | None]:
    if lock_path.is_file() != catalog_path.is_file():
        raise bootstrap.BootstrapError("Repository capability lock and catalog must be committed together")
    if not lock_path.is_file():
        return None, None
    catalog = bootstrap.load_json(catalog_path)
    releases, plugins = bootstrap.catalog_index(copy.deepcopy(catalog))
    lock = bootstrap.load_json(lock_path)
    bootstrap.validate_lock(lock, releases, plugins)
    return lock, catalog


def release_commits(lock: dict | None) -> dict[str, str]:
    if lock is None:
        return {}
    commits: dict[str, str] = {}
    for selection in lock["plugins"]:
        release = selection["release"]
        commit = selection["commit"]
        previous = commits.setdefault(release, commit)
        if previous != commit:
            raise bootstrap.BootstrapError(f"Selections from {release} disagree on the exact commit")
    return commits


def combined_catalog(existing: dict | None, candidate: dict, lock: dict | None) -> dict:
    bootstrap.catalog_index(copy.deepcopy(candidate))
    if existing is None:
        return candidate
    bootstrap.catalog_index(copy.deepcopy(existing))
    commits = release_commits(lock)
    candidates = {release["marketplace"]: release for release in candidate["releases"]}
    merged = []
    for release in existing["releases"]:
        replacement = candidates.pop(release["marketplace"], None)
        if replacement is None:
            merged.append(copy.deepcopy(release))
            continue
        if replacement["owner_repository"] != release["owner_repository"]:
            raise bootstrap.BootstrapError(f"Marketplace owner cannot change: {release['marketplace']}")
        if replacement["id"] != release["id"]:
            raise bootstrap.BootstrapError(f"Marketplace release cannot change: {release['marketplace']}")
        locked = commits.get(release["id"])
        if locked is not None and replacement["revision"] != locked:
            raise bootstrap.BootstrapError(f"Marketplace snapshot cannot change: {release['marketplace']}")
        if locked is None and replacement["revision"] != release["revision"]:
            raise bootstrap.BootstrapError(f"Marketplace snapshot cannot change: {release['marketplace']}")
        packages = {plugin["id"]: plugin for plugin in release["plugins"]}
        for plugin in replacement["plugins"]:
            existing_plugin = packages.get(plugin["id"])
            if existing_plugin is not None and existing_plugin != plugin:
                raise bootstrap.BootstrapError(f"Marketplace package cannot change: {plugin['id']}")
            packages[plugin["id"]] = plugin
        replacement = copy.deepcopy(replacement)
        replacement["plugins"] = [packages[key] for key in sorted(packages)]
        merged.append(replacement)
    merged.extend(candidates.values())
    result = {"schema_version": 1, "digest_format": "sha256-tree-v1", "releases": sorted(merged, key=lambda value: value["id"])}
    bootstrap.catalog_index(copy.deepcopy(result))
    return result


def closure(plugin_ids: set[str], plugins: dict[str, dict]) -> set[str]:
    pending = list(plugin_ids)
    selected = set(plugin_ids)
    while pending:
        plugin_id = pending.pop()
        plugin = plugins.get(plugin_id)
        if plugin is None:
            raise bootstrap.BootstrapError(f"Repository adoption selects unknown plugin: {plugin_id}")
        for dependency in plugin["dependencies"]["required"]:
            if dependency not in selected:
                selected.add(dependency)
                pending.append(dependency)
    return selected


def lock_document(
    existing: dict | None,
    catalog: dict,
    requested: list[str],
) -> dict:
    releases, plugins = bootstrap.catalog_index(copy.deepcopy(catalog))
    previous = {} if existing is None else {selection["id"]: copy.deepcopy(selection) for selection in existing["plugins"]}
    pinned_releases = release_commits(existing)
    selected = closure(set(requested) | CORE | set(previous), plugins)
    values = []
    for plugin_id in sorted(selected):
        if plugin_id in previous:
            values.append(previous[plugin_id])
            continue
        plugin = plugins[plugin_id]
        release = plugin["_release"]
        commit = pinned_releases.get(release["id"], release["revision"])
        values.append({
            "id": plugin_id,
            "release": release["id"],
            "commit": commit,
            "required_skills": sorted(plugin["skills"]),
            "path_scopes": [],
            "exceptions": [],
        })
    result = copy.deepcopy(existing) if existing is not None else {"schema_version": 1}
    result["schema_version"] = 1
    result["plugins"] = values
    bootstrap.validate_lock(copy.deepcopy(result), releases, plugins)
    return result


def plan(root: Path, input_path: Path, requested: list[str]) -> tuple[dict[Path, str | None], Path]:
    root = root.expanduser().resolve()
    if root.exists() and not root.is_dir():
        raise bootstrap.BootstrapError(f"Repository root is not a directory: {root}")
    if not root.exists() and not root.parent.is_dir():
        raise bootstrap.BootstrapError(f"Repository root parent does not exist: {root.parent}")
    input_path = input_path.expanduser().resolve()
    if not input_path.is_file():
        raise bootstrap.BootstrapError(f"Composition input does not exist: {input_path}")
    lock_path = root / LOCK
    catalog_path = root / CATALOG
    existing_lock, existing_catalog = load_existing(lock_path, catalog_path)
    candidate = compose_catalog.compose_catalog(bootstrap.load_json(input_path), bootstrap.platform_name())
    catalog = combined_catalog(existing_catalog, candidate, existing_lock)
    lock = lock_document(existing_lock, catalog, requested)
    host_targets = repo_config.plan(
        lock_path,
        catalog_path,
        root=root,
        scope="project",
        prospective_paths=[lock_path, catalog_path],
        lock_document=lock,
        catalog_document=catalog,
        read_paths=[input_path],
    )
    targets = {lock_path: rendered(lock), catalog_path: rendered(catalog), **host_targets}
    return targets, root


def run(root: Path, input_path: Path, requested: list[str], mode: str) -> list[str]:
    if mode not in {"preview", "check", "write"}:
        raise bootstrap.BootstrapError(f"Unknown repository mode: {mode}")
    targets, root = plan(root, input_path, requested)
    changed = {path: value for path, value in targets.items() if repo_config.text_at(path) != value}
    drift = [path.relative_to(root).as_posix() for path in changed]
    if mode == "write":
        repo_config.write_batch(changed)
    return drift


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--plugin", action="append", required=True)
    parser.add_argument("--mode", required=True, choices=("preview", "check", "write"))
    arguments = parser.parse_args(argv)
    try:
        drift = run(arguments.root, arguments.input, arguments.plugin, arguments.mode)
    except (bootstrap.BootstrapError, OSError, UnicodeError, ValueError) as error:
        print(f"Repository adoption failed: {error}", file=sys.stderr)
        return 1
    if drift:
        prefix = "Updated" if arguments.mode == "write" else "Would update" if arguments.mode == "preview" else "Drift in"
        print(prefix + ": " + ", ".join(drift))
    return int(arguments.mode == "check" and bool(drift))


if __name__ == "__main__":
    raise SystemExit(main())
