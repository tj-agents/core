---
name: session-guidance
description: Session guidance for an explicitly selected engineering lifecycle, including workflow ownership, staged skill loading, repair responsibility and authorized delivery continuity.
kind: contract
domain: process
---

# Selected engineering session guidance

These conventions apply when engineering is selected for the current scope. They grant no
implementation, publication or installation authority beyond the standing standards-defect default
below. Product profiles and compatibility policy remain
with the project. The common maintained-plan contract is `base:plan-artifacts`. The common
continuation owner is `base:goal-continuation`; it selects `engineering:persistent-workflow` when
an authorized task has a future decision that may outlive the current session.

## A task has an owning lifecycle — load it before the first edit

Authorized long-term or multi-phase work selects `engineering:plan-execution`, even when the user does
not name a plan or skill. Read an existing canonical goal before edits and keep its progress current.
A bounded behavior change selects `engineering:feature`; a defect selects `engineering:bugfix`.
Planning-only work selects `engineering:plan-authoring` and does not authorize implementation.
A question or review request alone grants no implementation authority. A status question during already
authorized execution should be answered before that execution continues.

## A link to another skill is a stage pointer, not a read

Load a referenced skill when its stage is actually entered, never because a document you are reading names
it. A procedure step, table row or route line says which skill owns that stage. Do not load the corpus
transitively. Use the host's native skill invocation when available or read its advertised source file.

## Keep large changes reviewable

Before implementing or expanding a large refactor or multi-concern change, apply
`engineering:git-branching` to define and measure PR-sized delivery slices. Deliver one slice at a time
by default: validate, review and merge when ready and authorized, then start the next from the updated
base. When work must build on an unmerged PR, maintain a proper stack. Allocate worktrees for active
execution needs independently of the number of branches. One goal may span many PRs. A phase label or
an existing open PR never justifies accumulating the whole goal in one diff. Reassess an oversized
candidate before adding more scope; preserve atomic behavior and security when choosing boundaries.

## Preserve one owner through completion

Act on authorized reversible work and keep the canonical plan aligned with observed results. A phase,
commit, open PR or context boundary does not narrow the original scope. Honor user limits and real
external-action gates. Use `engineering:handoff` for an actual authorized context transfer; it checkpoints
first, invokes one selected machine launcher, and releases the previous writer. Prompt-only requests
remain prompt-only. Missing runtime capabilities must be reported accurately, not assumed installed.

Follow `engineering:committing` for local checkpoints and the repository's selected delivery convention
when delivery is authorized. Bind remote monitoring to the exact repository, head and run; never imply
pending CI is owned without an active monitor. A failed test selects `engineering:failing-tests` and its
diagnose, repair and focused verification loop. Do not weaken a check merely to produce a pass.

## Maintain the right source owner

Give shared behavior one source owner, preserve published compatibility commitments, and record material
out-of-scope defects with an objective resolution condition in the existing project's debt or plan owner.
A defect in a consumed standards package or its source repository is the exception: a stale or broken
standard, including the automation that missed it, is a defect to diagnose, never a manual step to hand
to the user, and so is a standard that caused or failed to prevent a mistake. Diagnose it and launch `engineering:handoff` in bounded
side-workstream mode (the side workstream's goal records the defect) in the same turn, before the
current task resumes, without asking, regardless of that task's own authority; announcing a later or
separate fix instead of launching is a violation. This rule is the standing authorization: it covers
implementing, testing, opening the PR and merging once that repository's gates pass. Installing into
any other scope (the consuming repository included), publishing outside that repository, and
destructive operations stay gated; explicit user limits still hold.
Before committing or returning a terminal result, check the work against the standards that governed
it and reconcile every problem encountered: it is fixed, handed off, or already has the owning debt
entry. `engineering:docs-and-debt` defines the selected repository convention. Do not create a second
ledger for a standalone goal just to satisfy a repository-oriented procedure.
