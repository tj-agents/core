# Merge worktree cleanup fallback progress

- Plan: `plans/merge-worktree-cleanup/MERGE_WORKTREE_CLEANUP_PLAN.md`
- Roadmap: `plans/merge-worktree-cleanup/MERGE_WORKTREE_CLEANUP_ROADMAP.md`
- Roadmap item: `merge-worktree-cleanup/fallback`
- Worktree: `C:\Users\tommy\source\repos\tj-agents\core\.worktrees\Fix-AutonomousHandoffSelection`
- Branch: `Fix/AutonomousHandoffSelection`
- PR: not opened
- Dependency/package gates: none
- Last reconciled: 2026-09-25 after the approved incremental review of the review-checkpoint delta

## Current state

- The exact Winwrap `Refactor-Value-Window-Factories` residual directory is empty, unregistered, and has no
  remaining topic branch, but a fresh non-recursive removal still fails because another process holds it.
- Winwrap's primary checkout and other linked worktrees now contain unrelated active work and must not be
  changed by this plan.
- Core PR #35 merged as `fb1be0a4e2663b34de4cad7f9d08501a367f431c`; exact post-merge CI run
  `36080559767` completed successfully. Core has no publish workflow, so no version-sync PR was created.
- The remaining root cause is host ordering: `engineering:merge` removes the linked worktree before applying
  `base:cd`, while per-command `workdir`, shell `cd`, and `git -C` do not retarget Codex or Claude.
- The packaged canonical `.agents/machine/handoff-codex/scripts` launcher cannot find the package-root
  `resources/machine/scripts/agent-cli.ps1`; the shallower host `skills` copies can.
- The implementation is committed and published: `base:cd`, `handoff`, and merge Step 5 transfer active
  directory removal to a confirmed native retarget or one successor; all three shared launchers resolve the
  deeper packaged canonical layout; the nine generated layouts are exercised; release metadata is 2.1.7.
- PR #38 merged on `main` as `fc7b78e6ba032451e974220918e8b91181290496`. The predecessor session was
  attached to the linked core worktree; this primary-checkout successor owns its physical removal.
- The clean linked target was unregistered by non-forced Git removal, but Windows denied deleting its now-empty
  root directory. Its local merged branch remains until that path is physically absent, as the final-inventory
  gate requires.
- Commit `e5b2dd0` selects and executes `engineering:handoff` when the next action moves to another owner or
  repository; `handoff-format` is explicitly pointer formatting, not a transfer. Full and incremental docs
  review are approved through `54b1fd4`; this review-only stamp is the remaining uncommitted state.

## Next Steps

Scope: whole plan through all remaining phases and terminal delivery.
Current slice: commit the review stamp, run final validation, and open the 2.1.8 PR without merging it.
Remaining scope: retry the core and exact Winwrap empty residual directories after their external handles
clear; delete the core merged branch only after its target is physically absent; obtain Tommy's explicit
approval before merging the standards PR; then finish plan closeout.
Done when: the residual directory is absent, the standards PR and plan closeout are merged, and core's base
and worktree inventory are clean.

## Completed work

- Winwrap Git cleanup completed through merged-branch deletion and linked-worktree unregistration.
- Core workflow correction, release metadata, generated outputs, and review remediations landed in PR #35.
- PR #35 cleanup returned core's primary checkout to clean current `main` and deleted its merged local branch.
- Host-retarget ordering, directory-release handoff ownership, packaged launcher resolution, focused coverage,
  2.1.7 metadata, and generated outputs landed in PR #38.
- PR #38 merged as `fc7b78e6ba032451e974220918e8b91181290496` after its green `verify` check.

## Verification

- Winwrap heads `52e65d3` and `404b795` are ancestors of `origin/main`; no open PR owns either branch.
- Current 2.1.8 candidate: 18 focused process-standard tests, plan-workflow, workflow-adoption, and workflow-contract
  suites pass; package generation and `pwsh .agents/sync-generated.ps1 -Check` pass.

## Reviews

- Docs review and its incremental pass are approved through `54b1fd4`; canonical work order: `reviews/Fix-AutonomousHandoffSelection.md`.

## Decisions, discoveries, blockers, and deviations

- Never force-remove the residual directory or terminate an owning process without explicit authority.
- Do not treat an empty residual directory as cleanup success or let the predecessor continue removal after
  a handoff; the successor owns physical removal and final verification after host release.
- The post-PR retry reconfirmed that the exact Winwrap residual is empty and unregistered, but non-recursive
  removal still failed because another process holds the directory.
- The core linked target is likewise unregistered and empty, but Windows denied its non-forced root-directory
  removal; do not force it or delete `Docs/CloseMergeWorktreeCleanup` until the path is physically absent.
- Do not merge the standards PR without Tommy's explicit approval.
- `workflow_ops.py skills` still looks for the obsolete flat `.agents/skills/...` path for kind-based skills;
  resolve when skill recording locates canonical kind paths and its regression coverage passes.
- Repository-wide `plan_graph.py` is currently red only for the pre-existing
  `plans/repo-declared-config/REPO_DECLARED_CONFIG_PROGRESS.md`, which has its own active sibling worktree;
  this plan does not edit or adopt that unrelated owner.
