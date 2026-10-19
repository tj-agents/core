#!/usr/bin/env python3
"""The per-host record of tj-agents revisions a launch verified as published main and installed."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import time
from typing import Iterable

SHA = re.compile(r"^[0-9a-f]{40}$")
GENERATIONS_FILE = "generations.json"
GENERATION_HISTORY = 64


def generations_path(plugins: Path, host: str) -> Path:
    return plugins / "cache" / ".tj-agents-rolling" / host / GENERATIONS_FILE


def read_generations(path: Path) -> list[dict[str, object]]:
    try:
        document = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return []
    entries = document.get("verified") if isinstance(document, dict) else None
    return [entry for entry in entries or () if isinstance(entry, dict)
            and isinstance(entry.get("repository"), str) and isinstance(entry.get("revision"), str)
            and SHA.fullmatch(entry["revision"]) and isinstance(entry.get("verified_at"), (int, float))]


def record_generations(path: Path, revisions: Iterable[tuple[str, str]], now: float | None = None) -> None:
    current = {(repository, revision) for repository, revision in revisions if SHA.fullmatch(revision)}
    entries = [entry for entry in read_generations(path) if (entry["repository"], entry["revision"]) not in current]
    moment = time.time() if now is None else now
    entries.extend({"repository": repository, "revision": revision, "verified_at": moment}
                   for repository, revision in sorted(current))
    kept = []
    for repository in sorted({entry["repository"] for entry in entries}):
        members = sorted((entry for entry in entries if entry["repository"] == repository),
                         key=lambda entry: entry["verified_at"])
        kept.extend(members[-GENERATION_HISTORY:])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps({"schema_version": 1, "verified": kept}, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)
