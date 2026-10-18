---
name: write-issue
description: Classify a reported observation or requested backlog item and delegate to its specific bug, mistake, debt, feature or task writer. Use when asked to log, record or write an issue without a precise kind; recording alone does not authorize implementation.

kind: convention
domain: process
---

# Record an issue

Read [the shared record contract](../../resources/problem-records.md), then select one writer from the
facts and the user's intended outcome:

| Request | Writer |
|---|---|
| Faulty software behavior | `engineering:write-bug` |
| An observed agent or process error | `engineering:write-mistake` |
| A deliberate shortcut or deferred compromise | `engineering:write-debt` |
| New or changed product behavior | `engineering:write-feature` |
| A concrete piece of work with a completion condition | `engineering:write-task` |

Load and follow that writer. Preserve the observation, source owner, existing record identity and repair
links. A user-supplied issue number may already determine the kind: read it before choosing another.
Ask only when missing facts leave materially different actions. A suspected cause stays unknown.

Delegate once for the requested outcome. A bug's deliberate deferral does not automatically require a
second debt record; create a linked record only for a distinct compromise with its own exit condition.
The specific writer owns reconciliation, format, selected storage, persistence and verification. Do not
create another template, submit directly, start an addressing workflow or implement the recorded work.
