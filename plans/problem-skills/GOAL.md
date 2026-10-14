# Bug and mistake recording/addressing skills

Status: complete; PR #206 merged and generated publication verified on 2026-10-11.
Branch: Feature/ProblemSkills
Base: origin/main at 429ad56751720e2cb369c3aa2e25a3b53b801234
Worktree: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-ProblemSkills
PR: https://github.com/tj-agents/core/pull/206
Originating session: 01a12b10-3519-7f41-8e4f-7afa6828fef0
Execution owner: Codex session 01a12c10-0de6-7152-a9f2-9e5f374021f8
Lane: L7 terminal verification and cleanup; source design, implementation and independent review are complete.

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

Foundation complete. The coordinator can advance the separate handoff-priority design using the shipped
recording/addressing contract. This terminal goal is preserved at
C:/Users/TommySeery/source/repos/tj-agents/core/.git/agent-workflow/runs/problem-skills/completed-goal.md.
The merged linked worktree is eligible for verified cleanup; there is no remaining foundation implementation.

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
        "evidence": "Exact-head PR CI, focused packaging and source-contract example passed. Causal regenerate job published eight host entries and the shared contract on main. Installed consumer acceptance is separate."
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
        "evidence": "Exact-head PR CI, focused packaging and source-contract example passed. Causal regenerate job published eight host entries and the shared contract on main. Installed consumer acceptance is separate."
      }
    }
  ],
  "candidate_head": "f1a0db58f63c545e449addb645bf9b96134e32dd"
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

## Review and remediation

- First candidate: dcbe1a335fbdc7b4cb661a0235858207e9f634c8 against
  429ad56751720e2cb369c3aa2e25a3b53b801234. One pre-review synchronization observed zero behind.
- Native Codex review completed without actionable regressions and independently passed all 21
  source-layout tests, catalog and harness checks. Captured native-review log is in this workflow's
  Git-private artifacts. Applicable tier gate returned no stack conventions; agent file pairing passed.
- A fresh bounded workflow lens identified R001: common required fields need a compatible historical-entry
  rule. Its primary review specialist was unavailable on this account; the declared equivalent fallback
  ran against the same immutable bundle. Corrected result identities/citations were validated under v2.
- Canonical work order: reviews/Feature-ProblemSkills.md. Initial judgment changes-requested; R001 is the
  sole finding. Parent verified it against the frozen record contract and preserved M001-M007 observations.
- L4 exclusive remediation changes only the shared contract and engineering digest. Existing entry facts
  remain; common fields are reconciled from evidence when the incident is updated or addressed, with
  explicit unknowns and an investigation next action. A fresh incremental review must cover that commit.
- Both-host source coverage check passed at the first frozen head. Installed-host behavior is not claimed.

- Remediation packaging linkage test passed, catalog check reports zero changes and harness check passes all
  three manifests. The L4 writer released its lease; git diff --check passed. The fixed candidate is ready
  for a fresh incremental watermark before publication.

- Final review complete and approved at 98283b7614114b4e73b02763ecc7c15dfcd1c478. R001 is resolved;
  the initial pass judgment remains immutable. Both native incremental review and a fresh workflow lens
  found no actionable defects. Final-head host coverage passed; normalized v2 result validation passed.
- Publication preflight: the richer ledger parser does not accept this canonical legacy GOAL format, so
  the skill's supported inline checks were used. Branch has no owning PR, zero behind origin/main,
  three local commits ready for its first stable push, no dirty authored code and no red platform-sync PR.
  One coherent 23-file foundation slice is within the recorded size budget. Runtime review JSON is stored
  in Git-private state. No second progress ledger was created.

## Delivery recovery

- PR #206 opened as a draft at 98283b7614114b4e73b02763ecc7c15dfcd1c478; exact-head monitor
  reported guard failure in run 38167988381. Windows/Linux checks were still running at that observation.
- Cause confirmed: authored catalog skill additions were committed together with the generated engineering
  digest. scripts/check_generated_paths.py rejects digest changes because the post-merge job owns them.
  The failed job is 114554443369; gh run view could not read its log while sibling jobs were active.
  The completed job log was read through gh api and captured as ci-guard-job-log, confirming the digest.
- Correction: restore only the digest field to the frozen base, preserving all four authored skill additions.
  Source and packaging already passed focused checks after local digest generation; CI regenerates digests
  before its full suites. Future local regeneration must leave these digest fields uncommitted.
- Phase: L5 mechanical single-field restoration under the tiny inline follow-up allowance; no source
  workflow or host wiring changes. This owner retains the existing causal repair and PR, with no duplicate job.
- State: in-progress. Next action: run the guard at the correcting committed head, review that small delta,
  push one stable correction and monitor the new exact-head required CI. Resolution condition: the authored
  roster remains present, the generated digest is excluded, and required CI passes the correcting head.

- Correcting head f1a0db58f63c545e449addb645bf9b96134e32dd passes the committed generated-path guard.
  Captured artifact: problem-skills-guard-fix/artifacts/6118696b1a4f2779-generated-guard.log.
  The correction remains under native incremental review and a fresh workflow lens; PR #206 remains draft
  at its earlier head until the stable correction is reviewed and its binding refreshed.

- Guard correction review complete and approved at f1a0db58f63c545e449addb645bf9b96134e32dd.
  Fresh workflow lens found no actionable regression. Parent rejected the native proposal to undo the
  correction: it used the incremental review base, whereas the actual PR guard targets origin/main and
  passes. Final watermark, coverage and validated result are current; no open findings remain.

## Exact-head CI wait

- Stable correcting head f1a0db58f63c545e449addb645bf9b96134e32dd is pushed to PR #206.
  Delivery binding and PR body were refreshed; independent review watermark covers that exact head.
- CI run 38168830211: generated-path guard and verify-linux passed. verify-windows remains in progress
  at the latest material monitor transition and fresh confirming read. PR is draft and MERGEABLE.
- One reconnect-safe foreground monitor owns PR #206/head f1a0db5; it is not an unattended wake.
  After Windows succeeds, fresh-check the full terminal set, mark ready, merge under recorded authority,
  then observe the causal regeneration job and preserve the completed goal during verified cleanup.

## Source delivery

- PR #206 merged at 2026-10-11T19:55:02Z; reviewed head f1a0db58f63c545e449addb645bf9b96134e32dd.
- Landing commit: d3fc4d49ca412d9e9811faa3b07aed4d43ff0f70. Required guard, verify-windows and verify-linux all passed
  on the exact correcting head in run 38168830211. Review is approved with no open findings.
- Source delivery is complete; causal generated publication is the remaining acceptance step.

## Terminal outcome

- PR #206 is MERGED at reviewed head f1a0db58f63c545e449addb645bf9b96134e32dd.
  Landing commit d3fc4d49ca412d9e9811faa3b07aed4d43ff0f70; required Windows/Linux verification and
  generated-path guard passed in exact-head PR run 38168830211. Both review findings/recovery actions are resolved.
- Causal push run 38170019843 has head d3fc4d49ca412d9e9811faa3b07aed4d43ff0f70.
  Its publication job regenerate (114560486079) completed successfully. Published commit
  73f1fbcc24efdda8ed1c0b0ccf07dc4064e7782c has that landing commit as its parent.
- Verified remote main contains all eight Claude/Codex skill entries and the packaged shared resource with
  the historical-entry rule. This proves generated publication; no consumer profile installation is claimed.
- Existing M001-M007 facts remain intact. Scope is the four foundation skills and common record contract;
  handoff priority dispatch remains with its separate coordinator-owned workstream.
- Primary-checkout fast-forward encountered an unrelated existing TECH_DEBT.md edit. It was left intact;
  terminal evidence is preserved in Git-private state rather than overwriting another owner's document.
- No foundation tasks remain. Cleanup will use the repository's merge proof and exact native attachment.

```completion
{
  "outcome": "Bug and mistake recording/addressing foundation merged in PR #206 and published for both hosts.",
  "acceptance": [
    {
      "id": "records",
      "criterion": "Shared record contract defines evidence, ownership, deduplication and complete blockers.",
      "evidence": [
        {
          "source": "Disposable source-contract exercise and shipped problem-records.md",
          "result": "Passed with repeated-report append, retained bug evidence and complete conflict record."
        }
      ],
      "owner": "complete",
      "next_action": "none"
    },
    {
      "id": "repair",
      "criterion": "Addressing reuses existing repair lifecycles and preserves kind-specific history.",
      "evidence": [
        {
          "source": "Independent full and incremental reviews; fixing commit 98283b7614114b4e73b02763ecc7c15dfcd1c478",
          "result": "Approved; historical facts retained and missing fields reconciled only from evidence."
        }
      ],
      "owner": "complete",
      "next_action": "none"
    },
    {
      "id": "hosts",
      "criterion": "Both host entry points and common resource are packaged from canonical source.",
      "evidence": [
        {
          "source": "PR CI source-layout packaging check; remote main 73f1fbcc24efdda8ed1c0b0ccf07dc4064e7782c",
          "result": "Eight generated host entries and shared resource verified."
        }
      ],
      "owner": "complete",
      "next_action": "none"
    },
    {
      "id": "validation",
      "criterion": "Required repository checks pass on the exact reviewed delivery head.",
      "evidence": [
        {
          "source": "PR run 38168830211 at f1a0db58f63c545e449addb645bf9b96134e32dd",
          "result": "guard, verify-windows and verify-linux all SUCCESS."
        }
      ],
      "owner": "complete",
      "next_action": "none"
    },
    {
      "id": "delivery",
      "criterion": "Foundation source is committed, independently reviewed and merged.",
      "evidence": [
        {
          "source": "tj-agents/core PR 206 at f1a0db58f63c545e449addb645bf9b96134e32dd",
          "result": "MERGED; approved current watermark and no open findings."
        }
      ],
      "owner": "complete",
      "next_action": "none"
    },
    {
      "id": "publication",
      "criterion": "Observe generated publication causally tied to this PR merge.",
      "evidence": [
        {
          "source": "Run 38170019843 job 114560486079; commit 73f1fbcc24efdda8ed1c0b0ccf07dc4064e7782c",
          "result": "Regenerate SUCCESS; publication commit parent is the exact landing commit d3fc4d49ca412d9e9811faa3b07aed4d43ff0f70."
        }
      ],
      "owner": "complete",
      "next_action": "none"
    }
  ],
  "deliveries": [
    {
      "repository": "tj-agents/core",
      "pr": 206,
      "head": "f1a0db58f63c545e449addb645bf9b96134e32dd"
    }
  ],
  "open_tasks": []
}
```
