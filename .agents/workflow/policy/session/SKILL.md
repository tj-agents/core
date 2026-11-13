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
misrouted message by sending a retraction to the original recipient. `agent:message` (`tj message`)
delivers natively to a Claude session's inbox and to a Codex session's feed, which it reads on demand.

Phases, commits, open PRs, handoffs and briefs never narrow the original scope. Use `workflow:handoff`
only for an actual transfer of ownership.

## Finish

Finish only when delivery, validation and any authorized handoff are done. A merged PR, a Stop event or a
question about a missed close-out is not completion. A new mistake callout is answered and corrected first.

```text
A: add report export. B: an unrelated terminal-close bug is reported.
Keep A's next action; tell the user about B and record it through the selected profile.
User calls out a mistake: answer, correct the active task, then reassess completion.
Delivery and validation complete, no owned wait: finish.
```
