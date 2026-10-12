# Stop hook must not make a non-owner reconcile a foreign owner

Status: launched 2026-10-12 as a bounded standards-defect side workstream (standing authorization in
`engineering:session-guidance`) from the coordinating Claude session in `C:\Users\TommySeery\source\repos\career`.

## Defect (observed 2026-10-12)

The coordinating Claude session's shell had drifted into
`tj-agents/dotnet/.worktrees/Feature-ScriptedScaffold` for read-only inspection. That checkout's
`.agents/continuation/owner.json` belongs to a different live process: Codex PID 16108 holds the foreground lease,
with `harness: codex`. The owner had committed after recording `head` (`dd93709` recorded, branch at `618584a`).

The Claude Stop hook blocked the coordinator with:

> Reconcile the canonical continuation owner before ending this turn: owner-head-changed

The only correct actor for that is the owner. A non-owner writing its owner record would be a second writer.

Cause, in `.agents/hooks/continuation_stop.py` `outcome()`, identical on `main` and on PR #209's head `e7df895`:
`runtime.check_identity(owner, …)` raises inside the `try` **before** the early return
`if not obligation and owner.get("foreground") and not foreground_owns_current_process(owner, runtime): return None`.
So any session whose `cwd` sits in a checkout whose live foreground owner is another process gets blocked on that
owner's identity drift.

## Outcome

For a cwd-discovered owner, which on PR #209 means a non-associated one, whose foreground lease is held by
another verified live process, the Stop hook returns no block for the current session, whatever that owner's
identity drift. Every blocking path for the actual owner, an associated controller, an execution obligation or a
supervised launch stays unchanged. A regression test in `.agents/hooks/tests/test_continuation_stop.py` covers
it. Shape the test so it fails on the current ordering and passes after the fix.

## Constraints

- **Stack on PR #209** (`Fix/ControllerGoalAssociation`), which rewrites the same function. This branch starts
  at its head `e7df895d41a2faaab73743f98978b08212a99bc0`. Open the PR with base `Fix/ControllerGoalAssociation`.
  Do not write in #209's branch or checkout. After #209 merges, retarget and reconcile per
  `engineering:git-branching`.
- Do not weaken the owner's own checks. A dead or unverifiable foreground lease must still block as today.
  "Unknown is never foreign."
- Regenerate generated outputs per this repository's `AGENTS.md` and run its required checks, on both hosts'
  payloads where applicable.

## Authorization

The standing standards-defect authorization covers implement, test, open the PR, and merge once this
repository's gates pass. Installing into other scopes, publishing elsewhere and destructive operations stay gated.

## Checkout

- Worktree: `C:\Users\TommySeery\source\repos\tj-agents\core.worktrees\Fix-ForeignForegroundStopOrder`
- Branch: `Fix/ForeignForegroundStopOrder`, from `origin/Fix/ControllerGoalAssociation` `e7df895`, no upstream yet
- PR: not opened. Single writer: the successor launched for this goal.

## Lane

L4: a specified causal fix with a regression test.

## Next Steps

1. Acknowledge pickup under Progress. Read the repository `AGENTS.md`, this goal, PR #209's description, and
   `outcome()`.
2. Write the failing regression test (foreign verified-live foreground plus owner head drift: expect no block),
   then reorder or guard the identity check so it applies only when this session may own the record. Keep
   every existing test green.
3. Run the repository's required checks and regenerate outputs. Review, then open the PR stacked on
   `Fix/ControllerGoalAssociation`. Merge after #209 lands and gates pass.
4. Record the evidence here and close the session per core's completion rule.

## Progress

- 2026-10-12: defect diagnosed by the coordinating session; worktree created; handoff launching.
- 2026-10-12: successor picked up the goal in `Fix/ForeignForegroundStopOrder` at stack parent `e7df895d41a2faaab73743f98978b08212a99bc0`; PR #209 remains open against `main`. Next: add the regression that exposes the Stop-hook ordering defect.
- 2026-10-12: added the verified-foreign-foreground early return before owner identity reconciliation, preserving blocking behavior for missing, stale, reused, and unknown process identities. The first regression failed before the reorder and passed after it. `python -B .agents/hooks/tests/test_continuation_stop.py`, `python -B .agents/hooks/tests/test_continuation_runtime.py`, and `python -B tests/test_harness_manifests.py` passed; the manifest suite ran 16 tests with 3 skips. Regenerated local catalog and host payloads with Windows PowerShell because `pwsh` is unavailable; generated paths remain uncommitted. Native review completed against stack parent `e7df895` without findings. Committed locally.

Next: push this child branch and open its PR against `Fix/ControllerGoalAssociation`.
- 2026-10-12: added the verified-foreign-foreground early return before owner identity reconciliation, preserving blocking behavior for missing, stale, reused, and unknown process identities. The first regression failed before the reorder and passed after it. `python -B .agents/hooks/tests/test_continuation_stop.py`, `python -B .agents/hooks/tests/test_continuation_runtime.py`, and `python -B tests/test_harness_manifests.py` passed; the manifest suite ran 16 tests with 3 skips. Regenerated local catalog and host payloads with Windows PowerShell because `pwsh` is unavailable; generated paths remain uncommitted. Native review completed against stack parent `e7df895` without findings. Committed locally.

Next: push this child branch and open its PR against `Fix/ControllerGoalAssociation`.
- 2026-10-12: successor picked up the goal in `Fix/ForeignForegroundStopOrder` at stack parent `e7df895d41a2faaab73743f98978b08212a99bc0`; PR #209 remains open against `main`. Next: add the regression that exposes the Stop-hook ordering defect.
