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
PLANNING_REQUEST = re.compile(
    r"\b(?:only\s+plan|plan(?:ning)?\s+only|(?:continue|resume)\s+planning)\b",
    re.IGNORECASE,
)
OWNER_REFERENCE = re.compile(r"\b(?:goal|plan|roadmap)\b", re.IGNORECASE)
LONG_RUNNING = re.compile(
    r"\b(?:all\s+(?:remaining\s+)?phases|end[- ]to[- ]end|entire\s+(?:migration|project)|"
    r"long[- ]term|multi[- ]phase|multiple\s+phases|through\s+completion)\b|"
    r"\bP\d+\s*(?:-|\u2013)\s*P\d+\b",
    re.IGNORECASE,
)
SIDE_WORKSTREAM = re.compile(
    r"\b(?:side\s+(?:task|thing|work(?:stream)?)|separate\s+(?:task|workstream)|"
    r"distinct(?:ly)?\s+(?:actionable\s+)?(?:task|workstream))\b",
    re.IGNORECASE,
)
ACTIVE_WORK = re.compile(
    r"\b(?:active|current|original|main|primary)\s+(?:goal|task|work(?:stream)?)\b",
    re.IGNORECASE,
)
HANDOFF_ACTION = re.compile(
    r"\b(?:hand\s*off|delegate|dispatch|launch|invoke|do\s+(?:a\s+)?handoff)\b[^.!?\n]{0,80}"
    r"\b(?:side\s+(?:task|thing|work(?:stream)?)|separate\s+(?:task|workstream)|"
    r"distinct(?:ly)?\s+(?:actionable\s+)?(?:task|workstream))\b|"
    r"\b(?:side\s+(?:task|thing|work(?:stream)?)|separate\s+(?:task|workstream)|"
    r"distinct(?:ly)?\s+(?:actionable\s+)?(?:task|workstream))\b[^.!?\n]{0,80}"
    r"\b(?:hand\s*off|delegate|dispatch|launch|invoke|do\s+(?:a\s+)?handoff)\b",
    re.IGNORECASE,
)
DIRECT_HANDOFF = re.compile(
    r"(?:^|[.!?;\n]\s*)(?:please\s+|can\s+you\s+|could\s+you\s+|would\s+you\s+|"
    r"go\s+ahead\s+and\s+)?(?:hand\s+(?:off\b|(?:this|it|that)\s+off\b)|"
    r"do\s+(?:a\s+)?handoff\b|handoff\b)",
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


def selects_handoff(prompt: str, cwd: Path) -> bool:
    if not prompt.strip() or PLANNING_ONLY.search(prompt):
        return False
    if DIRECT_HANDOFF.search(prompt):
        return True
    return (
        SIDE_WORKSTREAM.search(prompt) is not None
        and HANDOFF_ACTION.search(prompt) is not None
        and (active_goal(cwd) or ACTIVE_WORK.search(prompt) is not None)
    )


def contract_path(script: Path, relative_path: str, name: str) -> Path:
    payload_root = script.resolve().parent.parent
    candidates = (
        payload_root / ".agents" / relative_path,
        payload_root / relative_path,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError(
        f"cannot read {name} contract; expected one of: "
        + ", ".join(str(path) for path in candidates)
    )


def load_context(script: Path, relative_path: str, name: str) -> str:
    contract = contract_path(script, relative_path, name)
    try:
        text = contract.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        raise RuntimeError(f"cannot read {name} contract at {contract}: {error}") from error
    if not text.startswith("---\n") or "\n---\n" not in text or not text.strip():
        raise RuntimeError(f"cannot read {name} contract at {contract}: invalid SKILL.md")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return (
        f"engineering:{name} automatically selected "
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
        if PLANNING_REQUEST.search(prompt):
            context = load_context(
                Path(__file__), "engineering/workflow/plan-authoring/SKILL.md", "plan-authoring"
            )
        elif selects_handoff(prompt, cwd):
            context = load_context(
                Path(__file__), "engineering/workflow/handoff/SKILL.md", "handoff"
            )
        elif selects_plan_execution(prompt, cwd):
            context = load_context(
                Path(__file__), "engineering/workflow/plan-execution/SKILL.md", "plan-execution"
            )
        else:
            return 0
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
