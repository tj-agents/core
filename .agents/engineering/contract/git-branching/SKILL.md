---
name: git-branching
description: Branch hygiene for agent work — planning-only authoring may begin without a delivery worktree, but active delivery branches carry their plan and ledger with substantive work. Covers branching from fetched `origin/main`, capitalized `<Type>/<Name>` casing, syncing reused worktrees, keeping branch-local refactors with their feature, when a stack is warranted, and splitting durable guidance from runtime work. Use before delivery work or when creating or reusing a branch/worktree.

kind: contract
domain: process
---

# Branching

**Before starting delivery work, create a branch for it if you are not already on one.** Never commit code to
the default branch or to an unrelated one. Planning-only authoring may start in the normal checkout; once
delivery begins, the owning branch carries the plan and ledger with its substantive work.

## Fetch first, and branch from the remote default — never from local `main`

```bash
git fetch origin --quiet && git checkout -b <Type>/<Name> origin/main
```

Local `main` silently drifts behind, and branching off it builds and tests everything against a stale
tree. **That staleness is invisible locally: the build is green, because it is green against the old
tree.** It is how work that has already merged gets reinvented, and how a PR later trips the
current-with-base rule in the `merging` skill — by which point the wasted work is already done.

**Reusing an existing branch or worktree?** At session start, fetch and check
`git rev-list --count HEAD..origin/main`; sync before working, and never build on a stale tip. Don't
reflex-merge the default branch every turn: it will not refresh already-loaded instructions (only a fresh
session does), and mutating a dirty tree mid-task invites conflicts. Merge when you are behind and the
tree is clean.

## `<Type>/<Name>`, with the type prefix capitalized

`Feature/`, `Refactor/`, `Bug/`, `Fix/`, `Docs/`, `Chore/`. **Never create a lowercase variant of an
existing name.** A case-insensitive filesystem cannot hold two casings of one ref, so a remote carrying
both `feature/x` and `Feature/x` breaks `git fetch` and `git pull` **for everyone** with
`cannot lock ref … File exists`. Before creating a branch, match the casing of any existing branch of the
same name exactly.

## Don't branch to refactor code from the feature you are already on

If the code only lives on the current feature branch and is not yet in the default branch, the refactor is
part of that feature — stay on the branch and commit there. A fresh `Refactor/*` branch is only for code
**already merged**. Branching off an in-flight feature fragments it across two PRs and orphans the
original.

## Stack only for a real dependency

Stack a branch on another only when the child cannot build or pass without the parent's unmerged code —
never to enforce merge order alone (independent PRs land correctly in sequence without a shared branch;
confirm with `git merge-tree`) — and only by branching the child from the parent's tip once the parent's
commits exist; retargeting an already-diverged PR needs a manual rebase and force-push, not just a base
change.

GitHub retargets a stacked PR's base automatically only when the parent's head branch is deleted on
merge — check that repo's `delete_branch_on_merge` setting first; it's off on several of Tommy's repos.
Retargeting just moves the base pointer, so the child's diff stays clean only when the parent landed as a
merge commit (same SHAs on `origin/main`, the `merging` skill's `--merge` strategy); a squashed or
rebase-merged parent gives new SHAs, so rebase the child with `git rebase --onto origin/main
<old-parent-tip> <child>` before trusting its diff again. GitHub has no stacking beyond that — keep a
dependent stack to one parent→child pair without Graphite or `spr`, and confirm CI's base-branch
allowlist covers it.

## Working docs ride along; durable guidance does not

Non-code working markdown is non-breaking. Plans, roadmaps, and ledgers ride the branch that owns their active
delivery slice, so a material update can share the substantive commit instead of creating a transport tail.
Planning-only authoring needs no worktree, but one logical ledger must never be edited in two checkouts.
Scratch notes and tech-debt files may ride the branch that owns their subject. Never force-push to tidy a
stray markdown file swept in by `git add -A`.

**Durable global guidance is different.** When feature work changes an always-loaded instruction file, a
playbook, or a skill, split that change immediately onto a `Docs/*` branch cut from the remote default,
review it, and land it on its own. Never leave guidance stranded behind a feature PR or mixed into a
runtime commit — every later session reads the guidance, not the feature.
