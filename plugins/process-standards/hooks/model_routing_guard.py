r"""Reject literal model selection where delegation must use the routing policy."""

import json
import re
import subprocess
import sys
from pathlib import Path

from hook_runtime import claim_invocation


MODEL_SLUG = re.compile(r"(?i)\b(?:" + "gpt" + r"|" + "claude" + r")-[a-z0-9][a-z0-9._-]*\b")
ROUTING_FLAG = re.compile(
    r"(?i)(?<![\w-])(?:--model|-model|--effort|-reasoningeffort)\s+(?:['\"])?([^\s'\"]+)"
)
DELEGATION_TEXT = re.compile(
    r"(?i)\b(?:dispatch|subagent|spawn_agent|launch-(?:claude|codex))\b|\bAgent\s*\("
)
CLAUDE_AGENT_CALL = re.compile(r"(?is)\bAgent\s*\(\s*\{(?P<body>.*?)\}\s*\)")
CODEX_AGENT_CALL = re.compile(r"(?is)\bspawn_agent\s*\(\s*\{(?P<body>.*?)\}\s*\)")
WORKFLOW_AGENT_CALL = re.compile(r"(?is)(?<![A-Za-z])agent\s*\([^,]+,\s*\{(?P<body>.*?)\}\s*\)")
WRITE_TOOLS = {
    "write",
    "edit",
    "multiedit",
    "notebookedit",
    "apply_patch",
    "edit_file",
    "write_file",
    "multi_edit",
}
SHELL_TOOLS = {"bash", "powershell", "exec_command", "unified_exec", "local_shell"}
PATH_KEYS = ("file_path", "notebook_path", "path", "filepath")
CONTENT_KEYS = ("content", "new_string", "new_source", "patch")


def is_resolved_reference(value):
    return value.startswith(("$", "<", "{", "[", "`"))


def violations(text, include_slugs=True):
    found = []
    if include_slugs:
        found.extend((match.start(), "literal model slug") for match in MODEL_SLUG.finditer(text))
    for match in ROUTING_FLAG.finditer(text):
        if not is_resolved_reference(match.group(1)):
            found.append((match.start(), "literal routing argument"))
    return sorted(found)


def has_assignment(text, name):
    return re.search(rf"(?i)(?:['\"]?{re.escape(name)}['\"]?)\s*[:=]", text) is not None


def delegation_call_violations(text):
    found = []
    for pattern, required in (
        (CLAUDE_AGENT_CALL, ("model",)),
        (CODEX_AGENT_CALL, ("model", "reasoning_effort")),
        (WORKFLOW_AGENT_CALL, ("model", "effort")),
    ):
        for match in pattern.finditer(text):
            for field in required:
                if not has_assignment(match.group("body"), field):
                    found.append((match.start(), f"delegation omits {field}"))
    return found


def skill_route_violations(text):
    if not DELEGATION_TEXT.search(text):
        return []
    front_matter = re.match(r"(?s)\A---\s*\n(.*?)\n---", text)
    if front_matter and re.search(r"(?m)^route:\s*\S", front_matter.group(1)):
        return []
    return [(0, "delegating skill omits route declaration")]


def guarded_path(path):
    normalized = str(path).replace("\\", "/").lower()
    name = Path(normalized).name
    if name == "skill.md" or "/scripts/" in normalized:
        return True
    if "/workflows/" in normalized and Path(normalized).suffix in {
        ".md",
        ".py",
        ".ps1",
        ".sh",
        ".yml",
        ".yaml",
    }:
        return True
    return False


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def written_paths(tool_input):
    paths = []
    for key in PATH_KEYS:
        value = tool_input.get(key)
        if isinstance(value, str):
            paths.append(value)
    patch = tool_input.get("patch")
    if isinstance(patch, str):
        paths.extend(
            match.group(1).strip()
            for match in re.finditer(r"^\*\*\* (?:Add|Update) File: (.+)$", patch, re.MULTILINE)
        )
    return paths


def written_content(tool_input):
    parts = [tool_input.get(key) for key in CONTENT_KEYS]
    parts.extend(strings(tool_input.get("edits") or []))
    return "\n".join(part for part in parts if isinstance(part, str))


def scan_repository(root):
    completed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=True,
        capture_output=True,
        text=True,
    )
    failures = []
    for relative in (entry for entry in completed.stdout.split("\0") if entry):
        if not guarded_path(relative):
            continue
        path = root / relative
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        findings = violations(content) + delegation_call_violations(content)
        if Path(relative).name.lower() == "skill.md":
            findings += skill_route_violations(content)
        for offset, reason in sorted(findings):
            line = content.count("\n", 0, offset) + 1
            failures.append((relative.replace("\\", "/"), line, reason))
    return failures


def check_mode(arguments):
    root = Path(arguments[0] if arguments else ".").resolve()
    try:
        failures = scan_repository(root)
    except (OSError, subprocess.SubprocessError) as error:
        print(f"model routing guard could not scan {root}: {error}", file=sys.stderr)
        return 2
    for relative, line, reason in failures:
        print(f"{relative}:{line}: {reason}; resolve routing and pass returned values", file=sys.stderr)
    return 2 if failures else 0


def hook_mode():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    tool_name = str(data.get("tool_name") or "").lower()
    tool_input = data.get("tool_input") or {}
    normalized_tool = tool_name.rsplit(".", 1)[-1]
    if tool_name in WRITE_TOOLS:
        paths = written_paths(tool_input)
        if not any(guarded_path(path) for path in paths):
            return 0
        content = written_content(tool_input)
        hits = violations(content) + delegation_call_violations(content)
        if any(Path(path).name.lower() == "skill.md" for path in paths):
            hits += skill_route_violations(content)
    elif tool_name in SHELL_TOOLS:
        command = tool_input.get("command") or tool_input.get("cmd") or ""
        hits = violations(command, include_slugs=False) if isinstance(command, str) else []
    elif normalized_tool in {"agent", "spawn_agent"}:
        hits = []
        model = tool_input.get("model")
        if not isinstance(model, str) or not model.strip() or model == "inherit":
            hits.append((0, "delegation omits routed model"))
        if normalized_tool == "spawn_agent":
            effort = tool_input.get("reasoning_effort")
            if not isinstance(effort, str) or not effort.strip():
                hits.append((0, "delegation omits routed effort"))
    else:
        return 0
    if not hits or not claim_invocation(data, "model-routing-guard"):
        return 0
    sys.stderr.write(
        "MODEL ROUTING GUARD - blocked an unrouted model or effort selection.\n\n"
        "Resolve this delegated task through ~/.claude/routing/route.py and pass the returned values. "
        "The policy is the only place that maps lanes to models.\n"
    )
    return 2


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        return check_mode(sys.argv[2:])
    return hook_mode()


if __name__ == "__main__":
    raise SystemExit(main())
