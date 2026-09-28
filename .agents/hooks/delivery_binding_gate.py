r"""PostToolUse hook: opening a PR binds its delivery owner, instead of someone remembering to.

The waste this prevents is the whole babysitting loop. `persistent-delivery` and
`persistent-workflow` already describe a delivery that drives itself from branch to merged, and
`persistent_workflow_merge_gate.py` already refuses an unattended auto-merge that no continuation
owns. Nothing ever *started* one. A PR was opened, the turn ended, and the next transition waited
for a human to notice and say "carry on" - once per CI wait, once per red check, once per review,
once per merge.

So the trigger stops being "the model decided persistent-workflow is relevant" and becomes the PR
existing, exactly as `skill_router.py` made the trigger the path being written. On a successful
`gh pr create` this hook runs `.agents/workflows/workflow_ops.py delivery-bind`, which reads
authoritative forge state once, resolves the repository's recorded standing merge authorization
against the exact head's path set, and writes `.agents/persistent-workflow-binding.json`. Then it
tells the agent - through the PostToolUse stderr channel, which cannot block because the tool has
already run - that the owner is bound and which continuation now owes the wait.

It never widens authority. The binding it writes records `absent` whenever the diff touches a
stop-class path or the PR carries the hold label, and `absent` is what makes
`delivery_runtime.decide()` return its `merge-authorization` human gate. Binding a delivery is not
authorizing a merge; it is naming who is watching.

Opt-in is `.agents/delivery-authorization.json`, the same table the resolver reads: a repo that has
not recorded a standing instruction gets no automatic binding. A present but unreadable table is a
loud stop, never a silent skip - the failure mode this repo cares about is a mechanism that looks
wired and is inert.

Claude only, for the reason `.agents/plugins/manifests/codex/engineering-hooks.json` already records for `red_run_gate.py`:
Codex exposes no tool-result event, so there is nothing for this hook to register on there. Codex
reaches the same binding through the `open-pr` procedure, which names the command.

Contract: exit 0 = say nothing; exit 2 = stderr is fed back to the agent.
"""

import json
import re
import sys
from pathlib import Path

from hook_runtime import (
    CommandTimeout,
    NETWORK_COMMAND_TIMEOUT_SECONDS,
    claim_invocation,
    own_payload_root,
    run_command,
)

# The message is what the agent acts on, and Windows defaults these streams to cp1252.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

CONFIG_FILE = ".agents/delivery-authorization.json"
BINDING_FILE = ".agents/persistent-workflow-binding.json"
HOOK_NAME = "delivery-binding-gate"
SHELL_TOOLS = {"bash", "powershell"}
RESULT_KEYS = ("tool_response", "tool_result", "tool_output")

# `gh pr create`, in any flag order, and not `gh pr create --help` or a `gh pr view`.
_PR_CREATE = re.compile(r"\bgh\s+pr\s+create\b")
_HELP = re.compile(r"(?:^|\s)(?:--help|-h)(?:\s|$)")
_PR_URL = re.compile(r"https://github\.com/[^/\s]+/[^/\s]+/pull/(\d+)")


def announce(message):
    sys.stderr.write(message)
    sys.exit(2)


def tool_output(data):
    for key in RESULT_KEYS:
        value = data.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            for inner in ("stdout", "output", "content", "result"):
                candidate = value.get(inner)
                if isinstance(candidate, str):
                    return candidate
            return json.dumps(value)
    return ""


def created_pr(data):
    """The PR number `gh pr create` printed, or None when it printed no PR URL.

    A failed create prints no URL, so absence is the whole success test - this hook never re-reads
    the forge to find out whether the command it just watched worked.
    """
    match = _PR_URL.search(tool_output(data))
    return match.group(1) if match else None


def working_directory(data):
    for key in ("cwd", "working_directory", "workdir"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value
    tool_input = data.get("tool_input") or {}
    for key in ("cwd", "working_directory", "workdir"):
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return "."


def find_config(cwd):
    """The opted-in repo root at or above `cwd`, or None. Walking up rather than asking git keeps a
    worktree, a submodule and a plain checkout on the same answer, as the merge gates do."""
    try:
        base = Path(cwd).resolve()
    except OSError:
        return None
    for candidate in (base, *base.parents):
        if (candidate / CONFIG_FILE).is_file():
            return candidate
    return None


def existing_owner(root):
    """The PR number this worktree's binding already owns, or None when it holds no readable one.

    An unreadable binding counts as none: `delivery-bind` overwrites it, which is the recovery.
    """
    try:
        parsed = json.loads((root / BINDING_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    owner = str(parsed.get("pr", "")).strip() if isinstance(parsed, dict) else ""
    return owner or None


def workflow_ops(root):
    """The operations module beside this hook when it runs from a plugin payload, and the repo's own
    otherwise. A vendored copy and an installed plugin must reach the same code."""
    beside = own_payload_root(__file__) / "workflows" / "workflow_ops.py"
    if beside.is_file():
        return beside
    return root / ".agents" / "workflows" / "workflow_ops.py"


def bind(root, pr):
    try:
        completed = run_command(
            [
                sys.executable,
                "-B",
                str(workflow_ops(root)),
                "--root",
                str(root),
                "--workflow-run-id",
                f"delivery-bind-pr-{pr}",
                "delivery-bind",
                "--pr",
                str(pr),
            ],
            capture_output=True,
            text=True,
            cwd=str(root),
            timeout=NETWORK_COMMAND_TIMEOUT_SECONDS,
        )
    except CommandTimeout as error:
        return None, str(error)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()[:800]
        return None, detail or f"delivery-bind exited {completed.returncode}"
    try:
        return json.loads(completed.stdout.strip().splitlines()[-1]), None
    except (ValueError, IndexError):
        return None, "delivery-bind produced no readable result"


def authorization_line(resolution):
    stopped = resolution.get("stopped_by")
    if stopped is None:
        return (
            "Merge authorization: AUTO, from this repository's recorded standing instruction. Once "
            "the exact head is green and independently reviewed, the continuation may enqueue it "
            "without asking."
        )
    if stopped.get("class") == "hold-label":
        return (
            "Merge authorization: ABSENT - this PR carries the `"
            + str(stopped.get("label"))
            + "` hold label, so it stops at its merge gate whatever it touches."
        )
    if stopped.get("class") == "no-recorded-authorization":
        return (
            "Merge authorization: ABSENT - this repository records no standing instruction, so the "
            "delivery stops at its merge gate and asks."
        )
    where = (
        "this repository's own always-stop list"
        if stopped.get("class") == "repository-declared"
        else "the `" + str(stopped.get("class")) + "` class"
    )
    return (
        "Merge authorization: ABSENT - `"
        + str(stopped.get("path"))
        + "` matches "
        + where
        + ", which the standing instruction always stops. Drive it to green and reviewed, then ask "
        "for this one."
    )


def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    if not isinstance(data, dict):
        return 0
    if str(data.get("tool_name", "")).lower() not in SHELL_TOOLS:
        return 0
    command = (data.get("tool_input") or {}).get("command", "")
    if not isinstance(command, str) or not _PR_CREATE.search(command) or _HELP.search(command):
        return 0
    pr = created_pr(data)
    if pr is None:
        return 0

    root = find_config(working_directory(data))
    if root is None:
        return 0  # repo records no standing instruction — not this hook's business
    if not claim_invocation(data, HOOK_NAME):
        return 0

    held = existing_owner(root)
    if held is not None:
        if held == pr:
            return 0  # this same delivery already has its owner; delivery-bind is the only rebinder
        announce(
            "DELIVERY BINDING GATE: PR #"
            + pr
            + " was opened but this worktree still owns PR #"
            + held
            + " through " + BINDING_FILE + ", so the new PR has nothing watching it. That binding "
            "should have been removed at its terminal. Resolve PR #" + held + " or run `python "
            ".agents/workflows/workflow_ops.py --workflow-run-id delivery-release delivery-release "
            "--reason <terminal>`, then bind PR #" + pr + "."
        )

    result, failure = bind(root, pr)
    if failure is not None:
        announce(
            "DELIVERY BINDING GATE: PR #"
            + pr
            + " was opened but its delivery owner could not be bound ("
            + failure
            + "). Run `python .agents/workflows/workflow_ops.py --workflow-run-id "
            "delivery-bind-pr-" + pr + " delivery-bind --pr " + pr + "` and read the error, or "
            "enter the persistent-workflow skill and bind it by hand. Do not leave this PR with no "
            "continuation owning its wait."
        )

    binding = result.get("binding", {})
    resolution = result.get("authorization_resolution", {})
    announce(
        "DELIVERY BINDING GATE: PR #"
        + pr
        + " now has a delivery owner. "
        + BINDING_FILE
        + " binds head "
        + str(binding.get("head", ""))[:12]
        + " in "
        + str(binding.get("worktree", ""))
        + ".\n"
        + authorization_line(resolution)
        + "\nEnter the persistent-workflow skill now and give this binding a continuation that "
        "owns the wait — do not end the turn with the PR unowned. The continuation drives exact-head "
        "CI, dispatches one fresh debugging context per failure, obtains independent current-head "
        "review, and stops at whichever terminal the binding records. Release it with "
        "`workflow_ops.py delivery-release --reason <terminal>` when the delivery ends."
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001 - a broken gate must never wedge a session
        sys.exit(0)
