#!/usr/bin/env python3
"""Read and validate a repository's plugin lock (`.agents/plugins.lock.json`)."""

from __future__ import annotations

from pathlib import Path
import re

import lock_io


LOCK_NAME = "plugins.lock.json"
SCHEMA_VERSION = 3
MARKETPLACE_NAME = "tj-agents"
MARKETPLACE_REPOSITORY = "tj-agents/marketplace"
ALLOWED_OWNERS = ("tj-agents", "Concertable")
CORE_PLUGINS = ("base", "engineering", "machine")
NAME = re.compile(r"[a-z][a-z0-9-]*\Z")
REPOSITORY = re.compile(r"(?P<owner>[A-Za-z0-9-]+)/(?P<name>[A-Za-z0-9_][A-Za-z0-9_.-]*)\Z")
GIT_SUFFIX = ".git"
REVISION = re.compile(r"v(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\Z|[0-9a-f]{40}\Z")


def resolve(root: Path) -> Path:
    return root / ".agents" / LOCK_NAME


def is_current(lock: dict) -> bool:
    return isinstance(lock, dict) and lock.get("schema_version") == SCHEMA_VERSION


def plugin_id(name: str, marketplace: str = MARKETPLACE_NAME) -> str:
    return f"{name}@{marketplace}"


def split(identity: str) -> tuple[str, str]:
    name, _, marketplace = identity.partition("@")
    return name, marketplace


def valid_identity(identity: object) -> bool:
    if not isinstance(identity, str) or identity.count("@") != 1:
        return False
    name, marketplace = split(identity)
    return bool(NAME.fullmatch(name) and NAME.fullmatch(marketplace))


def overlay_id(identity: str) -> str:
    """The `<marketplace>/<plugin>` form used by harness requirement overlays."""
    name, marketplace = split(identity)
    return f"{marketplace}/{name}"


def validate_marketplace(name: str, value: object) -> dict:
    if not isinstance(name, str) or not NAME.fullmatch(name):
        raise lock_io.LockError(f"Invalid marketplace name: {name!r}")
    if not isinstance(value, dict) or set(value) != {"repository", "revision"}:
        raise lock_io.LockError(f"marketplaces.{name} must contain exactly repository and revision")
    repository, revision = value["repository"], value["revision"]
    match = REPOSITORY.fullmatch(repository) if isinstance(repository, str) else None
    if match is None or match["owner"] not in ALLOWED_OWNERS or match["name"].lower().endswith(GIT_SUFFIX):
        raise lock_io.LockError(
            f"marketplaces.{name}.repository must be <owner>/<repository> without .git, owned by " + " or ".join(ALLOWED_OWNERS)
        )
    if (name == MARKETPLACE_NAME) != (repository == MARKETPLACE_REPOSITORY):
        raise lock_io.LockError(f"The {MARKETPLACE_NAME} marketplace must be {MARKETPLACE_REPOSITORY} and nothing else may use that name")
    if not isinstance(revision, str) or not REVISION.fullmatch(revision):
        raise lock_io.LockError(f"marketplaces.{name}.revision must be a vN.N.N tag or a full lowercase commit")
    return value


def validate(lock: dict) -> tuple[dict, list[str]]:
    """Return the marketplace pins and the sorted `<plugin>@<marketplace>` selections, or raise."""
    if not is_current(lock) or set(lock) != {"schema_version", "marketplaces", "plugins"}:
        raise lock_io.LockError(f"{LOCK_NAME} must contain exactly schema_version {SCHEMA_VERSION}, marketplaces and plugins")
    marketplaces = lock["marketplaces"]
    if not isinstance(marketplaces, dict) or MARKETPLACE_NAME not in marketplaces:
        raise lock_io.LockError(f"marketplaces must be an object that includes {MARKETPLACE_NAME}")
    for name, value in marketplaces.items():
        validate_marketplace(name, value)
    repositories = [value["repository"].lower() for value in marketplaces.values()]
    if len(set(repositories)) != len(repositories):
        raise lock_io.LockError("Two marketplaces pin the same repository")
    identities = lock["plugins"]
    if not isinstance(identities, list) or any(not isinstance(identity, str) for identity in identities):
        raise lock_io.LockError("plugins must be a list of <plugin>@<marketplace> names")
    for identity in identities:
        if not valid_identity(identity) or split(identity)[1] not in marketplaces:
            raise lock_io.LockError(f"Invalid plugin {identity!r}: use <plugin>@<marketplace> with a declared marketplace")
    if len(set(identities)) != len(identities):
        raise lock_io.LockError("plugins must not repeat a plugin")
    unused = sorted(set(marketplaces) - {split(identity)[1] for identity in identities})
    if unused:
        raise lock_io.LockError("Declared marketplaces select no plugin: " + ", ".join(unused))
    missing = [plugin_id(name) for name in CORE_PLUGINS if plugin_id(name) not in identities]
    if missing:
        raise lock_io.LockError("Repository lock omits core plugins: " + ", ".join(missing))
    return dict(sorted(marketplaces.items())), sorted(identities)
