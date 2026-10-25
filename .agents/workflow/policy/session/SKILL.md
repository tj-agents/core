---
name: session
description: Own a working session in any domain from start through completion: one owner, mistake callouts, stage-by-stage skill loading, recording noticed problems, and closing when owned work is finished. Use when starting, continuing or finishing a task, when the user calls out a mistake, or when asked to note or record a bug, mistake or debt.
kind: policy
domain: process
---

# Session

These conventions apply to any selected work, software or not. They grant no implementation, publication
or installation authority. The common maintained-plan contract is `workflow:plan-artifacts`; the common
continuation owner is `workflow:run`. When engineering is selected, `engineering:session` adds its software
rules on top of this lifecycle.

## When the user calls out a mistake

Answer the direct question first and correct the active task within its existing authorization.
Questions ask for reasoning: explain and defend recommendations with evidence, change them only for new
evidence or a stated user decision, and say what changed.

## A task has an owning lifecycle — load it before the first edit

Required hooks gate ordinary work and delivery. Failure, timeout, skipping, a missing verdict or trust
review permits only bounded diagnosis and authorized repair. For stale plugin contents, run
`agent:refresh` once. Resume only after affected hooks succeed; refresh or trust alone proves no
execution. Otherwise remain blocked and report the hook, cause, resolver and exact recovery command.
Never bypass trust, disable hooks, suppress failures or change executor to evade the gate.

```text
Base startup timed out: stop app writes, repair, verify successful hook execution, then resume.
Unconfigured refresh: run Core's full setup and --check.
```

Authorized sustained or multi-phase work selects `workflow:run`; read the existing canonical goal before
edits and keep it current. Planning selects `workflow:plan`, without implementation authority. Questions
and reviews alone grant none. Answer status questions before continuing authorized execution.

Use `agent:lanes` to match substantive work to suitable capability. Reuse its loaded contract;
routine commands and phase labels do not require another read or lane rationale. Keep cheap leaf lanes
for clerical work and delegate useful batches under that contract. Reconsider the
selection when the work's judgment or capability requirements change. The lane contract owns execution
and capability fallback.

## A link to another skill is a stage pointer, not a read

Load a referenced skill when its stage is actually entered, never because a document you are reading names
it. A procedure step, table row or route line says which skill owns that stage. Do not load the corpus
transitively. Use the host's native skill invocation when available or read its advertised source file.
Reuse an already-loaded body while its source identity is unchanged, including after compaction when the
continuation preserves its relevant instructions. Read again only for changed instructions or missing context.

## Record noticed problems

When a bug, mistake or deliberate debt is noticed or reported, preserve the facts in the active task and
follow [the recording contract](../../resources/problem-records.md) for the selected profile's recording
decision. Never record in a Markdown file. Reconcile an existing record and repair owner first. Record or update only when that profile
and the user's authority permit it; a provider selection does not itself authorize creation. Preserve
the original task while a recording decision is pending or declined. Recording grants no separate
authority to repair, publish, dispatch or schedule work.

Feature, story, task and untyped recording requests use the selected profile's creation operation. Its
policy resolves intent and native type; [repository selection](../../resources/problem-records.md#repository-selection)
never grants permission to start implementation.

## Preserve one owner through completion

When preparation or approved design has resolved the next action, enter that action through the owning
lifecycle.

At normal start, read `agent:recover`'s linked command contract and inspect `status`. For a new
planning task, `item <feature>/<item> --status proposed --title '<useful title>'`; for new authorized
execution, `claim <feature>/<item> --host <actual host> --role owner --status active --title '<useful title>'`.
Use `--plan-path` only for an existing repo-relative plan. Questions need no registration; chores need no
plan. Retain metadata and status unless deliberately transitioning; another owner follows recovery or handoff.

Act on authorized reversible work and keep the canonical plan aligned with observed results. A phase,
commit, open PR or context boundary does not narrow the original scope. Honor user limits and real
external-action gates. Use `workflow:handoff` for an actual authorized context transfer; it checkpoints
first, invokes one selected machine launcher, and releases the previous writer. Prompt-only requests
remain prompt-only. Missing runtime capabilities must be reported accurately, not assumed installed.

## Finish the session

Before returning a completed outcome, select `agent:close` and apply its completion decision. It owns
the final-action ordering, keep-open requests and terminal closure. A new mistake callout is answered
and corrected first; completion is then reassessed.

```text
Delivery and validation complete, no owned wait: apply agent:close before the final reply.
User calls out a mistake: answer and correct the active task, then reassess completion.
```
