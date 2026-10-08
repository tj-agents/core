import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile

from workflow_route import HOST_GENERATED_PROMPTS, prompt_text


CALLOUT = re.compile(
    r"\b(?:you|you've|you're|you are)\b[^.!?\n]{0,100}"
    r"\b(?:mistake|wrong|ignored|violated|failed to|keep doing|keep picking)\b|"
    r"\b(?:that|this|that's|that is|this is)\s+(?:is\s+)?(?:a\s+)?"
    r"(?:mistake|wrong|incorrect)\b",
    re.I,
)
EXPLICIT_FEEDBACK = re.compile(
    r"(?:^|[.!?;\n])\s*(?:please\s+|can you\s+|could you\s+|i want you to\s+)?"
    r"(?:send|draft|submit|write|give|file)\s+(?:a\s+|the\s+|some\s+)?feedback\b",
    re.I,
)
REPAIR_LIMIT = re.compile(
    r"\b(?:do not|don't|dont|stop|never)\s+(?:launch(?:ing)?|hand(?:ing)?\s*off|"
    r"repair(?:ing)?|fix(?:ing)?|make changes)\b|\b(?:answer|explain)\s+only\b",
    re.I,
)
LAUNCHER = re.compile(r"launch-codex\.ps1|launch_codex\.py|launch_claude\.py", re.I)
LAUNCH_SUCCESS = re.compile(r"Launched (?:codex-cli\s+\S+|codex handoff tab|claude handoff tab)")
TAIL_BYTES = 1 << 20
MESSAGE = (
    "CALLOUT REPAIR: answer the user's direct question first. Check the governing standard and "
    "launch engineering:handoff in bounded side-workstream mode for the responsible source owner "
    "in this same turn. An apology, automatic SendFeedback, or memory update does not replace "
    "repair. A skill load, a promised launch, or a failed launcher is not launch evidence. "
    "Respect explicit user limits."
)


def texts(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from texts(item)
    elif isinstance(value, list):
        for item in value:
            yield from texts(item)


def state_path(session):
    key = hashlib.sha256(session.encode()).hexdigest()[:20]
    return Path(tempfile.gettempdir()) / f"callout-repair-{key}.json"


def load_state(session):
    if not session:
        return {}
    try:
        value = json.loads(state_path(session).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def save_state(session, prompt, pending):
    if not session:
        return
    state_path(session).write_text(json.dumps({"prompt": prompt, "pending": pending}), encoding="utf-8")


def transcript_records(path):
    if not path:
        return []
    try:
        with Path(path).open("rb") as stream:
            stream.seek(0, 2)
            stream.seek(max(0, stream.tell() - TAIL_BYTES))
            lines = stream.read().splitlines()
    except OSError:
        return []
    records = []
    for line in lines:
        try:
            value = json.loads(line)
        except (ValueError, UnicodeError):
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


def message(record):
    if record.get("type") == "response_item" and isinstance(record.get("payload"), dict):
        return record["payload"]
    if record.get("type") in ("user", "assistant") and isinstance(record.get("message"), dict):
        return record["message"]
    return record


def human_prompt(record):
    if record.get("isMeta") or record.get("isCompactSummary") or record.get("isSidechain"):
        return None
    origin = record.get("origin")
    if isinstance(origin, dict) and origin.get("kind") not in (None, "human"):
        return None
    value = message(record)
    if value.get("role") != "user":
        return None
    content = value.get("content")
    if isinstance(content, list):
        content = [dict(item, type="text") if isinstance(item, dict) and item.get("type") == "input_text"
                   else item for item in content]
    return prompt_text(content)


def current_turn(records):
    for index in range(len(records) - 1, -1, -1):
        prompt = human_prompt(records[index])
        if prompt is not None:
            return prompt, records[index + 1:]
    return None, records


def assistant_answer(records):
    for record in records:
        value = message(record)
        if value.get("role") != "assistant" or value.get("channel") == "analysis":
            continue
        content = value.get("content")
        if isinstance(content, str) and content.strip():
            return True
        if isinstance(content, list) and any(
            isinstance(item, dict) and item.get("type") in ("text", "output_text")
            and isinstance(item.get("text"), str) and item["text"].strip() for item in content
        ):
            return True
    return False


def launcher_call(value):
    text = "\n".join(texts(value))
    return bool(LAUNCHER.search(text) and re.search(r"-+WorkingDirectory|-+working-directory", text, re.I)
                and re.search(r"-+PromptPath|-+prompt-path", text, re.I))


def source_owner_handoff(value):
    if isinstance(value, dict) and value.get("event") == "agent-handoff-submitted":
        paths = [value.get("worktree"), value.get("prompt_path")]
        if not all(isinstance(item, str) and item for item in paths):
            return False
    else:
        text = "\n".join(texts(value)).replace('\\"', '"')
        paths = []
        for flag in (r"-+WorkingDirectory|-+working-directory", r"-+PromptPath|-+prompt-path"):
            match = re.search(rf"(?:{flag})\s+('([^']+)'|\"([^\"]+)\"|([^\s,;)]+))", text, re.I)
            if match is None:
                return False
            paths.append(next(item for item in match.groups()[1:] if item is not None).replace("\\\\", "\\"))
    workdir, prompt_path = map(Path, paths)
    if not prompt_path.is_absolute():
        prompt_path = workdir / prompt_path
    try:
        body = prompt_path.read_text(encoding="utf-8-sig")[:65536]
        match = re.search(r"(?im)^\s*Read\s+(.+?\.md)(?:\s+and\b|\s*$)", body)
        if match is None:
            return False
        goal = Path(match.group(1).strip("`\"' "))
        if not goal.is_absolute():
            goal = workdir / goal
        context = goal.read_text(encoding="utf-8-sig")[:65536]
    except (OSError, UnicodeError):
        return False
    return bool(re.search(r"(?im)^## Authorization\b", context)
                and re.search(r"standards[- ](?:defect|repair)|source[- ]owner repair", context, re.I))


def launch_succeeded(records):
    pending = {}
    for record in records:
        value = message(record)
        if value.get("type") in ("custom_tool_call", "function_call"):
            tool_input = value.get("input", value.get("arguments"))
            if value.get("call_id") and launcher_call(tool_input):
                pending[value["call_id"]] = tool_input
        elif value.get("type") in ("custom_tool_call_output", "function_call_output"):
            tool_input = pending.pop(value.get("call_id"), None)
            if tool_input is not None and successful_result(value, tool_input):
                return True
        content = value.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use" and block.get("name") in ("Bash", "PowerShell"):
                if block.get("id") and launcher_call(block.get("input")):
                    pending[block["id"]] = block["input"]
            elif block.get("type") == "tool_result":
                tool_input = pending.pop(block.get("tool_use_id"), None)
                if tool_input is not None and successful_result(block, tool_input):
                    return True
    return False


def successful_result(value, tool_input):
    if value.get("is_error") or value.get("error"):
        return False
    parts = list(texts(value.get("content", value.get("output", ""))))
    for text in list(parts):
        try:
            decoded = json.loads(text)
        except ValueError:
            continue
        if isinstance(decoded, (dict, list)):
            parts.extend(texts(decoded))
    output = "\n".join(parts)
    if re.search(r"Script failed|Process exited with code [1-9]|\"exit_code\"\s*:\s*[1-9]", output):
        return False
    if LAUNCH_SUCCESS.search(output) is None:
        return False
    for line in output.splitlines():
        try:
            receipt = json.loads(line)
        except ValueError:
            continue
        if isinstance(receipt, dict) and receipt.get("event") == "agent-handoff-submitted":
            return source_owner_handoff(receipt)
    return source_owner_handoff(tool_input)


def emit(event, context, deny=False):
    output = {"hookEventName": event, "additionalContext": context}
    if deny:
        output.update(permissionDecision="deny", permissionDecisionReason=context)
    print(json.dumps({"hookSpecificOutput": output}))


def main():
    data = json.load(sys.stdin)
    if not isinstance(data, dict):
        return 0
    event = data.get("hook_event_name") or data.get("hookEventName")
    if any(key in data for key in ("agent_id", "agentId", "agent_type")):
        return 0
    session = data.get("session_id") or data.get("sessionId") or ""
    if event == "UserPromptSubmit":
        prompt = data.get("prompt")
        if not isinstance(prompt, str) or prompt.lstrip().startswith(HOST_GENERATED_PROMPTS):
            return 0
        origin = data.get("origin")
        if data.get("isMeta") or data.get("isSidechain") or data.get("isCompactSummary"):
            return 0
        if isinstance(origin, dict) and origin.get("kind") not in (None, "human"):
            return 0
        pending = bool(CALLOUT.search(prompt)) and not REPAIR_LIMIT.search(prompt)
        save_state(session, prompt, pending)
        if pending:
            emit(event, MESSAGE)
        return 0
    if event not in ("PreToolUse", "Stop"):
        return 0
    state = load_state(session)
    prompt, records = current_turn(transcript_records(data.get("transcript_path") or data.get("transcriptPath")))
    if prompt is None:
        prompt = state.get("prompt", "")
    if REPAIR_LIMIT.search(prompt) or EXPLICIT_FEEDBACK.search(prompt):
        return 0
    tool = str(data.get("tool_name", "")).lower().replace("_", "")
    feedback = tool.endswith("sendfeedback")
    pending = bool(CALLOUT.search(prompt)) or (state.get("pending") and state.get("prompt") == prompt)
    if not pending and not feedback:
        return 0
    if launch_succeeded(records):
        save_state(session, prompt, False)
        return 0
    if event == "PreToolUse":
        if feedback:
            save_state(session, prompt, True)
            emit(event, MESSAGE, deny=True)
        elif launcher_call(data.get("tool_input")) and not assistant_answer(records):
            emit(event, "Answer the user's direct question before launching the callout repair handoff.", deny=True)
    elif not (data.get("stop_hook_active") or data.get("stopHookActive")):
        print(json.dumps({"decision": "block", "reason": MESSAGE}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, TypeError):
        sys.exit(0)
