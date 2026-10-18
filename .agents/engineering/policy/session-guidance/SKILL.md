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

When the user calls out a mistake, answer the direct question first, then load and follow
`engineering:self-repair`. It owns whether a consumed Core standard caused or failed to prevent the
mistake, and the required bounded source-repair handoff. Existing user limits and scope gates still apply.
Questions ask for reasoning: explain and defend recommendations with evidence, change them only for new
evidence or a stated user decision, and say what changed.

During normal work, when an applicable standard is ambiguous, silent or improvable, propose its
refinement in the same turn as a question to the user: name the standard, the gap, concrete wording or a
snippet, and why. Continue the current task under the existing standard while awaiting the decision. If
accepted, launch `engineering:handoff` in bounded side-workstream mode to the standard's source owner
under the standing authorization. Established standards defects still require immediate repair.

## A task has an owning lifecycle — load it before the first edit

Authorized long-term or multi-phase work selects `engineering:plan-execution`, even when the user does
not name a plan or skill. Read an existing canonical goal before edits and keep its progress current.
A bounded behavior change selects `engineering:feature`; a defect selects `engineering:bugfix`.
Planning-only work selects `engineering:plan-authoring` and does not authorize implementation.
A question or review request alone grants no implementation authority. A status question during already
authorized execution should be answered before that execution continues.

Use `engineering:lanes` to match substantive work to suitable capability. Reuse its loaded contract;
routine commands and phase labels do not require another read or lane rationale. Keep cheap leaf lanes
for clerical work and delegate useful batches under that contract. Reconsider the
selection when the work's judgment or capability requirements change. The lane contract owns execution
and capability fallback, including when the engineering runtime is unavailable.
On Claude, hand multi-phase work and any delegated design, implementation, or review phase to Codex before
delegating. An explicit user choice of Claude may keep non-frontier work local; otherwise do not fall back.

## Repository routine-decision delegation

Read routine delegation from the actual checkout's `.agents/settings.json`. Within
`configuration.core.auto_approve`, an explicit `design` overrides `all`, including false. The flat
`configuration.core.auto_approve_design` alias applies only when the nested object is absent. When
the effective design value is true, proceed with routine design and convention choices, including the recording
needed by work the user already authorized. Explain and record the rationale. Planning-only work remains
planning-only. An explicit user decision reservation, task scope, or stricter repository rule still
controls. A procedural gate added by an agent does not reserve a decision for the user. This setting grants
no merge, publication, installation, permission, or other external authority.

## A link to another skill is a stage pointer, not a read

Load a referenced skill when its stage is actually entered, never because a document you are reading names
it. A procedure step, table row or route line says which skill owns that stage. Do not load the corpus
transitively. Use the host's native skill invocation when available or read its advertised source file.
Reuse an already-loaded body while its source identity is unchanged, including after compaction when the
continuation preserves its relevant instructions. Read again only for changed instructions or missing context.

## Record noticed problems

When a bug, mistake, or deliberate debt is noticed or reported, record it under the relevant shared
problem-record convention while the observation is available: `engineering:write-bug`,
`engineering:write-mistake`, or `engineering:write-debt`. Reconcile an existing record and repair owner
first; repeated evidence updates that record. Recording stays within the current authorization and grants
no separate authority to repair, publish, dispatch, or schedule work. Use the addressing workflow only
when repair is already authorized, and preserve the original task while the record is updated.

Recording requests for features or tasks select `engineering:write-feature` or `engineering:write-task`;
an untyped recording request selects `engineering:write-issue`. These writers share
[repository selection and persistence](../../resources/problem-records.md).

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

At normal start, read `machine:recover-agents`' linked command contract and inspect `status`. For a new
planning task, `item <feature>/<item> --status proposed --title '<useful title>'`; for new authorized
execution, `claim <feature>/<item> --host <actual host> --role owner --status active --title '<useful title>'`.
Use `--plan-path` only for an existing repo-relative plan. Questions need no registration; chores need no
plan. Retain metadata and status unless deliberately transitioning; another owner follows recovery or handoff.

Act on authorized reversible work and keep the canonical plan aligned with observed results. A phase,
commit, open PR or context boundary does not narrow the original scope. Honor user limits and real
external-action gates. Use `engineering:handoff` for an actual authorized context transfer; it checkpoints
first, invokes one selected machine launcher, and releases the previous writer. Prompt-only requests
remain prompt-only. Missing runtime capabilities must be reported accurately, not assumed installed.

Follow `engineering:committing` for local checkpoints and the repository's selected delivery convention
when delivery is authorized. Bind remote monitoring to the exact repository, head and run; never imply
pending CI is owned without an active monitor. A failed test selects `engineering:failing-tests` and its
diagnose, repair and focused verification loop. Do not weaken a check merely to produce a pass.

When all owned work is done, select `machine:close` and prepare its post-report operation before
delivering the final completion report. `base:goal-continuation` owns this requirement for ordinary
tasks as well as goals and deliveries. The close operation owns verified host closure and its keep-open,
active-dialogue and unsupported-host handling. A handoff predecessor follows `engineering:handoff`'s
release instead.

## Maintain the right source owner

Give shared behavior one source owner, preserve published compatibility commitments, and record material
out-of-scope defects with an objective resolution condition through the relevant shared writer. Plans
link the canonical record under [the shared recording contract](../../resources/problem-records.md).
A defect in a consumed standards package or its source repository is the exception: a stale or broken
standard, including the automation that missed it, is a defect to diagnose, never a manual step to hand
to the user, and so is a standard that caused or failed to prevent a mistake. Diagnose it and follow
`engineering:self-repair` in the same turn, after answering the user's direct question and before the
current task resumes. That workflow owns the repair authorization, admission, disposition, and delivery
procedure; explicit user limits still hold.
Before committing or returning a terminal result, check the work against the standards that governed
it and reconcile every problem encountered: it is fixed, handed off, or already has the owning debt
entry. `engineering:write-debt` defines the selected repository convention. Do not create a second
ledger for a standalone goal just to satisfy a repository-oriented procedure.
