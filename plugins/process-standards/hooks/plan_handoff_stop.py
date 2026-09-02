import json
import re
import subprocess
import sys
from pathlib import Path

HOOK_ROOT = str(Path(__file__).resolve().parent)
if HOOK_ROOT not in sys.path:
    sys.path.insert(0, HOOK_ROOT)

from plan_graph import (
    BLOCKER_FIELDS,
    blocker_details,
    is_paused,
    is_terminal,
    ledger_errors,
    ledger_root,
    looks_like_legacy_blocker,
    metadata,
    next_steps,
    plan_path,
)

ABSOLUTE_LEDGER = re.compile(
    r"[A-Za-z]:[\\/][^\"'\r\n<>|]*?[\\/]plans[\\/][A-Za-z0-9_.() \\/-]+?_PROGRESS\.md",
    re.IGNORECASE,
)
RELATIVE_LEDGER = re.compile(
    r"plans[\\/][A-Za-z0-9_.() \\/-]+?_PROGRESS\.md",
    re.IGNORECASE,
)
WORKDIR = re.compile(r"[\"']?(?:workdir|cwd)[\"']?\s*:\s*[\"']([^\"']+)", re.IGNORECASE)
CD_WORKDIR = re.compile(
    r"^\s*cd\s+(?:\"([^\"]+)\"|'([^']+)'|([^\r\n]+?))\s*$",
    re.IGNORECASE | re.MULTILINE,
)
MUTATING_TOOL_NAMES = {
    "apply_patch",
    "edit",
    "edit_file",
    "multiedit",
    "multi_edit",
    "write",
    "write_file",
}
MUTATING_PATH_KEYS = {"path", "filepath"}
PATCH_FILE_TARGET = re.compile(
    r"\*\*\*\s+(?:Add|Update|Delete)\s+File:\s*"
    r"((?:[A-Za-z]:[\\/])?[^\"'\r\n<>|]*?_PROGRESS\.md)",
    re.IGNORECASE,
)
CONTEXT_TRANSFER_DIRECTIVE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:"
    r"(?:please\s+)?(?:clear|reset|restart)\s+(?:the\s+)?context\b|"
    r"(?:continue|resume|start|pick\s+(?:this|it|the\s+work)\s+up|move)\b"
    r"[^\n]{0,120}\b(?:fresh|new|separate)\s+context\b"
    r")",
    re.IGNORECASE | re.MULTILINE,
)


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def workdirs(value):
    if isinstance(value, str):
        for match in WORKDIR.finditer(value):
            yield match.group(1)
        for match in CD_WORKDIR.finditer(value):
            yield next(item for item in match.groups() if item is not None).strip()
    elif isinstance(value, dict):
        for name, item in value.items():
            if name.lower() in {"cwd", "workdir"} and isinstance(item, str):
                yield item
            else:
                yield from workdirs(item)
    elif isinstance(value, list):
        for item in value:
            yield from workdirs(item)


def user_content(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                yield item
            elif isinstance(item, dict) and item.get("type") in {"text", "input_text"}:
                text = item.get("text")
                if isinstance(text, str):
                    yield text


def payload(value):
    if not isinstance(value, dict):
        return None
    if isinstance(value.get("payload"), dict):
        return value["payload"]
    if value.get("type") in {"user", "assistant"} and isinstance(value.get("message"), dict):
        return value["message"]
    return value


def genuine_user_message(value):
    candidate = payload(value)
    if candidate is None or candidate.get("role") != "user":
        return False
    content = candidate.get("content")
    if isinstance(content, list):
        if any(
            isinstance(item, dict) and item.get("type") in {"tool_result", "function_call_output"}
            for item in content
        ):
            return False
    return not any("<hook_prompt" in text for text in user_content(content))


def structured_mutation_targets(value):
    if isinstance(value, dict):
        for name, item in value.items():
            normalized = name.casefold().replace("-", "").replace("_", "")
            if normalized in MUTATING_PATH_KEYS and isinstance(item, str):
                yield item
            elif isinstance(item, (dict, list)):
                yield from structured_mutation_targets(item)
    elif isinstance(value, list):
        for item in value:
            yield from structured_mutation_targets(item)


def patch_mutation_targets(value):
    for item in strings(value):
        yield from (match.group(1) for match in PATCH_FILE_TARGET.finditer(item))


def mutating_tool_input(name, tool_input):
    normalized = (name or "").casefold().replace("-", "_")
    targets = list(patch_mutation_targets(tool_input))
    if normalized.rsplit(".", 1)[-1] in MUTATING_TOOL_NAMES:
        targets.extend(structured_mutation_targets(tool_input))
    if not targets:
        return None
    return {
        "targets": list(dict.fromkeys(targets)),
        "workdirs": [{"workdir": item} for item in workdirs(tool_input)],
    }


def intentional_contexts(record):
    candidate = payload(record)
    if candidate is None:
        return
    if genuine_user_message(record):
        yield {
            "source": "user",
            "values": list(user_content(candidate.get("content"))),
        }
    if candidate.get("type") in {"custom_tool_call", "function_call"}:
        tool_input = candidate.get("input", candidate.get("arguments"))
        context = mutating_tool_input(candidate.get("name"), tool_input)
        if context is not None:
            context["source"] = "mutation"
            yield context
    content = candidate.get("content")
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") in {"tool_use", "function_call"}:
                tool_input = item.get("input", item.get("arguments"))
                context = mutating_tool_input(item.get("name"), tool_input)
                if context is not None:
                    context["source"] = "mutation"
                    yield context


def transcript_turn(path):
    if not path or not Path(path).is_file():
        return []
    records = []
    with Path(path).open(encoding="utf-8") as stream:
        for line in stream:
            try:
                records.append(json.loads(line))
            except (TypeError, ValueError):
                continue
    start = 0
    for index in range(len(records) - 1, -1, -1):
        if genuine_user_message(records[index]):
            start = index
            break
    return records[start:]


def git_root(cwd):
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
            capture_output=True,
            check=True,
            text=True,
            timeout=5,
        )
        return Path(result.stdout.strip()).resolve()
    except (OSError, subprocess.SubprocessError):
        return None


def git_branch(root):
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "branch", "--show-current"],
            capture_output=True,
            check=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def add_if_ledger(paths, candidate):
    try:
        resolved = candidate.resolve()
    except OSError:
        return
    if resolved.is_file() and resolved.name.upper().endswith("_PROGRESS.MD"):
        paths.add(resolved)


def context_root(path):
    candidate = Path(path).resolve()
    return git_root(candidate) or candidate


def context_owns_ledger(path, bases, source):
    text = path.read_text(encoding="utf-8")
    declared_worktree = metadata(text, "Worktree")
    roots = {context_root(base) for base in bases}
    if declared_worktree:
        owner = Path(declared_worktree).resolve()
        if owner.is_dir():
            return owner in roots
        if source == "mutation" and ledger_root(path) in roots:
            return True
        owner_branch = metadata(text, "Branch")
        if owner_branch:
            return any(git_branch(root) == owner_branch for root in roots)
        return False
    owner_branch = metadata(text, "Branch")
    if owner_branch:
        return any(git_branch(root) == owner_branch for root in roots)
    return ledger_root(path) in roots


def transcript_ledgers(records, cwd):
    paths = set()
    contexts = [context for record in records for context in intentional_contexts(record)]
    targeted_bases = set()
    for context in contexts:
        values = list(strings(context))
        explicit_bases = {Path(path).resolve() for path in workdirs(context)}
        bases = explicit_bases or targeted_bases or {Path(cwd).resolve()}
        targeted_bases.update(explicit_bases)
        candidates = set()
        for value in values:
            absolute_matches = list(ABSOLUTE_LEDGER.finditer(value))
            for match in absolute_matches:
                add_if_ledger(candidates, Path(match.group(0).rstrip("`),.;")))
            for match in RELATIVE_LEDGER.finditer(value):
                absolute_spans = (item.span() for item in absolute_matches)
                if any(start <= match.start() < end for start, end in absolute_spans):
                    continue
                relative = Path(match.group(0).replace("\\", "/").rstrip("`),.;"))
                for base in bases:
                    add_if_ledger(candidates, context_root(base) / relative)
        for path in candidates:
            if context_owns_ledger(path, bases, context.get("source")):
                paths.add(path)
    return paths


def branch_ledgers(root):
    if root is None:
        return set()
    branch = git_branch(root)
    paths = set()
    for path in (root / "plans").rglob("*_PROGRESS.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        worktree = metadata(text, "Worktree")
        owner_branch = metadata(text, "Branch")
        same_worktree = False
        if worktree:
            try:
                same_worktree = Path(worktree).resolve() == root
            except OSError:
                same_worktree = False
        if same_worktree or (branch and owner_branch == branch):
            paths.add(path.resolve())
    return paths


def logical_ledger_key(path):
    return path.relative_to(ledger_root(path)).as_posix().casefold()


def owner_copy_score(path):
    text = path.read_text(encoding="utf-8")
    declared_worktree = metadata(text, "Worktree")
    if not declared_worktree:
        return 1
    try:
        owner = Path(declared_worktree).resolve()
        return 0 if owner == ledger_root(path) else 1
    except OSError:
        return 1


def canonical_ledgers(paths):
    grouped = {}
    for path in paths:
        grouped.setdefault(logical_ledger_key(path), []).append(path)
    return {
        min(candidates, key=lambda path: (owner_copy_score(path), str(path).casefold()))
        for candidates in grouped.values()
    }


def expected_pointer(path):
    root = ledger_root(path)
    plan = plan_path(path)
    text = path.read_text(encoding="utf-8")
    declared_worktree = metadata(text, "Worktree")
    owner_branch = metadata(text, "Branch")
    if declared_worktree and Path(declared_worktree).is_dir():
        opener_path = str(Path(declared_worktree).resolve())
        opener = f'cd "{opener_path}"' if " " in opener_path else f"cd {opener_path}"
    elif owner_branch:
        opener = f"/open-worktree {owner_branch}"
    else:
        opener_path = str(root)
        opener = f'cd "{opener_path}"' if " " in opener_path else f"cd {opener_path}"
    plan_reference = plan.resolve().as_posix()
    ledger_reference = path.resolve().as_posix()
    return (
        f"{opener}\n"
        f"Read @{plan_reference} and @{ledger_reference} and do what its `## Next Steps` says."
    )


def handoff_summary(body):
    summary = re.sub(r"\s+", " ", body.split("\n\n", 1)[0]).strip()
    if len(summary) > 240:
        summary = summary[:237].rstrip() + "..."
    return summary


def handoff_reason(path, body):
    return f"Why: `{path.name}` owns unfinished work from this turn: {handoff_summary(body)}"


def expected_handoff(path, pointer, body):
    return f"{handoff_reason(path, body)}\n\n```text\n{pointer}\n```"


def normalized_handoff_text(value):
    value = re.sub(r"```(?:text)?", "", value, flags=re.IGNORECASE)
    value = value.replace("`", "")
    value = re.sub(r"(?<=\S)-\s+(?=\S)", "-", value)
    return re.sub(r"\s+", " ", value).strip()


def handoff_present(message, path, pointer):
    normalized_message = normalized_handoff_text(message)
    reason = normalized_handoff_text(
        f"Why: {path.name} owns unfinished work from this turn:"
    )
    normalized_pointer = normalized_handoff_text(pointer)
    reason_position = normalized_message.find(reason)
    pointer_position = normalized_message.find(
        normalized_pointer,
        reason_position + len(reason),
    )
    return reason_position >= 0 and pointer_position >= 0


def ends_with_pointer(message, pointer):
    return normalized_handoff_text(message).endswith(normalized_handoff_text(pointer))


def context_transfer_attempted(message, active):
    if CONTEXT_TRANSFER_DIRECTIVE.search(message):
        return True
    normalized_message = normalized_handoff_text(message)
    return any(
        normalized_handoff_text(pointer) in normalized_message
        or normalized_handoff_text(
            f"Why: {path.name} owns unfinished work from this turn:"
        ) in normalized_message
        for path, pointer, _, _ in active
    )


def evaluate(data):
    cwd = Path(data.get("cwd") or ".").resolve()
    records = transcript_turn(data.get("transcript_path") or data.get("transcriptPath"))
    ledgers = transcript_ledgers(records, cwd)
    if not records:
        ledgers |= branch_ledgers(git_root(cwd))
    ledgers = canonical_ledgers(ledgers)
    active = []
    blocked = []
    malformed_blockers = []
    for path in sorted(ledgers):
        graph_errors = ledger_errors(path)
        if graph_errors:
            return block_once(data, "PLAN GRAPH GATE: " + " | ".join(graph_errors))
        body = next_steps(path.read_text(encoding="utf-8"))
        if body is None:
            return block_once(
                data,
                f"HANDOFF GATE: {path.name} is missing its required `## Next Steps` section.",
            )
        if is_paused(body) or is_terminal(body):
            continue
        details = blocker_details(body)
        if details:
            blocked.append((path, expected_pointer(path), details))
        elif looks_like_legacy_blocker(body):
            malformed_blockers.append(path)
        else:
            pointer = expected_pointer(path)
            active.append((path, pointer, body, expected_handoff(path, pointer, body)))
    if malformed_blockers:
        names = ", ".join(path.name for path in malformed_blockers)
        return block_once(
            data,
            (
                f"BLOCKER HANDOFF GATE: {names} describes blocked work without the required "
                "four-line contract. Start `## Next Steps` with non-empty `Blocked:`, "
                "`Blocked by:`, `Unblock action:`, and `Resume when:` lines. Do not emit the "
                "blocked plan's continuation pointer."
            ),
        )
    active = list(
        {
            pointer: (path, pointer, body, handoff)
            for path, pointer, body, handoff in active
        }.values()
    )
    message = (data.get("last_assistant_message") or data.get("lastAssistantMessage") or "").replace(
        "\r\n", "\n"
    )
    message = "\n".join(line.rstrip() for line in message.split("\n"))
    blocked_failures = []
    for path, pointer, details in blocked:
        if normalized_handoff_text(pointer) in normalized_handoff_text(message):
            blocked_failures.append(f"{path.name}: remove the blocked plan's continuation pointer")
        required = tuple(
            f"{name}: {value}"
            for name, value in zip(BLOCKER_FIELDS, details)
        )
        missing = [line for line in required if line not in message]
        if missing:
            blocked_failures.append(
                f"{path.name}: report these exact lines: " + "; ".join(missing)
            )
    failures = []
    if blocked_failures:
        failures.append("BLOCKER HANDOFF GATE: " + " | ".join(blocked_failures))
    active_transfer = bool(active) and context_transfer_attempted(message, active)
    if active_transfer:
        missing = [
            (path, pointer, body, handoff)
            for path, pointer, body, handoff in active
            if not handoff_present(message, path, pointer)
        ]
        ends_with_handoff = any(ends_with_pointer(message, pointer) for _, pointer, _, _ in active)
        if missing or not ends_with_handoff:
            names = ", ".join(path.name for path, _, _, _ in (missing or active))
            failures.append(
                f"HANDOFF GATE: {names} was selected for context transfer, but the final "
                "response omitted its explained continuation or placed prose after it."
            )
    if not failures:
        return {}
    required = [
        "\n".join(
            f"{name}: {value}"
            for name, value in zip(BLOCKER_FIELDS, details)
        )
        for _, _, details in blocked
    ]
    if active_transfer:
        required.extend(handoff for _, _, _, handoff in active)
    replacement = "\n\n".join(required)
    repair = (
        "Rewrite the response and end it with this complete handoff block. Nothing may "
        "follow the final pointer:"
        if active_transfer
        else "Rewrite the response with these required blocker lines:"
    )
    return block_once(
        data,
        (
            "\n\n".join(failures)
            + "\n\n"
            + repair
            + "\n\n"
            + replacement
        ),
    )


def block_once(data, reason):
    if data.get("stop_hook_active") or data.get("stopHookActive"):
        return {
            "systemMessage": (
                "Plan handoff repair was already attempted in this turn; allowing the turn to end "
                "to prevent a recursive Stop-hook loop."
            )
        }
    return {"decision": "block", "reason": reason}


def main():
    data = {}
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
        result = evaluate(data)
    except Exception as error:
        result = block_once(data, f"HANDOFF GATE ERROR: validation could not complete: {error}")
    json.dump(result, sys.stdout)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
