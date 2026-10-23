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
ALLOWED_OWNERS = ("tj-agents", "Concertable")
CORE_REPOSITORY = "tj-agents/core"
CORE_PLUGINS = ("agent-store", "base", "engineering", "machine")
NAME = re.compile(r"[a-z][a-z0-9-]*\Z")
REPOSITORY = re.compile(r"(?P<owner>[A-Za-z0-9-]+)/(?P<name>[A-Za-z0-9_][A-Za-z0-9_.-]*)\Z")
GIT_SUFFIX = ".git"


def resolve(root: Path) -> Path:
    return root / ".agents" / SELECTION_NAME


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
    name, marketplace = split(identity)
    return f"{marketplace}/{name}"


def validate_marketplace(name: str, value: object) -> dict:
    if not isinstance(name, str) or not NAME.fullmatch(name):
        raise lock_io.LockError(f"Invalid marketplace name: {name!r}")
    if not isinstance(value, dict) or set(value) != {"repository"}:
        raise lock_io.LockError(f"marketplaces.{name} must contain exactly repository")
    repository = value["repository"]
    match = REPOSITORY.fullmatch(repository) if isinstance(repository, str) else None
    if match is None or match["owner"] not in ALLOWED_OWNERS or match["name"].lower().endswith(GIT_SUFFIX):
        raise lock_io.LockError(
            f"marketplaces.{name}.repository must be <owner>/<repository> without .git, owned by " + " or ".join(ALLOWED_OWNERS)
        )
    if (name == MARKETPLACE_NAME) != (repository == MARKETPLACE_REPOSITORY):
        raise lock_io.LockError(f"The {MARKETPLACE_NAME} marketplace must be {MARKETPLACE_REPOSITORY} and nothing else may use that name")
    if repository == CORE_REPOSITORY:
        raise lock_io.LockError(f"{CORE_REPOSITORY} is published through the {MARKETPLACE_NAME} marketplace; select {MARKETPLACE_REPOSITORY}")
    return value


def validate(lock: dict) -> tuple[dict, list[str]]:
    """Return the marketplaces and the sorted `<plugin>@<marketplace>` selections, or raise."""
    if not is_current(lock) or set(lock) != {"schema_version", "marketplaces", "plugins"}:
        raise lock_io.LockError(f"{SELECTION_NAME} must contain exactly schema_version {SCHEMA_VERSION}, marketplaces and plugins")
    marketplaces = lock["marketplaces"]
    if not isinstance(marketplaces, dict) or not marketplaces:
        raise lock_io.LockError("marketplaces must be a nonempty object")
    for name, value in marketplaces.items():
        validate_marketplace(name, value)
    seen: dict[str, str] = {}
    for name, value in marketplaces.items():
        other = seen.setdefault(value["repository"].lower(), name)
        if other != name:
            raise lock_io.LockError(f"Marketplaces {other} and {name} select the same repository {value['repository']}")
    identities = lock["plugins"]
    if not isinstance(identities, list) or not identities or any(not isinstance(identity, str) for identity in identities):
        raise lock_io.LockError("plugins must be a list of <plugin>@<marketplace> names")
    for identity in identities:
        if not valid_identity(identity) or split(identity)[1] not in marketplaces:
            raise lock_io.LockError(f"Invalid plugin {identity!r}: use <plugin>@<marketplace> with a declared marketplace")
    if len(set(identities)) != len(identities):
        raise lock_io.LockError("plugins must not repeat a plugin")
    unused = sorted(set(marketplaces) - {split(identity)[1] for identity in identities})
    if unused:
        raise lock_io.LockError("Declared marketplaces select no plugin: " + ", ".join(unused))
    return dict(sorted(marketplaces.items())), sorted(identities)


def without_retired_core_marketplace(sources: dict, identities: list) -> tuple[dict, list]:
    retired = {name for name, value in sources.items() if value["repository"] == CORE_REPOSITORY}
    if not retired or not isinstance(identities, list):
        return sources, identities
    migrated = []
    for identity in identities:
        name, marketplace = split(identity) if isinstance(identity, str) else ("", "")
        if marketplace in retired:
            if name not in CORE_PLUGINS:
                raise lock_io.LockError(f"Legacy plugin {identity} has no {MARKETPLACE_NAME} replacement")
            identity = plugin_id(name)
        if identity not in migrated:
            migrated.append(identity)
    sources = {name: value for name, value in sources.items() if name not in retired}
    sources.setdefault(MARKETPLACE_NAME, {"repository": MARKETPLACE_REPOSITORY})
    return sources, migrated


def migrate(lock: dict) -> dict:
    if not isinstance(lock, dict) or lock.get("schema_version") not in {2, 3}:
        raise lock_io.LockError("Migration accepts only schema_version 2 or 3 plugin locks")
    if lock["schema_version"] == 2:
        if set(lock) != {"schema_version", "marketplace", "plugins"}:
            raise lock_io.LockError("Legacy lock has invalid fields")
        marketplaces = {MARKETPLACE_NAME: lock["marketplace"]}
        names = lock["plugins"]
        if not isinstance(names, list) or any(not isinstance(name, str) or not NAME.fullmatch(name) for name in names):
            raise lock_io.LockError("Legacy lock plugins must be plugin names")
        identities = [plugin_id(name) for name in names]
    else:
        if set(lock) != {"schema_version", "marketplaces", "plugins"}:
            raise lock_io.LockError("Legacy lock has invalid fields")
        marketplaces, identities = lock["marketplaces"], lock["plugins"]
    if not isinstance(marketplaces, dict):
        raise lock_io.LockError("Legacy lock marketplaces must be an object")
    sources = {}
    for name, value in marketplaces.items():
        if not isinstance(value, dict) or set(value) != {"repository", "revision"} or not isinstance(value["revision"], str) or not value["revision"]:
            raise lock_io.LockError(f"Legacy marketplace {name} has invalid fields")
        sources[name] = {"repository": value["repository"]}
    sources, identities = without_retired_core_marketplace(sources, identities)
    document = {"schema_version": SCHEMA_VERSION, "marketplaces": sources, "plugins": identities}
    validate(document)
    return document
