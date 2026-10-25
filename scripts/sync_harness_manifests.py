#!/usr/bin/env python3
"""Validate package harness declarations against authored sources and hook wiring."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
DISTRIBUTION_REPOSITORY = "tj-agents/marketplace"
HOST_ROOTS = {
    "codex": re.compile(r"\$\{PLUGIN_ROOT\}/([^\"']+)"),
    "claude": re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\"'@]+)"),
}
REQUIRED_KEYS = {"marketplaces", "plugins", "hooks", "permissions"}
PACKAGES_SPEC = importlib.util.spec_from_file_location(
    "harness_package_sync", Path(__file__).resolve().with_name("sync_plugin_packages.py")
)
PACKAGES = importlib.util.module_from_spec(PACKAGES_SPEC)
PACKAGES_SPEC.loader.exec_module(PACKAGES)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def inside(root: Path, relative: str) -> Path:
    path = (root / Path(*PurePosixPath(relative).parts)).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes repository: {relative}")
    return path


def expected_hooks(root: Path, config: dict, plugin: str) -> list[dict]:
    by_path: dict[str, set[str]] = {}
    for host, relative in config.get("host_hook_sources", {}).get(plugin, {}).items():
        payload = load(inside(root, relative))
        for groups in payload.get("hooks", {}).values():
            for group in groups:
                for hook in group.get("hooks", []):
                    arguments = hook.get("args")
                    parts = [hook.get("command", ""), hook.get("commandWindows", "")]
                    if isinstance(arguments, list):
                        parts.extend(argument for argument in arguments if isinstance(argument, str))
                    for command in parts:
                        for match in HOST_ROOTS[host].finditer(command):
                            by_path.setdefault(match.group(1), set()).add(host)
    return [
        {"path": path, "hosts": sorted(hosts)}
        for path, hosts in sorted(by_path.items())
    ]


def validate_requires(root: Path, config: dict, catalog: dict, plugin: str, requires: dict) -> None:
    if set(requires) not in (REQUIRED_KEYS, REQUIRED_KEYS | {"setup"}):
        raise ValueError(f"{plugin}: harness requires fields must be {sorted(REQUIRED_KEYS)}")
    if "setup" in requires:
        setup = requires["setup"]
        if not isinstance(setup, dict) or set(setup) != {"script"} or not isinstance(setup["script"], str):
            raise ValueError(f"{plugin}: invalid setup declaration")
        script = PurePosixPath(setup["script"])
        if script.is_absolute() or ".." in script.parts or script.suffix != ".py" or not setup["script"]:
            raise ValueError(f"{plugin}: invalid setup declaration")
        if not inside(root, setup["script"]).is_file():
            raise ValueError(f"{plugin}: setup script is unavailable")
    required_marketplaces = requires["marketplaces"]
    marketplace_name = PACKAGES.core_marketplace(root, config)
    entries = PACKAGES.catalog_index(catalog)
    catalog_marketplaces = PACKAGES.catalog_marketplaces(entries)
    for marketplace in required_marketplaces:
        if set(marketplace) != {"id", "repository"}:
            raise ValueError(f"{plugin}: invalid marketplace declaration")
        package = catalog_marketplaces.get(marketplace["id"])
        if package is None:
            raise ValueError(f"{plugin}: marketplace declaration disagrees with catalog: {marketplace}")
        expected = DISTRIBUTION_REPOSITORY if marketplace["id"] == marketplace_name else package["owner_repository"]
        if marketplace["repository"] != expected:
            raise ValueError(f"{plugin}: marketplace declaration disagrees with catalog: {marketplace}")
        if package["source"].removesuffix(".git") != f"https://github.com/{package['owner_repository']}":
            raise ValueError(f"{plugin}: marketplace source disagrees with catalog owner: {marketplace}")
    plugin_id = f"{marketplace_name}/{plugin}"
    if plugin_id not in entries:
        raise ValueError(f"{plugin}: missing catalog entry {plugin_id}")
    expected_plugins = sorted([plugin_id, *entries[plugin_id]["dependencies"]["required"]])
    if requires["plugins"] != expected_plugins:
        raise ValueError(f"{plugin}: required plugins must be {expected_plugins}")
    expected_marketplaces = sorted({value.split("/", 1)[0] for value in expected_plugins})
    actual_marketplaces = sorted(item["id"] for item in required_marketplaces)
    if actual_marketplaces != expected_marketplaces or any(value not in catalog_marketplaces for value in actual_marketplaces):
        raise ValueError(f"{plugin}: marketplace declarations disagree with required plugins")
    if requires["hooks"] != expected_hooks(root, config, plugin):
        raise ValueError(f"{plugin}: declared hooks disagree with both host manifests")
    permissions = requires["permissions"]
    if set(permissions) not in ({"claude_allow", "codex_prefix_rules"}, {"claude_allow", "codex_prefix_rules", "auto_merge"}):
        raise ValueError(f"{plugin}: invalid permissions declaration")
    scopes = [permissions]
    if "auto_merge" in permissions:
        if not isinstance(permissions["auto_merge"], dict) or set(permissions["auto_merge"]) != {"claude_allow", "codex_prefix_rules"}:
            raise ValueError(f"{plugin}: invalid auto-merge permissions declaration")
        scopes.append(permissions["auto_merge"])
    for scope in scopes:
        if len(scope["claude_allow"]) != len(set(scope["claude_allow"])):
            raise ValueError(f"{plugin}: duplicate Claude permission")
        for command in scope["claude_allow"]:
            if re.match(r"^PowerShell\(&\s+\*\\", command, re.IGNORECASE):
                raise ValueError(f"{plugin}: wildcard script path in Claude permission: {command}")
        for rule in scope["codex_prefix_rules"]:
            if set(rule) != {"pattern", "justification", "match", "not_match"}:
                raise ValueError(f"{plugin}: invalid Codex prefix rule")
            if not all(rule.get(field) for field in ("pattern", "justification", "match", "not_match")):
                raise ValueError(f"{plugin}: Codex prefix rules require pattern, justification and examples")


def synchronize(root: Path, check: bool) -> dict[str, dict]:
    config = load(root / ".agents/plugins/sources.json")
    catalog = load(root / ".agents/catalog/catalog.json")
    directory = root / ".agents/plugins/harness"
    expected = {scope["plugin"] for scope in config["scopes"]}
    found = {path.stem for path in directory.glob("*.json")}
    if found != expected:
        raise ValueError(f"Harness manifest roster drift: expected {sorted(expected)}, found {sorted(found)}")
    result: dict[str, dict] = {}
    for plugin in sorted(expected):
        path = directory / f"{plugin}.json"
        manifest = load(path)
        required = {"schema_version", "plugin", "source_roots", "requires"}
        if set(manifest) != required or manifest.get("schema_version") != 1:
            raise ValueError(f"{path}: invalid manifest shape or schema version")
        if manifest["plugin"] != f"{PACKAGES.core_marketplace(root, config)}/{plugin}":
            raise ValueError(f"{path}: plugin identity mismatch")
        expected_roots = sorted(scope["root"] for scope in config["scopes"] if scope["plugin"] == plugin)
        roots = manifest["source_roots"]
        if not isinstance(roots, list) or not all(isinstance(value, str) for value in roots) or roots != sorted(set(roots)):
            raise ValueError(f"{path}: source roots must be sorted unique paths")
        if not set(expected_roots).issubset(roots):
            raise ValueError(f"{path}: source roots must include {expected_roots}")
        resources = [inside(root, resource["source"]) for resource in config.get("resources", []) if resource["plugin"] == plugin]
        for relative in set(roots) - set(expected_roots):
            source = inside(root, relative)
            if source.relative_to(root.resolve()).as_posix() != relative or not source.exists() or not any(source == resource or resource.is_dir() and source.is_relative_to(resource) for resource in resources):
                raise ValueError(f"{path}: source root is not a canonical shipped {plugin} resource: {relative}")
        validate_requires(root, config, catalog, plugin, manifest["requires"])
        result[plugin] = manifest
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifests = synchronize(args.root.resolve(), args.check)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Harness manifest sync failed: {error}", file=sys.stderr)
        return 1
    print(f"{'Checked' if args.check else 'Synchronized'} {len(manifests)} harness manifests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
