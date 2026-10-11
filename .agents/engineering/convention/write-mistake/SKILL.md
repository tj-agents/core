---
name: write-mistake
description: Record an observed agent or process mistake once, with evidence, source ownership, repair linkage, and retained learning history. Use when an agent mistake is noticed, reported, deferred, blocked, or connected to an existing bug, debt, or standards repair.

kind: convention
domain: process
---

# Recording mistakes

Read [the shared problem-record contract](../../resources/problem-records.md). Record an observed mistake
while the evidence is available, within the current authorization. Recording creates no authority to
repair, publish, dispatch, or schedule work.

Use a repository-declared mistake owner or typed shared register. Otherwise add the entry to root
`MISTAKES.md`. Use a stable `M` identifier and every shared field. Preserve the concrete observation and
evidence; state whether its cause is confirmed or unknown without inventing an explanation.

First reconcile an existing incident and its repair owner. Add repeated observations as dated evidence.
When a mistake is already addressed by a bug, debt, or standards repair, link that repair and retain the
incident as learning history. Merge incident records only when their common cause is known. Do not create
a duplicate repair or job for a related observation.

Keep resolved mistakes with their final state, causal verification, and learning evidence. A blocked or
deferred record remains an outstanding obligation with its resolver and observable resume condition.
