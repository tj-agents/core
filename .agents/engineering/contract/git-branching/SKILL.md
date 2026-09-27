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

## Fetch first; use the remote default or the recorded stack parent

```bash
git fetch origin --quiet && git checkout -b <Type>/<Name> origin/main
```

Local `main` silently drifts behind, and branching off it builds and tests everything against a stale
tree. **That staleness is invisible locally: the build is green, because it is green against the old
tree.** It is how work that has already merged gets reinvented, and how a PR later trips the
current-with-base rule in the `merging` skill — by which point the wasted work is already done.

For a dependent stack layer, branch from its recorded parent's current tip instead of `origin/main`.
The parent must already contain the dependency; changing a PR's base does not transplant commits.

**Reusing an existing branch or worktree?** At session start, fetch and check
`git rev-list --count HEAD..<actual-base>` against the PR's default or stack-parent base; sync before
working, and never build on a stale tip. Don't
reflex-merge the default branch every turn: it will not refresh already-loaded instructions (only a fresh
session does), and mutating a dirty tree mid-task invites conflicts. Merge when you are behind and the
tree is clean.

## `<Type>/<Name>`, with the type prefix capitalized

`Feature/`, `Refactor/`, `Bug/`, `Fix/`, `Docs/`, `Chore/`. **Never create a lowercase variant of an
existing name.** A case-insensitive filesystem cannot hold two casings of one ref, so a remote carrying
both `feature/x` and `Feature/x` breaks `git fetch` and `git pull` **for everyone** with
`cannot lock ref … File exists`. Before creating a branch, match the casing of any existing branch of the
same name exactly.

## Large changes default to reviewable PR slices

A goal, feature, refactor or plan phase is not automatically one PR. Before implementing a large or
multi-concern change, divide it into focused delivery slices. Prefer stacked PRs for dependent slices;
put independent slices on branches from the remote default. Keep one goal and owner across them.

Record each slice's purpose, included code and tests, base/parent, dependencies, expected size and
verification gate in the existing plan or PR description. When branches exist, record their exact base
and head SHAs and PR links. This delivery map is required before growing a large change, not something
to reconstruct at merge time. Re-evaluate it when a new concern, review repair or integration failure
would expand the current PR.

Measure the proposed PR against its actual base with `git diff --numstat <base>...HEAD` and
`git diff --shortstat <base>...HEAD`. Count the proposed uncommitted work too. Report generated files,
lockfiles, documentation and mechanical moves separately from substantive code and tests; do not hide
their total. Line counts are a review warning, not a target or proof of safety. Unless the repository
sets a stricter budget, around 1,000 substantive added/deleted lines or 40 substantive changed files
requires an explicit split assessment before adding more scope, requesting final review or publishing
another candidate. Smaller changes spanning unrelated concerns need that assessment too.

Choose coherent boundaries, not equal-sized batches of files. Each landed slice must build, retain
working exposed behavior, preserve security invariants and include its relevant tests. Keep an atomic
schema/API/caller cutover together when splitting it would break those guarantees. Do not create dead
APIs, compatibility adapters forbidden by the project, or failing intermediate branches just to shrink
the displayed diff. Where possible, extract tested preparatory refactors or independent infrastructure
first. A large exception needs a recorded concrete reason, rejected split boundaries, measured size and
validation plan; "same feature", "same phase", or "already on this branch" is not sufficient.

Small repairs to the current slice stay with it. A substantial next slice may stack on code that has
not merged yet, including a refactor of that code. Do not orphan the parent or create an independent
branch that loses its dependency. If a PR is already oversized, preserve its exact head and working
changes and assess recovery before rewriting history. Map possible boundaries and compare the benefit
of smaller reviews with the cost of reconstructing and qualifying new intermediate states. An already
reviewed, validated candidate may warrant a frozen-scope exception, with its exact evidence and rejected
split options recorded; sunk effort alone is not a reason. When splitting, validate each layer and prove
the final stack tree preserves the intended result before superseding or rewriting the original PR.

## Maintain a dependent stack

Each child targets its immediate parent's branch; only the bottom PR targets the stack trunk, normally
`main`. Review each layer against that parent and validate its cumulative tree. Keep the stack map,
base/head SHAs and remaining scope in the one owning ledger. New slices continue the authorized goal;
they do not require routine permission or a new session.

Use verified native forge stack support or already-installed tooling where available. Do not assume
that a website feature is enabled locally, install tooling without authorization, or cap a necessary
stack at one parent-child pair merely because no stack tool is installed. Native Git and the forge CLI
can manage a recorded stack; check CI base-branch filters and equivalent merge protection for every
layer. Never bypass checks because a child targets another feature branch.

For manually managed GitHub branches, confirm base retargeting after the parent lands; branch deletion
settings affect it. A merge commit preserves the parent's SHAs. A squash or rebase merge usually needs
the child's own commits replayed onto the new base, using the recorded old parent tip rather than
replaying the whole parent. Inspect the resulting diff and rerun affected checks. Native stack support
may automate this; verify the result rather than applying a second manual rebase.

Land from the bottom up. Never merge a child into its unmerged parent's feature branch and call that
independent delivery. Parent edits require reconciling descendants and their exact-head review/CI
evidence. A stack improves review boundaries; it does not remove integration or deployment gates.

Research basis: [Google's small-change guidance](https://google.github.io/eng-practices/review/developer/small-cls.html)
and [GitHub's stacked PR documentation](https://docs.github.com/en/pull-requests/get-started/about-stacked-prs).
The numeric assessment triggers above are this workflow's heuristic, not a universal research cutoff.

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
