from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import tempfile


RECEIPTS = "agents-workflow-route"
DIRECT_CONTROL = re.compile(r"^\s*(?:please\s+)?(?P<action>pause|cancel|stop|resume|continue)"
                            r"(?:\s+(?:(?:this|it)(?:\s+(?:work|task|goal|plan|execution))?|"
                            r"(?:the|our|my)?\s*(?:work|task|goal|plan|execution)))?\s*[.!?]*\s*$", re.I)


def direct_control(prompt: str) -> str | None:
    match = DIRECT_CONTROL.fullmatch(prompt)
    return match["action"].lower() if match else None


def receipt_path(session: str) -> Path:
    digest = hashlib.sha256(session.encode("utf-8")).hexdigest()
    return Path(tempfile.gettempdir()) / RECEIPTS / f"{digest}.json"


def read_receipt(session: str) -> dict:
    try:
        value = json.loads(receipt_path(session).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}
