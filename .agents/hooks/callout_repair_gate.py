import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import uuid

from workflow_route import HOST_GENERATED_PROMPTS, prompt_text
from worktree_placement_gate import normalized_extraction_input, shell_kind, shell_segments, tokens_of


try:
    from handoff_admission import validate as validate_disposition
except ModuleNotFoundError:
    HANDOFF_SCRIPTS = Path(__file__).resolve().parents[1] / "engineering" / "workflow" / "handoff" / "scripts"
    if str(HANDOFF_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(HANDOFF_SCRIPTS))
    try:
        from admission import validate as validate_disposition
    except ModuleNotFoundError:
        validate_disposition = None


CALLOUT = re.compile(
    r"\b(?:you|you've|you're|you are)\b[^.!?\n]{0,100}"
    r"\b(?:mistake|wrong|ignored|violated|failed to|keep doing|keep picking)\b|"
    r"\b(?:that|this|that's|that is|this is)\s+(?:is\s+)?(?:a\s+)?"
    r"(?:mistake|wrong|incorrect)\b",
    re.I,
)
STANDARDS_CONTEXT = re.compile(r"\b(?:standard|skill|hook|rule|plugin|handoff|workflow|lane|model)s?\b", re.I)
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
    "if it caused or failed to prevent the mistake, follow engineering:self-repair. Admit runnable "
    "work through engineering:handoff; otherwise record a current typed disposition with "
    "scripts/admission.py check. An apology, automatic SendFeedback, or memory update does not replace "
    "repair. A skill load, a promised launch, or a stale disposition is not evidence. "
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


def obligations(state):
    values = state.get("obligations")
    if isinstance(values, list):
        return [value for value in values if isinstance(value, dict)
                and isinstance(value.get("prompt"), str) and isinstance(value.get("callout_id"), str)]
    if state.get("pending") and isinstance(state.get("prompt"), str):
        return [{"prompt": state["prompt"], "callout_id": state.get("callout_id", "")}]
    return []


def completed_prompts(state):
    values = state.get("completed")
    return {value for value in values if isinstance(value, str)} if isinstance(values, list) else set()


def save_state(session, values, completed=()):
    if not session:
        return
    current = values[-1] if values else {}
    state_path(session).write_text(
        json.dumps({"obligations": values, "completed": sorted(set(completed)), "prompt": current.get("prompt", ""),
                    "pending": bool(values), "resolved": False,
                    "callout_id": current.get("callout_id", "")}),
        encoding="utf-8",
    )


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
        if not any(
            isinstance(item, dict) and item.get("type") in ("input_text", "text")
            for item in content
        ):
            return None
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


def launcher_command(value):
    if isinstance(value, str):
        return value, value, {}
    normalized = normalized_extraction_input(value)
    if not isinstance(normalized, dict):
        return None, normalized, {}
    for container in (normalized, normalized.get("action")):
        if not isinstance(container, dict):
            continue
        for key in ("command", "cmd", "script", "input"):
            if isinstance(container.get(key), str):
                variables = next(
                    (item for item in (container.get("environment"), container.get("env"), container.get("variables"))
                     if isinstance(item, dict)),
                    {},
                )
                return container[key], normalized, variables
    return None, normalized, {}


def launcher_path(value, variables, workdir=None):
    match = re.fullmatch(r"\$([A-Za-z_][A-Za-z0-9_]*)", value)
    if match:
        value = variables.get(match.group(1))
    if not isinstance(value, str) or not value or re.search(r"[$`%]", value):
        return None
    path = Path(value)
    if not path.is_absolute():
        if workdir is None:
            return None
        path = workdir / path
    try:
        return path.resolve()
    except (OSError, RuntimeError, ValueError):
        return None


def launcher_invocation(value, tool=""):
    command, normalized, variables = launcher_command(value)
    if not isinstance(command, str) or not command.strip():
        return None
    segments = shell_segments(command, shell_kind(tool, normalized))
    if segments is None or len(segments) != 1:
        return None
    tokens = tokens_of(segments[0])
    if not tokens:
        return None
    launcher_indices = [
        index for index, token in enumerate(tokens)
        if LAUNCHER.fullmatch(Path(token).name)
    ]
    if len(launcher_indices) != 1:
        return None
    launcher_index = launcher_indices[0]
    if launcher_index:
        interpreter = Path(tokens[0]).stem.casefold()
        if interpreter not in {"python", "python3", "py"} or any(token != "-B" for token in tokens[1:launcher_index]):
            return None
    arguments = {}
    index = launcher_index + 1
    while index < len(tokens):
        flag = tokens[index].casefold()
        if flag in {"-workingdirectory", "--working-directory"}:
            name = "worktree"
        elif flag in {"-promptpath", "--prompt-path"}:
            name = "prompt_path"
        else:
            index += 1
            continue
        if name in arguments or index + 1 >= len(tokens):
            return None
        arguments[name] = tokens[index + 1]
        index += 2
    if set(arguments) != {"worktree", "prompt_path"}:
        return None
    worktree = launcher_path(arguments["worktree"], variables)
    prompt_path = launcher_path(arguments["prompt_path"], variables, worktree)
    if worktree is None or prompt_path is None:
        return None
    return {"worktree": worktree, "prompt_path": prompt_path}


def source_owner_handoff(receipt, invocation, session, prompt, callout_id):
    if not isinstance(receipt, dict) or receipt.get("event") != "agent-handoff-submitted":
        return False
    paths = [receipt.get("worktree"), receipt.get("prompt_path")]
    if not all(isinstance(item, str) and item for item in paths):
        return False
    workdir, prompt_path = map(Path, paths)
    if not workdir.is_absolute():
        return False
    if not prompt_path.is_absolute():
        prompt_path = workdir / prompt_path
    try:
        workdir = workdir.resolve()
        prompt_path = prompt_path.resolve()
        if workdir != invocation["worktree"] or prompt_path != invocation["prompt_path"]:
            return False
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
    expected = {
        "Repair workflow": "engineering:self-repair",
        "Callout session": session,
        "Callout id": callout_id,
        "Prompt SHA256": prompt_digest(prompt),
    }
    return bool(re.search(r"(?im)^## Authorization\b", context)
                and re.search(r"standards[- ](?:defect|repair)|source[- ]owner repair", context, re.I)
                and re.search(r"(?im)^Source owner:\s*\S.+$", context)
                and all(re.search(rf"(?im)^{re.escape(label)}:\s*{re.escape(value)}\s*$", context)
                        for label, value in expected.items()))


def launch_succeeded(records, session, prompt, callout_id):
    pending = {}
    for record in records:
        value = message(record)
        if value.get("type") in ("custom_tool_call", "function_call"):
            tool_input = value.get("input", value.get("arguments"))
            invocation = launcher_invocation(tool_input, value.get("name", ""))
            if value.get("call_id") and invocation:
                pending[value["call_id"]] = invocation
        elif value.get("type") in ("custom_tool_call_output", "function_call_output"):
            invocation = pending.pop(value.get("call_id"), None)
            if invocation is not None and successful_result(value, invocation, session, prompt, callout_id):
                return True
        content = value.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use" and block.get("name") in ("Bash", "PowerShell"):
                invocation = launcher_invocation(block.get("input"), block.get("name", ""))
                if block.get("id") and invocation:
                    pending[block["id"]] = invocation
            elif block.get("type") == "tool_result":
                invocation = pending.pop(block.get("tool_use_id"), None)
                if invocation is not None and successful_result(block, invocation, session, prompt, callout_id):
                    return True
    return False


def successful_result(value, invocation, session, prompt, callout_id):
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
        if source_owner_handoff(receipt, invocation, session, prompt, callout_id):
            return True
    return False


def prompt_digest(prompt):
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def command_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return "\n".join(texts(value))
    return ""


def disposition_command(value):
    text = command_text(value)
    if not re.search(r"(?:^|[\\/])admission\.py\b|\bhandoff_admission\.py\b", text, re.I):
        return None
    fields = {}
    for flag in ("record", "id", "session", "prompt-sha256", "callout-id"):
        match = re.search(rf"--{flag}\s+('([^']+)'|\"([^\"]+)\"|([^\s,;)]+))", text, re.I)
        if match is None:
            return None
        fields[flag.replace("-", "_")] = next(item for item in match.groups()[1:] if item is not None)
    for flag in ("source-root", "host"):
        match = re.search(rf"--{flag}\s+('([^']+)'|\"([^\"]+)\"|([^\s,;)]+))", text, re.I)
        if match is not None:
            fields[flag.replace("-", "_")] = next(item for item in match.groups()[1:] if item is not None)
    if not re.search(r"\bcheck\b", text, re.I):
        return None
    return fields


def result_json(value):
    parts = list(texts(value.get("content", value.get("output", ""))))
    for text in list(parts):
        try:
            decoded = json.loads(text)
        except ValueError:
            continue
        if isinstance(decoded, (dict, list)):
            parts.extend(texts(decoded))
    for part in parts:
        for line in str(part).splitlines():
            try:
                decoded = json.loads(line)
            except ValueError:
                continue
            if isinstance(decoded, dict) and decoded.get("event") == "agent-handoff-disposition":
                return decoded
    return None


def valid_disposition(records, session, prompt, callout_id):
    if validate_disposition is None or not callout_id:
        return False
    expected = {
        "session": session,
        "prompt_sha256": prompt_digest(prompt),
        "callout_id": callout_id,
    }
    pending = {}
    for record in records:
        value = message(record)
        if value.get("type") in ("custom_tool_call", "function_call"):
            command = disposition_command(value.get("input", value.get("arguments")))
            if command and value.get("call_id"):
                pending[value["call_id"]] = command
        elif value.get("type") in ("custom_tool_call_output", "function_call_output"):
            command = pending.pop(value.get("call_id"), None)
            receipt = result_json(value)
            if command and receipt and not value.get("is_error") and not value.get("error"):
                if all(command.get(key) == value_ for key, value_ in expected.items()):
                    try:
                        result = validate_disposition(
                            command["record"], command["id"], session, expected["prompt_sha256"], callout_id,
                            source_root=command.get("source_root"), harness=command.get("host")
                        )
                    except (OSError, ValueError, TypeError):
                        result = {"valid": False}
                    if result.get("valid") and all(receipt.get(key) == result.get(key) for key in result):
                        return True
        for block in value.get("content", []) if isinstance(value.get("content"), list) else []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                command = disposition_command(block.get("input"))
                if command and block.get("id"):
                    pending[block["id"]] = command
            elif block.get("type") == "tool_result":
                command = pending.pop(block.get("tool_use_id"), None)
                receipt = result_json(block)
                if command and receipt and not block.get("is_error"):
                    if all(command.get(key) == value_ for key, value_ in expected.items()):
                        try:
                            result = validate_disposition(
                                command["record"], command["id"], session, expected["prompt_sha256"], callout_id,
                                source_root=command.get("source_root"), harness=command.get("host")
                            )
                        except (OSError, ValueError, TypeError):
                            result = {"valid": False}
                        if result.get("valid") and all(receipt.get(key) == result.get(key) for key in result):
                            return True
    return False


def emit(event, context, deny=False):
    output = {"hookEventName": event, "additionalContext": context}
    if deny:
        output.update(permissionDecision="deny", permissionDecisionReason=context)
    print(json.dumps({"hookSpecificOutput": output}))


def repair_operation(tool, tool_input):
    if tool == "read":
        return True
    normalized = normalized_extraction_input(tool_input)
    text = command_text(normalized)
    records = {"BUGS.md", "MISTAKES.md", "TECH_DEBT.md", "GOAL.md"}
    if tool in {"applypatch", "apply_patch"}:
        headers = re.findall(r"(?im)^\*\*\* (Update|Add|Delete) File:\s*(.+)$", text)
        return bool(headers) and all(
            operation in {"Update", "Add"} and Path(path.strip()).name in records
            for operation, path in headers
        )
    if tool in {"write", "edit", "multiedit"}:
        paths = []

        def collect_paths(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if key in {"file_path", "path"} and isinstance(item, str):
                        paths.append(item)
                    else:
                        collect_paths(item)
            elif isinstance(value, list):
                for item in value:
                    collect_paths(item)

        collect_paths(normalized)
        return bool(paths) and all(Path(path).name in records for path in paths)
    command = next((value for value in (
        normalized.get("command") if isinstance(normalized, dict) else None,
        normalized.get("cmd") if isinstance(normalized, dict) else None,
        normalized.get("script") if isinstance(normalized, dict) else None,
        normalized.get("input") if isinstance(normalized, dict) else None,
    ) if isinstance(value, str)), "")
    if not command:
        return False
    segments = shell_segments(command, shell_kind(tool, normalized))
    if segments is None or len(segments) != 1:
        return False
    command = segments[0]
    if re.fullmatch(r"\s*(?:rg|grep|cat|type|get-content|select-string)\b.*", command, re.I):
        return True
    if re.fullmatch(r"\s*git\s+(?:diff|show|log)\b.*", command, re.I):
        return True
    if re.fullmatch(r"\s*git\s+worktree\s+add\b.*", command, re.I):
        return True
    return bool(re.fullmatch(
        r"\s*(?:python(?:3)?|py)\s+(?:-B\s+)?(?:[^\s]+[\\/])?(?:admission\.py|handoff_admission\.py)\s+check\b.*",
        command,
        re.I,
    ) or re.fullmatch(r"\s*\S*write-(?:bug|mistake|debt)\S*.*", command, re.I))


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
        pending = bool(CALLOUT.search(prompt) and STANDARDS_CONTEXT.search(prompt)) and not REPAIR_LIMIT.search(prompt)
        values = obligations(load_state(session))
        existing = next((value for value in reversed(values) if value["prompt"] == prompt), None)
        callout_id = existing["callout_id"] if existing else (str(uuid.uuid4()) if pending else "")
        if pending and existing is None:
            values.append({"prompt": prompt, "callout_id": callout_id})
            save_state(session, values, completed_prompts(load_state(session)))
        if pending:
            emit(
                event,
                f"{MESSAGE}\nAdmission binding: session={session}; callout_id={callout_id}; "
                f"prompt_sha256={prompt_digest(prompt)}",
            )
        return 0
    if event not in ("PreToolUse", "Stop"):
        return 0
    state = load_state(session)
    completed = completed_prompts(state)
    current_prompt, records = current_turn(transcript_records(data.get("transcript_path") or data.get("transcriptPath")))
    values = obligations(state)
    obligation = next((value for value in reversed(values) if value["prompt"] == current_prompt), None)
    if obligation is None and values:
        obligation = values[0]
    prompt = obligation["prompt"] if obligation else (current_prompt or "")
    if REPAIR_LIMIT.search(current_prompt or ""):
        return 0
    tool = str(data.get("tool_name", "")).lower().replace("_", "")
    feedback = tool.endswith("sendfeedback")
    pending = obligation is not None or (
        bool(CALLOUT.search(prompt) and STANDARDS_CONTEXT.search(prompt)) and prompt not in completed
    )
    if not pending and (not feedback or prompt in completed or (not values and completed and current_prompt is None)):
        return 0
    callout_id = obligation.get("callout_id", "") if obligation else ""
    if launch_succeeded(records, session, prompt, callout_id):
        values = [value for value in values if value is not obligation]
        save_state(session, values, completed | {prompt})
        if not values:
            return 0
        obligation = values[0]
        prompt = obligation["prompt"]
        callout_id = obligation["callout_id"]
    if values and all(
        valid_disposition(records, session, value["prompt"], value["callout_id"])
        for value in values
    ):
        return 0
    if event == "PreToolUse":
        if feedback and not EXPLICIT_FEEDBACK.search(current_prompt or prompt):
            emit(event, MESSAGE, deny=True)
        elif launcher_invocation(data.get("tool_input"), tool):
            if not assistant_answer(records):
                emit(event, "Answer the user's direct question before launching the callout repair handoff.", deny=True)
        elif not repair_operation(tool, data.get("tool_input")) and not feedback:
            emit(event, MESSAGE, deny=True)
    else:
        binding = ""
        if callout_id:
            binding = (
                f" Admission binding: session={session}; callout_id={callout_id}; "
                f"prompt_sha256={prompt_digest(prompt)}"
            )
        print(json.dumps({"decision": "block", "reason": MESSAGE + binding}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, TypeError):
        sys.exit(0)
