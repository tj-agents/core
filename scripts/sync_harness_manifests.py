#!/usr/bin/env python3
"""Validate package harness declarations and refresh their authored-source digests."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
HOST_ROOTS = {
    "codex": re.compile(r"\$\{PLUGIN_ROOT\}/([^\"']+)"),
    "claude": re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\"'@]+)"),
}
REQUIRED_KEYS = {"marketplaces", "plugins", "hooks", "permissions"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def inside(root: Path, relative: str) -> Path:
    path = (root / Path(*PurePosixPath(relative).parts)).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes repository: {relative}")
    return path


def add_path(root: Path, relative: str, members: dict[str, bytes], excludes: set[str]) -> None:
    root = root.resolve()
    source = inside(root, relative)
    if not source.exists():
        raise ValueError(f"Missing harness source: {relative}")
    paths = sorted(source.rglob("*")) if source.is_dir() else [source]
    for path in paths:
        if not path.is_file() or path.suffix == ".pyc" or "__pycache__" in path.parts:
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Harness source escapes repository: {path}")
        name = path.relative_to(root).as_posix()
        if name not in excludes:
            data = path.read_bytes()
            # Git may check out text as CRLF or LF. Bind the declaration to the same
            # authored content on both hosts without rewriting opaque binary assets.
            members[name] = data.replace(b"\r\n", b"\n") if b"\0" not in data else data


def source_projection(config: dict, plugin: str) -> dict:
    projection = {
        "scopes": [item for item in config["scopes"] if item["plugin"] == plugin],
        "host_adapter_roots": config["host_adapter_roots"],
        "host_manifest_roots": config["host_manifest_roots"],
        "host_hook_sources": config.get("host_hook_sources", {}).get(plugin, {}),
        "resources": [item for item in config.get("resources", []) if item["plugin"] == plugin],
        "prerequisites": config["prerequisites"][plugin],
    }
    workflow = config.get("workflow")
    if workflow and workflow.get("plugin") == plugin:
        projection["workflow"] = workflow
    return projection


def source_digest(root: Path, manifest: dict, config: dict, plugin: str) -> str:
    excludes = set(manifest["source_excludes"])
    allowed = {".agents/catalog/catalog.json"} if plugin == "machine" else set()
    if excludes - allowed:
        raise ValueError(f"{plugin}: unsupported source exclusions: {sorted(excludes - allowed)}")
    members: dict[str, bytes] = {}
    for relative in manifest["source_roots"]:
        add_path(root, relative, members, excludes)
    projection = source_projection(config, plugin)
    members[".agents/plugins/sources.json#" + plugin] = (
        json.dumps(projection, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    for resource in projection["resources"]:
        add_path(root, resource["source"], members, excludes)
    for relative in projection["host_hook_sources"].values():
        add_path(root, relative, members, excludes)
    for host, relative in config["host_manifest_roots"].items():
        add_path(root, f"{relative}/{plugin}.json", members, excludes)
    skill_names = {
        path.parent.name
        for relative in manifest["source_roots"]
        for path in inside(root, relative).rglob("SKILL.md")
    }
    for relative in config["host_adapter_roots"].values():
        for name in skill_names:
            add_path(root, f"{relative}/{name}", members, excludes)
    if "workflow" in projection:
        add_path(root, projection["workflow"]["source"], members, excludes)
    digest = hashlib.sha256()
    for relative, data in sorted(members.items()):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(len(data)).encode("ascii"))
        digest.update(b"\0")
        digest.update(data)
    return "sha256:" + digest.hexdigest()


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
        required = {"schema_version", "plugin", "source_roots", "source_excludes", "source_digest", "requires"}
        if set(manifest) != required or manifest.get("schema_version") != 1:
            raise ValueError(f"{path}: invalid manifest shape or schema version")
        if manifest["plugin"] != f"base-agents/{plugin}":
            raise ValueError(f"{path}: plugin identity mismatch")
        expected_roots = sorted(scope["root"] for scope in config["scopes"] if scope["plugin"] == plugin)
        if manifest["source_roots"] != expected_roots:
            raise ValueError(f"{path}: source roots must be {expected_roots}")
        validate_requires(root, config, catalog, plugin, manifest["requires"])
        digest = source_digest(root, manifest, config, plugin)
        if manifest["source_digest"] != digest:
            if check:
                raise ValueError(f"{path}: stale source digest")
            manifest["source_digest"] = digest
            path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
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
