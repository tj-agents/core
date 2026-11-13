---
name: address-review
description: Fix a completed review's findings one at a time on the reviewed branch, commit each fix with its test, then review only the fix delta. Use when asked to address review findings.

kind: workflow
domain: process
---

# Address a review

Owns fixing a completed review's findings. It starts only when the user asks for fixes, passes `--fix` to
`engineering:review`, or the implementing workflow already covers repairing its candidate; a review-only
request ends at the findings. `engineering:review-lifecycle` owns where a finding may be fixed.

Take one finding, or one tightly coupled group, at a time under a single writer: fix it, add the test that
fails before and passes after where the defect is testable, run the smallest relevant check and commit with
explicit pathspecs. Never run two writers at once, even on disjoint files. Keep each finding's original text
and severity; record only its disposition and evidence. A finding that cannot be fixed now is recorded
through the selected profile with an objective resolution condition. Fix the fixable part of a split
finding now; a genuine product or architecture decision stops with its owner and resume condition.

After the last fix, run `engineering:incremental-review` over the fix delta; new findings re-enter this
loop. Finish when every finding has a disposition and the delta review is clean.

```text
Review 3f1c2a9..8e04d17: HIGH F-1 export breaks on commas; MEDIUM F-2 missing null guard.
F-1: quote through csv.writer + test_export_quotes_commas -> commit c91b5e2.
F-2: guard + test_export_skips_null_title -> commit d40a7f3.
incremental-review 8e04d17..d40a7f3: clean. Report F-1, F-2 fixed at d40a7f3.
```

Report fixed findings with their commits, any recorded deferral and its owner, the checks run and the new
reviewed head.
