# Select execution lanes before implementation

## Outcome and authority

Make execution workflows load `engineering:lanes` and select the lane appropriate to the next phase
before implementation, including standalone and runtime-unavailable execution. A planning session must
not silently implement an approved plan on its design model.

Tommy explicitly interrupted the approved skill-kind migration to require lower-model implementation and
fix why the lanes skill had not been selected. The standing standards-defect rule in
`engineering:session-guidance` authorizes this separate repair through implementation, testing, PR and
merge once repository gates pass. Normal-profile installation, hook-trust changes and publication outside
this repository remain separately gated. Do not refresh or install plugins for this task.

## Owner and isolation

- Checkout: `C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-ExecutionLaneSelection`
- Branch: `Fix/ExecutionLaneSelection`
- Starting commit: `7145363ee934ca1526a735e5b5d8ba4ecee80332` (fetched `origin/main`).
- Origin: `tj-agents/core`.
- This file is the single side-workstream goal and progress owner.
- Original task, retained by the originating session:
  `C:\Users\TommySeery\.claude\plans\tj-agents-core\SKILL_KIND_RENAME.md`.
  Do not edit that plan, perform its taxonomy migration, or adopt its ownership.
- The originating checkout has unrelated modified repo-declared-config plan documents; leave them alone.
- One successor owns this repair checkout after launch. No other implementation writer exists here.

## Diagnosis and source evidence

The original session completed the taxonomy design, received "yep nice lets go", and announced
implementation without first selecting an execution lane. Tommy interrupted before any implementation
commands or edits. The session's omission is real; the source workflow also lacks the necessary step.

`.agents/engineering/workflow/plan-execution/SKILL.md` never explicitly loads `engineering:lanes`.
Its standalone/runtime-unavailable section exits before the remaining repository procedure; that path
allows execution with available tools without lane selection. Repository dispatch also permits direct
execution and parent fallback without connecting that choice to the selected phase lane.

The existing `.agents/engineering/contract/lanes/SKILL.md` already defines L1 as design only and
requires selecting again as the phase changes. Preserve that single owner rather than duplicating its
ladder. Historical in-session lane execution and model-control investigation work is already merged;
preserve its small/medium in-session execution and substantial-design transfer distinction.

## Bounded repair

1. Add an explicit lane-loading and phase-selection step before the execution-mode fork in
   `plan-execution`, so both standalone and repository execution receive it.
2. Reconcile the lifecycle entry instructions in `session-guidance` and any directly necessary
   `lanes` clarification so a completed design transitions to implementation at its selected lane.
3. Direct execution and fallback must respect the canonical lane rules. A missing preferred worker
   must not silently promote a complete implementation goal into L1. Preserve permitted tiny inline
   work and supported native fallbacks; report actual capability limits accurately.
4. Preserve the current distinction between bounded lower-lane workers in an existing session and
   a fresh execution owner for substantial critical-plan design. Do not require a new terminal solely
   to obtain a cheaper model, a second writer, or a handoff for every phase.
5. Keep model identifiers and effort mappings exclusively in the canonical lane tables. Do not give
   a multi-stage workflow a fixed lane in metadata or introduce a parallel ladder.
6. Update the shipped harness manifest when required by the shared maintained-plan contract. Shared
   behavior remains authored in `.agents`; host entry points stay thin.

Inspect the repository's existing instruction-delivery tests and add or adjust meaningful regression
coverage for the lane step reaching both execution modes and surviving phase transitions/fallback.
Use focused existing checks; do not assert prose snapshots that merely mirror implementation wording.

## Execution lanes

This bounded, diagnosed instruction repair starts at **L4**: the mechanism, intended behavior and
acceptance are specified, and repository checks can catch delivery regressions. Resolve the actual
model/effort from the installed canonical Codex lane table. Keep clerical edits at L5 when a separate
bounded worker is worthwhile. Re-route review under `engineering:lanes`; L1 is reserved for genuinely
new design decisions and is not the implementation or delivery executor.

Load `engineering:lanes` before the first deliverable edit. This handoff already supplies the fresh L4
owner for the bounded repair; do not recursively transfer it just because this goal is a plan file.

## Verification and delivery

Read this checkout's `README.md`, `AGENTS.md`, and `SOURCE_LAYOUT.md`. The fetched default branch uses
source-only PRs: generated paths are rejected by CI and refreshed after merge on main. Run
`python -B scripts/update_catalog_digests.py` and `pwsh .agents/sync-generated.ps1` for local tests,
then require `pwsh .agents/sync-generated.ps1 -Check`; leave generated output out of the PR.
Run the relevant instruction/session delivery checks and verify AGENTS/CLAUDE pairing in both
directions. Observe the normal immutable review, CI and merge gates. Commit verified authored changes,
open the focused PR, and carry it through merge under the standing authorization. Record the PR,
commit, checks, and actual completion or concrete external gate here. A source merge does not prove
installed host adoption and does not change instructions already loaded by the original session.

## Progress

- 2026-10-04: Pickup `EXECUTION_LANE_SELECTION_PICKUP_20261004` acknowledged by successor
  session `01a107e8-754e-7d53-a613-1bbd8f398a73` at `2026-10-04 17:17:17 UTC`.
  Confirmed exact checkout and `Fix/ExecutionLaneSelection`; fetched origin and verified zero commits
  behind `origin/main`. Loaded plan-execution, bugfix and lanes. Installed canonical Codex table resolves
  selected L4 to `gpt-6.1-sol` with `medium` reasoning effort. This session owns the bounded repair.
- Delivery slice: one focused source instruction repair plus delivery regressions, based on
  `7145363ee934ca1526a735e5b5d8ba4ecee80332`; no generated distribution output will be staged.
- 2026-10-04: Diagnosed missing lane selection before standalone and repository execution.
- Created isolated branch from fetched default; no source implementation changes yet.
- Native Codex 0.160.0 is available. Launch uses the shipped terminal and lane-resolution helpers,
  preserving installed plugins and hook trust without an automatic marketplace refresh.
- Pickup marker: `EXECUTION_LANE_SELECTION_PICKUP_20261004`.
- Launch submission is not acknowledgement; successor records actual pickup below.
- Repair implemented in the canonical plan-execution, session-guidance and lanes definitions. Both
  execution modes now receive lane loading before implementation; phase changes and fallback reselect
  without treating inherited settings as an applied lane. Tiny follow-ups and substantial-design transfer
  remain owned by the existing lane contract.
- Local verification: packaged engineering hooks (8), process standards (19), lane tables (23), workflow
  route (17), and plan workflow acceptance (19) passed. Generation check reports zero drift; catalog and
  all three harness declarations pass validation. Existing harness requirements cover the same shipped
  lane definition, tables and hooks; this change introduces no dependency, permission or hook requirement.
  AGENTS/CLAUDE audit: four files, zero pair/pointer errors. Whitespace check passed.
- One plan-workflow parity check initially observed source formatting newer than the generated mirror;
  regenerated before rerunning the same 19 tests, which passed. No check was weakened.
- Continuation owner initialized as `6619eff697e53df499c9d2de`; foreground delivery remains in this
  session. No unattended wake is claimed until registration succeeds.

## Next Steps

1. Commit the verified authored candidate and freeze its exact base/head for independent L4 docs review.
2. Open the focused PR, bind exact-head validation, and merge when repository gates pass. Keep this goal aligned with
   observed evidence; record any real blocker with its resolver and observable resume condition.
3. Return the result to the original task through this file. Do not modify the skill-kind rename plan
   or install this change into a normal profile.
