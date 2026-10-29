---
name: review
description: Review a branch, PR, commit range or selected paths with the host's native reviewer and the relevant standards injected into that repository. Use for a full code review or a targeted review; use incremental-review for a later sweep, staged-review for explicit resumable partitioning, and docs-review for documentation.
metadata:
  tj-agents-kind: operation
  tj-agents-domain: process
---

# Canonical isolated code review

Read and follow the [canonical shared definition](../../../../.agents/engineering/skills/review/SKILL.md) in full.
This entry point adds only Claude Code's reviewers; the shared procedure is authored once under `.agents/`.

## Claude Code reviewers

- **Native layer (Stage 3):** the built-in `code-review` skill, invoked through the Skill tool with
  `<effort> <frozen-base>..<frozen-head>`, adding ` -- <scoped paths>` for a bounded scope. Never pass
  `--comment` or `--fix`; the calling skill owns both.
- **Security layer (Stage 6):** the built-in `security-review` skill. It takes no target and diffs the
  working tree against `origin/HEAD`'s merge-base, so use it only when the checkout is clean at the frozen
  head, scope is `all`, and `trunk_base` equals `git merge-base origin/HEAD <frozen-head>`. Otherwise use the
  `security` lens.
