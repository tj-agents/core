---
name: session-guidance
description: Session guidance for an explicitly selected engineering lifecycle, including workflow ownership, staged skill loading, repair responsibility and authorized delivery continuity.
kind: policy
domain: process
---

# Selected engineering session guidance

These conventions apply when engineering is selected for the current scope. They grant no
implementation, publication or installation authority beyond the standing standards-defect default
below. Product profiles and compatibility policy remain
with the project. The common maintained-plan contract is `base:plan-artifacts`. The common
continuation owner is `base:goal-continuation`; it selects `engineering:persistent-workflow` when
an authorized task has a future decision that may outlive the current session.

## When the user calls out a mistake

When the user calls out a mistake, before apologizing or drafting feedback, check whether a governing
standard caused or failed to prevent the mistake. This includes a missing, ambiguous, contradictory,
mispriced or unenforced standard across every
consumed `tj-agents` plugin on both hosts. Answer the user's direct question first. If it did,
launch `engineering:handoff` in bounded
side-workstream mode in the same turn under the standing authorization, before the original task resumes.
An apology, a SendFeedback draft or local memory does not substitute for this source-owner repair. Existing
user limits and scope gates still apply. Questions ask for reasoning: explain and defend recommendations with
evidence, change them only for new evidence or a stated user decision, and say what changed.

## A task has an owning lifecycle — load it before the first edit

Authorized long-term or multi-phase work selects `engineering:plan-execution`, even when the user does
not name a plan or skill. Read an existing canonical goal before edits and keep its progress current.
A bounded behavior change selects `engineering:feature`; a defect selects `engineering:bugfix`.
Planning-only work selects `engineering:plan-authoring` and does not authorize implementation.
A question or review request alone grants no implementation authority. A status question during already
authorized execution should be answered before that execution continues.

Before implementation, load `engineering:lanes`, select the next phase's lane, and apply it through the
current host's supported controls or a bounded lane worker. Select again as the phase changes or a
dispatch falls back. Design approval does not select an implementation lane. The canonical lane contract
owns direct execution, tiny inline follow-ups, capability limits, and when substantial design needs a
fresh execution owner; apply it even when the engineering runtime is unavailable.
On Claude, hand multi-phase work and any delegated design, implementation, or review phase to Codex before
delegating. An explicit user choice of Claude may keep non-frontier work local; otherwise do not fall back.

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

When preparation or approved design has resolved the next action, enter that action through the owning
lifecycle. A failed CI observation requires recovery under `engineering:plan-execution`; it does not end
ownership or establish a CI result.

Act on authorized reversible work and keep the canonical plan aligned with observed results. A phase,
commit, open PR or context boundary does not narrow the original scope. Honor user limits and real
external-action gates. Use `engineering:handoff` for an actual authorized context transfer; it checkpoints
first, invokes one selected machine launcher, and releases the previous writer. Prompt-only requests
remain prompt-only. Missing runtime capabilities must be reported accurately, not assumed installed.

Follow `engineering:committing` for local checkpoints and the repository's selected delivery convention
when delivery is authorized. Bind remote monitoring to the exact repository, head and run; never imply
pending CI is owned without an active monitor. A failed test selects `engineering:failing-tests` and its
diagnose, repair and focused verification loop. Do not weaken a check merely to produce a pass.

A terminal goal closes its own session as its final action, after its workflow's remaining steps and
the completion report: run `machine:peer-cli`'s
`finish.ps1` when `cleanup_proof.py` printed `removable` for this merged linked worktree,
`close.ps1` for any other checkout. Stay open while the final message asks the user something or is
an answer that exists only in the transcript. A handoff predecessor follows `engineering:handoff`'s
release instead.

## Maintain the right source owner

Give shared behavior one source owner, preserve published compatibility commitments, and fix, hand off or
record every defect you notice before moving on, as `engineering:docs-and-debt` defines.
A defect in a consumed standards package or its source repository is the exception: a stale or broken
standard, including the automation that missed it, is a defect to diagnose, never a manual step to hand
to the user, and so is a standard that caused or failed to prevent a mistake. Diagnose it and launch
`engineering:handoff` in bounded side-workstream mode (the side workstream's goal records the defect)
in the same turn, after answering the user's direct question and before the current task resumes,
without asking, regardless of that task's own
authority; announcing a later or separate fix instead of launching is a violation. This rule is the
standing authorization: it covers implementing, testing, opening the PR and merging once that
repository's gates pass. Installing into any other scope (the consuming repository included),
publishing outside that repository, and destructive operations stay gated; explicit user limits still
hold.
When a plan or task changes how a repository's code is written, apply `engineering:docs-and-debt`'s
direction-change rule before code depends on it.
Before committing or returning a terminal result, check the work against the standards that governed
it and reconcile every problem encountered: it is fixed, handed off, or already has the owning debt
entry. `engineering:docs-and-debt` defines the selected
repository convention. Do not create a second ledger for a standalone goal just to satisfy a
repository-oriented procedure.
