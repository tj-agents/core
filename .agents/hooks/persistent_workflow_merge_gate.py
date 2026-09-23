r"""PreToolUse hook: no `gh pr merge --auto` on a not-yet-settled PR without a bound continuation.

The waste this prevents: an agent enables auto-merge on a PR whose CI or merge
queue has **not** reached a terminal state, then the turn ends. Nothing is left
watching. GitHub silently drops the PR from the queue on a conflict (``merging``
skill state 3) or never re-evaluates a glitchy auto-merge (state 4), and the
delivery stalls for hours looking exactly like "still waiting". The ``merging``
skill already says: when a queue or check resolves after this turn, enter
``persistent-workflow`` so one native continuation owns the wait. That was prose.

This gate makes it enforced. It fires only on a command that **enables**
auto-merge (``gh pr merge ... --auto``). It allows the enqueue when:

* the PR is already terminal — ``mergeStateStatus`` is ``CLEAN`` and every check
  has finished — so ``--auto`` merges within the turn and no continuation is
  owed; or
* a persistent-workflow binding artifact
  (``.agents/persistent-workflow-binding.json``) exists in the merge's checkout
  and its ``repo`` / ``pr`` / ``head`` / ``worktree`` match the PR and head being
  enqueued. That file is what ``persistent-workflow`` writes when it binds a
  continuation, updates on every rebind, and deletes on a terminal.

It blocks — fails CLOSED, like ``merge_review_gate.py`` — a ``--auto`` enqueue of
a non-terminal PR with no matching binding, and on any state it cannot resolve.
A wrong guess here delays one enqueue by one turn; the failure it prevents costs
hours.

Scope mirrors ``merge_review_gate.py``: it reuses that module's command parsing
and checkout resolution, speaks only for a repo carrying
``.agents/persistent-workflow-gate.json``, and judges the checkout the merge
actually runs in. ``--disable-auto`` and every non-``--auto`` merge form are not
its business (the review gate covers those). It is wired for Claude only —
``SHELL_TOOLS`` is ``{bash, powershell}`` — for the same reason the review gate
is: it fails closed, and Codex's shell tool name is not yet observed in a real
hook payload, so a wrong Codex registration would block a legitimate merge.

Contract: exit 0 = allow; exit 2 = block (stderr is fed back to the agent).
"""

import json
import sys
from pathlib import Path

from hook_runtime import NETWORK_COMMAND_TIMEOUT_SECONDS, claim_invocation, run_command
from merge_review_gate import (
    canonical_merge_target_dir,
    invokes_pushd_before_merge,
    is_codex_invocation,
    is_merge_enable,
    invokes_merge,
    merge_target_dir,
    normalize_slug,
    pr_number,
    repo_flag,
)

# This message is what the agent acts on, and Windows defaults these streams to cp1252.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

CONFIG_FILE = ".agents/persistent-workflow-gate.json"
BINDING_FILE = ".agents/persistent-workflow-binding.json"
HOOK_NAME = "persistent-workflow-merge-gate"

# Lowercased, and the hook's whole vocabulary. Claude only, deliberately: this gate fails CLOSED, so
# a matcher naming a shell the script cannot parse a command out of would block a real merge. Codex's
# shell tool name is not established, exactly as for merge_review_gate.py.
SHELL_TOOLS = {"bash", "powershell"}

_GIT_CWD = ["."]

# A check is not yet settled while its run has not completed; a legacy commit-status is not settled
# while it is pending or merely expected.
_PENDING_CHECK_STATUSES = {"queued", "in_progress", "pending", "waiting", "requested", ""}
_PENDING_STATUS_STATES = {"pending", "expected", ""}
# Only this one merge-state means "GitHub will merge this now". Every other value — a pending queue,
# a behind branch, a blocking review, an unknown — means the enqueue is a walk-away.
_SETTLED_MERGE_STATE = "clean"


def block(reason):
    sys.stderr.write(reason)
    sys.exit(2)


def enables_auto(command):
    """True only when the command turns auto-merge ON.

    ``--auto`` is a substring of ``--disable-auto``; strip the disable form first so a pure
    ``--disable-auto`` (the safe direction, the review gate's concern, not this one) is not read as
    an enable. The documented ``--disable-auto && ... --auto`` re-assert compound still counts.
    """
    if not invokes_merge(command) or not is_merge_enable(command):
        return False
    return "--auto" in command.replace("--disable-auto", " ")


def find_config(cwd):
    """The opted-in repo root at or above ``cwd``, or ``None``. Walk up rather than ask git so a
    worktree, a submodule and a plain checkout give the same answer (as ``merge_review_gate``)."""
    try:
        base = Path(cwd).resolve()
    except OSError:
        return None
    for candidate in (base, *base.parents):
        if (candidate / CONFIG_FILE).is_file():
            return candidate / CONFIG_FILE
    return None


def gh_json(*args):
    """Run ``gh`` where the merge runs, never where the hook process happens to sit."""
    return run_command(
        ["gh", *args], capture_output=True, text=True, check=True, cwd=_GIT_CWD[0],
        timeout=NETWORK_COMMAND_TIMEOUT_SECONDS,
    ).stdout.strip()


def pr_state(target):
    """``(number, head_oid, is_terminal)`` for the PR the merge names, or the current branch's PR
    when it names none. Raises on any unresolvable piece so the caller fails closed."""
    args = ["pr", "view"]
    if target:
        args.append(target)
    args += ["--json", "number,headRefOid,mergeStateStatus,statusCheckRollup"]
    parsed = json.loads(gh_json(*args))
    number = parsed.get("number")
    head = parsed.get("headRefOid")
    if not isinstance(number, int) or not isinstance(head, str) or not head:
        raise ValueError("gh pr view returned no number/headRefOid")
    return str(number), head, pr_is_terminal(parsed)


def pr_is_terminal(parsed):
    """The PR will merge within this turn: merge-state settled AND no check still running.

    Anything else — a pending queue entry, a behind branch, a blocking gate, an unreadable rollup —
    is a walk-away and needs a bound continuation.
    """
    if str(parsed.get("mergeStateStatus", "")).strip().lower() != _SETTLED_MERGE_STATE:
        return False
    rollup = parsed.get("statusCheckRollup")
    if not isinstance(rollup, list):
        return False
    for check in rollup:
        if not isinstance(check, dict):
            return False
        # CheckRun carries `status`/`conclusion`; a legacy StatusContext carries `state`.
        if "status" in check or "conclusion" in check:
            if str(check.get("status", "")).strip().lower() in _PENDING_CHECK_STATUSES:
                return False
        else:
            if str(check.get("state", "")).strip().lower() in _PENDING_STATUS_STATES:
                return False
    return True


def read_binding(config_root):
    """The parsed binding artifact beside the gate config, or ``None`` when it is absent or unreadable
    (unreadable is treated as absent — the block message tells the agent to write it)."""
    path = config_root / BINDING_FILE
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def binding_mismatch(binding, *, repo, pr, head, config_root):
    """A human-readable reason the binding does not cover this exact enqueue, or ``None`` when it
    does. ``repo`` may be ``None`` when this checkout's origin is unreadable — then it is not checked."""
    bound_pr = str(binding.get("pr", "")).strip()
    if bound_pr != str(pr):
        return f"is bound to PR #{bound_pr or '?'}, not #{pr}"
    bound_head = str(binding.get("head", "")).strip().lower()
    if not bound_head:
        return "records no head SHA"
    if not (head.lower().startswith(bound_head) or bound_head.startswith(head.lower())):
        return f"is bound to head {bound_head[:12]}, but PR #{pr} is at {head[:12]}"
    if repo is not None:
        bound_repo = normalize_slug(str(binding.get("repo", "")))
        if bound_repo is not None and bound_repo != repo:
            return f"is bound to repository {bound_repo}, not {repo}"
    bound_worktree = binding.get("worktree")
    if isinstance(bound_worktree, str) and bound_worktree.strip():
        try:
            same = Path(bound_worktree).resolve() == config_root.resolve()
        except OSError:
            same = False
        if not same:
            return f"is bound to worktree {bound_worktree}, not this checkout"
    return None


def local_repo_slug():
    try:
        url = run_command(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, check=True, cwd=_GIT_CWD[0],
        ).stdout.strip()
    except Exception:  # noqa: BLE001 - no origin / broken remote; the caller does not check repo then
        return None
    return normalize_slug(url)


def resolve_target_dir(command, data):
    """The checkout the merge runs in, mirroring ``merge_review_gate`` exactly.

    Returns the directory, or blocks when a Codex payload or a Claude ``pushd`` form cannot prove one.
    """
    canonical_target = canonical_merge_target_dir(command)
    if is_codex_invocation(data):
        if canonical_target is None:
            if not claim_invocation(data, HOOK_NAME):
                sys.exit(0)
            block(
                "AUTO-MERGE GATE: Codex cannot prove this merge's checkout because hooks do not "
                "receive an exec_command workdir. Use exactly `pushd \"<absolute-checkout>\" && gh "
                "pr merge <number> [--merge|--squash|--rebase] --auto`, with no additional shell "
                "commands, then retry."
            )
        return canonical_target
    if canonical_target is not None:
        return canonical_target
    if invokes_pushd_before_merge(command):
        if not claim_invocation(data, HOOK_NAME):
            sys.exit(0)
        block(
            "AUTO-MERGE GATE: Claude cannot prove this merge's pushd checkout. Use exactly `pushd "
            "\"<absolute-checkout>\" && gh pr merge <number> [--merge|--squash|--rebase] --auto`, "
            "with no additional shell commands, then retry."
        )
    return merge_target_dir(command, data)


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)  # not our JSON — don't interfere

    if str(data.get("tool_name", "")).lower() not in SHELL_TOOLS:
        sys.exit(0)

    command = (data.get("tool_input") or {}).get("command", "")
    if not isinstance(command, str) or not enables_auto(command):
        sys.exit(0)

    _GIT_CWD[0] = resolve_target_dir(command, data)

    config_path = find_config(_GIT_CWD[0])
    if config_path is None:
        sys.exit(0)  # repo did not opt in — not this gate's business
    config_root = config_path.parent.parent  # <root>/.agents/<file> -> <root>
    if not claim_invocation(data, HOOK_NAME):
        sys.exit(0)

    named = repo_flag(command)
    local = local_repo_slug()
    if named is not None and local is not None and named != local:
        sys.exit(0)  # names another repository — its own auto-merge is not gated here

    try:
        number, head, terminal = pr_state(pr_number(command))
    except Exception as exc:  # noqa: BLE001 - a merge with an unresolvable state must not slip through
        block(
            "AUTO-MERGE GATE: cannot resolve the PR's checks / merge-queue state (" + str(exc) + "). "
            "Refusing to enable auto-merge until the state is known, or enter the persistent-workflow "
            "skill to bind a continuation."
        )

    if terminal:
        sys.exit(0)  # CLEAN and every check finished — `--auto` merges this turn, nothing to own

    binding = read_binding(config_root)
    if binding is None:
        block(
            "AUTO-MERGE GATE: PR #" + number + " is being enqueued with --auto but its checks / "
            "merge queue have not settled, and no persistent-workflow binding exists at "
            + BINDING_FILE + ". Enter the persistent-workflow skill to bind this PR/head/worktree to "
            "one native continuation that owns the wait, or drop --auto and merge once the checks "
            "finish."
        )

    reason = binding_mismatch(
        binding, repo=local, pr=number, head=head, config_root=config_root
    )
    if reason is not None:
        block(
            "AUTO-MERGE GATE: " + BINDING_FILE + " " + reason + ". Re-bind the persistent-workflow "
            "continuation to PR #" + number + " at " + head[:12] + " before enabling auto-merge."
        )

    sys.exit(0)  # a matching continuation owns this wait → allow the enqueue


if __name__ == "__main__":
    main()
