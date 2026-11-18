# Prevent Git maintenance from racing PlanWorkflowHarness teardown

Status: blocked before handoff; the isolated repair worktree is clean at base 376df0ced5283a4ee4247d07feb10e8671b64475.

## Outcome

Stop automatic Git maintenance from racing temporary repository cleanup in PlanWorkflowHarness. Add a focused regression that verifies the harness does not start detached maintenance or garbage-collection children from repository construction through `pr-slice-rollover`.

## Context and authority

Observed 2026-10-12 in causal core CI run 38266381371, attempt 1. Linux failed in PlanWorkflowHarness.__exit__ while removing /tmp/.../admin/.git: OSError: [Errno 39] Directory not empty. The same exact tree passed its reviewed PR CI and causal CI attempt 2 passed after retry, so the failure is intermittent and independent of PR #219.

Diagnosis evidence is retained in the core workflow artifact 914089a66cff593a-causal-main-ci-failure.log. The reviewed PR and merge trees are identical. Bounded Git TRACE2 evidence showed detached maintenance child starts. Existing tests/test_check_generated_paths.py disables gc.auto and maintenance.auto because Git metadata writes can race fixture cleanup; that precedent supports the cause.

- Kind: bug
- Stable problem record: [B006 — Plan workflow fixture teardown races detached Git maintenance](../../BUGS.md#b006-plan-workflow-fixture-teardown-races-detached-git-maintenance) in the core bug register.
- Priority: P2
- Source owner: tj-agents/core PlanWorkflowHarness test fixture
- State: blocked
- Blocker: required native launcher capability is unavailable under the current explicit profile and machine-permission limits.
- Resolver: the machine launcher owner or explicit authority to install/update the required launcher and hook/permission wiring.
- Resume condition: a supported native handoff can run without changing a normal profile or machine permissions, or the user explicitly authorizes those specific changes.

Standing engineering:session-guidance authorizes repair, testing, review, PR and merge for a diagnosed shared standards defect. The current task explicitly forbids normal-profile refresh and machine-permission changes. The canonical handoff prelaunch gate requires marketplace/plugin and hook-trust/permission convergence. No launcher invocation occurred and no handoff was claimed. This goal remains the sole repair owner until a supported bounded handoff is available; B006 is the canonical problem record.

## Repair scope

Worktree: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-PlanFixtureMaintenanceRace
Branch: Fix/PlanFixtureMaintenanceRace
Base: 376df0ced5283a4ee4247d07feb10e8671b64475
Owner: unassigned successor after the blocker is resolved
Lane: L4 specified implementation

Set gc.auto=0 and maintenance.auto=false immediately after initializing the fixture repository and before its first commit. Add a focused TRACE2 regression over repository construction through pr-slice-rollover that verifies no maintenance or garbage-collection child starts.

Do not alter consumer profiles, installed plugins, machine permissions or unrelated test fixtures. Do not combine this fix with the already merged convention-approval configuration repair.

## Acceptance

- Publish B006 through the docs closeout branch, then fetch and reconcile that register entry before implementation so no duplicate problem record is created.
- Disable automatic GC and maintenance before the harness makes its first commit.
- Verify the fixture lifecycle through pr-slice-rollover starts no detached maintenance or GC child.
- Run the focused regression and required repository checks.
- Complete independent review, exact-head Windows/Linux CI, guarded PR delivery and causal generated publication.
- Preserve the original convention-approval repair and its independently owned docs closeout.

## Next action

Blocked until the resume condition above is met. Once unblocked, select one L4 implementation owner, apply the two repository-local settings before the first commit, and add the bounded TRACE2 regression. Then follow the normal focused verification, review and delivery gates.

## Progress

- 2026-10-12: PR #219's reviewed-head Windows/Linux CI passed. Causal main CI attempt 1 exposed this intermittent Linux fixture teardown failure; attempt 2 passed. The merge/configuration tree is unchanged from the reviewed candidate.
- 2026-10-12: read-only diagnosis connected the .git cleanup race to automatic Git maintenance using four bounded TRACE2 child starts and the existing gc.auto/maintenance.auto fixture precedent.
- 2026-10-12: worktree Fix/PlanFixtureMaintenanceRace was created clean at 376df0ced5283a4ee4247d07feb10e8671b64475. A canonical native handoff could not pass its prelaunch gate within the existing explicit prohibition on profile refresh and machine-permission changes; no launcher was invoked. Keep the repair blocked and unassigned until the stated capability becomes available.
