#!/usr/bin/env python3
"""Read and validate a repository's plugin lock (`.agents/plugins.lock.json`)."""

from __future__ import annotations

from pathlib import Path
import re

import bootstrap_capabilities as bootstrap


LOCK_NAME = "plugins.lock.json"
LEGACY_LOCK_NAME = "capabilities.lock.json"
SCHEMA_VERSION = 2
MARKETPLACE_NAME = "tj-agents"
MARKETPLACE_REPOSITORY = "tj-agents/marketplace"
CORE_PLUGINS = ("base", "engineering", "machine")
PLUGIN_NAME = re.compile(r"[a-z][a-z0-9-]*\Z")
REVISION = re.compile(r"v(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\Z|[0-9a-f]{40}\Z")


def resolve(root: Path) -> Path:
    """Return the repository's lock, preferring the current name over the legacy one."""
    directory = root / ".agents"
    current = directory / LOCK_NAME
    legacy = directory / LEGACY_LOCK_NAME
    if current.is_file() and legacy.is_file():
        raise bootstrap.BootstrapError(f"{directory}: both {LOCK_NAME} and {LEGACY_LOCK_NAME} exist; remove the legacy lock")
    return legacy if legacy.is_file() and not current.is_file() else current


def is_current(lock: dict) -> bool:
    return isinstance(lock, dict) and lock.get("schema_version") == SCHEMA_VERSION


def validate(lock: dict) -> tuple[dict, list[str]]:
    """Return the marketplace pin and the sorted plugin names, or raise on an invalid lock."""
    if not is_current(lock) or set(lock) != {"schema_version", "marketplace", "plugins"}:
        raise bootstrap.BootstrapError(f"{LOCK_NAME} must contain exactly schema_version {SCHEMA_VERSION}, marketplace and plugins")
    marketplace = lock["marketplace"]
    if not isinstance(marketplace, dict) or set(marketplace) != {"repository", "revision"}:
        raise bootstrap.BootstrapError("marketplace must contain exactly repository and revision")
    if marketplace["repository"] != MARKETPLACE_REPOSITORY:
        raise bootstrap.BootstrapError(f"marketplace.repository must be {MARKETPLACE_REPOSITORY}")
    revision = marketplace["revision"]
    if not isinstance(revision, str) or not REVISION.fullmatch(revision):
        raise bootstrap.BootstrapError("marketplace.revision must be a vN.N.N tag or a full lowercase commit")
    names = lock["plugins"]
    if not isinstance(names, list) or any(not isinstance(name, str) or not PLUGIN_NAME.fullmatch(name) for name in names):
        raise bootstrap.BootstrapError("plugins must be a list of plugin names")
    if len(set(names)) != len(names):
        raise bootstrap.BootstrapError("plugins must not repeat a plugin")
    missing = [name for name in CORE_PLUGINS if name not in names]
    if missing:
        raise bootstrap.BootstrapError("Repository lock omits core plugins: " + ", ".join(f"{MARKETPLACE_NAME}/{name}" for name in missing))
    return marketplace, sorted(names)
