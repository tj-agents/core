---
name: address-bug
description: Reconcile one actionable recorded bug with its existing repair owner, run the appropriate defect lifecycle, and update the canonical record only after causal verification. Use when the user asks to fix a named bug or to work an actionable bug record.

kind: workflow
domain: process
---

# Address a recorded bug

Read [the shared problem-record contract](../../resources/problem-records.md). This workflow selects and
tracks repair; it does not replace `engineering:bugfix`, `engineering:failing-tests`, or an existing plan
owner.

1. Use the selected profile provider's read/list/update/close commands. Reconcile the named record, or
   select one actionable high-value record quickly. Do not deep-rank every
   record. Prefer an unblocked `P0` or `P1`, then the first useful `P2` or `P3`; priority does not pause
   unrelated work except for `engineering:self-repair`'s shared agent-lifecycle exception.
2. Reconcile an existing goal, session, branch, PR, or writer before writing or dispatching. If another
   owner already has the causal repair, update the record with the link and evidence instead of starting a
   second writer. Update blocked records with their real reason and resume condition.
3. Re-enter an existing authorized goal through `engineering:plan-execution`. When an active failing test
   already bounds the work, use the narrower `engineering:failing-tests` loop. Otherwise use
   `engineering:bugfix` for diagnosis and repair. These lifecycles own implementation and verification.
4. Link related mistake or debt incidents to the repair. Keep cause unknown until evidence confirms it;
   do not merge records merely because symptoms resemble each other.
5. Set `resolved` only when the record's objective causal resolution condition has been tested and attach
   that evidence. Retain the resolved bug. If the repair cannot proceed, leave it `blocked` or `deferred`
   with the shared contract's required fields and continue the original task where it remains authorized.

Answer a user's direct question before entering this workflow. Recording or selecting a record does not
grant repair or publication authority beyond the active task.

## Example

```text
Work Items bug WI-241 reports that an export without a title returns HTTP 500. PR #91 already contains
the causal repair and its regression test. Link WI-241 to PR #91 and keep its existing owner; do not open
a second branch. After the regression test passes against the repaired export, record that evidence and
set WI-241 to resolved.
```
