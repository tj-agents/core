import io
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path

from hook_runtime import claim_invocation, declared_plugin_root


IMPLEMENTATION = ".agents/hooks/plan_handoff_stop.py"
TRUSTED_FILES = (
    ".agents/hooks/plan_handoff_stop_launcher.py",
    IMPLEMENTATION,
    ".agents/hooks/plan_graph.py",
)


def blob_oid(root, implementation=IMPLEMENTATION, revision=None):
    target = f"{revision}:{implementation}" if revision else str(root / implementation)
    command = ["git", "-C", str(root), "rev-parse", target] if revision else [
        "git",
        "-C",
        str(root),
        "hash-object",
        target,
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def implementation_is_current(root):
    return all(
        (checked_out := blob_oid(root, implementation))
        and (origin_main := blob_oid(root, implementation, "origin/main"))
        and checked_out == origin_main
        for implementation in TRUSTED_FILES
    )


def block_once(data, reason):
    if data.get("stop_hook_active") or data.get("stopHookActive"):
        return {
            "systemMessage": (
                "Plan handoff hook repair was already attempted in this turn; allowing the turn "
                "to end to prevent a recursive Stop-hook loop."
            )
        }
    return {"decision": "block", "reason": reason}


def plugin_delivered():
    """True when this copy came from an installed plugin rather than a repo's vendored copy.

    The currency check below asks whether a repo's checkout still matches its origin/main. A
    plugin has no such repo above it, so the check can only ever fail - which would block every
    turn. Under plugin delivery the plugin IS the author, so there is nothing to verify.
    """
    return declared_plugin_root(__file__) is not None


def main():
    raw = sys.stdin.buffer.read()
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except Exception:
        data = {}
    if not claim_invocation(data, "plan-handoff-gate"):
        return
    sys.stdin = io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8")
    if plugin_delivered():
        runpy.run_path(str(Path(__file__).resolve().parent / "plan_handoff_stop.py"), run_name="__main__")
        return
    root = Path(__file__).resolve().parents[2]
    if not implementation_is_current(root):
        try:
            data = json.loads(raw.decode("utf-8-sig"))
        except Exception:
            data = {}
        result = block_once(
            data,
            (
                "HANDOFF GATE ERROR: this checkout's plan handoff hook bundle differs from "
                "origin/main. Sync this branch with current main before relying on plan handoffs."
            ),
        )
        json.dump(result, sys.stdout)
        sys.stdout.write("\n")
        return
    runpy.run_path(str(root / IMPLEMENTATION), run_name="__main__")


if __name__ == "__main__":
    main()
