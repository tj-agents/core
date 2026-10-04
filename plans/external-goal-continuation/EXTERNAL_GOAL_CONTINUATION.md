# Keep an approved PR owned through its merge wait

## Outcome and authorization

Tommy requested a waiter that automatically completes an authorized merge after checks and review, and
asked to fix the recurring need for intervention across his codebases. This side workstream repairs the
shared continuation runtime and its usage guidance. The standing standards-defect authorization covers
implementation, tests, review, PR and merge after repository gates. Normal-profile installation, hook
trust changes, unrelated merges and repository-wide GitHub settings changes are outside this task.

Do not ask for routine continuation or another approval of this bounded source repair. Honor actual
tool-policy decisions and report an authentic external gate with its concrete action and resolver.

## Ownership and current delivery

- Side checkout: `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-ExternalGoalContinuation`.
- Side branch: `Fix/ExternalGoalContinuation`; base `743c34a43bc538d9a58bac92b7dc65fef4024b8a`.
- This file is the side repair's single goal. Start at L4 after loading `engineering:lanes` and `bugfix`.
  The defect, intended boundary and verification below are specified. Re-route other stages as needed.
- Original rename goal: `C:/Users/TommySeery/.claude/plans/tj-agents-core/SKILL_KIND_RENAME.md`.
  Original owner: session `01a107f2-6ad0-7233-9e21-af4840e20a81`, observed PID `29788`.
  Do not edit its files, change its scheduler, claim its lease, or launch another rename executor.
- PR #90 is the original owner's current slice. Observed head `6686c557071be939f32a275d2abd6fe99f3e6d6b`
  has completed incremental review and is being monitored by that owner through
  `skill-kind-slice-a-delivery-refresh`, CI run `37226393963`. Tommy approved its merge previously and
  explicitly requested automatic completion in the originating conversation. It must not need approval again.
- GitHub `allow_auto_merge` is currently false. This does not prevent the supported owner from waiting for
  exact-head checks and then performing the authorized merge. Do not enable repository-wide automation
  or merge before the applicable checks merely to make the request look complete.
- Preserve the original core checkout's unrelated repo-declared-config plan documents.

## Reproduced mechanism

The rename session invoked `continuation_runtime.py init --root .` in its Feature-SkillKindReader
checkout, but supplied `--owner` under the primary repository's `.git/agent-workflow/runs/` directory.
The runtime rejected that path with `canonical-owner-path-required` before examining the goal argument.
The supported owner belongs at `<worktree>/.agents/continuation/owner.json`; omitting `--owner` selects it.
Keep that owner-path invariant.

There is a second, real runtime limitation: both source and installed engineering 2.1.16 implementations
require `goal.is_relative_to(root)` in `initialize`, rejecting the explicitly selected external plan with
`goal-must-exist-inside-worktree`. The workflow contract supports an existing external canonical goal and
forbids making a competing copy. A path-placement error must not be misreported as absence of scheduling.
`check_identity` independently repeats the containment requirement and emits `canonical-goal-unavailable`;
repair both entry and resumed execution. The complete source and installed runtimes match after newline
normalization. No continuation owner or scheduler record currently exists for the original goal.

Evidence: `.agents/workflows/continuation_runtime.py`, `initialize` and `main`; the existing rename session
transcript's 2026-10-04 18:20:53Z init invocation and its result. The original goal records the error and
absence of a registered continuation. Source runtime and shipped runtime currently share the restriction.

The delivery binder has a separate causal defect in the same wait: `workflow_ops.standing_authorization`
returns absent when the repository has no standing table; `delivery_bind` always rewrites authorization
from that result. No supported CLI input carries the user's recorded approval for this PR, and the
router sends a green reviewed candidate to a human merge-authorization gate. Neither the external goal's
approval nor the continuation owner's authority is consumed. A path-only fix would therefore still ask
Tommy again. Repair both mechanisms before claiming this outcome.

## Bounded repair and invariants

1. Accept an explicitly supplied absolute path to an existing external canonical goal. Normalize and
   retain that exact identity; do not relocate, copy, or silently create the goal. Preserve existing
   worktree-relative goals. Reject relative escapes, missing paths and non-files with actionable evidence.
2. Keep the owner record at its canonical per-worktree location, Git identity checks, exact PR/head/review
   binding, explicit authorization, finite budgets and exclusive writer lease. An external goal adds no
   permission to access unrelated files, install a plugin, or merge another PR.
3. Correct usage guidance and failure reporting so a noncanonical owner argument directs the caller to
   the documented default. Distinguish that recoverable invocation error from an actually unavailable
   runtime. A capable owner must try the supported invocation and complete initialization, foreground
   claim, registration and observed wake before claiming durable continuation.
4. Preserve the original owner through delayed checks, repair and its already-authorized merge. User
   approval remains in the goal/authority record and must survive a wake without another prompt. This
   repair must not rewrite the repository authorization table or weaken any stop class.
5. Keep headless execution within the selected execution lane using the canonical lane mechanism if the
   touched launch path otherwise silently falls back to a planning model. Report any separate mechanism
   requiring new design instead of hardcoding model IDs or broadening this change unboundedly.
6. Add one explicit optional approval-record input to the existing delivery binder. Its structured record
   carries repository, PR number, exact worktree/branch, permitted merge mode, the actual user's wording
   and the source of that authorization. The agent may supply this only from an observed user instruction;
   a goal file's existence or implementation approval never invents merge authority. Keep one binder as
   the writer of the delivery binding; do not hand-edit an existing binding to override its result.
7. Match the recorded approval to the same PR/worktree/branch, then bind the current exact remote head and
   re-evaluate all existing stop-class paths and hold labels. A scoped approval can resolve absence of a
   repository-wide table; it cannot bypass a stop class or hold. Preserve the approval wording/provenance
   through rebinding approved repairs to this same PR, subject to those fresh checks. It must never carry
   into another PR, checkout or branch, and no supplied approval keeps today's absent-authority behavior.
   The original PR uses ordinary merge after terminal checks because GitHub auto-merge is disabled.
8. Update persistent-delivery and persistent-workflow guidance to distinguish standing authorization,
   recorded approval for one PR and actual missing authorization. An already-approved merge must not
   become a user question merely because the task resumes or a supported same-PR repair changes its head.

The current runtime also binds an owner to one checkout and branch; `apply_receipt` permits a head rebind,
not relocation into the next slice. Preserve that constraint in this focused patch and report it accurately.
Do not claim that accepting an external goal alone provides cross-worktree continuation. A clean terminal
owner transition or a separately designed transfer must precede retiring a checkout that holds live state.
The supported foreground transition completes that slice's recorded delivery condition, releases its
binding, checkpoints its runtime owner and removes its scheduler, then initializes and claims the next
worktree's owner against the same canonical goal. Preserve old receipts and one active writer. Finishing
a slice-specific runtime owner never marks the full goal complete; automatic cross-worktree supervisor
handoff is a separate capability and must not be claimed by this change.

## Acceptance

- Reproduce both original rejection stages and add focused tests proving that a canonical owner plus an
  absolute external goal initializes successfully; local goals still work; invalid owner, absent goal,
  directory goal and relative escape remain rejected.
- Prove the external goal is preserved in the state and actual child prompt across claim, yield and wake.
  A live foreground owner prevents a second writer; process identity and stale-head checks stay effective.
- Exercise the existing delivery transition tests with explicit merge authority and an external goal:
  pending checks wait, green reviewed exact head advances, a failed check routes repair, and an unexpected
  head change does not merge stale evidence. No real PR merges in synthetic tests.
- Prove scoped approval without a standing table is accepted only for its declared identity; absent or
  mismatched approval remains blocked; a stop path/hold still blocks; adding a stop path on a repaired
  head revokes unattended delivery; a successor PR does not inherit the previous approval. Verify the
  approved current-head binding reaches the router's merge action without another human decision.
- Run a bounded native/runtime acceptance probe using disposable local artifacts, the selected lower
  lane and supported registration/removal. It must prove more than source generation. Do not interfere
  with the live rename owner or claim normal-profile activation.
- Update any changed shipped harness declaration, generate locally, and require generation `-Check`,
  focused runtime/scheduler tests and paired AGENTS/CLAUDE validation. Current core PRs carry authored
  source only; generated files stay out of the commit and regenerate on main after merge.
- Obtain exact-head review and CI; commit, open the focused PR and merge under this task's authorization.
  Follow post-merge generation. Report the usable source/package revision and actual adoption boundary.

## Progress

- Pickup observed: `EXTERNAL_GOAL_CONTINUATION_PICKUP_20261004`, session `01a10853-2449-7201-8430-da461f8c606b`, native owner PID `27616`.
- Checkout/branch verified; fast-forwarded to current main `0f716f6` before edits. L4 resolved from `.agents/lanes/codex.json` and applied to the bounded implementation worker.
- Delivery slices: runtime/binder/regression repair on `Fix/ExternalGoalContinuation` (expected 6 files, under 1,000 lines); durable usage guidance on a subsequent `Docs/*` branch from updated main. Tests/review/CI gate each slice. No dependency on PR #90.
- Pickup marker: `EXTERNAL_GOAL_CONTINUATION_PICKUP_20261004`.
- Launch and pickup must be recorded as observed facts, not inferred from this goal's existence.

## Verification and current gate

- Runtime and binder repair implemented in four authored files (about 250 changed lines). Binding 29/29 and router 28/28 tests pass; continuation full run reached 29 tests with one 30-second subprocess transport timeout, whose isolated rerun passed (5.577s); the new external-goal transition test also passed alone (20.529s). Scheduler, goal-contract, paired agent files, generation -Check and harness checks pass.
- Native probe: `C:/Users/TommySeery/AppData/Local/Temp/external-goal-native-zsk72daq`. Real scheduler registration, live-foreground no-launch, yield, native L4 wake, valid complete nonce/owner receipt, exact external goal in child prompt and scheduler removal observed. Outer adapter output wrapper timed out; terminal artifacts independently verified. No normal-profile installation or hook activation claimed.
- Known flat lifecycle skill resolver defect is already owned by `docs/workflows/TECH_DEBT.md`; use loaded canonical skill files for this run.

## Next Steps

Scope: whole plan through all remaining phases and terminal delivery.
Current slice: freeze, independently review and deliver runtime/binder repair.
Remaining scope: separately deliver durable usage guidance, follow post-merge generation, report original-owner adoption boundary.
Done when: both repair slices are reviewed and merged with generation green and concrete adoption instructions recorded.

1. Verify the exact checkout/branch and record the pickup marker, actual session identity and selected L4
   lane here before source edits. This is a bounded side handoff; no critical-plan receipt exists.
2. Load the lane and bugfix lifecycle, implement the bounded runtime/guidance correction, and execute the
   regression and runtime acceptance described above. Do not recursively hand off this specified repair.
3. Carry review, CI and authorized merge to completion, with one real continuation if a result will outlive
   the turn. Use this in-worktree goal to own the repair while testing an external fixture.
4. Leave a concrete result here for the original owner: revision, verification, supported initialization
   command with its external plan and canonical owner path, and any real activation gate. The original
   owner alone adopts it and claims its foreground lease. Preserve its active work and authority.
