import json
import re
import sys

from forge_poll_gate import ConfigUnusable, extract_command, find_config
from hook_runtime import claim_invocation


HOOK_NAME = "compact-output-gate"
DEFAULT_PATTERNS = (
    re.compile(r"\bdotnet\s+(?:test|build)\b", re.IGNORECASE),
    re.compile(r"\bdotnet\s+ef\s+database\s+update\b", re.IGNORECASE),
    re.compile(r"\b(?:npm|pnpm|yarn)\s+(?:run\s+)?(?:test|build|check)\b", re.IGNORECASE),
    re.compile(r"\b(?:pytest|python(?:3)?\s+-m\s+(?:pytest|unittest))\b", re.IGNORECASE),
    re.compile(r"\bsync-generated\.ps1\b", re.IGNORECASE),
    re.compile(r"\bgh\s+run\s+view\b.*--log(?:-failed)?\b", re.IGNORECASE),
)
WRAPPER = re.compile(
    r"^\s*(?:python(?:3)?(?:\s+-B)?\s+)?\"?(?:\.[\\/])?\.agents[\\/]workflows[\\/]workflow_ops\.py\"?(?=\s).*\brun\b.*\s--\s",
    re.IGNORECASE | re.DOTALL,
)
SHELL_CONTROL = re.compile(r"[;&`\r\n]|\||\$\(|[<>]\s*\(", re.DOTALL)


def configured_patterns(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ConfigUnusable(f"{path.name} exists but could not be read: {error}") from error
    entries = value.get("compact_output_patterns", [])
    if not isinstance(entries, list):
        raise ConfigUnusable(f"{path.name} `compact_output_patterns` must be a list")
    try:
        return (*DEFAULT_PATTERNS, *(re.compile(entry, re.IGNORECASE) for entry in entries))
    except (TypeError, re.error) as error:
        raise ConfigUnusable(f"{path.name} has an invalid compact-output pattern: {error}") from error


def requires_capture(command, patterns):
    wrapped = WRAPPER.search(command) and not SHELL_CONTROL.search(command)
    return not wrapped and any(pattern.search(command) for pattern in patterns)


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    command = extract_command(data.get("tool_name", ""), data.get("tool_input") or {})
    if not command:
        return 0
    config = find_config(data.get("cwd") or data.get("workdir") or ".")
    if config is None:
        return 0
    try:
        patterns = configured_patterns(config)
    except ConfigUnusable as error:
        sys.stderr.write(f"COMPACT OUTPUT GATE: {error}")
        return 2
    if not requires_capture(command, patterns):
        return 0
    if not claim_invocation(data, HOOK_NAME):
        return 0
    sys.stderr.write(
        "COMPACT OUTPUT GATE: validation and forge logs must run through "
        "`.agents/workflows/workflow_ops.py --workflow-run-id <id> run --label <label> -- <command>`. "
        "The helper stores full output under Git-private workflow artifacts and returns bounded JSON."
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
