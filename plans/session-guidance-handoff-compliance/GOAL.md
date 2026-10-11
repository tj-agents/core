# Self-repair handoff priority and deferral

Status: resumed by the existing native owner; priority/deferral design in progress.
Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-SessionGuidanceHandoffCompliance
Branch: Fix/SessionGuidanceHandoffCompliance
PR: https://github.com/tj-agents/core/pull/199
Native owner: 01a12ad4-3f5b-7c72-ad11-ea65007cdd0c
Coordinator: 01a12b10-3519-7f41-8e4f-7afa6828fef0
Updated: 2026-10-11
Lane: L3 for bounded design of validated deferred dispositions and existing-hook integration;
route specified implementation/review to L4 once those choices are resolved.

## Outcome and authority

Preserve this session's existing self-repair work and make handoff eligibility and priority use the new
problem-record skills. Tommy requested deferring a handoff when a bug blocks it, it would interfere with
other work, or it cannot execute now, recording the obligation instead. He explicitly made the skills a
prerequisite. After their completion he asked, 'ok all done it says, next handoff?' This authorizes the
next bounded priority/deferral slice and reopening this existing owner instead of starting a duplicate.

The existing standards-defect repair and goal-wide delivery authority continue through implementation,
review, required CI, merge and causal generated publication. The previous narrow goal required a native
launch for every callout; that requirement is superseded here by an evidence-backed valid disposition.
The existing unfinished source work is retained and reconciled with this requested behavior. Do not
implement a policy that still forces blocked or conflicting work to spawn a new terminal.

Shared design: C:/Users/TommySeery/source/repos/tj-agents/docs/plans/handoff-priority/PLAN.md
Shared roadmap: C:/Users/TommySeery/source/repos/tj-agents/docs/plans/agentic-delivery/ROADMAP.md
This goal owns source implementation and delivery. The coordinator owns those shared docs; do not edit
its checkout or adopt unrelated workstreams.

## Verified prerequisite and existing work

- PR #206 merged at 2026-10-11T19:55:02Z, landing d3fc4d49ca412d9e9811faa3b07aed4d43ff0f70.
  Generated publication succeeded in run 38170019843; publication commit
  73f1fbcc24efdda8ed1c0b0ccf07dc4064e7782c contains the both-host skill entries.
- Fetched main contains write-bug, address-bug, write-mistake, address-mistake and the shared
  .agents/engineering/resources/problem-records.md. Use that actual contract: blocked_by is a category
  (capability, dependency, conflict, capacity); link the concrete blocking item/owner separately.
  Preserve the selected BUGS.md/MISTAKES.md/area TECH_DEBT.md or repository-declared register owners.
- This exact native owner was observed non-live before preparation; no second native owner appeared for
  this worktree. The existing source head was cb6825236d97784f28e8286f56e99981911e4f89.
  The untracked reviews/Fix-SessionGuidanceHandoffCompliance.md belongs to this work: preserve it.
- PR #199 remains open. Its old run 38139935559 reports guard and verify-linux failures, Windows success.
  Reconcile the failed evidence and stale base in this same owner; do not re-run an unchanged failed head.
  PR #206 found that generated catalog digests must remain uncommitted even when authored skill lists
  change. Inspect the actual #199 failure before assuming it has that same cause.
- PR #196 remains open and its native context is non-live. The previous goal explicitly excluded the
  cancelled native-handoff receipt/wording work. Preserve that exclusion and its artifacts; do not resume,
  merge, close or adopt #196 without separate authority. Its open state alone is not a prerequisite.

## Scope and composition

The reusable eligibility/priority decision belongs with the handoff workflow and a small shared operation
or contract where warranted by skill-authoring. Self-repair, handoff and later orchestration must consume
one source of that decision. Keep problem recording in the new write/address skills. Do not build a
monolithic orchestration skill here or copy the record contract into multiple skills.

Before dispatch:

1. Resolve the problem/work item, authority, existing canonical repair owner, exact native session and
   launch attempt. Reuse an in-flight owner; reopen a verified closed resumable context when appropriate.
   Unknown identity or ambiguous launch is reconciled, never treated as permission for another writer.
2. Evaluate required capabilities, actual dependency evidence, conflicting owners/paths/shared resources,
   and available capacity. Use evidence and existing supported interfaces; do not invent a global scheduler
   or equate 'process is alive' with meaningful progress. A source merge alone is not installed adoption.
3. Runnable independent work may launch through the supported handoff/open skills. Rank eligible items by
   impact/urgency, how much authorized work they unblock, then age. P1 is not a global pause or permission
   to ignore conflicts, authority or capacity.
4. If blocked/deferred, use the appropriate write skill to update the canonical record with reason,
   category, concrete blocker/conflicting owner, resolver, observable resume condition and next action.
   Ordinary feature work stays in its own goal and links the problem; do not label it a bug for storage.
   Repeated reports update one record and never create recursive tabs. Deferral retains the obligation.

Replace unconditional same-turn launch guidance and its host enforcement together. A mere claim,
missing/unrelated record, stale owner link or forged 'deferred' string must not release the gate. A
verifiable recorded deferred disposition may satisfy the current response while its repair stays open.
Verified existing ownership is also a valid disposition; an apology or worker substituted for the
requested independent native context is not. Preserve explicit user limits and existing delivery authority.

The existing continuation/monitor can be used only where supported and actually initialized. This slice
must make a dependency transition eligible for reconsideration without duplicate dispatch, with focused
coverage. Full machine-wide atomic capacity, event delivery and unattended orchestration remain a later
runtime slice. Do not claim a document wakes an agent or silently add a second polling service.

## Completion and validation

- Shared source drives Codex and Claude decision/enforcement paths; include required manifests, catalogs,
  thin adapters and focused host-coverage updates, without committing generated distribution or digests.
- Demonstrate a broken read capability defers dependent work, while an unrelated runnable task proceeds.
- Demonstrate conflicting writers and full capacity create valid linked deferred records, not launches.
- Demonstrate an existing repair/context is reused and repeated or ambiguous attempts never duplicate it.
- Reject missing/stale/unrelated deferred evidence; keep the original obligation until causal resolution.
- Demonstrate dependency completion permits reevaluation once through the supported mechanism, without
  claiming an unimplemented background wake. Preserve actual live-owner identity during reconciliation.
- Run focused behavior checks, independent review, required Windows/Linux CI and causal publication.
  Freeze a stable candidate; broaden local checks only for relevant changes or unexplained failures.
- Land this bounded change under the existing delivery authority and record concrete completion evidence.
  If a PR-sized split is needed, use sequential slices with one owner and a proper dependency; do not
  resurrect or duplicate the unfinished #199 delivery. Keep runtime-wide proposals out of this change.

## Next Steps

Pickup acknowledged on 2026-10-11 by native session `01a12ad4-3f5b-7c72-ad11-ea65007cdd0c`;
`CODEX_THREAD_ID` matches the recorded owner. Normal sandboxed reads succeeded for this goal, the
priority pointer and source files. The previous review work order is preserved. Fetched `origin/main`
contains prerequisite publication `73f1fbcc24efdda8ed1c0b0ccf07dc4064e7782c` and its problem-record contract.

Reconcile current main with this PR's owned files and failed CI. Resolve the bounded design above, then implement,
validate, review and deliver the priority/deferral behavior through the existing owning lifecycle.
Keep this goal current with actual progress and the remaining action. Use a real supported continuation
owner when a delayed result requires one; do not report unattended monitoring without runtime evidence.
The previous evidence below is historical and must be refreshed for the changed acceptance criteria.

## Previous-slice host coverage (revalidate the changed behavior)

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/hooks/callout_repair_gate.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "A pending Core-callout repair remains blocked at Stop until a verified standards-defect handoff launch exists.",
      "source": ".agents/plugins/manifests/claude/engineering-hooks.json",
      "mapping": "Claude already dispatches the shared callout gate at Stop.",
      "verification": {"level": "source", "result": "passed", "evidence": "CalloutRepairGateTests.test_callout_blocks_automatic_feedback_and_terminal_stop exercises the shared Stop gate; test_manifests_ship_only_supported_callout_events verifies the existing Claude Stop dispatch."}
    },
    {
      "host": "codex",
      "behavior": "A pending Core-callout repair cannot end the Codex turn until a verified standards-defect handoff launch exists.",
      "source": ".agents/plugins/manifests/codex/engineering-hooks.json",
      "mapping": "Codex Stop dispatch will invoke the shared callout gate alongside its existing terminal gates.",
      "verification": {"level": "source", "result": "passed", "evidence": "CalloutRepairGateTests.test_callout_blocks_automatic_feedback_and_terminal_stop exercises the shared Stop gate; test_manifests_ship_only_supported_callout_events requires the Codex Stop dispatch to ship it."}
    }
  ]
}
```

## Previous-slice verification

- `test_process_standards.py` passed all 23 tests, including the routed self-repair callout contract.
- Focused terminal-gate and host-adapter tests passed: `CalloutRepairGateTests.test_callout_blocks_automatic_feedback_and_terminal_stop`, `CalloutRepairGateTests.test_manifests_ship_only_supported_callout_events`, and `TaskWorkflowAcceptanceTests.test_task_skills_keep_one_canonical_body_and_thin_host_entries`.
- Host coverage validation passed. Package synchronization reported 512 files from 76 shared definitions with no remaining changes.
- The candidate was rebased onto `origin/main` at `0411b56134367ccfd42d9765e11ece5ea9f5aedf`; the focused validation set and generation checks passed again on the rebased head.
- The stale source-layout skill count and session-context mutation expectation reported by the draft PR's CI were repaired; `tests.test_source_layout` and `tests.test_engineering_hooks` passed.
