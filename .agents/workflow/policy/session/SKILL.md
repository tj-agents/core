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
Apply [Record noticed problems](#record-noticed-problems) to a reported side problem while preserving
the active goal and next action.

## A task has an owning lifecycle — load it before the first edit

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

When a bug, mistake or deliberate debt is noticed or reported during item A, preserve A's goal and next
action. Follow [the recording contract](../../resources/problem-records.md) to reconcile the affected
source, existing record and repair owner, then invoke the selected profile's qualified creation operation
for a new item B when its policy and user authority permit. A local Markdown entry is not a tracker
operation. Keep unsent facts with A while recording is blocked, pending or declined; continue unaffected
authorized work.

Reporting, recording, repair authority, priority and handoff are separate decisions. A question,
frustration or bug callout alone leaves A active. Creating B or having standing repair authority does
not prioritize, implement or dispatch B. Honor an explicit request to fix, reprioritize or hand off B;
retain A's remaining work and ownership unless the user replaces or transfers it.

Correct defects required for A's existing acceptance condition within A's authorization. Establish that
relationship with evidence before changing source. An issue number or severity alone establishes no
dependency. If A cannot safely proceed, explain the concrete blocker, resolver and decision needed;
continue independent authorized work without silently replacing A with a separate repair goal.

```text
A: add report export. B: an unrelated terminal-close bug is reported.
Record B through the selected create-work-item operation; continue report export.
"Why did the terminal stay open?" asks for an answer and recording, without starting B.
The export's existing acceptance check fails because its CSV writer corrupts quoted fields:
correct that defect within A, citing the failing export check.
"Fix the terminal bug first": retain A's next action, then reconcile B's owner and enter its repair.
```

Feature, story, task and untyped recording requests use the selected profile's creation operation. Its
policy resolves intent and native type; [repository selection](../../resources/problem-records.md#repository-selection)
never grants permission to start implementation.

## Preserve one owner through completion

Coordinate with another agent when its verified responsibility needs the information. Before sending,
establish the exact recipient, its current responsibility from an owned goal, work-item binding or explicit
assignment, and the concrete decision or action the message supports. Shared checkout, parent conversation,
similar title and convenience do not establish that relationship. Unknown or irrelevant ownership keeps the
information with the current task while ownership is reconciled. Existing task authority covers necessary
coordination with a verified responsible recipient; do not add a confirmation step to every message.

Correct a mistaken route in the original recipient's conversation by identifying and retracting the earlier
assignment. That correction does not assign it the repair. Resolve the actual owner before routing work again.
`agent:message` implements admission and delivery evidence for independent Codex sessions; native
in-conversation messaging follows the same responsibility decision.

```text
The repair goal names session A as owner; session B shares its repository but owns a naming migration.
Send repair evidence to A because it changes A's next diagnostic step. Keep B out of the repair.
If an earlier message assigned B the repair, retract that assignment in B using its original delivery receipt.
```

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
