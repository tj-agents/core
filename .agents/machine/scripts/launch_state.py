"""Tell the terminal bootstrap whether its launcher reached the native CLI."""

from __future__ import annotations

import os
from pathlib import Path


ENVIRONMENT = "BASE_AGENTS_LAUNCH_STATE"


def _record(state: str) -> None:
    path = os.environ.get(ENVIRONMENT)
    if not path:
        return
    try:
        Path(path).write_text(state, encoding="utf-8")
    except OSError:
        pass


def ready() -> None:
    _record("ready")


def started() -> None:
    _record("started")
    os.environ.pop(ENVIRONMENT, None)
