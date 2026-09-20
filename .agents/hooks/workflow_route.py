"""Deterministically load the owning workflow for an authorized execution prompt."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys


EXECUTION = re.compile(
    r"\b(?:carry\s+on|complete|continue|deliver|execute|finish|implement|proceed|resume|"
    r"work\s+through)\b",
    re.IGNORECASE,
)

PLANNING_ONLY = re.compile(
    r"\b(?:do\s+not|don't)\s+(?:execute|implement|make\s+changes)|"
    r"\b(?:only\s+plan|plan(?:ning)?\s+only|without\s+(?:executing|implementing))\b|"
    r"\b(?:continue|resume)\s+planning\b",
    re.IGNORECASE,
)
OWNER_REFERENCE = re.compile(r"\b(?:goal|plan|roadmap)\b", re.IGNORECASE)
LONG_RUNNING = re.compile(
    r"\b(?:all\s+(?:remaining\s+)?phases|end[- ]to[- ]end|entire\s+(?:migration|project)|"
    r"long[- ]term|multi[- ]phase|multiple\s+phases|through\s+completion)\b|"
    r"\bP\d+\s*(?:-|\u2013)\s*P\d+\b",
    re.IGNORECASE,
)
COMPLETE_STATUS = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?status\s*:?\s*(?:complete|completed|done|closed)\b"
)


def active_goal(cwd: Path) -> bool:
    goal = cwd / "GOAL.md"
    try:
        body = goal.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return False
    except (OSError, UnicodeError) as error:
        raise RuntimeError(f"cannot read active goal at {goal}: {error}") from error
    return not COMPLETE_STATUS.search(body)


def selects_plan_execution(prompt: str, cwd: Path) -> bool:
    """Return whether this prompt authorizes continued plan execution."""
    if not prompt.strip() or PLANNING_ONLY.search(prompt):
        return False
    if re.search(r"\bplan-execution\b", prompt, re.IGNORECASE):
        return True

    executing = EXECUTION.search(prompt) is not None
    if active_goal(cwd):
        return executing
    return executing and (
        LONG_RUNNING.search(prompt) is not None
        or OWNER_REFERENCE.search(prompt) is not None
    )


def contract_path(script: Path) -> Path:
    payload_root = script.resolve().parent.parent
    candidates = (
        payload_root / ".agents/engineering/workflow/plan-execution/SKILL.md",
        payload_root / "engineering/workflow/plan-execution/SKILL.md",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError(
        "cannot read plan-execution contract; expected one of: "
        + ", ".join(str(path) for path in candidates)
    )


def load_context(script: Path) -> str:
    contract = contract_path(script)
    try:
        text = contract.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        raise RuntimeError(f"cannot read plan-execution contract at {contract}: {error}") from error
    if not text.startswith("---\n") or "\n---\n" not in text or not text.strip():
        raise RuntimeError(f"cannot read plan-execution contract at {contract}: invalid SKILL.md")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return (
        f"engineering:plan-execution automatically selected "
        f"(source SHA-256 {digest})\nSource: {contract}\n\n{text.strip()}"
    )


def main() -> int:
    if sys.version_info < (3, 9):
        print("workflow-route: Python 3.9 or newer is required.", file=sys.stderr)
        return 1
    try:
        data = json.load(sys.stdin)
        event = data.get("hook_event_name") or data.get("hookEventName")
        if event != "UserPromptSubmit":
            return 0
        prompt = data.get("prompt")
        cwd_value = data.get("cwd")
        if not isinstance(prompt, str) or not isinstance(cwd_value, str):
            raise RuntimeError("UserPromptSubmit payload requires string prompt and cwd fields")
        cwd = Path(cwd_value).resolve()
        if not selects_plan_execution(prompt, cwd):
            return 0
        context = load_context(Path(__file__))
    except (json.JSONDecodeError, OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"workflow-route: {error}", file=sys.stderr)
        return 2

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
