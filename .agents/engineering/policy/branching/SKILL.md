---
name: branching
description: Find existing work, then branch from the fetched remote default with a `<Type>/<Name>` branch and an isolated checkout only for concurrent writers. Use when starting or reusing a branch or worktree.

kind: policy
domain: process
---

# Branching

Owns where work runs: existing-work lookup, branch base and name, PR boundaries and checkout allocation.

## Continue existing work before starting new work

Before branching or creating a worktree, run one `gh pr list` for open PRs by the author or bot touching the
same area, plus the unmerged remote branches. Continue matching work instead of starting fresh.
Corrections to existing work return to its owning PR: add only the changes its head lacks and return its URL.
Separately requested work with its own outcome gets its own branch.

```bash
git fetch origin --quiet
default=$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)
gh pr list --state open --author @me --search MapIndex --json number,headRefName,title
git branch -r --no-merged "origin/$default" --list "origin/*MapIndex*"
git switch -c Feature/MapIndex "origin/$default"   # only when neither command found the work
```

## Branch from the fetched remote default

Fetch once per work item and branch from `origin/<default>`, never local `main`: a stale local base builds
green against an old tree and reinvents work that already merged. The default branch and unrelated branches
are not implementation targets. When reusing a branch, run `git rev-list --count HEAD..<actual-base>` and merge
the base when behind and the tree is clean; do not re-merge every turn.

## `<Type>/<Name>`, with the type prefix capitalized

`Feature/`, `Refactor/`, `Bug/`, `Fix/`, `Docs/`, `Chore/`. Match the casing of any existing branch of the same
name exactly: a remote holding both `feature/x` and `Feature/x` breaks `git fetch` and `git pull` for everyone
on a case-insensitive filesystem with `cannot lock ref … File exists`.

## PR boundaries

The selected profile, or the user, decides how many PRs deliver the outcome. Every landed PR builds, keeps
exposed behavior working and includes its tests; never split a cutover into broken intermediate states.

## Worktrees follow active execution

Reuse an available checkout once its previous work is preserved and no writer, build, monitor or session owns
it; verify branch and status before switching. Create a separate worktree only for a concurrent writer or
build, or on request, through `engineering:open-worktree`, which claims it and later retires it. Never run two
writers in one checkout. Working markdown rides the branch that owns its subject; never edit one plan file in
two checkouts.
