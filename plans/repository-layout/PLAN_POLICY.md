# Repository-owned maintained plans: Claude policy slice

Authorization: Tommy approved the repository-layout proposal and said "go ahead with this" on 2026-10-07.
This is a bounded independent implementation/delivery slice, not ownership of the entire migration.
Working checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Docs-RepoOwnedPlanConventions
Branch: Docs/RepoOwnedPlanConventions
Base: origin/main 61d4920477a313528f855babd2e4ee4ccdf3d8f6.
Lane: L4, specified shared-policy change with regression and documentation validation.
Full goal owner: Codex, Feature/RepositoryOwnedLayout, with the goal at
C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-RepositoryOwnedLayout/plans/repository-layout/REPOSITORY_LAYOUT_PROPOSAL.md.
You are not alone in the codebase; preserve others' edits and adapt to their disjoint ownership.

## Outcome and owned paths

Update the shipped common maintained-plan contract so goals for repository work belong in that repository.
Respect an existing declared plans/docs-plans convention; otherwise default to plans/<goal>/.
The active delivery branch owns current planning state. Before execution/handoff, promote any host scratch
draft into the repository owner, preserve its decisions/progress, and verify recovery references.
Standalone non-repository tasks keep their own task-directory goal. Runtime state and secrets stay outside Git.

Own:
- .agents/base/policy/plan-artifacts/SKILL.md and its existing shipped context/test surfaces.
- .agents/engineering/convention/plans/SKILL.md, workflow/plan-authoring/SKILL.md and
  utility/workboard/SKILL.md only where needed to make this resolved storage contract consistent.
- The existing focused tests and README documentation directly needed for these policy changes.

Do not own allocation/helper scripts, open-worktree conventions, marketplace/kit source, finisher scripts,
other project migrations or the full-goal artifact. If those expose issues, record a concrete return to
the full-goal owner; do not start overlapping repair writers.

## Delivery boundary and acceptance

The shared text is authored once under .agents and ships to both hosts through existing package generation.
Inspect the harness manifest for each changed standard; update it in the same change when requirements
change, otherwise record why current declarations cover the unchanged delivery mechanism.
Never commit plugins generated output. No copying this contract into consumer AGENTS files as normal setup.
Update plan discovery to prefer repository-owned current goals while preserving discovery of unfinished
legacy external goals until migration. Do not silently delete those external goals or require a new ledger
for standalone tasks.

Verify repository plans, existing declared conventions, linked-checkout ownership, standalone goals and
legacy discovery; use focused meaningful tests/doc checks and the existing docs-review procedure.
Commit the stable source change, open the plain GitHub PR, complete required review/CI and merge through
normal core gates under this goal authorization. Native Claude acceptance must observe the shipped
contract; generation alone is not host acceptance. Do not stop at an open PR when delivery can continue.

## Next Steps

Scope: this independently owned policy slice through reviewed, green, authorized merge and return evidence.
Current slice: common plan-storage contract and consistent discovery/documentation.
Remaining scope: full core helper, cleanup, marketplace, project/machine migration stays with the Codex owner.
Done when: the policy source is merged, generated/host acceptance is recorded and its PR/result returned
to the full-goal owner without duplicate writers or goal copies.

1. Read this goal, AGENTS.md, README.md, selected bugfix/feature and lane contracts; confirm branch/head.
   Write .agents/continuation/plan-policy-pickup.json with harness claude, your session identity, branch,
   head, timestamp and first_action before deliverable writes; the predecessor observes this file.
2. Read the owned current source, apply the specified contract, validate focused behavior and commit.
3. Review, publish the plain GitHub PR and own exact-head CI to authorized merge. Initialize the supported
   persistent workflow when delayed results require it. Keep this goal current at real transitions.
4. Return the PR, merged source/generation identities, verification and any concrete remaining gate to
   the full-goal owner's goal. Preserve its writer ownership: use an outcome file in this checkout and
   announce its absolute path rather than editing its canonical goal concurrently.
