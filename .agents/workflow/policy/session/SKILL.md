---
name: session
description: Own a working session in any domain from start to finish. Use when starting, continuing or finishing a task, when the user calls out a mistake, or when a side bug, mistake or debt is noticed.
kind: policy
domain: process
---

# Session

Owns the lifecycle of any selected work, software or not. It grants no implementation, publication or
installation authority. `engineering:session` adds software rules when Engineering is selected.

## Enter the owning lifecycle before the first edit

Authorized sustained or multiphase work enters `workflow:run`; planning enters `workflow:plan` without
implementation authority. Questions and reviews grant none; answer a status question before continuing.
Match substantive work to capability through `agent:lanes`; routine commands need no lane rationale.

## A link to another skill is a stage pointer, not a read

Load a referenced skill when its stage is actually entered, never because a document you are reading names
it, through native invocation or its advertised source. Reuse a loaded body while its source is unchanged,
including after compaction.

## When the user calls out a mistake

Answer the direct question first, then correct the active task within its authorization. A question asks
for reasoning: defend a recommendation with evidence and change it only for new evidence or a user
decision, saying what changed. Audit the session for other mistakes only when reporting a terminal result.

## Incidental problems

Keep the active goal, tell the user and record only through the selected profile, as
[Incidental problems](../../resources/problem-records.md#incidental-problems) describes.

## One owner

One session owns a goal. Message another session only for a blocker it must act on or a final result it
is waiting for, after verifying from its goal, work-item binding or explicit assignment that it is
responsible. A shared checkout, parent conversation or similar title does not establish that. Correct a
misrouted message by sending a retraction to the original recipient.
[`agent:message`](https://github.com/tj-agents/agent/blob/main/.agents/agent/utility/message/SKILL.md) owns
delivery, receiving, waiting and delivery receipts for both hosts.

Phases, commits, open PRs, handoffs and briefs never narrow the original scope. Use `workflow:handoff`
only for an actual transfer of ownership.

## Finish

Finish only when delivery, validation and any authorized handoff are done. A merged PR, a Stop event or a
question about a missed close-out is not completion. A new mistake callout is answered and corrected first.

In a managed TJ session, completion has two parts: request it with `tj finish` once the whole authorized
outcome is delivered, then send the final response. The host records that exact turn's response; TJ delivers
it to an explicit parent when present, checks ownership and authored changes, completes the linked item,
and saves a durable closeout receipt. A successful `tj finish` confirms intent only. Use `tj receipt` or
`tj status` to distinguish the recorded result from completed cleanup. A missing invocation leaves the
session visibly incomplete; it never causes a synthetic prompt or another model turn.

Before yielding with genuine pending work, record `tj wait user|child|ci|approval "reason"`. Resume the
same authorized outcome when its dependency resolves. When the user asks to keep the session open, record
`tj hold`; release it with `tj hold --release` only when that request is withdrawn. A hold survives new
input and permits final-result delivery while preventing closure. New user input cancels pending completion.
Do not mark the work item Done separately as a substitute for this protocol. Agent owns the
[managed-session commands](https://github.com/tj-agents/agent#managed-sessions); the CLI enforces their
state and cleanup rules.

```text
A: add report export. B: an unrelated terminal-close bug is reported.
Keep A's next action; tell the user about B and record it through the selected profile.
User calls out a mistake: answer, correct the active task, then reassess completion.
Delivery and validation complete, no owned wait: finish.
```
