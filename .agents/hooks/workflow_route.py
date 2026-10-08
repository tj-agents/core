"""Deterministically load the owning workflow for an authorized execution prompt."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import sys
import tempfile
import time


EXECUTION = re.compile(
    r"\b(?:carry\s+on|complete|continue|deliver|execute|finish|implement|proceed|resume|"
    r"work\s+through)\b",
    re.IGNORECASE,
)
IMPLEMENTATION = re.compile(
    r"\b(?:build|create|implement|add|write|refactor|migrate|repair|fix|change|update)\b",
    re.IGNORECASE,
)
QUESTION = re.compile(
    r"^\s*(?:why|what|when|where|who|how|should|could|would)\b|\?\s*$",
    re.IGNORECASE,
)
EXPLICIT_CLAUDE = re.compile(
    r"\b(?:use|keep|stay|run|do)\s+(?:this\s+)?(?:on\s+)?claude\b|"
    r"\bi\s+want\s+claude\s+to\s+(?:do|handle|implement|build|run)\b|"
    r"\bclaude\s+(?:should|must|can)\s+(?:do|handle|implement|build|run)\b",
    re.IGNORECASE,
)
TINY_INLINE = re.compile(
    r"\b(?:just|only|single|one)\b[^.!?\n]{0,80}\b(?:change|adjust|update|fix)\b"
    r"[^.!?\n]{0,120}\b(?P<path>[A-Za-z0-9][A-Za-z0-9._/-]*\.[A-Za-z0-9_-]+)\b",
    re.IGNORECASE,
)
TINY_EXCLUSIONS = re.compile(
    r"\b(?:new|create|build|test|tests|phase|phases|multiple|several|and then|then)\b",
    re.IGNORECASE,
)
READ_TOOLS = {"Read", "Glob", "Grep"}
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
DISPATCH_TOOLS = {"Task", "Workflow"}
SHELL_TOOLS = {"Bash", "PowerShell", "shell", "exec_command", "unified_exec", "local_shell"}
READ_ONLY_SHELL_COMMAND = re.compile(
    r"(?:pwd|dir|get-location)|(?:ls|get-childitem)(?:\s+[-A-Za-z0-9_./\\]+)?|"
    r"(?:cat|type|get-content)\s+[-A-Za-z0-9_./\\]+",
    re.IGNORECASE,
)
CODEX_LAUNCHER_PATH = re.compile(
    r"(?:^|[/\\])handoff-codex[/\\]scripts[/\\]launch-codex\.ps1$",
    re.IGNORECASE,
)
POWERSHELL_EXECUTABLES = {"powershell", "powershell.exe", "pwsh", "pwsh.exe"}

PLANNING_DIRECTIVE = re.compile(
    r"(?:^|[.!?;:,\n]|\b(?:and|but|then)\b)\s*"
    r"(?:(?:please|can\s+you|could\s+you|would\s+you)\s+)*"
    r"(?P<directive>(?:(?P<negated>"
    r"(?:(?:i\s+want\s+(?:you\s+)?to\s+)?(?:do\s+not|don't|never|not)|"
    r"i\s+(?:do\s+not|don't|never)\s+want\s+(?:you\s+)?to|"
    r"i\s+want\s+(?:you\s+)?not\s+to)\s+)|"
    r"i\s+want\s+(?:you\s+)?to\s+)?"
    r"(?:(?P<limited>only\s+plan|plan(?:ning)?\s+only|"
    r"(?:continue|resume)\s+(?:planning|with\s+planning\s+only))\b(?!-)|"
    r"(?P<author>plan\b(?!-)|(?:draft|write|create|revise|update|design)\s+"
    r"(?:(?:a|an|the|this|that|our|my)\s+)?"
    r"(?:(?:new|existing|current|phased)\s+)?plan\b(?!-))"
    r"(?P<author_only>\s+only\b)?))",
    re.IGNORECASE,
)
EXECUTION_RESTRICTION = re.compile(
    r"\b(?:do\s+not|don't)\s+(?:execute|implement|make\s+changes)\b|"
    r"\bwithout\s+(?:executing|implementing)\b",
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
    r"do\s+(?:a\s+)?handoff\b|handoff\b)|"
    r"\b(?:delegate|dispatch)\s+(?:an?\s+)?(?:(?:architectural|design)\s+)?"
    r"(?:design|review)\b",
    re.IGNORECASE,
)
COMPLETE_STATUS = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?status\s*:?\s*(?:complete|completed|done|closed)\b"
)
GOAL_REFERENCE = re.compile(
    r"(?<![A-Za-z0-9_.-])(?P<path>(?:[A-Za-z0-9_.-]+[\\/])*GOAL\.md)\b",
    re.IGNORECASE,
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
    if not prompt.strip():
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
    if not prompt.strip():
        return False
    if QUESTION.search(prompt) or re.search(
        r"\b(?:do\s+not|don't|never)\s+(?:hand\s*off|delegate|dispatch)\b", prompt, re.IGNORECASE
    ):
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


def planning_intent(prompt: str) -> tuple[str | None, str]:
    evidence = prompt.replace("\u2019", "'")
    matches = list(PLANNING_DIRECTIVE.finditer(evidence))
    for match in reversed(matches):
        if match["negated"]:
            start, end = match.span("directive")
            evidence = evidence[:start] + " " + evidence[end:]
    restricted = EXECUTION_RESTRICTION.search(evidence) is not None
    authoring = any(
        not match["negated"] and (
            match["limited"] or match["author_only"] or (match["author"] and restricted)
        )
        for match in matches
    )
    return ("authoring" if authoring else "blocked" if restricted else None), evidence


def prompt_digest(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def unquoted(prompt: str) -> str:
    return re.sub(r"(['\"]).*?\1", "", prompt, flags=re.DOTALL)


def canonical_goal(prompt: str, cwd: Path, previous: dict | None = None) -> Path | None:
    root = cwd.resolve()
    previous = previous or {}
    recorded = previous.get("goal_path")
    if isinstance(recorded, str):
        try:
            path = Path(recorded).resolve()
            path.relative_to(root)
        except (OSError, ValueError):
            pass
        else:
            if path.name == "GOAL.md" and (
                path.is_file() or (not (root / ".git").exists() and path == root / "GOAL.md")
            ):
                return path
    references = [match["path"] for match in GOAL_REFERENCE.finditer(unquoted(prompt))]
    if references:
        try:
            path = (root / references[-1]).resolve()
            path.relative_to(root)
        except (OSError, ValueError):
            return None
        if path.name == "GOAL.md" and path.is_file():
            return path
        return None
    standalone = root / "GOAL.md"
    if not (root / ".git").exists():
        return standalone
    if standalone.is_file():
        return standalone
    return None


def explicit_claude(prompt: str) -> bool:
    return EXPLICIT_CLAUDE.search(prompt) is not None


def substantive(prompt: str) -> bool:
    return len(re.findall(r"\w+", prompt)) >= 8


def tiny_inline(prompt: str, cwd: Path, previous: dict) -> bool:
    if previous.get("mode") == "codex" or not previous.get("substantive"):
        return False
    if TINY_EXCLUSIONS.search(prompt):
        return False
    matches = list(TINY_INLINE.finditer(prompt))
    if len(matches) != 1:
        return False
    path = Path(matches[0]["path"])
    return not path.is_absolute() and ".." not in path.parts and (cwd / path).is_file()


def prompt_mode(prompt: str, cwd: Path, harness: str | None, previous: dict | None = None) -> str:
    if harness != "claude":
        return "conversation"
    intent, evidence = planning_intent(prompt)
    previous = previous or {}
    if intent or QUESTION.search(evidence):
        return "conversation"
    if explicit_claude(unquoted(evidence)):
        return "explicit-claude"
    if previous.get("mode") == "codex":
        return "codex"
    if tiny_inline(evidence, cwd, previous):
        return "tiny-inline"
    return "codex" if (
        IMPLEMENTATION.search(evidence)
        or selects_plan_execution(evidence, cwd)
        or selects_handoff(evidence, cwd)
    ) else "conversation"


def route(prompt: str, cwd: Path, harness: str | None = None,
          mode: str | None = None) -> str | None:
    intent, evidence = planning_intent(prompt)
    if intent == "authoring":
        return load_context(
            Path(__file__), "engineering/workflow/plan-authoring/SKILL.md", "plan-authoring"
        )
    if intent == "blocked":
        return None
    if harness == "claude" and mode == "codex":
        return load_context(Path(__file__), "engineering/workflow/handoff/SKILL.md", "handoff")
    if selects_handoff(evidence, cwd):
        return load_context(Path(__file__), "engineering/workflow/handoff/SKILL.md", "handoff")
    if selects_plan_execution(evidence, cwd):
        return load_context(
            Path(__file__), "engineering/workflow/plan-execution/SKILL.md", "plan-execution"
        )
    return None


def receipt_path(session: str) -> Path:
    digest = hashlib.sha256(session.encode("utf-8")).hexdigest()
    return Path(tempfile.gettempdir()) / RECEIPTS / f"{digest}.json"


def record_receipt(session: str, prompt_id=None, *, prompt: str | None = None,
                   mode: str = "conversation", goal_path: Path | None = None) -> None:
    path = receipt_path(session)
    now = time.time()
    receipt = {"routed_at": now, "mode": mode}
    if isinstance(prompt_id, str) and prompt_id:
        receipt["prompt_id"] = prompt_id
    if isinstance(prompt, str):
        receipt["prompt_digest"] = prompt_digest(prompt)
        receipt["substantive"] = substantive(prompt)
    if goal_path is not None:
        receipt["goal_path"] = str(goal_path)
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


def recovered_receipt(data: dict, harness: str | None) -> tuple[dict, str | None]:
    session = data.get("session_id")
    transcript = data.get("transcript_path")
    cwd = data.get("cwd")
    if not all(isinstance(value, str) and value for value in (session, cwd)):
        return {}, None
    receipt = read_receipt(session)
    if not isinstance(transcript, str) or not transcript:
        return receipt, None
    found = last_prompt(Path(transcript))
    if found is None:
        return receipt, None
    prompt, submitted = found
    prompt_id = data.get("prompt_id") if isinstance(data.get("prompt_id"), str) else None
    current_digest = prompt_digest(prompt)
    routed_at = receipt.get("routed_at")
    current = (
        receipt.get("prompt_digest") == current_digest
        and isinstance(routed_at, (int, float))
        and routed_at >= submitted
        and (not prompt_id or receipt.get("prompt_id") == prompt_id)
    )
    if prompt_id and receipt.get("prompt_id") == prompt_id and "prompt_digest" not in receipt:
        current = True
    if current:
        return receipt, None
    if not claim_recovery(session, submitted):
        return receipt, None
    resolved_cwd = Path(cwd).resolve()
    mode = prompt_mode(prompt, resolved_cwd, harness, receipt)
    goal_path = canonical_goal(prompt, resolved_cwd, receipt) if mode == "codex" else None
    try:
        context = route(prompt, resolved_cwd, harness, mode)
    except (OSError, RuntimeError, ValueError) as error:
        context = f"workflow-route: cannot recover this prompt's route: {error}"
    record_receipt(session, prompt_id, prompt=prompt, mode=mode, goal_path=goal_path)
    return read_receipt(session), RECOVERED + context if context else None


def command(data: dict) -> str:
    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    for key in ("command", "cmd", "script", "input"):
        value = tool_input.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, list) and all(isinstance(token, str) for token in value):
            return " ".join(value)
    return ""


def codex_launcher(command_text: str) -> bool:
    if not isinstance(command_text, str) or any(
        token in command_text for token in ("|", ";", ">", "<", "`", "$", "\n", "\r", "(", ")")
    ):
        return False
    try:
        tokens = shlex.split(command_text, posix=False)
    except ValueError:
        return False
    if len(tokens) >= 2 and tokens[0] == "&":
        return (
            command_text.count("&") == 1
            and CODEX_LAUNCHER_PATH.search(tokens[1].strip("'\"")) is not None
        )
    if "&" in command_text:
        return False
    if not tokens or tokens[0].casefold() not in POWERSHELL_EXECUTABLES:
        return False
    index = 1
    while index < len(tokens):
        option = tokens[index].casefold()
        if option in {"-noprofile", "-nologo", "-noninteractive"}:
            index += 1
            continue
        if option == "-executionpolicy" and index + 1 < len(tokens):
            index += 2
            continue
        if option in {"-file", "-f"} and index + 1 < len(tokens):
            return CODEX_LAUNCHER_PATH.search(tokens[index + 1].strip("'\"")) is not None
        return False
    return False


def handoff_preparation(data: dict, receipt: dict) -> bool:
    tool_input = data.get("tool_input")
    recorded = receipt.get("goal_path")
    if not isinstance(tool_input, dict) or not isinstance(recorded, str):
        return False
    path = tool_input.get("file_path") or tool_input.get("path")
    content = tool_input.get("content")
    if not isinstance(path, str) or not isinstance(content, str):
        return False
    try:
        requested = Path(path).resolve()
        canonical_goal = Path(recorded).resolve()
    except OSError:
        return False
    return requested == canonical_goal and "# Goal" in content and "## Next Steps" in content


def read_only_shell(command_text: str) -> bool:
    if any(token in command_text for token in ("|", ">", "<", "`", "$", "\n", "\r")):
        return False
    commands = re.split(r"\s*(?:&&|;)\s*", command_text.strip())
    return bool(commands) and all(
        READ_ONLY_SHELL_COMMAND.fullmatch(item) is not None for item in commands
    )


def denied_tool(data: dict, receipt: dict, harness: str | None) -> str | None:
    if harness != "claude" or receipt.get("mode") != "codex":
        return None
    tool = data.get("tool_name")
    if tool in READ_TOOLS:
        return None
    if tool in WRITE_TOOLS:
        if handoff_preparation(data, receipt):
            return None
        goal_path = receipt.get("goal_path")
        return ("CODEX HANDOFF REQUIRED: load engineering:handoff; only write the canonical goal "
                f"({goal_path}) with # Goal and "
                "## Next Steps before the installed Codex launcher.")
    if tool in DISPATCH_TOOLS:
        return "CODEX HANDOFF REQUIRED: load engineering:handoff, complete read-only preparation, then launch the installed Codex handoff before making deliverable changes or delegating work."
    if tool in SHELL_TOOLS:
        command_text = command(data)
        if codex_launcher(command_text) or read_only_shell(command_text):
            return None
        return "CODEX HANDOFF REQUIRED: read-only preparation is allowed; load engineering:handoff and invoke the installed Codex launcher before other shell execution."
    return None


def recover(data: dict, harness: str | None) -> tuple[dict, str | None]:
    if any(key in data for key in ("agent_id", "agentId", "agent_type", "turn_id", "turnId")):
        return {}, None
    return recovered_receipt(data, harness)


def emit(event: str, context: str | None = None, denial: str | None = None) -> None:
    output = {"hookEventName": event}
    if context:
        output["additionalContext"] = context
    if denial:
        output["permissionDecision"] = "deny"
        output["permissionDecisionReason"] = denial
    print(json.dumps({"hookSpecificOutput": output}, ensure_ascii=True))
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
    harness = None
    if len(sys.argv) == 3 and sys.argv[1] == "--harness" and sys.argv[2] == "claude":
        harness = "claude"
    if event == "PreToolUse":
        receipt, context = recover(data, harness)
        denial = denied_tool(data, receipt, harness)
        if context or denial:
            emit("PreToolUse", context, denial)
        return 0
    if event != "UserPromptSubmit":
        return 0
    try:
        prompt = data.get("prompt")
        cwd_value = data.get("cwd")
        if not isinstance(prompt, str) or not isinstance(cwd_value, str):
            raise RuntimeError("UserPromptSubmit payload requires string prompt and cwd fields")
        session = data.get("session_id")
        previous = read_receipt(session) if isinstance(session, str) and session else {}
        resolved_cwd = Path(cwd_value).resolve()
        mode = prompt_mode(prompt, resolved_cwd, harness, previous)
        goal_path = canonical_goal(prompt, resolved_cwd, previous) if mode == "codex" else None
        context = route(prompt, resolved_cwd, harness, mode)
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"workflow-route: {error}", file=sys.stderr)
        return 2
    if context:
        emit("UserPromptSubmit", context)
    if isinstance(session, str) and session:
        record_receipt(session, data.get("prompt_id"), prompt=prompt, mode=mode, goal_path=goal_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
