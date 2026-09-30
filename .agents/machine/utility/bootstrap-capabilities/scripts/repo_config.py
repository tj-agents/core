#!/usr/bin/env python3
"""Generate project host settings from a committed capability lock."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

import bootstrap_capabilities as bootstrap


CORE_PLUGINS = {"base-agents/base", "base-agents/engineering", "base-agents/machine"}
MANAGED_START = "# BEGIN repo-declared agent capabilities"
MANAGED_END = "# END repo-declared agent capabilities"
TABLE = re.compile(r"^\s*\[\s*(marketplaces|plugins)(?:\.|\])")
HEADER = re.compile(r"^\s*\[")


def validate_requires(requires: dict, label: str) -> None:
    if not isinstance(requires, dict) or set(requires) != {"marketplaces", "plugins", "hooks", "permissions"}:
        raise bootstrap.BootstrapError(f"{label}: invalid harness requirements")
    if not isinstance(requires["marketplaces"], list) or not isinstance(requires["hooks"], list):
        raise bootstrap.BootstrapError(f"{label}: invalid marketplace or hook requirements")
    bootstrap.require_string_list(requires["plugins"], f"{label}.plugins")
    permissions = requires["permissions"]
    if not isinstance(permissions, dict) or set(permissions) != {"claude_allow", "codex_prefix_rules"}:
        raise bootstrap.BootstrapError(f"{label}: invalid harness permissions")
    bootstrap.require_string_list(permissions["claude_allow"], f"{label}.claude_allow")
    rules = permissions["codex_prefix_rules"]
    if not isinstance(rules, list):
        raise bootstrap.BootstrapError(f"{label}: invalid Codex prefix rules")
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) != {"pattern", "justification", "match", "not_match"}:
            raise bootstrap.BootstrapError(f"{label}: invalid Codex prefix rule")
        for field in ("pattern", "match", "not_match"):
            if not bootstrap.require_string_list(rule[field], f"{label}.{field}"):
                raise bootstrap.BootstrapError(f"{label}: empty Codex {field}")
        bootstrap.require_string(rule["justification"], f"{label}.justification")


def declarations(lock_path: Path, catalog_path: Path) -> tuple[dict[str, dict], dict[str, bool], list[str], list[dict]]:
    catalog = bootstrap.load_json(catalog_path)
    releases, plugins = bootstrap.catalog_index(catalog)
    selections = bootstrap.validate_lock(bootstrap.load_json(lock_path), releases, plugins)
    selected = {selection["id"] for selection in selections}
    missing = sorted(CORE_PLUGINS - selected)
    if missing:
        raise bootstrap.BootstrapError("Repository lock omits core plugins: " + ", ".join(missing))
    sources: dict[str, dict] = {}
    required_plugins: set[str] = set()
    claude_allow: set[str] = set()
    codex_rules: dict[str, dict] = {}
    requirements = []
    for selection in selections:
        plugin = plugins[selection["id"]]
        release = plugin["_release"]
        marketplace = release["marketplace"]
        expected = release["owner_repository"]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", expected):
            raise bootstrap.BootstrapError(f"Invalid marketplace owner: {marketplace}")
        source = release["source"].removesuffix(".git")
        if source != f"https://github.com/{expected}":
            raise bootstrap.BootstrapError(f"Marketplace source disagrees with catalog owner: {source}")
        prior = sources.get(marketplace)
        if prior is not None and prior["id"] != release["id"]:
            raise bootstrap.BootstrapError(f"Conflicting marketplace releases: {marketplace}")
        sources[marketplace] = release
        requires = plugin.get("harness")
        validate_requires(requires, selection["id"])
        requirements.append(requires)
    overlay_path = lock_path.resolve().parent / "repository-harness.json"
    if overlay_path.is_file():
        overlay = bootstrap.load_json(overlay_path)
        if not isinstance(overlay, dict) or set(overlay) != {"schema_version", "requires"} or overlay["schema_version"] != 1:
            raise bootstrap.BootstrapError(f"{overlay_path}: invalid repository harness overlay")
        validate_requires(overlay["requires"], str(overlay_path))
        requirements.append(overlay["requires"])
    for requires in requirements:
        required_plugins.update(requires["plugins"])
        for marketplace in requires["marketplaces"]:
            if not isinstance(marketplace, dict) or set(marketplace) != {"id", "repository"}:
                raise bootstrap.BootstrapError("Invalid required marketplace")
            source_release = sources.get(marketplace["id"])
            if source_release is None or source_release["owner_repository"] != marketplace["repository"]:
                raise bootstrap.BootstrapError(f"Required marketplace disagrees with selected release: {marketplace['id']}")
        claude_allow.update(requires["permissions"]["claude_allow"])
        for rule in requires["permissions"]["codex_prefix_rules"]:
            codex_rules[json.dumps(rule, sort_keys=True)] = rule
    missing = sorted(required_plugins - selected)
    if missing:
        raise bootstrap.BootstrapError("Repository lock omits harness-required plugins: " + ", ".join(missing))
    identities = {
        f"{plugin['name']}@{marketplace}": plugin["id"] in selected
        for marketplace, release in sorted(sources.items())
        for plugin in release["plugins"]
    }
    return dict(sorted(sources.items())), dict(sorted(identities.items())), sorted(claude_allow), [codex_rules[key] for key in sorted(codex_rules)]


def claude_settings(path: Path, sources: dict[str, dict], identities: dict[str, bool], allow: list[str]) -> str:
    settings = bootstrap.load_json(path) if path.is_file() else {}
    settings["extraKnownMarketplaces"] = {
        name: {"source": {"source": "github", "repo": release["owner_repository"], "ref": release["revision"]}, "autoUpdate": False}
        for name, release in sources.items()
    }
    settings["enabledPlugins"] = identities
    permissions = settings.get("permissions", {})
    if not isinstance(permissions, dict):
        raise bootstrap.BootstrapError(f"{path}: permissions must be an object")
    existing_allow = permissions.get("allow", [])
    if not isinstance(existing_allow, list) or any(not isinstance(entry, str) for entry in existing_allow):
        raise bootstrap.BootstrapError(f"{path}: permissions.allow must be a string list")
    unmanaged_allow = sorted(set(existing_allow) - set(allow))
    if unmanaged_allow:
        raise bootstrap.BootstrapError(f"{path}: unmanaged permissions.allow entries: " + ", ".join(unmanaged_allow))
    permissions["allow"] = allow
    settings["permissions"] = permissions
    return json.dumps(settings, indent=2, ensure_ascii=False) + "\n"


def unmanaged_codex(text: str) -> str:
    if text.count(MANAGED_START) != text.count(MANAGED_END) or text.count(MANAGED_START) > 1:
        raise bootstrap.BootstrapError("Malformed managed section in .codex/config.toml")
    if MANAGED_START in text:
        before, rest = text.split(MANAGED_START, 1)
        _, after = rest.split(MANAGED_END, 1)
        text = before + after.lstrip("\r\n")
    lines = text.splitlines(keepends=True)
    kept: list[str] = []
    skip = False
    for line in lines:
        if HEADER.match(line):
            skip = bool(TABLE.match(line))
        if not skip:
            kept.append(line)
    return "".join(kept).rstrip()


def codex_settings(path: Path, sources: dict[str, dict], identities: dict[str, bool]) -> str:
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    prefix = unmanaged_codex(existing)
    lines = [MANAGED_START]
    for marketplace, release in sources.items():
        sparse_paths = sorted({".agents/plugins", ".claude-plugin", *(
            plugin["package_path"].split("/", 1)[0] for plugin in release["plugins"]
        )})
        lines += [f"[marketplaces.{marketplace}]", 'source_type = "git"',
                  f'source = "https://github.com/{release["owner_repository"]}.git"',
                  f'ref = "{release["revision"]}"',
                  f"sparse_paths = {json.dumps(sparse_paths)}", ""]
    for identity, enabled in identities.items():
        lines += [f'[plugins."{identity}"]', f"enabled = {str(enabled).lower()}", ""]
    lines.append(MANAGED_END)
    return (prefix + "\n\n" if prefix else "") + "\n".join(lines) + "\n"


def codex_rules(rules: list[dict]) -> str:
    lines = ["# Generated from repository-declared agent harness requirements.", ""]
    for rule in rules:
        lines += [
            "prefix_rule(",
            f"    pattern = {json.dumps(rule['pattern'], ensure_ascii=False)},",
            '    decision = "allow",',
            f"    justification = {json.dumps(rule['justification'], ensure_ascii=False)},",
            f"    match = {json.dumps(rule['match'], ensure_ascii=False)},",
            f"    not_match = {json.dumps(rule['not_match'], ensure_ascii=False)},",
            ")",
            "",
        ]
    return "\n".join(lines)


def run(lock_path: Path, catalog_path: Path, mode: str) -> list[str]:
    root = lock_path.resolve().parent.parent
    sources, identities, allow, rules = declarations(lock_path, catalog_path)
    targets = {
        root / ".claude" / "settings.json": claude_settings(root / ".claude" / "settings.json", sources, identities, allow),
        root / ".codex" / "config.toml": codex_settings(root / ".codex" / "config.toml", sources, identities),
    }
    drift = []
    for path, expected in targets.items():
        actual = path.read_text(encoding="utf-8") if path.is_file() else None
        if actual == expected:
            continue
        drift.append(path.relative_to(root).as_posix())
        if mode == "write":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
    rule_path = root / ".codex" / "rules" / "agent-harness.rules"
    expected_rules = codex_rules(rules) if rules else None
    actual_rules = rule_path.read_text(encoding="utf-8") if rule_path.is_file() else None
    if actual_rules != expected_rules:
        drift.append(rule_path.relative_to(root).as_posix())
        if mode == "write":
            if expected_rules is None:
                rule_path.unlink()
            else:
                rule_path.parent.mkdir(parents=True, exist_ok=True)
                rule_path.write_text(expected_rules, encoding="utf-8")
    return drift


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", required=True, type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--mode", required=True, choices=("write", "check"))
    args = parser.parse_args(argv)
    try:
        catalog = args.catalog or bootstrap.catalog_for_lock(args.lock, Path(__file__).resolve())
        drift = run(args.lock, catalog, args.mode)
    except (bootstrap.BootstrapError, OSError, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    if drift:
        print(("Updated" if args.mode == "write" else "Drift in") + ": " + ", ".join(drift))
    return int(args.mode == "check" and bool(drift))


if __name__ == "__main__":
    raise SystemExit(main())
