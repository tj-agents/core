#!/usr/bin/env python3
"""The per-host record of tj-agents revisions a launch verified as published main and installed."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Iterable

SHA = re.compile(r"^[0-9a-f]{40}$")
GENERATIONS_FILE = "generations.json"
GENERATION_HISTORY = 64


def generations_path(plugins: Path, host: str) -> Path:
    return plugins / "cache" / ".tj-agents-rolling" / host / GENERATIONS_FILE


def read_generations(path: Path) -> list[dict[str, object]] | None:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return []
    except OSError:
        return None
    try:
        document = json.loads(text)
    except ValueError:
        return []
    entries = document.get("verified") if isinstance(document, dict) else None
    return [entry for entry in entries or () if isinstance(entry, dict)
            and isinstance(entry.get("repository"), str) and isinstance(entry.get("revision"), str)
            and SHA.fullmatch(entry["revision"]) and isinstance(entry.get("verified_at"), (int, float))] \
        if isinstance(entries, list) else []


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
    return {"schema_version": 1, "verified": bounded}
