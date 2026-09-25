# Merge worktree cleanup fallback

## Authorized scope

Follow the Winwrap handoff through completion: safely clean the two merged Winwrap worktrees
and local branches, then correct core's shared merge workflow so repositories without
`scripts/worktrees.ps1` still receive safe post-merge cleanup. Do not change Winwrap library or
documentation content, delete remote branches, force-push, or remove dirty, unmerged, primary,
or open-PR-owned worktrees.

## Problem

The shared `engineering:merge` workflow requires immediate post-merge worktree cleanup but
directs repositories to `./scripts/worktrees.ps1 close ...` without a documented fallback.
Winwrap does not ship that helper, and a completed stacked merge left its primary checkout on
`Feature/Device-Io` plus a linked `Refactor/Winwrap-Structure` worktree.

## Decisions

- Keep `.agents/engineering/workflow/merge/SKILL.md` as the canonical source and regenerate
  host/distribution outputs.
- Preserve every existing cleanup gate: never remove the primary checkout, dirty or unmerged
  content, or a branch with an open PR.
- Use native Git only as the fallback when the repository helper is absent, with explicit
  verification before each destructive step.

## Phases

### 1. Clean up Winwrap

- Fetch current refs and verify both worktree heads are ancestors of `origin/main`.
- Inspect tracked and untracked state in every worktree and confirm no open PR owns either
  branch.
- Move the primary checkout to current `main`, delete the merged feature branch, close the clean
  linked worktree, and delete its merged local branch.
- Verify final worktree, branch, and status inventory. If Windows holds only an empty residual
  directory open after Git unregisters it, preserve that fact until the handle clears and retry
  without terminating an unrelated process.

Verification gate: fresh Git worktree/branch/status evidence demonstrates current `main`, no
merged local branches, no registered linked worktree, and no user-owned untracked files lost.

### 2. Correct and deliver the shared workflow

- Inspect the canonical merge contract, routed standards, package manifests, generation rules,
  and related tests.
- Add the smallest explicit helper-absent fallback and make cleanup completion an unmistakable
  delivery gate while preserving the safety rules.
- Add or update focused regression coverage, refresh required package versions/catalog digests,
  regenerate distributions, and run repository-mandated validation.
- Review the exact candidate and deliver it through the repository's normal workflow where the
  current authorization and repository state permit.

Verification gate: focused tests plus `pwsh .agents/sync-generated.ps1 -Check` pass, independent
review findings are resolved, and delivery reaches its authorized terminal state.

## Acceptance criteria

- Winwrap's primary checkout is current `main`; both specified merged local branches are gone;
  the linked worktree is unregistered and its directory is removed once no external process
  holds it.
- The canonical merge workflow explicitly supports repositories without
  `scripts/worktrees.ps1` and makes post-merge cleanup a required, evidenced transition.
- Generated outputs and package/catalog metadata agree with canonical sources.
- Required tests, generation checks, review, and authorized delivery are complete.
