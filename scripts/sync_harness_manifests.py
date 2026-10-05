#!/usr/bin/env python3
"""Validate package harness declarations against authored sources and hook wiring."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
HOST_ROOTS = {
    "codex": re.compile(r"\$\{PLUGIN_ROOT\}/([^\"']+)"),
    "claude": re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\"']+)"),
}
REQUIRED_KEYS = {"marketplaces", "plugins", "hooks", "permissions"}


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
                    for field in ("command", "commandWindows"):
                        command = hook.get(field, "")
                        for match in HOST_ROOTS[host].finditer(command):
                            by_path.setdefault(match.group(1), set()).add(host)
    return [
        {"path": path, "hosts": sorted(hosts)}
        for path, hosts in sorted(by_path.items())
    ]


def validate_requires(root: Path, config: dict, catalog: dict, plugin: str, requires: dict) -> None:
    if set(requires) != REQUIRED_KEYS:
        raise ValueError(f"{plugin}: harness requires fields must be {sorted(REQUIRED_KEYS)}")
    marketplaces = requires["marketplaces"]
    releases = {release["marketplace"]: release for release in catalog["releases"]}
    for marketplace in marketplaces:
        if set(marketplace) != {"id", "repository"}:
            raise ValueError(f"{plugin}: invalid marketplace declaration")
        release = releases.get(marketplace["id"])
        if release is None or release["owner_repository"] != marketplace["repository"]:
            raise ValueError(f"{plugin}: marketplace declaration disagrees with catalog: {marketplace}")
        if release["source"].removesuffix(".git") != f"https://github.com/{marketplace['repository']}":
            raise ValueError(f"{plugin}: marketplace source disagrees with catalog owner: {marketplace}")
    plugin_id = f"base-agents/{plugin}"
    entries = {
        item["id"]: item
        for release in catalog["releases"]
        for item in release["plugins"]
    }
    if plugin_id not in entries:
        raise ValueError(f"{plugin}: missing catalog entry {plugin_id}")
    expected_plugins = sorted([plugin_id, *entries[plugin_id]["dependencies"]["required"]])
    if requires["plugins"] != expected_plugins:
        raise ValueError(f"{plugin}: required plugins must be {expected_plugins}")
    expected_marketplaces = sorted({value.split("/", 1)[0] for value in expected_plugins})
    actual_marketplaces = sorted(item["id"] for item in marketplaces)
    if actual_marketplaces != expected_marketplaces or any(value not in releases for value in actual_marketplaces):
        raise ValueError(f"{plugin}: marketplace declarations disagree with required plugins")
    if requires["hooks"] != expected_hooks(root, config, plugin):
        raise ValueError(f"{plugin}: declared hooks disagree with both host manifests")
    permissions = requires["permissions"]
    if set(permissions) != {"claude_allow", "codex_prefix_rules"}:
        raise ValueError(f"{plugin}: invalid permissions declaration")
    if len(permissions["claude_allow"]) != len(set(permissions["claude_allow"])):
        raise ValueError(f"{plugin}: duplicate Claude permission")
    for command in permissions["claude_allow"]:
        if re.match(r"^PowerShell\(&\s+\*\\", command, re.IGNORECASE):
            raise ValueError(f"{plugin}: wildcard script path in Claude permission: {command}")
    for rule in permissions["codex_prefix_rules"]:
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
        if manifest["plugin"] != f"base-agents/{plugin}":
            raise ValueError(f"{path}: plugin identity mismatch")
        expected_roots = sorted(scope["root"] for scope in config["scopes"] if scope["plugin"] == plugin)
        if manifest["source_roots"] != expected_roots:
            raise ValueError(f"{path}: source roots must be {expected_roots}")
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
