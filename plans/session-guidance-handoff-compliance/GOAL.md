# Self-repair handoff priority and deferral

Status: bounded priority/deferral implementation and focused verification complete; independent review next.
Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-SessionGuidanceHandoffCompliance
Branch: Fix/SessionGuidanceHandoffCompliance
PR: https://github.com/tj-agents/core/pull/199
Native owner: 01a12ad4-3f5b-7c72-ad11-ea65007cdd0c
Coordinator: 01a12b10-3519-7f41-8e4f-7afa6828fef0
Updated: 2026-10-11
Lane: L4 implementation complete; L4 independent review next, then L7 delivery operations.

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

## Selected bounded design and delivery slice

Keep the decision with `engineering:handoff`: one skill-local Python admission helper, explicitly mapped
into engineering's hook resources, serves both hosts. No new skill, machine-wide scheduler or capacity
service is introduced. The optional machine-readable disposition stays inside its canonical problem entry;
the published problem-record contract and write skills remain the record owners.

The current callout receives a per-prompt nonce. Only a paired successful admission-check invocation can
identify a record for the gate, which rereads its linkage and current evidence. Matching hashes establish
bytes, not factual claims; bounded capability/dependency observations and verified native ownership must
support the disposition. Accept verified existing ownership or an actionable recorded deferral for the
current response while preserving the repair obligation. Unknown identity or ambiguous launch reserves
the existing attempt. Filter for eligibility before priority, unblocking value and age.

Reevaluate dependency changes through an explicit foreground check or an already supported continuation.
No document is represented as an automatic wake. Capacity evidence is limited to an explicitly declared
local budget and verified occupied owners. Native history, goal linkage and exclusion evidence are separate
from a claim of meaningful progress.

PR #199 remains the owning review. Its base is reconciled with published prerequisite `73f1fbc`; merge
checkpoint `54e08c5` preserves the existing source work and main's generated digests. Old CI run
`38139935559` failed the digest guard and two Linux tab-close fixtures; the digest is reconciled and main
contains the independently landed fixture fixes. The atomic slice includes shared admission, policy,
both-host gate integration, packaging and their focused tests. Splitting the policy from enforcement would
leave an exposed contradictory intermediate behavior. Target fewer than 800 substantive added lines;
measure again before review and assess a split if the candidate exceeds the branching threshold.

The continuation owner is initialized at `.agents/continuation/owner.json` and claimed by verified native
PID `30148`. Its old-head delivery binding was released as superseded; bind the next stable PR head before
monitoring. Scheduled Task `AgentStandards-Continuation-ff2ad4f1dc6319ace691dd23311c7b7e6cc430276e194683b581f82fac5c399f`
is registered. An explicit supported wake returned `working` while the foreground lease stayed with this
native owner and no headless child was launched.

## Next Steps

Pickup acknowledged on 2026-10-11 by native session `01a12ad4-3f5b-7c72-ad11-ea65007cdd0c`;
`CODEX_THREAD_ID` matches the recorded owner. Normal sandboxed reads succeeded for this goal, the
priority pointer and source files. The previous review work order is preserved. Fetched `origin/main`
contains prerequisite publication `73f1fbcc24efdda8ed1c0b0ccf07dc4064e7782c` and its problem-record contract.

Finish the focused source/process integration checks, commit the stable authored candidate, synchronize
its actual base once before independent review, and deliver through PR #199.
Keep this goal current with actual progress and the remaining action. Use a real supported continuation
owner when a delayed result requires one; do not report unattended monitoring without runtime evidence.
The source-level evidence below covers this candidate; live hook adoption is not claimed.

## Host coverage

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/hooks/callout_repair_gate.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "A pending Core-callout repair remains blocked until a verified launch, distinct native repair owner, or current typed deferred disposition exists.",
      "source": ".agents/plugins/manifests/claude/engineering-hooks.json",
      "mapping": "Claude dispatches the shared callout gate at Stop; the gate imports the packaged handoff admission evaluator.",
      "verification": {"level": "source", "result": "passed", "evidence": "CalloutRepairGateTests.test_callout_blocks_automatic_feedback_and_terminal_stop exercises the shared Stop gate; test_manifests_ship_only_supported_callout_events verifies the existing Claude Stop dispatch."}
    },
    {
      "host": "codex",
      "behavior": "A pending Core-callout repair cannot end the Codex turn without a verified launch, distinct native repair owner, or current typed deferred disposition.",
      "source": ".agents/plugins/manifests/codex/engineering-hooks.json",
      "mapping": "Codex Stop dispatch invokes the same shared gate and packaged admission evaluator as Claude.",
      "verification": {"level": "source", "result": "passed", "evidence": "CalloutRepairGateTests.test_callout_blocks_automatic_feedback_and_terminal_stop exercises the shared Stop gate; test_manifests_ship_only_supported_callout_events requires the Codex Stop dispatch to ship it."}
    }
  ]
}
```

## Current verification and slice assessment

- Focused admission tests: 8 passed, including current PID start identity, distinct native repair reuse,
  positive unique capacity occupancy, both-goal conflict overlap, stale/forged evidence rejection,
  eligibility ranking and once-per-fingerprint dependency transition.
- Callout-gate tests: 15 passed, including both hosts, current nonce/paired-check receipt requirements,
  explicit limits, invalid launches, and typed deferral that does not cache a resolved obligation.
- Generation and package invariants passed: 532 files from 81 canonical definitions, tier payloads,
  generated-tree currency, catalog digests and all three harness declarations. The packaged evaluator's
  `check --help` ran successfully. Generated files and catalog digests remain excluded from the commit.
- The first 34-test source integration run preceded regeneration and failed with eight catalog-drift
  errors. The same 34 tests passed after regeneration. The process-contract suite passed after replacing
  the superseded launch-only assertion with launch/reuse/validated-deferral and authority requirements.
- The added ownership/conflict regressions exceeded the initial 800-added-line target. Keep the scope
  frozen. Splitting the shared evaluator from policy/gate cutover would ship either unused admission
  machinery or a gate that still forces blocked work to launch. Splitting host wiring would preserve
  contradictory host outcomes. Runtime-wide capacity, scheduling and native receipt changes stay excluded.
  Full candidate against origin/main: 18 authored files, 877 added/33 deleted runtime-test-metadata lines,
  135 added/18 deleted guidance lines, and 202 added/3 deleted working-doc lines. This is the explicit
  frozen-scope exception at the roughly 1,000 substantive-line assessment trigger, for the rejected atomic
  split boundaries above. Required Windows/Linux CI validates the entire cutover.

## Historical verification (superseded source-only slice)

- `test_process_standards.py` passed all 23 tests, including the routed self-repair callout contract.
- Focused terminal-gate and host-adapter tests passed: `CalloutRepairGateTests.test_callout_blocks_automatic_feedback_and_terminal_stop`, `CalloutRepairGateTests.test_manifests_ship_only_supported_callout_events`, and `TaskWorkflowAcceptanceTests.test_task_skills_keep_one_canonical_body_and_thin_host_entries`.
- Host coverage validation passed. Package synchronization reported 512 files from 76 shared definitions with no remaining changes.
- The candidate was rebased onto `origin/main` at `0411b56134367ccfd42d9765e11ece5ea9f5aedf`; the focused validation set and generation checks passed again on the rebased head.
- The stale source-layout skill count and session-context mutation expectation reported by the draft PR's CI were repaired; `tests.test_source_layout` and `tests.test_engineering_hooks` passed.
