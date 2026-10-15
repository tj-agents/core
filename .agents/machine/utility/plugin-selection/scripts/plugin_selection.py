#!/usr/bin/env python3
"""Read and validate a repository's plugin selection (`.agents/plugins.json`)."""

from __future__ import annotations

from pathlib import Path
import re

import lock_io


SELECTION_NAME = "plugins.json"
SCHEMA_VERSION = 1
MARKETPLACE_NAME = "tj-agents"
MARKETPLACE_REPOSITORY = "tj-agents/marketplace"
CORE_PLUGINS = ("base", "engineering", "machine")
PLUGIN_NAME = re.compile(r"[a-z][a-z0-9-]*\Z")


def resolve(root: Path) -> Path:
    return root / ".agents" / SELECTION_NAME


def is_current(selection: dict) -> bool:
    return isinstance(selection, dict) and selection.get("schema_version") == SCHEMA_VERSION


def validate(selection: dict) -> tuple[dict, list[str]]:
    """Return the marketplace and sorted plugin names, or raise on invalid selection."""
    if not is_current(selection) or set(selection) != {"schema_version", "marketplace", "plugins"}:
        raise lock_io.LockError(f"{SELECTION_NAME} must contain exactly schema_version {SCHEMA_VERSION}, marketplace and plugins")
    marketplace = selection["marketplace"]
    if not isinstance(marketplace, dict) or set(marketplace) != {"repository"}:
        raise lock_io.LockError("marketplace must contain exactly repository")
    if marketplace["repository"] != MARKETPLACE_REPOSITORY:
        raise lock_io.LockError(f"marketplace.repository must be {MARKETPLACE_REPOSITORY}")
    names = selection["plugins"]
    if not isinstance(names, list) or any(not isinstance(name, str) or not PLUGIN_NAME.fullmatch(name) for name in names):
        raise lock_io.LockError("plugins must be a list of plugin names")
    if len(set(names)) != len(names):
        raise lock_io.LockError("plugins must not repeat a plugin")
    return marketplace, sorted(names)


def migrate(lock: dict) -> dict:
    if not isinstance(lock, dict) or lock.get("schema_version") != 2:
        raise lock_io.LockError("Migration accepts only schema_version 2 plugin locks")
    marketplace = lock.get("marketplace")
    names = lock.get("plugins")
    if not isinstance(marketplace, dict) or marketplace.get("repository") != MARKETPLACE_REPOSITORY:
        raise lock_io.LockError("Legacy marketplace.repository must be tj-agents/marketplace")
    return {"schema_version": SCHEMA_VERSION, "marketplace": {"repository": MARKETPLACE_REPOSITORY}, "plugins": names}
