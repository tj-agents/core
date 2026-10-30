---
name: session
description: Own the software-specific rules of an engineering session: standards-defect repair, feature and bugfix lifecycle selection, routine-decision delegation, reviewable delivery slices and source ownership. Use when starting, continuing or finishing work under an explicitly selected engineering lifecycle.
kind: policy
domain: process
---

# Engineering session

These conventions apply when engineering is selected for the current scope, on top of
`workflow:session`. They grant no implementation, publication or installation authority beyond
the eligible internal repair authority in `engineering:self-repair`. Product profiles and compatibility
policy remain with the project. `workflow:run` selects `workflow:continue` when an authorized
task has a future decision that may outlive the current session.

## When the user calls out a mistake

For a suspected reusable agent-standard or tooling defect, load `engineering:self-repair` before any host
product feedback, to establish source ownership, causal evidence and repair eligibility. Apply
[Workflow's recording and priority decision](../../../workflow/policy/session/SKILL.md#record-noticed-problems)
before entering its repair phase. Self-repair owns source authority and the no-source-change outcome.
Existing user limits and scope gates still apply. Personal application maintenance uses the existing engineering lifecycle within the
authorized goal; it does not need a second repair workflow.

During normal work, when an applicable standard is ambiguous, silent or improvable, propose its
refinement in the same turn as a question to the user: name the standard, the gap, concrete wording or a
snippet, and why. Continue the current task under the existing standard while awaiting the decision. If
accepted, apply the same Workflow priority decision before implementing the refinement.
Established standards defects follow `engineering:self-repair`'s source and authority decision.

```text
During report export, the user points out an unrelated reusable close-tool defect.
Load self-repair to assess the source, record through the selected operation, and keep export active.
If the user asks to fix the close tool first, reconcile its repair owner before implementation.
```

## Select the engineering lifecycle before the first edit

A bounded behavior change selects `engineering:feature`; a defect selects `engineering:bugfix`.
Creating a PR or editing its description enters `engineering:open-pr` before the forge write; use its
proposed-body validation and authoritative readback for CLI and connector writes.

## Start repository work from a current base

Before starting or resuming a substantive work item, including planning, fetch the remote and identify its
current default branch. Check the checkout against that fetched base, or against the recorded parent when
working on a stack. Start an independent new delivery branch from the fetched remote default; start a
dependent stack branch from its verified parent tip. Bring an existing delivery branch up to date before
working when its tree is clean; `engineering:branching` owns the branch procedure.
For planning-only work in the normal checkout, fast-forward a clean default branch to the fetched remote
default before editing, or use another checkout already current with that base. Preserve uncommitted changes:
resolve a dirty checkout or use another current checkout before a sync that would alter it. Perform this
check at the work-item boundary, not for every prompt within the same work.

```text
Planning on clean local main, two commits behind origin/main: fetch and fast-forward before editing.
New independent Feature/MapIndex: branch from the fetched remote default.
Dependent Feature/MapUi: branch from its verified parent Feature/MapIndex tip.
```

## Repository routine-decision delegation

Read routine delegation from the actual checkout's `.agents/settings.json`. Within
`configuration.core.auto_approve`, an explicit `design` overrides `all`, including false. When
the effective design value is true, proceed with routine design and convention choices, including the recording
needed by work the user already authorized. Explain and record the rationale. Planning-only work remains
planning-only. An explicit user decision reservation, task scope, or stricter repository rule still
controls. A procedural gate added by an agent does not reserve a decision for the user. This setting grants
no merge, publication, installation, permission, or other external authority.

## Keep large changes reviewable

Before implementing or expanding a large refactor or multi-concern change, apply
`engineering:branching` to define and measure PR-sized delivery slices. Deliver one slice at a time
by default: validate, review and merge when ready and authorized, then start the next from the updated
base. When work must build on an unmerged PR, maintain a proper stack. Allocate worktrees for active
execution needs independently of the number of branches. One goal may span many PRs. A phase label or
an existing open PR never justifies accumulating the whole goal in one diff. Reassess an oversized
candidate before adding more scope; preserve atomic behavior and security when choosing boundaries.

## Delivery checkpoints

A failed CI observation requires recovery under `workflow:run`; it does not end ownership or establish a
CI result.

Follow `engineering:committing` for local checkpoints and the repository's selected delivery convention
when delivery is authorized. Bind remote monitoring to the exact repository, head and run; never imply
pending CI is owned without an active monitor. A failed test selects `engineering:failing-tests` and its
diagnose, repair and focused verification loop. Do not weaken a check merely to produce a pass.

## Maintain the right source owner

Give shared behavior one source owner, preserve published compatibility commitments, and record material
out-of-scope defects with an objective resolution condition through the relevant shared writer. Plans
link the canonical record under [the shared recording contract](../../../workflow/resources/problem-records.md).
A defect in a consumed agent standard or tool is diagnosed at its source. Use `engineering:self-repair`
to establish causal evidence and whether its internal repair authority applies. Follow that decision
before starting a source change; outside automatic scope, explain the proposed repair and continue
unaffected authorized work while awaiting a decision. That workflow owns the repair authorization and
delivery procedure; explicit user limits still hold.
Before committing or returning a terminal result, check the work against the standards that governed it and reconcile every problem encountered: it is fixed, routed to an existing
owner, recorded when authorized, or retained in the active task pending the profile's recording decision. The shared recording contract defines that destination. Do not create a second
ledger for a standalone goal just to satisfy a repository-oriented procedure.
