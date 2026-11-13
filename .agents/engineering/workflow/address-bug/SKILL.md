---
name: address-bug
description: Reconcile one recorded bug with its existing repair owner, run the defect workflow and resolve the record only after causal verification. Use to fix a named bug or work a bug record.

kind: workflow
domain: process
---

# Address a recorded bug

Owns selecting and tracking the repair of a recorded bug. Read
[the shared problem-record contract](../../../workflow/resources/problem-records.md); `engineering:bugfix`,
`engineering:failing-tests` or an existing plan owns the repair itself.

1. Use the selected profile provider's read, list, update and close commands. Reconcile the named record,
   or pick one actionable high-value record quickly: an unblocked `P0` or `P1`, then the first useful `P2`
   or `P3`. Priority alone does not pause unrelated work.
2. Reconcile any existing goal, session, branch, PR or writer first. When another owner already has the
   causal repair, link it on the record instead of starting a second writer. A blocked record keeps its
   real reason and resume condition.
3. Otherwise repair through `engineering:failing-tests` when a failing test bounds the work, or
   `engineering:bugfix`; inside a Workflow assignment, return the evidence to its owner.
4. Link related mistake or debt records. Keep the cause unknown until evidence confirms it.
5. Set `resolved` only after the record's causal resolution condition is tested, with that evidence.

Answer a direct question before entering this workflow. Selecting a record grants no authority beyond the
active task.

```text
Bug WI-241: an export without a title returns HTTP 500. PR #91 already holds the causal repair and its
regression test, so link WI-241 to PR #91 rather than opening a second branch. Once the regression test
passes against the repaired export, record that evidence and set WI-241 to resolved.
```
