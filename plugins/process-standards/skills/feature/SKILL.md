---
name: feature
description: Implement an explicitly requested new or changed behavior from discovery through review, validation, and commit when no active plan owns the work. Use for feature requests and behavior changes; do not use for defect repair, planning-only requests, execution of an existing plan, or review-only requests.
domain: process
---

# Deliver a feature

Own an unplanned feature from the user's request to a completed repository outcome. If an explicit or
uniquely resolved active plan already owns the work, use that plan's execution workflow instead. A direct
question or report request is not implementation authority.

## Resolve the path

Read the repository's branch/worktree guidance and the standards owed by the paths likely to change. Interpret
the requirement, success conditions, scope, and any material ambiguity from repository evidence before
editing.

Use the short path when ownership is obvious, one coherent implementation follows existing patterns, and
focused validation can prove it. The short path creates no plan, ledger, workflow sidecar, or automatic
checkpoint. Do the discovery directly; dispatch at most one bounded independent read only when it adds real
evidence.

Promote before recovery becomes fragile when the work grows across phases, delivery worktrees, external
gates, or context/restart boundaries. Resolve and validate Workflow v2 repository state, then follow
[`plans`](../plans/SKILL.md) to create the durable plan and ledger and checkpoint them under
[`plan-checkpoint`](../plan-checkpoint/SKILL.md). A Kandev-managed task may own the outer worktree and host
session, but its identifiers are not workflow state. Continue under the plan's owner while the original
implementation authority still covers the work.
Promotion changes persistence, not the requested outcome.

## Execute the lifecycle

1. Discover repository ownership, applicable standards, analogous implementations, dependencies, and test
   impact. Parallelize only independent bounded reads.
2. Keep requirement interpretation, architecture, public contracts, data/security/migration implications,
   validation sufficiency, and final judgment with the parent.
3. Implement directly. A `mechanical-worker` may receive only a disjoint transformation under an exclusive
   writer lease; all writes remain serialized and the parent reconciles the reported paths against Git.
4. Run the focused checks that prove the implementation coherent, then apply
   [`committing`](../committing/SKILL.md) so branch-diff review has an immutable candidate.
5. Run the repository's focused independent [`review`](../review/SKILL.md). Because this lifecycle includes
   implementation, resolve actionable findings through [`address-review`](../address-review/SKILL.md), commit
   those fixes, and recheck only the resulting delta through
   [`incremental-review`](../incremental-review/SKILL.md).
6. Run every remaining repository-required validation tier. Enter
   [`failing-tests`](../failing-tests/SKILL.md) immediately for a red run and use
   [`remote-validation`](../remote-validation/SKILL.md) when validation belongs remotely.
7. Checkpoint only material recovery state and commit any remaining coherent change. Re-resolve the next safe,
   reversible action after every implementation, review, validation, checkpoint, and commit; continue while
   authorized work remains.
8. When the original authorization covers delivery, enter [`merge`](../merge/SKILL.md), reaching it through
   [`open-pr`](../open-pr/SKILL.md) when no PR exists. Waiting on a queue, CI run, publish, or the version-sync
   PR a merge generates is a poll, not a gate; own each to terminal, that generated PR included.

## Dispatch and fallback

Use the Workflow v2 semantic dispatch/result and provider/state envelopes in `.agents/workflows/contract/v2`
when present, or the packaged `../../workflows/contract/v2` bundle. Submit capabilities such as `evidence-explorer`,
`test-impact-analyst`, `review-lens`, or a leased `mechanical-worker`; never select an agent or model by name.
Subordinates return cited evidence and never choose architecture, scope, severity, or the next stage.

Validate each result. Give one focused follow-up to a correctable incomplete result, then cancel and perform
the same bounded objective in the parent on another invalid result, timeout, unavailable role/model, or
unsupported host capability. A cancelled or failed writer is reconciled from Git before any lease is reused.

## Terminal result

Return one completed repository outcome naming the implemented behavior, validation, review state, and
delivery state; a commit is not terminal while authorized delivery remains. Otherwise return one typed human
gate with its owner, required action, evidence, and observable resume condition. Do not expose internal agent
transcripts, model choices, routine continuation prompts, or a phase boundary as a stopping condition.
