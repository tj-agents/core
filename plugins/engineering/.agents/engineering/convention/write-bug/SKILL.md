---
name: write-bug
description: Record a discovered or reported software defect once, with concrete evidence, impact, repair ownership, and a verifiable resolution condition. Use when a bug is noticed, reported, deferred, blocked, or linked to an existing repair.

kind: convention
domain: process
---

# Recording bugs

Read [the shared problem-record contract](../../resources/problem-records.md). Record a bug while the
observation is available, within the current authorization. Recording creates no authority to repair,
publish, dispatch, or schedule work.

Use a repository-declared bug owner or typed shared register. Otherwise add the entry to root `BUGS.md`.
Use a stable `B` identifier and every shared field. Describe the observed faulty behavior and evidence,
then say whether its cause is confirmed or unknown. Do not turn a suspicion into a cause.

Before adding an entry, reconcile the relevant record and existing repair owner. Repeated reports add
dated evidence to the canonical record. When a known causal repair already has a bug or related problem
record, link it instead of opening a duplicate repair. A known defect deliberately left unfixed may also
need the owning area's debt entry under `engineering:write-debt`; link the two records rather than copying
the repair.

Keep a resolved bug with its final state and verification evidence. A blocked or deferred record remains
outstanding until its recorded resolver and observable resume condition permit the next action.
