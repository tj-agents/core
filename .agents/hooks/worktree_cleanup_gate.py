import json
import os
import subprocess
import sys
from pathlib import Path

from hook_runtime import claim_invocation


CONFIG_FILE = ".agents/worktree-cleanup-gate.json"
HOOK_NAME = "worktree-cleanup-gate"
VIOLATION_STATES = ("MERGED_NOT_IN_MAIN", "ORPHAN_FOLDER")
AUDIT_TIMEOUT_SECONDS = int(os.environ.get("WORKTREE_CLEANUP_GATE_TIMEOUT_SECONDS", "10"))


def find_config(cwd):
    try:
        base = Path(cwd).resolve()
    except OSError:
        return None
    for candidate in (base, *base.parents):
        path = candidate / CONFIG_FILE
        if path.is_file():
            return path
    return None


def audit_command(config_path):
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"{CONFIG_FILE} could not be read: {error}") from error
    command = config.get("audit_command") if isinstance(config, dict) else None
    if not isinstance(command, list) or not command or not all(
        isinstance(part, str) and part for part in command
    ):
        raise ValueError(f"{CONFIG_FILE} `audit_command` must be a non-empty string list.")
    return command


def run_audit(command, cwd):
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=AUDIT_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None
    except OSError as error:
        raise RuntimeError(str(error)) from error
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(detail or f"audit exited {result.returncode}")
    return result.stdout


def violations(output):
    return [
        line.strip()
        for line in output.splitlines()
        if any(state in line for state in VIOLATION_STATES)
    ]


def block(reason):
    json.dump({"decision": "block", "reason": reason}, sys.stdout)
    sys.stdout.write("\n")


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(data, dict):
        return 0
    event = data.get("hook_event_name") or data.get("hookEventName")
    if event not in {"Stop", "SessionStart"}:
        return 0
    if data.get("stop_hook_active") or data.get("stopHookActive"):
        return 0
    config_path = find_config(data.get("cwd") or ".")
    if config_path is None:
        return 0
    if not claim_invocation(data, HOOK_NAME):
        return 0
    try:
        output = run_audit(audit_command(config_path), config_path.parent.parent)
    except (ValueError, RuntimeError) as error:
        block(f"WORKTREE CLEANUP GATE: cannot run the configured audit: {error}")
        return 0
    if output is None:
        sys.stderr.write(
            f"WORKTREE CLEANUP GATE: the audit did not finish within {AUDIT_TIMEOUT_SECONDS}s; "
            "skipping this check rather than blocking on a slow environment.\n"
        )
        return 0
    found = violations(output)
    if found:
        block(
            "WORKTREE CLEANUP GATE: the repository audit found worktrees that need human cleanup. "
            "Run its `close` or `retire` command after inspecting them; it never deletes automatically.\n"
            + "\n".join(found)
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
