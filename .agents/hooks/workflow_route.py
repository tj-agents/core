"""Deterministically load the owning workflow for an authorized execution prompt."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time


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
RECEIPTS = "agents-workflow-route"
RECEIPT_RETENTION_SECONDS = 7 * 24 * 60 * 60
TRANSCRIPT_TAIL_BYTES = 1 << 20
HOST_GENERATED_PROMPTS = (
    "<command-name>", "<command-message>", "<local-command", "<task-notification>",
)
RECOVERED = (
    "workflow-route: the UserPromptSubmit hook did not deliver this prompt's route (it timed out "
    "or failed), so the route is delivered with this tool call instead.\n\n"
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


def route(prompt: str, cwd: Path) -> str | None:
    if PLANNING_REQUEST.search(prompt):
        return load_context(
            Path(__file__), "engineering/workflow/plan-authoring/SKILL.md", "plan-authoring"
        )
    if selects_handoff(prompt, cwd):
        return load_context(Path(__file__), "engineering/workflow/handoff/SKILL.md", "handoff")
    if selects_plan_execution(prompt, cwd):
        return load_context(
            Path(__file__), "engineering/workflow/plan-execution/SKILL.md", "plan-execution"
        )
    return None


def receipt_path(session: str) -> Path:
    digest = hashlib.sha256(session.encode("utf-8")).hexdigest()
    return Path(tempfile.gettempdir()) / RECEIPTS / f"{digest}.json"


def record_receipt(session: str, prompt_id=None) -> None:
    path = receipt_path(session)
    now = time.time()
    receipt = {"routed_at": now}
    if isinstance(prompt_id, str) and prompt_id:
        receipt["prompt_id"] = prompt_id
    try:
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(receipt), encoding="utf-8")
        entries = list(path.parent.iterdir())
    except OSError:
        return
    for stale in entries:
        try:
            if stale != path and stale.stat().st_mtime < now - RECEIPT_RETENTION_SECONDS:
                stale.unlink()
        except OSError:
            continue


def claim_recovery(session: str, submitted: float) -> bool:
    receipt = receipt_path(session)
    claim = receipt.parent / f"{receipt.stem}.{int(submitted * 1000)}.claim"
    try:
        claim.parent.mkdir(exist_ok=True)
        os.close(os.open(claim, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError:
        return False
    except OSError:
        return True
    return True


def read_receipt(session: str) -> dict:
    try:
        value = json.loads(receipt_path(session).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def prompt_text(content) -> str | None:
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        if any(isinstance(block, dict) and block.get("type") == "tool_result" for block in content):
            return None
        text = "\n".join(
            block["text"] for block in content
            if isinstance(block, dict) and block.get("type") == "text"
            and isinstance(block.get("text"), str)
        )
    else:
        return None
    if not text.strip() or text.lstrip().startswith(HOST_GENERATED_PROMPTS):
        return None
    return text


def last_prompt(transcript: Path) -> tuple[str, float] | None:
    try:
        with transcript.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            handle.seek(max(0, handle.tell() - TRANSCRIPT_TAIL_BYTES))
            tail = handle.read()
    except OSError:
        return None
    for line in reversed(tail.splitlines()):
        if b'"user"' not in line:
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if not isinstance(entry, dict) or entry.get("type") != "user":
            continue
        if entry.get("isMeta") or entry.get("isCompactSummary") or entry.get("isSidechain"):
            continue
        origin = entry.get("origin")
        if isinstance(origin, dict) and origin.get("kind") not in (None, "human"):
            continue
        message = entry.get("message")
        text = prompt_text(message.get("content")) if isinstance(message, dict) else None
        stamp = entry.get("timestamp")
        if text is None or not isinstance(stamp, str):
            continue
        try:
            submitted = datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()
        except ValueError:
            continue
        return text, submitted
    return None


def recover(data: dict) -> str | None:
    if any(key in data for key in ("agent_id", "agentId", "agent_type", "turn_id", "turnId")):
        return None
    session = data.get("session_id")
    transcript = data.get("transcript_path")
    cwd = data.get("cwd")
    if not all(isinstance(value, str) and value for value in (session, transcript, cwd)):
        return None
    prompt_id = data.get("prompt_id") if isinstance(data.get("prompt_id"), str) else None
    receipt = read_receipt(session)
    if prompt_id and receipt.get("prompt_id") == prompt_id:
        return None
    found = last_prompt(Path(transcript))
    if found is None:
        return None
    prompt, submitted = found
    routed_at = receipt.get("routed_at")
    if isinstance(routed_at, (int, float)) and routed_at >= submitted:
        if prompt_id:
            record_receipt(session, prompt_id)
        return None
    if not claim_recovery(session, submitted):
        return None
    try:
        context = route(prompt, Path(cwd).resolve())
    except (OSError, RuntimeError, ValueError) as error:
        context = f"workflow-route: cannot recover this prompt's route: {error}"
    record_receipt(session, prompt_id)
    return RECOVERED + context if context else None


def emit(event: str, context: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {"hookEventName": event, "additionalContext": context}
    }, ensure_ascii=True))
    sys.stdout.flush()


def main() -> int:
    if sys.version_info < (3, 9):
        print("workflow-route: Python 3.9 or newer is required.", file=sys.stderr)
        return 1
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError, UnicodeError) as error:
        print(f"workflow-route: {error}", file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        return 0
    event = data.get("hook_event_name") or data.get("hookEventName")
    if event == "PreToolUse":
        context = recover(data)
        if context:
            emit("PreToolUse", context)
        return 0
    if event != "UserPromptSubmit":
        return 0
    try:
        prompt = data.get("prompt")
        cwd_value = data.get("cwd")
        if not isinstance(prompt, str) or not isinstance(cwd_value, str):
            raise RuntimeError("UserPromptSubmit payload requires string prompt and cwd fields")
        context = route(prompt, Path(cwd_value).resolve())
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"workflow-route: {error}", file=sys.stderr)
        return 2
    if context:
        emit("UserPromptSubmit", context)
    session = data.get("session_id")
    if isinstance(session, str) and session:
        record_receipt(session, data.get("prompt_id"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
