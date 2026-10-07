#!/usr/bin/env python3
"""Compose a capability catalog from explicitly selected immutable Git snapshots."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from urllib.parse import urlsplit

import bootstrap_capabilities as bootstrap
import harness_permissions


SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-((?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*))?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$")
REPOSITORY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$")


def git(checkout: Path, arguments: list[str], data: bytes | None = None) -> bytes:
    environment = os.environ.copy()
    environment["GIT_NO_REPLACE_OBJECTS"] = "1"
    result = subprocess.run(
        ["git", "-C", str(checkout), *arguments], input=data,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment, check=False,
    )
    if result.returncode:
        raise bootstrap.BootstrapError(f"Git snapshot inspection failed ({arguments[0]})")
    return result.stdout


def origin_repository(origin: str) -> str:
    scp = re.fullmatch(r"git@github\.com:([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?", origin)
    if scp:
        return scp.group(1)
    try:
        url = urlsplit(origin)
        if url.scheme not in {"https", "ssh"} or url.hostname != "github.com" or url.port is not None or url.query or url.fragment:
            raise ValueError
        path = url.path.removeprefix("/").removesuffix(".git")
        if not REPOSITORY.fullmatch(path):
            raise ValueError
        return path
    except ValueError:
        raise bootstrap.BootstrapError("Origin must identify a GitHub repository") from None


def relative_path(value: str, label: str) -> str:
    bootstrap.require_string(value, label)
    path = value.removeprefix("./").rstrip("/")
    parts = PurePosixPath(path).parts
    if not parts or path.startswith("/") or "\\" in path or ":" in path or any(part in {".", ".."} for part in path.split("/")):
        raise bootstrap.BootstrapError(f"Unsafe package-relative path: {label}")
    return path


def read_snapshot(source: dict) -> dict[str, bytes]:
    checkout = Path(bootstrap.require_string(source.get("checkout"), "source.checkout"))
    repository = bootstrap.require_string(source.get("repository"), "source.repository")
    commit = source.get("commit")
    if not checkout.is_absolute() or not checkout.is_dir():
        raise bootstrap.BootstrapError("Source checkout must be an existing absolute directory")
    if not REPOSITORY.fullmatch(repository) or repository.endswith(".git"):
        raise bootstrap.BootstrapError("Source repository must be owner/repo")
    if not isinstance(commit, str) or not bootstrap.HEX_COMMIT.fullmatch(commit):
        raise bootstrap.BootstrapError("Source commit must be a full lowercase Git commit")
    origin = git(checkout, ["remote", "get-url", "origin"]).decode("utf-8").strip()
    if origin_repository(origin).lower() != repository.lower():
        raise bootstrap.BootstrapError("GitHub origin disagrees with source repository")
    if git(checkout, ["cat-file", "-t", commit]).strip() != b"commit":
        raise bootstrap.BootstrapError("Source commit must identify a real commit object")
    names = bootstrap.require_string_list(source.get("plugins"), "source.plugins")
    if not names or any(not bootstrap.SAFE_NAME.fullmatch(name) for name in names):
        raise bootstrap.BootstrapError("Source plugins must contain canonical package names")
    if source.get("version_plugin") not in names:
        raise bootstrap.BootstrapError("Source version_plugin must name a selected package")
    metadata = {".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json", ".agents/catalog/catalog.json"}
    entries = []
    for record in git(checkout, ["ls-tree", "-rz", "--full-tree", commit]).split(b"\0"):
        if not record:
            continue
        header, raw_path = record.split(b"\t", 1)
        path = raw_path.decode("utf-8")
        if path not in metadata and not any(path == f"plugins/{name}" or path.startswith(f"plugins/{name}/") for name in names):
            continue
        mode, kind, oid = header.split()
        if mode not in {b"100644", b"100755"} or kind != b"blob":
            raise bootstrap.BootstrapError(f"Snapshot rejects linked or non-file payload: {path}")
        relative_path(path, path)
        entries.append((path, oid))
    output = git(checkout, ["cat-file", "--batch"], b"".join(oid + b"\n" for _, oid in entries))
    files = {}
    offset = 0
    for path, oid in entries:
        end = output.index(b"\n", offset)
        found, kind, length = output[offset:end].split()
        size = int(length)
        if found != oid or kind != b"blob":
            raise bootstrap.BootstrapError("Git batch returned an unexpected object")
        offset = end + 1
        files[path] = output[offset:offset + size]
        offset += size + 1
    return files


def object_json(files: dict[str, bytes], path: str) -> dict:
    try:
        value = json.loads(files[path].decode("utf-8"))
    except (KeyError, UnicodeError, json.JSONDecodeError):
        raise bootstrap.BootstrapError(f"Missing or invalid snapshot JSON: {path}") from None
    if not isinstance(value, dict):
        raise bootstrap.BootstrapError(f"Snapshot JSON must be an object: {path}")
    return value


def marketplace(files: dict[str, bytes], names: list[str]) -> str:
    identities = []
    for host, path in (("claude", ".claude-plugin/marketplace.json"), ("codex", ".agents/plugins/marketplace.json")):
        manifest = object_json(files, path)
        identity = manifest.get("name")
        if not isinstance(identity, str) or not bootstrap.SAFE_NAME.fullmatch(identity):
            raise bootstrap.BootstrapError("Invalid marketplace identity")
        identities.append(identity)
        entries = manifest.get("plugins")
        if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
            raise bootstrap.BootstrapError("Invalid marketplace package declarations")
        for name in names:
            matches = [entry for entry in entries if entry.get("name") == name]
            if len(matches) != 1:
                raise bootstrap.BootstrapError(f"Marketplace must declare package exactly once: {name}")
            location = matches[0].get("source")
            if host == "codex":
                if not isinstance(location, dict) or location.get("source") != "local":
                    raise bootstrap.BootstrapError(f"Marketplace package must be local: {name}")
                location = location.get("path")
            if location not in {f"plugins/{name}", f"./plugins/{name}"}:
                raise bootstrap.BootstrapError(f"Marketplace package path must equal plugins/{name}")
    if identities[0] != identities[1]:
        raise bootstrap.BootstrapError("Native marketplace identities disagree")
    return identities[0]


def qualified(values: list[str], market: str, label: str) -> list[str]:
    return sorted(f"{market}/{value}" if "/" not in value else value for value in bootstrap.require_string_list(values, label))


def policy_entries(files: dict[str, bytes], repository: str, market: str) -> dict[str, dict]:
    path = ".agents/catalog/catalog.json"
    if path not in files:
        return {}
    catalog = object_json(files, path)
    if catalog.get("schema_version") != 1 or catalog.get("digest_format") != "sha256-tree-v1" or not isinstance(catalog.get("releases"), list):
        raise bootstrap.BootstrapError("Invalid source-owned catalog")
    policies = {}
    for release in catalog["releases"]:
        if not isinstance(release, dict):
            raise bootstrap.BootstrapError("Invalid source catalog release")
        if release.get("marketplace") != market:
            continue
        if release.get("owner_repository") != repository:
            raise bootstrap.BootstrapError("Source catalog marketplace owner disagrees")
        for plugin in release.get("plugins", []):
            if not isinstance(plugin, dict) or plugin.get("id") in policies:
                raise bootstrap.BootstrapError("Ambiguous source-owned catalog policy")
            policies[plugin.get("id")] = plugin
    return policies


def compose_catalog(document: dict, platform: str) -> dict:
    if document.get("schema_version") != 1 or not isinstance(document.get("sources"), list) or not document["sources"]:
        raise bootstrap.BootstrapError("Composition requires schema_version 1 and non-empty sources")
    bootstrap.require_string(platform, "Consumption platform")
    releases = []
    owners = {}
    for source in sorted(document["sources"], key=lambda item: item.get("repository", "") if isinstance(item, dict) else ""):
        if not isinstance(source, dict):
            raise bootstrap.BootstrapError("Each composition source must be an object")
        files = read_snapshot(source)
        market = marketplace(files, source["plugins"])
        repository = source["repository"]
        if market in owners:
            raise bootstrap.BootstrapError("Each marketplace must have one source snapshot")
        owners[market] = repository
        policies = policy_entries(files, repository, market)
        plugins = []
        for name in sorted(source["plugins"]):
            root = f"plugins/{name}/"
            payload = {path[len(root):]: data for path, data in files.items() if path.startswith(root)}
            native = {host: object_json(payload, f".{host}-plugin/plugin.json") for host in ("codex", "claude")}
            if any(manifest.get("name") != name for manifest in native.values()):
                raise bootstrap.BootstrapError(f"Native package identity disagrees: {name}")
            version = native["codex"].get("version")
            if not isinstance(version, str) or not SEMVER.fullmatch(version):
                raise bootstrap.BootstrapError(f"Codex package version must be semantic: {name}")
            if "version" in native["claude"] and native["claude"]["version"] != version:
                raise bootstrap.BootstrapError(f"Native package versions disagree: {name}")
            for manifest in native.values():
                if "repository" in manifest and origin_repository(bootstrap.require_string(manifest["repository"], "native repository")).lower() != repository.lower():
                    raise bootstrap.BootstrapError(f"Native package repository disagrees: {name}")
            plugin_id = f"{market}/{name}"
            harness = object_json(payload, "harness.json")
            if harness.get("schema_version") != 1 or harness.get("plugin") != plugin_id:
                raise bootstrap.BootstrapError(f"Harness identity disagrees: {plugin_id}")
            requires = harness.get("requires")
            harness_permissions.validate_requires(requires, plugin_id)
            if plugin_id not in requires["plugins"] or {"id": market, "repository": repository} not in requires["marketplaces"]:
                raise bootstrap.BootstrapError(f"Harness must declare its own package and marketplace: {plugin_id}")
            for hook in requires["hooks"]:
                if not isinstance(hook, dict) or set(hook) != {"path", "hosts"} or not isinstance(hook.get("hosts"), list) or not hook["hosts"] or any(host not in {"codex", "claude"} for host in hook["hosts"]):
                    raise bootstrap.BootstrapError(f"Invalid harness hook: {plugin_id}")
                if relative_path(hook.get("path"), "harness hook") not in payload:
                    raise bootstrap.BootstrapError(f"Missing harness hook payload: {plugin_id}")
            dependencies = sorted(set(qualified(requires["plugins"], market, plugin_id)) - {plugin_id})
            if "selection.json" in payload:
                selection = object_json(payload, "selection.json")
                if selection.get("plugin") != name:
                    raise bootstrap.BootstrapError(f"Selection identity disagrees: {plugin_id}")
                for field in ("dependencies", "prerequisites"):
                    if field in selection and qualified(selection[field], market, field) != dependencies:
                        raise bootstrap.BootstrapError(f"Selection dependencies disagree with harness: {plugin_id}")
            skills_by_host = []
            for host, manifest in native.items():
                roots = manifest.get("skills", "./skills/")
                roots = roots if isinstance(roots, list) else [roots]
                if not roots:
                    raise bootstrap.BootstrapError(f"Missing native skills roots: {plugin_id}")
                skills = set()
                for skill_root in roots:
                    prefix = relative_path(skill_root, f"{host} skills root") + "/"
                    if not any(path.startswith(prefix) for path in payload):
                        raise bootstrap.BootstrapError(f"Missing shipped skills root: {plugin_id}")
                    found = [path[len(prefix):].split("/")[0] for path in payload if path.startswith(prefix) and path[len(prefix):].count("/") == 1 and path.endswith("/SKILL.md")]
                    skills.update(found)
                if any(not bootstrap.SAFE_NAME.fullmatch(skill) for skill in skills):
                    raise bootstrap.BootstrapError(f"Invalid shipped skill identity: {plugin_id}")
                skills_by_host.append(sorted(skills))
            if skills_by_host[0] != skills_by_host[1]:
                raise bootstrap.BootstrapError(f"Native shipped skills disagree: {plugin_id}")
            policy = policies.get(plugin_id, {})
            plugin = {
                "id": plugin_id, "name": name, "package_path": f"plugins/{name}", "version": version,
                "description": native["codex"].get("description"), "status": policy.get("status", "current"),
                "platforms": policy.get("platforms", [platform]), "skills": skills_by_host[0],
                "dependencies": {"required": dependencies, "optional": []},
                "external_prerequisites": policy.get("external_prerequisites", {"required": [], "optional": []}),
                "harness": requires,
            }
            if "dependencies" in policy:
                if not isinstance(policy["dependencies"], dict) or qualified(policy["dependencies"].get("required"), market, "catalog dependencies") != dependencies:
                    raise bootstrap.BootstrapError(f"Source catalog dependencies disagree with harness: {plugin_id}")
                plugin["dependencies"]["optional"] = qualified(policy["dependencies"].get("optional"), market, "catalog optional dependencies")
            excludes = bootstrap.require_string_list(policy.get("digest_excludes", []), "digest_excludes")
            for excluded in excludes:
                if relative_path(excluded, "digest exclusion") != excluded or excluded not in payload:
                    raise bootstrap.BootstrapError(f"Invalid digest exclusion: {plugin_id}")
            if excludes:
                plugin["digest_excludes"] = excludes
            digest = hashlib.sha256()
            for path, data in sorted(payload.items()):
                if path not in excludes:
                    digest.update(path.encode("utf-8") + b"\0" + str(len(data)).encode("ascii") + b"\0" + data)
            plugin["digest"] = "sha256:" + digest.hexdigest()
            plugins.append(plugin)
        anchor = next(plugin for plugin in plugins if plugin["name"] == source["version_plugin"])
        releases.append({"id": f"{market}@{anchor['version']}", "owner_repository": repository,
                         "source": f"https://github.com/{repository}.git", "marketplace": market,
                         "revision": source["commit"], "version": anchor["version"], "plugins": plugins})
    for release in releases:
        for plugin in release["plugins"]:
            for declaration in plugin["harness"]["marketplaces"]:
                if not isinstance(declaration, dict) or set(declaration) != {"id", "repository"} or owners.get(declaration.get("id")) != declaration.get("repository"):
                    raise bootstrap.BootstrapError("Harness marketplace owner is unresolved or contradictory")
    catalog = {"schema_version": 1, "digest_format": "sha256-tree-v1", "releases": releases}
    bootstrap.catalog_index(copy.deepcopy(catalog))
    return catalog


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--platform", default=bootstrap.platform_name())
    arguments = parser.parse_args()
    try:
        catalog = compose_catalog(bootstrap.load_json(arguments.input), arguments.platform)
        rendered = json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"
        sys.stdout.write(rendered)
        return 0
    except (bootstrap.BootstrapError, OSError, UnicodeError, ValueError) as error:
        print(f"Catalog composition failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
