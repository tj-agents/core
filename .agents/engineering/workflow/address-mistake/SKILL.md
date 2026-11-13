---
name: address-mistake
description: Reconcile one recorded mistake with its existing correction owner, keep its learning history and resolve it only after causal verification. Use to address a named mistake or a mistake record.

kind: workflow
domain: process
---

# Address a recorded mistake

Owns returning a recorded mistake's correction to its owner while preserving the incident history. Read
[the shared problem-record contract](../../../workflow/resources/problem-records.md); it creates no second
repair engine.

1. Use the selected profile provider's read, list, update and close commands. Reconcile the named incident,
   or pick one actionable high-value record quickly: an unblocked `P0` or `P1`, then the first useful `P2`
   or `P3`.
2. Reconcile any existing goal, session, branch, PR or writer first. When a repair already owns the cause,
   link it and append evidence. Blocked and deferred incidents keep their reason, resolver and resume
   condition.
3. A defect in a consumed standard follows `engineering:session`'s source-owner repair rule. Otherwise
   repair an existing behavior defect through `engineering:bugfix`, or add prevention through
   `engineering:feature`; inside a Workflow assignment, return the evidence to its owner. An unknown cause
   stays an investigation. A correction only on an unmerged branch is not yet shipped.
4. Link a related bug or debt repair that owns the cause; merge incidents only on evidence of a common cause.
5. Set `resolved` only after the repair's causal resolution condition is tested, and keep the mistake as
   learning history.

Answer a direct question before entering this workflow. Selecting an incident grants no authority beyond
the active task.

```text
Mistake WI-412: a release checklist omitted a migration verification step. The linked plan already owns
the checklist correction, so append the evidence to WI-412 and link the plan. Once the plan proves the new
step works, record that evidence and resolve WI-412, keeping its history.
```
