---
name: bugfix
description: Diagnose and fix a defect, regression or crash through causal repair, regression coverage, review and commit when no plan or test-debug workflow owns it. Not for new behavior or review-only requests.

kind: workflow
domain: process
---

# Diagnose and repair a bug

Owns an unplanned defect from evidence to a verified causal repair. An active plan that owns the defect runs
under its own execution workflow; a named red test or test tier starts in `engineering:failing-tests`,
which returns here only for an unowned product defect. When a Workflow owner delegates a bounded slice, do
that slice and return its evidence to the same owner.

Use the quick path when the failure is reproducible, ownership is local and one cause dominates: keep the
work in the parent. Otherwise reduce logs to signatures and chronology and send independent read-only
questions to host-native subagents (`log-analyst`, `evidence-explorer`, `test-impact-analyst`), each with
the same baseline and no sibling conclusions. Require competing hypotheses with a discriminator for each;
the parent alone diagnoses the cause and chooses the repair.

1. Reproduce or anchor the defect in direct evidence; separate symptoms from the first incorrect state.
2. Choose the smallest repair that corrects the cause, without suppressing errors, weakening assertions,
   skipping coverage, widening timeouts or preserving an invalid state.
3. Add regression coverage at the lowest tier that proves both the failure and the repair.
4. Run focused checks through the shared `run` operation per `engineering:remote-validation`, then commit
   per `engineering:committing`. One writer at a time; a delegated `mechanical-worker` gets only a disjoint
   change and its paths are reconciled against Git.
5. Review the committed candidate once with `engineering:review` and fix its actionable findings; the
   selected profile decides whether fixes need another pass. Enter `engineering:failing-tests` for any red
   run.
6. When the work outgrows one session, follow `engineering:plans`. When the user's authorization covers
   delivery, continue through `engineering:open-pr` and `engineering:merge`.

Reconcile the defect's record through the selected profile under
[the recording contract](../../../workflow/resources/problem-records.md) and resolve it only after its
resolution condition is verified; a merged PR alone does not resolve it.

```text
GET /reports/42 returns 404 after archive and restore. The lookup keeps a stale archive filter; remove it
and add test_restored_report_is_found, which fails before the change and passes after. Run it, commit,
review, then record the passing test on the linked bug.
```

Return one outcome naming the defect, causal repair, regression evidence, validation, review and delivery
state, or one human gate with its owner, required action and resume condition.
