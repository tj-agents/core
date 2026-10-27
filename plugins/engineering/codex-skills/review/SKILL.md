---
name: review
description: Review a branch, PR, commit range or selected paths with the host's native reviewer and the relevant standards injected into that repository. Use for a full code review or a targeted review; use incremental-review for a later sweep, staged-review for explicit resumable partitioning, and docs-review for documentation.

kind: utility
domain: process
---

# Canonical isolated code review

Read and follow the [canonical shared definition](../../.agents/engineering/utility/review/SKILL.md) in full.
This entry point adds only Codex's reviewers; the shared procedure is authored once under `.agents/`.

## Codex reviewers

- **Native layer (Stage 3):** `codex review --base <frozen-base>`, run from a checkout at the frozen head.
  It cannot take a path scope, so the parent drops findings outside a bounded scope.
- **Security layer (Stage 6):** use the installed first-party Codex Security change-review plugin when
  its setup, permissions and reviewed candidate match the frozen scope. Discover its actual installed
  entry point. The cloud PR security service has separate eligibility and repository setup; invoke it
  only with authority for that external action. Record which runner and exact range actually ran.
  Otherwise use the bounded `security` lens over the required frozen range.

```text
Frozen API change + configured first-party plugin with matching scope -> native security review.
Plugin unavailable or scope mismatched -> security lens over that same frozen candidate.
```
