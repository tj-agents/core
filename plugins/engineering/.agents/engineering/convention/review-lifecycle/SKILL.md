---
name: review-lifecycle
description: One native review of base and head SHAs plus their diff, findings fixed on the branch with tests that prove them, and one severity vocabulary. Use when reviewing a change or fixing its findings.

kind: convention
domain: process
---

# Review lifecycle

Owns what a review covers, how its findings are resolved and the severity vocabulary.

- A review is one native review of the full base and head SHAs and the diff between them.
- Fix each finding on the reviewed branch, with a test that fails before the fix and passes after it where the
  defect is testable. Move a finding elsewhere only when it pre-existed on the base and the change neither
  exposes nor worsens it; record it through the selected profile.
- Review again only the delta that the fixes added.

Severity: `CRITICAL` is an immediately exploitable security, data-loss or catastrophic availability defect;
`HIGH` a likely correctness, security or boundary failure with material impact; `MEDIUM` a concrete defect
with limited impact; `LOW` a concrete rule violation with small impact. Every severity is actionable;
confidence stays separate from severity.

```text
Review 3f1c2a9..8e04d17: HIGH — src/export.py:41 — rows with a comma in the title break the CSV.
Fix: quote fields through csv.writer; add test_export_quotes_commas (fails before, passes after).
Next review: 8e04d17..c91b5e2 only.
```
