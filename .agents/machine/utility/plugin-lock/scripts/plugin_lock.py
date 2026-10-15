#!/usr/bin/env python3
"""Read and validate a repository's plugin lock (`.agents/plugins.lock.json`)."""

from __future__ import annotations

from pathlib import Path
import re

import lock_io


LOCK_NAME = "plugins.lock.json"
SCHEMA_VERSION = 2
MARKETPLACE_NAME = "tj-agents"
MARKETPLACE_REPOSITORY = "tj-agents/marketplace"
CORE_PLUGINS = ("base", "engineering", "machine")
PLUGIN_NAME = re.compile(r"[a-z][a-z0-9-]*\Z")
REVISION = re.compile(r"v(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\Z|[0-9a-f]{40}\Z")


def resolve(root: Path) -> Path:
    return root / ".agents" / LOCK_NAME


def is_current(lock: dict) -> bool:
    return isinstance(lock, dict) and lock.get("schema_version") == SCHEMA_VERSION


def validate(lock: dict) -> tuple[dict, list[str]]:
    """Return the marketplace pin and the sorted plugin names, or raise on an invalid lock."""
    if not is_current(lock) or set(lock) != {"schema_version", "marketplace", "plugins"}:
        raise lock_io.LockError(f"{LOCK_NAME} must contain exactly schema_version {SCHEMA_VERSION}, marketplace and plugins")
    marketplace = lock["marketplace"]
    if not isinstance(marketplace, dict) or set(marketplace) != {"repository", "revision"}:
        raise lock_io.LockError("marketplace must contain exactly repository and revision")
    if marketplace["repository"] != MARKETPLACE_REPOSITORY:
        raise lock_io.LockError(f"marketplace.repository must be {MARKETPLACE_REPOSITORY}")
    revision = marketplace["revision"]
    if not isinstance(revision, str) or not REVISION.fullmatch(revision):
        raise lock_io.LockError("marketplace.revision must be a vN.N.N tag or a full lowercase commit")
    names = lock["plugins"]
    if not isinstance(names, list) or any(not isinstance(name, str) or not PLUGIN_NAME.fullmatch(name) for name in names):
        raise lock_io.LockError("plugins must be a list of plugin names")
    if len(set(names)) != len(names):
        raise lock_io.LockError("plugins must not repeat a plugin")
    missing = [name for name in CORE_PLUGINS if name not in names]
    if missing:
        raise lock_io.LockError("Repository lock omits core plugins: " + ", ".join(f"{MARKETPLACE_NAME}/{name}" for name in missing))
    return marketplace, sorted(names)
