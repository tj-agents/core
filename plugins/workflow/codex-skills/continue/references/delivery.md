# Unattended software delivery

Owns keeping one PR moving across wakes after the user asked for unattended progress. `workflow:run` owns
the goal and its completion; Engineering owns review, CI and merge checks. Act only within the goal's
authority: merging, publishing or deploying beyond it needs the user.

## One binding

Bind exactly one PR: repository, PR number, absolute worktree and branch, full head SHA, and the pending
check and run IDs. A head this owner pushes replaces the binding. A head, PR or worktree changed by anyone
else ends ownership and goes to the user; never follow it. Reject any observation from another head.

## Each wake

Keep one background monitor per binding. It reads forge state and wakes the owner only for a material
transition or terminal result; an unchanged state produces no report, mutation or new continuation.
Run `workflows/workflow_ops.py` from the installed Workflow package, or `.agents/workflows/workflow_ops.py`
in a Core checkout, with `python3` on Linux/macOS:

```text
python -B workflows/workflow_ops.py --root ROOT --workflow-run-id ID monitor --kind pr --id NUMBER --head SHA
```

- **Exact-head failure:** dispatch one fresh native subagent with the repository, PR, branch, full SHA,
  failing check and run IDs and the failure signature. It reads the remote log first, reproduces only the
  failing scope and returns repair evidence; it does not monitor, widen scope or merge. The owner
  validates the repair, pushes it and rebinds the same monitor to the new head.
- **Green head:** review under `engineering:review`, then merge through `engineering:merge`.
- **Required human approval pending:** stay waiting with the binding intact and report the approval link
  once; do not ask the user to announce it.
- **Terminal** (merged, closed, superseded, external head, genuine user decision): stop and remove the host
  task and record the final PR, head, result and next decision in the goal. A merged PR returns to
  `workflow:run`; it is not completion.

## Codex CLI transport

To keep delivering after the Codex CLI process exits, follow `.codex/runtime/continuation/README.md` in the
installed Workflow package (the same path in a Core checkout).
