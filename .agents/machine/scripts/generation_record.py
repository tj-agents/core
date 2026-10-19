#!/usr/bin/env python3
"""The per-host record of tj-agents revisions a launch verified as published main and installed."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Iterable

SHA = re.compile(r"^[0-9a-f]{40}$")
SCHEMA_VERSION = 1
GENERATIONS_FILE = "generations.json"
GENERATION_HISTORY = 64


def generations_path(plugins: Path, host: str) -> Path:
    return plugins / "cache" / ".tj-agents-rolling" / host / GENERATIONS_FILE


def read_record(path: Path) -> tuple[str, list[dict[str, object]]]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return "readable", []
    except OSError:
        return "busy", []
    try:
        document = json.loads(raw.decode("utf-8-sig"))
    except ValueError:
        return "readable", []
    if not isinstance(document, dict):
        return "readable", []
    version = document.get("schema_version")
    if type(version) is int and version > SCHEMA_VERSION:
        return "newer", []
    entries = document.get("verified")
    if not isinstance(entries, list):
        return "readable", []
    return "readable", [entry for entry in entries if isinstance(entry, dict)
            and isinstance(entry.get("repository"), str) and isinstance(entry.get("revision"), str)
            and SHA.fullmatch(entry["revision"]) and isinstance(entry.get("verified_at"), (int, float))]


def read_generations(path: Path) -> list[dict[str, object]] | None:
    state, entries = read_record(path)
    return entries if state == "readable" else None


def merged_generations(entries: Iterable[dict[str, object]], revisions: Iterable[tuple[str, str]],
                       moment: float) -> dict[str, object]:
    current = {(repository, revision) for repository, revision in revisions if SHA.fullmatch(revision)}
    kept = [entry for entry in entries if (entry["repository"], entry["revision"]) not in current]
    kept.extend({"repository": repository, "revision": revision, "verified_at": moment}
                for repository, revision in sorted(current))
    bounded = []
    for repository in sorted({entry["repository"] for entry in kept}):
        members = sorted((entry for entry in kept if entry["repository"] == repository),
                         key=lambda entry: entry["verified_at"])
        bounded.extend(members[-GENERATION_HISTORY:])
    return {"schema_version": SCHEMA_VERSION, "verified": bounded}
