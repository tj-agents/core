# Merge worktree cleanup fallback progress

- Plan: `plans/merge-worktree-cleanup/MERGE_WORKTREE_CLEANUP_PLAN.md`
- Roadmap: `plans/merge-worktree-cleanup/MERGE_WORKTREE_CLEANUP_ROADMAP.md`
- Roadmap item: `merge-worktree-cleanup/fallback`
- Worktree: `C:\Users\tommy\source\repos\tj-agents\core\.worktrees\Docs-CloseMergeWorktreeCleanup`
- Branch: `Docs/CloseMergeWorktreeCleanup`
- PR: not opened for the host-retarget repair
- Dependency/package gates: none
- Last reconciled: 2026-09-25 at the focused-green host-retarget implementation milestone

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
- The implementation is complete in the working tree: `base:cd`, `handoff`, and merge Step 5 transfer active
  directory removal to a confirmed native retarget or one successor; all three shared launchers resolve the
  deeper packaged canonical layout; the nine generated layouts are exercised; release metadata is 2.1.7.
- This branch is synchronized with `origin/main` at `ce038fb`; the implementation, generated outputs, tests,
  and resumed plan state are the only uncommitted changes.

## Next Steps

Scope: whole plan through all remaining phases and terminal delivery.
Current slice: commit the focused-green candidate, complete review and any required remediation, then open
the standards PR.
Remaining scope: retry the exact empty Winwrap residual after its external handle clears; obtain Tommy's
explicit approval before merging the standards PR; then complete normal merge and plan closeout.
Done when: the residual directory is absent, the approved standards PR and plan closeout are merged, and
core's base and worktree inventory are clean.

## Completed work

- Winwrap Git cleanup completed through merged-branch deletion and linked-worktree unregistration.
- Core workflow correction, release metadata, generated outputs, and review remediations landed in PR #35.
- PR #35 cleanup returned core's primary checkout to clean current `main` and deleted its merged local branch.
- Host-retarget ordering, directory-release handoff ownership, packaged launcher resolution, focused coverage,
  2.1.7 metadata, and generated outputs are complete in this commit.

## Verification

- Winwrap heads `52e65d3` and `404b795` are ancestors of `origin/main`; no open PR owns either branch.
- Current candidate: 17 focused process-standard tests; all nine generated launcher layouts; packaging
  self-containment; CLI session recovery; 176 repository tests; 564 shared-runtime tests with 8 expected
  platform skips; generated-output check; and working-tree catalog digest check all pass.
- The committed-tree catalog check remains pending until the immutable candidate commit exists, because its
  `--source-revision HEAD` input intentionally excludes working-tree changes.

## Reviews

- `reviews/Fix-MergeWorktreeCleanupFallback.md` is complete for PR #35 through watermark `4d57819`; it does
  not cover the newly authorized host-retarget and launcher repair. A fresh full review is required.

## Decisions, discoveries, blockers, and deviations

- Never force-remove the residual directory or terminate an owning process without explicit authority.
- Do not treat an empty residual directory as cleanup success or let the predecessor continue removal after
  a handoff; the successor owns physical removal and final verification after host release.
- Do not merge the standards PR without Tommy's explicit approval.
- `workflow_ops.py skills` still looks for the obsolete flat `.agents/skills/...` path for kind-based skills;
  resolve when skill recording locates canonical kind paths and its regression coverage passes.
- Repository-wide `plan_graph.py` is currently red only for the pre-existing
  `plans/repo-declared-config/REPO_DECLARED_CONFIG_PROGRESS.md`, which has its own active sibling worktree;
  this plan does not edit or adopt that unrelated owner.
