---
name: bugfix
description: Diagnose and fix a defect, regression, crash, or incorrect existing behavior through causal repair, regression coverage, review, validation, and commit when no active plan or specialist test workflow owns it. Do not use for new behavior, planning-only requests, execution of an existing plan, review-only requests, or a named test tier already owned by its debug skill.

kind: workflow
domain: process
---

# Diagnose and repair a bug

Own an unplanned defect from evidence to a verified causal repair. If an explicit or uniquely resolved active
plan owns the defect, use that plan's execution workflow. If the request starts from a named red test or
integration/E2E tier, use its narrower debug workflow; return here only when that workflow identifies a
product defect whose repair is not already owned.

Resolve one owning lifecycle skill and only the technical skills directly routed by the changed paths. Use
`python .agents/workflows/workflow_ops.py --root . --workflow-run-id <id> skills --lifecycle bugfix --changed-path <path>` to record
their identities and content hashes, and reuse that record while those hashes remain unchanged. Use the
shared `inspect` operation once for routine repository state instead of reconstructing it through separate
shell calls.

## Classify before dispatching

Use the quick path when the failure is reproducible or directly evidenced, ownership is local, one causal
explanation dominates, and a focused regression check can prove the repair. Keep the work in the parent and
do not dispatch.

Use the investigation path for ambiguous ownership, noisy logs, cross-boundary or intermittent effects,
multiple plausible causes, or a proposed fix whose mechanism is not proven. Reduce supplied logs to failure
signatures and chronology before dispatching. Launch only independent bounded reads, normally:

- `log-analyst` for signatures, chronology, correlations, and evidence gaps;
- `evidence-explorer` for code-path ownership and an analogous working path; and
- `test-impact-analyst` for the affected test map and repository-supported checks.

Readers may overlap, but they receive the same immutable baseline and do not see one another's conclusions.
Require competing causal hypotheses and a discriminator for each. The parent alone weighs the evidence,
diagnoses the cause, and chooses the repair.

## Execute the repair lifecycle

1. Reproduce or anchor the defect in direct evidence. Separate symptoms from the first incorrect state or
   transition.
2. Choose the smallest repair that corrects the causal mechanism without suppressing errors, weakening
   expectations, skipping coverage, widening timeouts, or preserving an invalid state.
3. Implement directly. A `mechanical-worker` may receive only a disjoint transformation under an exclusive
   writer lease; all writes remain serialized and the parent reconciles the reported paths against Git.
4. Add or strengthen regression coverage at the lowest tier that proves both the failure and causal repair.
5. Run the focused checks through the shared `run` operation so detailed output remains an artifact and the
   model receives only bounded results. Then apply `engineering:committing` so
   branch-diff review has an immutable candidate.
6. Run the repository's focused independent `engineering:review`. Resolve actionable findings through
   `engineering:address-review`, commit those fixes, then use
   `engineering:incremental-review` for the changed delta.
7. Run every remaining repository-required tier. Enter
   `engineering:failing-tests` immediately for a red run and use
   `engineering:remote-validation` when validation belongs remotely.
8. Checkpoint only material recovery state and commit any remaining coherent change. After each result,
   review, validation, checkpoint, and commit, re-resolve the next safe reversible action and continue while
   the defect remains unresolved.
9. When the original authorization covers delivery (`engineering:merging` owns that goal-wide scope),
   enter `engineering:merge`, reaching it through
   `engineering:open-pr` when no PR exists. Waiting on a queue, CI run, publish, or the version-sync
   PR a merge generates is a poll, not a gate; own each to terminal, that generated PR included.

The quick path creates no plan, ledger, workflow sidecar, or automatic checkpoint. If investigation or repair
grows across phases, worktrees, external gates, or context/restart boundaries, resolve and validate Workflow
v2 repository state. Then promote through `engineering:plans`, checkpoint the durable artifacts under
`engineering:plan-checkpoint`, and continue under the durable owner without a routine
continuation prompt. A Kandev-managed task owns only the outer worktree and host-session association.

## Dispatch and failure recovery

Use the Workflow v2 semantic dispatch/result and provider/state envelopes in `.agents/workflows/contract/v2`
when present, or the packaged `../../workflows/contract/v2` bundle. Never select an agent or model by name, and never accept a
subordinate's root-cause claim as the diagnosis.

Validate cited evidence and acceptance conditions. Give one focused follow-up for a correctable incomplete
result. On another invalid result, timeout, cancellation, unavailable role/model, or unsupported host feature,
close that dispatch and execute the same bounded analysis in the parent. Reconstruct a failed writer's partial
paths from Git and restore exclusive ownership before retrying.

## Terminal result

Return one completed repository outcome naming the reproduced defect, causal repair, regression evidence,
validation, review state, and delivery state; a commit is not terminal while authorized delivery remains.
Otherwise return one typed human gate with its owner, required action, evidence, and observable resume
condition. Do not expose internal agent transcripts, model choices, competing-hypothesis chatter, or a
routine continuation prompt.
