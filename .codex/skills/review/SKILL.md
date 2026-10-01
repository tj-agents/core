---
name: review
description: Run the canonical isolated code-review workflow over one frozen branch, PR, commit-range, or path candidate with the host's native reviewer, relevant fresh read-only lenses, validated evidence, and parent-only deduplication, severity, judgment, and work-order writing. Use for a first full code review when asked to review a branch or PR; use incremental-review for later commits, big-review for a very large diff, docs-review for a meta-only diff, and address-review for existing findings.

kind: workflow
domain: process
model: gpt-6.1-sol
---

# Canonical isolated code review

Read and follow the [canonical shared definition](../../../.agents/engineering/workflow/review/SKILL.md) in full.
This entry point supplies only Codex discovery metadata; the shared procedure is authored once under `.agents/`.
