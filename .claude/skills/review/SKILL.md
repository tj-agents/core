---
name: review
description: Run the canonical isolated code-review workflow over one frozen branch, PR, commit-range, or path candidate with the host's native reviewer, relevant fresh read-only lenses, validated evidence, and parent-only deduplication, severity, judgment, and work-order writing. Use for a first full code review when asked to review a branch or PR; use incremental-review for later commits, big-review for a very large diff, docs-review for a meta-only diff, and address-review for existing findings.

kind: workflow
domain: process
---

# Canonical isolated code review

Read and follow the [canonical shared definition](../../../.agents/engineering/workflow/review/SKILL.md) in full.
This entry point adds only Claude Code's reviewers; the shared procedure is authored once under `.agents/`.

## Claude Code reviewers

- **Native layer (Stage 3):** the built-in `code-review` skill, invoked through the Skill tool with
  `<effort> <frozen-base>..<frozen-head>`, adding ` -- <scoped paths>` for a bounded scope. Never pass
  `--comment` or `--fix`; this workflow owns both.
- **Security layer (Stage 6):** the built-in `security-review` skill. It takes no target and diffs the
  working tree against `origin/HEAD`'s merge-base, so use it only when the checkout is clean at the frozen
  head, scope is `all`, and `trunk_base` equals `git merge-base origin/HEAD <frozen-head>`. Otherwise use the
  `security` lens.
