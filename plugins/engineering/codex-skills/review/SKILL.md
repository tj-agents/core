---
name: review
description: Run the canonical isolated code-review workflow over one frozen branch, PR, commit-range, or path candidate with the host's native reviewer, relevant fresh read-only lenses, validated evidence, and parent-only deduplication, severity, judgment, and work-order writing. Use for a first full code review when asked to review a branch or PR; use incremental-review for later commits, big-review for a very large diff, docs-review for a meta-only diff, and address-review for existing findings.

kind: workflow
domain: process
---

# Canonical isolated code review

Read and follow the [canonical shared definition](../../.agents/engineering/workflow/review/SKILL.md) in full.
This entry point adds only Codex's reviewers; the shared procedure is authored once under `.agents/`.

## Codex reviewers

- **Native layer (Stage 3):** `codex review --base <frozen-base>`, run from a checkout at the frozen head.
  It cannot take a path scope, so the parent drops findings outside a bounded scope.
- **Security layer (Stage 6):** Codex has no native security reviewer; use the `security` lens.
