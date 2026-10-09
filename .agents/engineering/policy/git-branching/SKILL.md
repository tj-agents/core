---
name: git-branching
description: Branch hygiene and reviewable delivery slices — finish and merge one ready, authorized PR at a time by default; maintain a proper stack whenever work must build on an unmerged PR; allocate worktrees for active execution needs. Covers fresh bases, branch casing, measured scope and independent guidance changes. Use before creating or reusing a delivery branch or worktree.

kind: policy
domain: process
---

# Branching

## Resolve the work before choosing its branch

The authorized outcome defines the work; its delivery slice defines the review boundary. A plan or
ledger preserves that identity, while branches and checkouts locate execution. Resolve the slice and
its owning review from the request, canonical plan, handoff, PR history and Git evidence before choosing
a publication branch. A branch lookup answers where a review runs; an empty result leaves work ownership
to be established from that evidence.

Corrections that complete or repair an existing slice return to its owning review, including corrections
implemented on another branch. Verify the review's current head and base, compare the correction commits
or equivalent patches with that head, and integrate only the missing changes into its branch. If that
review already contains them, update its explanation and return its URL. Preserve its base relationship
unless the actual dependency changed.

Separately authorized work with its own outcome follows the slice assessment below and may receive its
own review. Record that scope distinction in the existing plan or PR description. When the earlier review
is closed or merged, reconcile its result before choosing the next slice. Conflicting ownership evidence
leaves publication pending while safe local implementation and commits continue.

For plan-managed work, the ledger's `PR:` field names the owning review URL; `not opened` means the
assessed slice has no review yet. Update execution location separately during a handoff. The repository
state provider carries this field as `artifacts.pull_request`; `delivery-preflight` resolves it against
the forge, falling back to the current delivery binding and then the branch's review. Standalone work
carries the same facts in its existing goal or handoff and may supply the owning URL to preflight.

Once ownership is resolved, use a branch for that slice. The default branch and unrelated branches are
not implementation targets because their commits would mix delivery scopes. Planning-only authoring may
start in the normal checkout; the delivery branch carries its plan with its substantive work.

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

## Deliver one slice at a time

The default is sequential delivery: implement the current focused slice, validate and review it, merge
it as soon as it is ready and authorized, sync the remote default, then start the next slice from that
updated base. Plan the full sequence while keeping one delivery slice active by default. A future
dependency in a plan does not by itself require concurrent branches or open PRs.

A preparatory slice exists to unblock the named substantive work. Once it has landed and its required
checks are satisfied, begin that next authorized slice. Reuse the recorded split assessment while its
scope and measured inputs remain valid; repeat it only for a changed concern, dependency, base or
candidate. Required review and delivery checks still apply to their own candidate. Do not turn the
completed preparation into another round of preparation without identifying the new fact that requires
it.

When the next slice must proceed before its required parent can land, record the concrete constraint
preventing the parent from merging and why proceeding now is necessary. Use a stack for that overlap.
**Every PR that builds on another unmerged PR must be stacked**: branch from the parent's verified tip,
target the immediate parent, review the child-only delta and validate the cumulative tree. Once that
dependency exists, stack handling is required. The `stack` skill owns the procedure.

| Situation | Next action |
|---|---|
| Current slice is ready and authorized to land | Merge it, sync the default branch, then begin the next slice |
| Current slice still needs implementation, checks or review | Finish that slice and resolve its delivery blockers |
| A concrete constraint requires dependent work before the parent can land | Record the reason and maintain a proper parent/child stack |
| An independently authorized task needs concurrent work | Branch from the remote default and isolate its active writer |

Keep necessary stacks as small as the active work requires. Land ready parents promptly through the
selected merge workflow and reconcile their children before continuing. Preserve user delivery holds;
a hold is a constraint to resolve, not a reason to accumulate speculative descendants.

## Reviewable PR boundaries

A goal, feature, refactor or plan phase is not automatically one PR. Before implementing a large or
multi-concern change, divide it into focused delivery slices. Deliver those slices sequentially by default;
use the unmerged-dependency rule above when overlap is necessary. Keep one goal and owner across them.

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

Complete and land the current slice before beginning a substantial next slice by default. A separately
scoped change that depends on unmerged code follows the stack relationship above. Corrections within
the existing slice follow its owning review as resolved above. If a PR is already oversized, preserve its exact head and working
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

## Worktrees follow active execution

Branch/PR dependencies and checkout allocation are separate decisions. Reuse an available checkout for
sequential work once its previous work is safely preserved and no writer, build, monitor or active session
owns it. Verify the branch, status and task binding before switching. A separate worktree is appropriate
for concurrent writers/builds, necessary checkout isolation or an explicit request.

A stack can keep inactive layers as Git branches and use one active checkout. Allocate another checkout
only for work that needs one now. Before another dependency restore or build, account for available disk
space and the generated outputs already present in existing checkouts. Retire completed worktrees through
`engineering:open-worktree` once their commits and required evidence are safely preserved.

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
