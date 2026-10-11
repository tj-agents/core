# Bug and mistake recording/addressing skills

Status: ready for one native execution owner; pickup not yet observed.
Branch: Feature/ProblemSkills
Base: origin/main at 429ad56751720e2cb369c3aa2e25a3b53b801234
Worktree: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-ProblemSkills
PR: not opened
Originating session: 01a12b10-3519-7f41-8e4f-7afa6828fef0
Execution owner: unclaimed
Lane: L3 because record taxonomy and integration with existing repair owners need bounded design judgment.

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

Acknowledge this assignment in this file with your native session ID before deliverable writes. Verify
normal reads of this goal, one installed skill and a text file, then record the actual result and the
first source action. Load the owning feature/skill-authoring lifecycle, inspect merged write-debt,
address-debt, bugfix, MISTAKES.md and the limited #199 overlap. Implement the bounded compatible foundation
above, validate, review and deliver it. Keep this goal current through completion, including the PR and
verification evidence. Report the outcome back through this goal so the coordinator can advance the
recorded dependent handoff policy. A source merge does not mean an orchestration monitor is installed.
