---
name: feature
description: Implement a requested new or changed behavior from discovery through tests, review and commit when no active plan owns it. Not for defect repair, planning-only requests or review-only requests.

kind: workflow
domain: process
---

# Deliver a feature

Owns an unplanned feature from the request to a completed repository outcome. An active plan that owns the
work runs under its own execution workflow; a question or report request is not implementation authority.
When a Workflow owner delegates a bounded slice, do that slice and return its evidence to the same owner.

1. Read the repository's guidance and the standards for the paths likely to change; interpret the
   requirement and success conditions from repository evidence before editing. Before choosing how to
   build a reusable tool or mechanism, apply `base:solution-assessment`.
2. Keep requirement interpretation, architecture, public contracts, data, security and migration decisions
   and the final judgment in the parent. Independent read-only questions may go to host-native subagents
   (`evidence-explorer`, `test-impact-analyst`); a disjoint mechanical change may go to one
   `mechanical-worker`. One writer at a time; reconcile its reported paths against Git and validate every
   result before using it, falling back to the parent on an invalid one.
3. Implement, then run focused checks through the shared `run` operation per
   `engineering:remote-validation`. For browser-visible acceptance, establish
   [observable browser acceptance](../failing-tests/SKILL.md#observable-browser-acceptance) first. Commit
   per `engineering:committing`.
4. Review the committed candidate once with `engineering:review` and fix its actionable findings; the
   selected profile decides whether fixes need another pass. Enter `engineering:failing-tests` for any red
   run.
5. When the work outgrows one session, follow `engineering:plans`. When the user's authorization covers
   delivery, continue through `engineering:open-pr` and `engineering:merge`.

When the work delivers a tracked item, update it through the selected profile under
[the recording contract](../../../workflow/resources/problem-records.md); a merged PR alone does not resolve it.

```text
Work item WI-605: CSV export must include the account owner column. The JSON export already maps it, so
add the matching CSV mapping and test_csv_export_includes_owner. The test passes, review finds nothing,
commit; record the passing test on WI-605 before resolving it.
```

Return one outcome naming the behavior, validation, review and delivery state, or one human gate with its
owner, required action and resume condition. A commit is not terminal while authorized delivery remains.
