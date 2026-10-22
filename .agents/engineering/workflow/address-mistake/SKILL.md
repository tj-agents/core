---
name: address-mistake
description: Reconcile one actionable recorded mistake with its existing correction owner, preserve its learning history, and resolve it only after causal verification. Use when the user asks to address a named mistake or to work an actionable mistake record.

kind: workflow
domain: process
---

# Address a recorded mistake

Read [the shared problem-record contract](../../../workflow/resources/problem-records.md). This workflow preserves an
incident's history while returning the correction to its existing owner; it does not create another repair
engine.

1. Use the selected profile provider's read/list/update/close commands. Reconcile the named incident, or
   select one actionable high-value record quickly. Do not deep-rank
   every record. Prefer an unblocked `P0` or `P1`, then the first useful `P2` or `P3`; priority does not
   pause unrelated work except for `engineering:self-repair`'s shared agent-lifecycle exception.
2. Reconcile the existing goal, session, branch, PR, or writer before writing or dispatching. If a repair
   already owns the cause, link it and append evidence rather than creating a second writer. Keep blocked
   and deferred incidents current with their real reason, resolver, and observable resume condition.
3. For a defect in a consumed standard, follow the shipped `engineering:session` rule for the
   source-owner repair. For an authorized local governing correction with no existing repair owner,
   establish its governing source and evidence first, then enter `workflow:run` only when this correction
   is not already executing under that goal owner. Inside a bounded Workflow assignment, retain its owner
   and scope: use `engineering:bugfix` for an existing behavior defect or `engineering:feature` for new
   prevention behavior, then return verification and record evidence to the Workflow owner. An unknown
   cause stays an investigation action. Do not copy those engines, authorize new product scope, or rely on
   a correction that exists only on an unmerged branch as though it were shipped.
4. Link a related bug or debt repair where it owns the causal correction. Unknown cause remains unknown;
   merge incidents only after evidence confirms a common cause.
5. Set `resolved` only after the repair's objective causal resolution condition has been tested and record
   the verification evidence. Retain the mistake as learning history. A blocked record stays outstanding;
   continue the original task wherever it remains authorized.

Answer a user's direct question before entering this workflow. Recording or selecting an incident does
not grant repair or publication authority beyond the active task.

## Example

```text
Mistake WI-412 records that a release checklist omitted a migration verification step. The linked plan
already owns the checklist correction. Append the observed evidence to WI-412 and link that plan rather
than starting another repair. Once the plan's verification proves the new checklist step works, record the
evidence and resolve WI-412 while retaining its incident history.
```

```text
Input: M008 records a defect in a consumed engineering standard; no repair owns its cause.
Action: follow engineering:session's source-owner repair rule before starting the correction.
```
