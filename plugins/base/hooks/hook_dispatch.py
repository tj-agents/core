"""Run several hook scripts for one host event inside a single interpreter.

Each argument is a script path, absolute or beside this one, optionally followed by
``@<tool matcher>``. The host's sibling-hook merge is reproduced here, so one event costs one
interpreter launch instead of one per gate. Each gate still runs as its own ``__main__`` with its
own stdin, stdout and stderr.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
import re
import runpy
import sys
import traceback


HOOKS = Path(__file__).resolve().parent
DECISIONS = ("deny", "defer", "ask", "allow")
LEGACY_DECISIONS = {"approve": "allow", "block": "deny"}
BLOCKING_EXIT = 2


def exit_status(code) -> tuple[int, str]:
    if code is None:
        return 0, ""
    if isinstance(code, int):
        return code, ""
    return 1, f"{code}\n"


def captured(stream: io.TextIOWrapper) -> str:
    try:
        stream.flush()
        return stream.buffer.getvalue().decode("utf-8", errors="replace")
    except (ValueError, AttributeError):
        return ""


def run_gate(name: str, raw: bytes) -> tuple[int, str, str]:
    script = HOOKS / name if not Path(name).is_absolute() else Path(name)
    stdin = io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8")
    stdout = io.TextIOWrapper(io.BytesIO(), encoding="utf-8", write_through=True)
    stderr = io.TextIOWrapper(io.BytesIO(), encoding="utf-8", write_through=True)
    saved = sys.stdin, sys.stdout, sys.stderr, sys.argv, sys.path[:]
    sys.stdin, sys.stdout, sys.stderr, sys.argv = stdin, stdout, stderr, [str(script)]
    sys.path.insert(0, str(script.parent))
    code, message = 0, ""
    try:
        runpy.run_path(str(script), run_name="__main__")
    except SystemExit as exit:
        code, message = exit_status(exit.code)
    except Exception:
        traceback.print_exc(file=stderr)
        code = 1
    finally:
        sys.stdin, sys.stdout, sys.stderr, sys.argv, sys.path[:] = saved
    return code, captured(stdout), captured(stderr) + message


def parse(stdout: str):
    text = stdout.strip()
    if not text:
        return None
    try:
        value = json.loads(text)
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def merge(event: str, results: list[tuple[str, int, str, str]]) -> tuple[dict, str]:
    decisions: dict[str, list[str]] = {}
    contexts: list[str] = []
    blocks: list[str] = []
    messages: list[str] = []
    stops: list[str] = []
    stopped = False
    suppress = False
    specific: dict = {}
    diagnostics: list[str] = []

    for name, code, stdout, stderr in results:
        data = parse(stdout)
        if stdout.strip() and data is None:
            diagnostics.append(f"{name}: {stdout.strip()}")
        if code == BLOCKING_EXIT:
            reason = stderr.strip() or f"{name} blocked this {event} event."
            if event == "PreToolUse":
                decisions.setdefault("deny", []).append(reason)
            else:
                blocks.append(reason)
        elif stderr.strip():
            diagnostics.append(f"{name}: {stderr.strip()}")
        if data is None:
            continue

        output = data.get("hookSpecificOutput")
        if isinstance(output, dict):
            decision = output.get("permissionDecision")
            if decision in DECISIONS:
                reason = output.get("permissionDecisionReason")
                decisions.setdefault(decision, []).append(reason if isinstance(reason, str) else "")
            context = output.get("additionalContext")
            if isinstance(context, str) and context.strip():
                contexts.append(context.strip())
            for key, value in output.items():
                if key not in ("hookEventName", "permissionDecision", "permissionDecisionReason",
                               "additionalContext"):
                    specific.setdefault(key, value)

        decision = data.get("decision")
        if event == "PreToolUse" and decision in LEGACY_DECISIONS:
            reason = data.get("reason")
            decisions.setdefault(LEGACY_DECISIONS[decision], []).append(
                reason if isinstance(reason, str) else ""
            )
        elif decision == "block":
            reason = data.get("reason")
            blocks.append(reason.strip() if isinstance(reason, str) and reason.strip()
                          else f"{name} blocked this {event} event.")

        message = data.get("systemMessage")
        if isinstance(message, str) and message.strip():
            messages.append(message.strip())
        if data.get("continue") is False:
            stopped = True
            reason = data.get("stopReason")
            if isinstance(reason, str) and reason.strip():
                stops.append(reason.strip())
        if data.get("suppressOutput") is True:
            suppress = True

    merged: dict = {}
    output: dict = {}
    for decision in DECISIONS:
        if decision in decisions:
            output["permissionDecision"] = decision
            reasons = [reason.strip() for reason in decisions[decision] if reason.strip()]
            if reasons:
                output["permissionDecisionReason"] = "\n\n".join(reasons)
            break
    if contexts:
        output["additionalContext"] = "\n\n".join(contexts)
    for key, value in specific.items():
        output.setdefault(key, value)
    if output:
        merged["hookSpecificOutput"] = {"hookEventName": event, **output}
    if blocks:
        merged["decision"] = "block"
        merged["reason"] = "\n\n".join(blocks)
    if messages:
        merged["systemMessage"] = "\n".join(messages)
    if stopped:
        merged["continue"] = False
        if stops:
            merged["stopReason"] = "\n".join(stops)
    if suppress:
        merged["suppressOutput"] = True
    return merged, "\n".join(diagnostics)


def selected(spec: str, tool: str) -> str | None:
    name, separator, matcher = spec.rpartition("@")
    if not separator or not name.endswith(".py"):
        return spec
    if not tool:
        return name
    try:
        return name if re.fullmatch(matcher, tool) else None
    except re.error:
        return name


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("hook-dispatch: name the gate scripts to run.", file=sys.stderr)
        return 1
    raw = sys.stdin.buffer.read()
    try:
        data = json.loads(raw.decode("utf-8-sig")) if raw.strip() else {}
    except (UnicodeError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    event = data.get("hook_event_name") or data.get("hookEventName") or ""
    tool = data.get("tool_name") if isinstance(data.get("tool_name"), str) else ""

    names = [name for name in (selected(spec, tool) for spec in argv[1:]) if name]
    results = [(name, *run_gate(name, raw)) for name in names]
    merged, diagnostics = merge(event, results)
    if diagnostics:
        sys.stderr.write(diagnostics + "\n")
    if merged:
        sys.stdout.write(json.dumps(merged, ensure_ascii=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
