---
name: session
description: Own the engineering session from task selection through repair and completion. Use when starting, continuing or finishing work under an explicitly selected engineering lifecycle, or when asked to note or record a bug, mistake or debt.
kind: policy
domain: process
---

# Engineering session

These conventions apply when engineering is selected for the current scope. They grant no
implementation, publication or installation authority beyond the eligible internal repair authority in
`engineering:self-repair`. Product profiles and compatibility policy remain
with the project. The common maintained-plan contract is `workflow:plan-artifacts`. The common
continuation owner is `workflow:run`; it selects `engineering:persistent-workflow` when
an authorized task has a future decision that may outlive the current session.

## When the user calls out a mistake

When the user calls out a mistake, answer the direct question first and correct the active task within
its existing authorization. For a suspected reusable agent-standard or tooling defect, load
`engineering:self-repair` before any host product feedback, to establish source ownership, causal
evidence and repair eligibility. It owns the automatic-repair boundary and the no-source-change outcome. Existing user limits and scope gates
still apply. Personal application maintenance uses the existing engineering lifecycle within the
authorized goal; it does not need a second repair workflow.
Questions ask for reasoning: explain and defend recommendations with evidence, change them only for new
evidence or a stated user decision, and say what changed.

During normal work, when an applicable standard is ambiguous, silent or improvable, propose its
refinement in the same turn as a question to the user: name the standard, the gap, concrete wording or a
snippet, and why. Continue the current task under the existing standard while awaiting the decision. If
accepted, make the refinement in this session under the standing authorization.
Established standards defects follow `engineering:self-repair`'s source and authority decision.

```text
Standard: engineering:failing-tests. Gap: silent on timeouts under parallel test load.
Proposed: "Rerun a timed-out test file alone before treating it as a regression."
Why: three hook test files timed out at 6-way load and passed when run alone.
```

## A task has an owning lifecycle — load it before the first edit

Authorized long-term or multi-phase work selects `workflow:run`, even when the user does
not name a plan or skill. Read an existing canonical goal before edits and keep its progress current.
A bounded behavior change selects `engineering:feature`; a defect selects `engineering:bugfix`.
Planning-only work selects `workflow:plan` and does not authorize implementation.
A question or review request alone grants no implementation authority. A status question during already
authorized execution should be answered before that execution continues.

Use `machine:lanes` to match substantive work to suitable capability. Reuse its loaded contract;
routine commands and phase labels do not require another read or lane rationale. Keep cheap leaf lanes
for clerical work and delegate useful batches under that contract. Reconsider the
selection when the work's judgment or capability requirements change. The lane contract owns execution
and capability fallback, including when the engineering runtime is unavailable.

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

When a bug, mistake or deliberate debt is noticed or reported, preserve the facts in the active task and
follow [the recording contract](../../../workflow/resources/problem-records.md) for the selected profile's recording
decision. Never record in a Markdown file. Reconcile an existing record and repair owner first. Record or update only when that profile
and the user's authority permit it; a provider selection does not itself authorize creation. Preserve
the original task while a recording decision is pending or declined. Recording grants no separate
authority to repair, publish, dispatch or schedule work.

Feature, story, task and untyped recording requests use the selected profile's creation operation. Its
policy resolves intent and native type; [repository selection](../../../workflow/resources/problem-records.md#repository-selection)
never grants permission to start implementation.

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
lifecycle. A failed CI observation requires recovery under `workflow:run`; it does not end
ownership or establish a CI result.

At normal start, read `machine:recover-agents`' linked command contract and inspect `status`. For a new
planning task, `item <feature>/<item> --status proposed --title '<useful title>'`; for new authorized
execution, `claim <feature>/<item> --host <actual host> --role owner --status active --title '<useful title>'`.
Use `--plan-path` only for an existing repo-relative plan. Questions need no registration; chores need no
plan. Retain metadata and status unless deliberately transitioning; another owner follows recovery or handoff.

Act on authorized reversible work and keep the canonical plan aligned with observed results. A phase,
commit, open PR or context boundary does not narrow the original scope. Honor user limits and real
external-action gates. Use `workflow:handoff` for an actual authorized context transfer; it checkpoints
first, invokes one selected machine launcher, and releases the previous writer. Prompt-only requests
remain prompt-only. Missing runtime capabilities must be reported accurately, not assumed installed.

Follow `engineering:committing` for local checkpoints and the repository's selected delivery convention
when delivery is authorized. Bind remote monitoring to the exact repository, head and run; never imply
pending CI is owned without an active monitor. A failed test selects `engineering:failing-tests` and its
diagnose, repair and focused verification loop. Do not weaken a check merely to produce a pass.

## Finish the session

Before returning a completed outcome, select `machine:close` and apply its completion decision. It owns
the final-action ordering, keep-open requests and terminal closure. A new mistake callout is answered
and corrected first; completion is then reassessed.

```text
Delivery and validation complete, no owned wait: apply machine:close before the final reply.
User calls out a mistake: answer and correct the active task; assess suspected reusable defects through
engineering:self-repair's source and authority boundary before starting a standards repair.
```

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
