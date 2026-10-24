#!/usr/bin/env python3
"""Find and remove marketplace registrations superseded by the tj-agents marketplace (Python 3.11+)."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))

import plugin_autoupdate
import reload_plugins

CANONICAL = "tj-agents"


def owned(source: object) -> bool:
    if not isinstance(source, dict):
        return False
    if "source_type" in source:
        location = source.get("source") if source.get("source_type") == "git" else None
    else:
        location = source.get("repo") or source.get("url")
    repository = reload_plugins.repository(location)
    return bool(repository) and repository.split("/", 1)[0] == CANONICAL


def catalog_names(catalog: dict) -> set[str]:
    entries = catalog.get("plugins")
    return {entry["name"] for entry in entries if isinstance(entry, dict) and isinstance(entry.get("name"), str)} \
        if isinstance(entries, list) else set()


def claude_catalog(entry: object) -> set[str]:
    location = entry.get("installLocation") if isinstance(entry, dict) else None
    return catalog_names(reload_plugins.read_json(Path(location) / ".claude-plugin/marketplace.json")) if location else set()


def canonical_names(host: str) -> set[str]:
    if host == "claude":
        known = reload_plugins.read_json(reload_plugins.configuration_root("claude") / "plugins/known_marketplaces.json")
        return claude_catalog(known.get(CANONICAL))
    return catalog_names(plugin_autoupdate.marketplace_manifest(CANONICAL))


def enabled_from(identities: object, marketplace: str) -> list[str]:
    if isinstance(identities, dict):
        identities = [identity for identity, flag in identities.items()
                      if flag is True or isinstance(flag, dict) and flag.get("enabled") is True]
    return sorted(identity for identity in identities or []
                  if isinstance(identity, str) and identity.rpartition("@")[2] == marketplace)


def superseded(marketplace: str, source: object, offered: set[str], enabled: list[str], canonical: set[str]) -> bool:
    names = offered | {identity.rpartition("@")[0] for identity in enabled}
    return marketplace != CANONICAL and owned(source) and bool(names & canonical)


def replacement(identities: list[str]) -> str:
    return ", ".join(f"{identity} -> {identity.rpartition('@')[0]}@{CANONICAL}" for identity in identities)


def claude_layers(project: Path) -> list[tuple[Path, dict]]:
    root = reload_plugins.configuration_root("claude")
    return [(path, reload_plugins.read_json(path)) for path in (
        root / "settings.json", project / ".claude/settings.json", project / ".claude/settings.local.json")]


def claude_installed(marketplace: str) -> list[str]:
    installed = reload_plugins.read_json(
        reload_plugins.configuration_root("claude") / "plugins/installed_plugins.json").get("plugins")
    return sorted(identity for identity, entries in (installed or {}).items()
                  if identity.rpartition("@")[2] == marketplace and entries)


def review_claude(project: Path, executable: Callable[[], str], run: Callable) -> tuple[list[str], list[str]]:
    canonical = canonical_names("claude")
    if not canonical:
        return [], []
    known = reload_plugins.read_json(reload_plugins.configuration_root("claude") / "plugins/known_marketplaces.json")
    layers = claude_layers(project)
    removed, problems = [], []
    for path, settings in layers[1:]:
        for name, declaration in sorted((settings.get("extraKnownMarketplaces") or {}).items()):
            enabled = enabled_from(settings.get("enabledPlugins"), name)
            source = declaration.get("source") if isinstance(declaration, dict) else None
            if superseded(name, source, claude_catalog(known.get(name)), enabled, canonical):
                problems.append(f"legacy marketplace {name} is declared in {path}; remove it"
                                + (f" and switch {replacement(enabled)}" if enabled else ""))
    for name in sorted(known):
        enabled = sorted({identity for path, settings in layers
                          for identity in enabled_from(settings.get("enabledPlugins"), name)})
        source = known[name].get("source") if isinstance(known[name], dict) else None
        if not superseded(name, source, claude_catalog(known[name]), enabled, canonical):
            continue
        installed = claude_installed(name)
        if enabled or installed:
            problems.append(f"legacy marketplace {name} (claude) is still used by {', '.join(enabled or installed)}; "
                            f"switch {replacement(enabled or installed)}")
            continue
        run([executable(), "plugin", "marketplace", "remove", name], project)
        removed.append(f"claude:{name}")
    return removed, problems


def review_codex(project: Path, executable: Callable[[], str], run: Callable) -> tuple[list[str], list[str]]:
    canonical = canonical_names("codex")
    if not canonical:
        return [], []
    user = plugin_autoupdate.load_codex_config()
    layers = plugin_autoupdate.declarations(user)
    removed, problems = [], []
    for directory, layer in layers[1:]:
        for name, source in sorted(plugin_autoupdate.section(layer, "marketplaces").items()):
            enabled = enabled_from(plugin_autoupdate.section(layer, "plugins"), name)
            if superseded(name, source, catalog_names(plugin_autoupdate.marketplace_manifest(name)), enabled, canonical):
                problems.append(f"legacy marketplace {name} is declared in {directory / '.codex/config.toml'}; remove it"
                                + (f" and switch {replacement(enabled)}" if enabled else ""))
    cache = plugin_autoupdate.codex_home() / "plugins" / "cache"
    for name, source in sorted(plugin_autoupdate.section(user, "marketplaces").items()):
        enabled = sorted({identity for _, layer in layers
                          for identity in enabled_from(plugin_autoupdate.section(layer, "plugins"), name)})
        if not superseded(name, source, catalog_names(plugin_autoupdate.marketplace_manifest(name)), enabled, canonical):
            continue
        installed = sorted(f"{path.name}@{name}" for path in (cache / name).glob("*") if path.is_dir())
        if enabled or installed:
            problems.append(f"legacy marketplace {name} (codex) is still used by {', '.join(enabled or installed)}; "
                            f"switch {replacement(enabled or installed)}")
            continue
        run([executable(), "plugin", "marketplace", "remove", name], project)
        removed.append(f"codex:{name}")
    return removed, problems


def review(host: str, project: Path, executable: Callable[[], str], run: Callable = reload_plugins.run) -> tuple[list[str], list[str]]:
    return (review_claude if host == "claude" else review_codex)(project, executable, run)
