# Bug and mistake recording/addressing skills

Status: active; native execution pickup acknowledged on 2026-10-11.
Branch: Feature/ProblemSkills
Base: origin/main at 429ad56751720e2cb369c3aa2e25a3b53b801234
Worktree: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-ProblemSkills
PR: not opened
Originating session: 01a12b10-3519-7f41-8e4f-7afa6828fef0
Execution owner: Codex session 01a12c10-0de6-7152-a9f2-9e5f374021f8
Lane: L4 independent review of the completed foundation; L3 source/design decisions remain with this owner.

## Outcome and authorization

Tommy selected new bug and mistake skills as the next fix, following the recently merged debt skill pair,
and asked about independent handoffs. He subsequently specified that handoff priority/deferral must use
these recording skills, and that those skills must come first. This bounded side workstream implements
the foundation; the originating session retains the shared planning/coordination work in tj-agents/docs.
Use existing repository delivery authority for this goal's reviewed, green PRs. No unrelated installation,
profile change, Termboard implementation or lane redesign is authorized by this goal.

Shared design: C:/Users/TommySeery/source/repos/tj-agents/docs/plans/problem-management/PLAN.md
Dependent design: C:/Users/TommySeery/source/repos/tj-agents/docs/plans/handoff-priority/PLAN.md
Roadmap: C:/Users/TommySeery/source/repos/tj-agents/docs/plans/agentic-delivery/ROADMAP.md
Read these as design context. This file owns implementation status and next action. Do not edit the
originating session's docs checkout or adopt its other workstreams.

## Decisions and source context

1. Follow merged #173: separate `write-debt` and `address-debt`. Proposed counterparts are `write-bug`,
   `address-bug`, `write-mistake` and `address-mistake`; check the skill taxonomy and existing names before
   authoring. Recording and addressing must be independently useful. Share common semantics under one
   canonical owner; do not create a second copy of the bugfix or self-repair lifecycle.
2. Core #205 added root MISTAKES.md with stable incidents M001-M007. Preserve those observations, IDs and
   evidence; its addressed history is retained. Existing area-owned TECH_DEBT.md entries follow write-debt's
   remove-on-resolution rule. Retention is kind-specific and must not erase the mistake learning record.
3. Physical file consolidation remains a user preference under discussion. For this compatible first slice,
   preserve existing paths and conventions, with BUGS.md for bug records where a repository has no declared
   bug record owner. A declared existing shared problem register may hold typed entries. Do not migrate all
   consumers or rename the merged debt files merely to make the new skills work. One canonical record per
   repair is mandatory; one physical file for all kinds has not been settled. Clarify this implemented
   default in this goal; do not claim the user selected it.
4. Capture evidence, kind, impact/priority, source owner, state, linked repair/session/PR, next action and
   verifiable resolution. Support deferred records with reason, blocked_by/conflicting owner, resolver and
   observable resume condition. Deduplicate repeated symptoms under their causal repair. Unknown cause is
   recorded as unknown, not invented. Mistakes can link to a bug/debt repair rather than spawning copies.
5. Use existing bugfix for actual defect repair. #199 (Fix/SessionGuidanceHandoffCompliance) owns the pending
   self-repair workflow and session-guidance wiring; #196 owns related handoff enforcement. Both remain open
   at preparation. Do not restart their repair, create competing policy writers or depend on a skill as
   shipped if it exists only on an unmerged branch. Reconcile relevant current source; source-policy overlap
   may require a recorded dependency or narrowly coordinated change. #168 also owns older noticed-problem
   guidance, much of which reached main through #173. Use merged source as the baseline.
6. Handoff priority/deferral is the next dependent slice, not implemented here. This foundation records a
   deferred obligation truthfully; it must not claim a saved document launches or wakes an agent. Priority
   ranks runnable work after capability, dependency, conflict and capacity checks; P1 is not a global pause.
7. Apply the generic convention to consuming repositories on both hosts. Canonical definitions live in
   .agents, with thin Codex and Claude entry points. Ship required manifest/catalog/source companion updates
   in this same change. Do not commit generated plugins output.

## Evidence and owner reconciliation

- Fetched remote main immediately before worktree creation; main includes #173 and #205.
- Open PR inventory, registered worktrees, native peer inventory and conversation searches for write-bug
  and write-mistake found no owner for this new foundation. This is a new task, not a restarted repair.
- Existing self-repair session: 01a12ad4-3f5b-7c72-ad11-ea65007cdd0c; observed non-live. Its work and PR remain
  owned there. Reopen via open-codex if separately selected; do not create another context for its task.
- The normal launcher resolver selects approved codex-cli 0.163.0-alpha.1. Parent's already-running sandbox
  still fails before PowerShell starts. That does not disprove fresh-launch recovery. Verify the successor's
  own ordinary reads and report the actual failure if present; never disable hooks or bypass trust to proceed.
- Only this native handoff is requested now. Do not recursively launch a swarm for every deferred finding.
  Respect Tommy's explicit sequencing and capacity concern; keep out-of-scope items in their owning records.

## Acceptance and delivery

- New bugs/mistakes and repeated reports produce the correct canonical records without a separate reminder.
- Addressing selects an actionable record, reuses the existing repair owner/lifecycle, checks resolution
  and applies the correct retention. A blocked record remains an outstanding obligation with a next action.
- Demonstrate the shared record fields for a capability blocker and a conflicting writer; no duplicate task.
- Codex and Claude entry points, discovery/routing and required harness artifacts agree with canonical source.
- Use focused behavior/contract checks and one disposable consumer example. Run required repository checks;
  avoid broad repeated tests without a failure or changed input. Installed acceptance is separate evidence.
- Commit, independent review, PR, required CI and merge under existing goal/repository authority; use a real
  supported continuation owner if waiting. Do not stop at a PR with no owner for its checks. Report any actual
  host capability gate and preserve remaining safe work; no invented permission gate or unattended claim.

## Next Steps

Freeze the verified authored candidate, synchronize once with origin/main and run independent review.
Resolve any actionable findings, then push the reviewed head, open the foundation PR and own its exact
required CI through merge. Observe the causal generated publication on main and record completion here
so the coordinator can advance the dependent handoff policy. Installed consumer acceptance remains
separate from the source-contract exercise; this work does not install an orchestration monitor.

## Execution progress

- Pickup: acknowledged the prepared native side-workstream assignment from this exact checkout.
  Normal reads of this goal, the installed engineering `write-debt` entry point and repository text
  succeeded. No fresh-launch read failure was observed.
- Phase: L3 investigation and bounded contract design; resolved against `.agents/lanes/codex.json`.
  The prepared launch records this owner at that lane. Later implementation and review lanes will be
  selected separately and applied through supported bounded workers where required.
- First source action: inspected canonical write-debt, address-debt, bugfix, session-guidance and
  MISTAKES.md. Existing incident facts and IDs will be preserved. Plan-execution owns this existing goal;
  feature was consulted and correctly routes existing plans back to that owner.
- Delivery observation: ordinary gh reads cannot access its configuration under the current sandbox.
  Scoped gh reads succeeded; PR #199 remains OPEN and its exact overlap was inspected.

## Current slice and design

- One coherent foundation PR on the prepared Feature/ProblemSkills branch, base origin/main
  429ad56751720e2cb369c3aa2e25a3b53b801234; preparation head 62ba9760712429a5e6eeff73371cc3dabd17fab3.
  Expected size: roughly 450 authored lines across shared guidance, four skills, eight host adapters,
  companion metadata and focused package checks. This is itself guidance delivery, not a guidance
  drive-by mixed into product implementation. No runtime hook, scheduler or dispatch change is included.
- Common record semantics will live in `.agents/engineering/resources/problem-records.md`, explicitly
  mapped into the engineering package. Each kind keeps its own storage and retention convention.
  Bugs retain resolved status and verification by default; debt deletes verified resolved entries;
  mistakes preserve stable learning history. Existing registers override the storage default.
- `write-bug` and `write-mistake` are conventions; `address-bug` and `address-mistake` select the existing
  repair lifecycle and keep the canonical record updated, without copying its engine.
- Add one independent recording section to session-guidance, outside PR #199's callout body.
  `address-mistake` uses shipped session-guidance for standards repair; no dependency on unmerged self-repair.
  PR #199 was observed OPEN and its exact diff inspected. Catalog additions remain additive.
- Recording supports one causal repair with related incident links, explicit unknown cause, capability,
  dependency, conflicting-writer and capacity deferrals, and truthful next action/resume evidence.
- Implementation phase: L4, specified source/adapters/metadata with testable packaging choices, applied
  through one bounded worker as required by lanes. This owner keeps design, scope and delivery decisions.
- Continuation owner initialized: afea5b5078fa7f6436ece091. Foreground claimed to native PID 29620; scheduler registration succeeded, but automatic approval review
  rejected the manual wake as potentially launching unattended work. The scheduled task is removed;
  delivery remains owned in the foreground. No unattended continuation is claimed.
- Git fetch succeeded; branch is zero commits behind origin/main. Scoped GitHub reads succeeded.

## Host coverage

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/engineering/resources/problem-records.md",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Record bugs and mistakes with one causal repair owner and preserve kind-specific resolution history.",
      "source": ".claude/skills/write-bug/SKILL.md",
      "mapping": "Thin Claude entries load the same canonical convention and addressing workflows; the engineering SessionStart policy selects recording.",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Both-host packaging/linkage and shared-contract source exercise passed; installed-host behavior acceptance is not claimed."
      }
    },
    {
      "host": "codex",
      "behavior": "Record bugs and mistakes with one causal repair owner and preserve kind-specific resolution history.",
      "source": ".codex/skills/write-bug/SKILL.md",
      "mapping": "Thin Codex entries load the same canonical convention and addressing workflows; the engineering SessionStart policy selects recording.",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Both-host packaging/linkage and shared-contract source exercise passed; installed-host behavior acceptance is not claimed."
      }
    }
  ]
}
```

- Workflow lifecycle-name discovery hit its already-recorded flat-layout defect in
  `docs/workflows/TECH_DEBT.md`. The supported explicit name=canonical-path input successfully recorded
  plan-execution without changing that independent runtime owner. No competing repair was launched.

## Implementation and verification

- Four canonical skills, eight thin host entries, shared record contract, discovery, catalog/source mapping
  and harness metadata are implemented. Existing M001-M007 incident facts are unchanged. The bounded L4
  writer released its source lease after focused validation; this owner now freezes the review candidate.
- Catalog digest check passed with zero changes; harness synchronization check passed for all three manifests.
- Eight source-layout regressions passed, including both-host shared resource packaging, payload containment
  and deterministic generation (46.302 seconds). Earlier negative source-layout cases passed; the eight
  catalog-blocked cases were rerun after the digest was refreshed.
- Harness-manifest tests passed: 14 tests in 10.978 seconds. The sandboxed subprocess spawn denial was
  reproduced as a capability restriction and the same test passed with scoped elevated execution.
- Disposable source-contract exercise passed at
  C:/Users/TOMMYS~1/AppData/Local/Temp/problem-records-c9792cad96e84a48bd022c9e387a7ddb:
  one causal bug record, repeated evidence append, retained resolved evidence and a complete conflict blocker.
  This is source evidence; no installed Claude or Codex consumer behavior acceptance is claimed.
- Validation logs are captured in the Git-private workflow run foundation-implementation artifacts directory.
  git diff --check passed. No generated distribution output is included in the authored candidate.
- Commit/push clerical steps use the L7 tiny-follow-up allowance inline; review uses fresh read-only lenses
  at the canonical review stage, with final judgment and artifact writing retained by this owner.
