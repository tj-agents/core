---
name: review
description: Review a branch, PR, commit range or paths with the host's native reviewer plus the standards the repository selects, and return findings. Use for code review; docs-review covers documentation.

kind: utility
domain: process
---

# Canonical isolated code review

Read and follow the [canonical shared definition](../../../../.agents/engineering/utility/review/SKILL.md) in full.
This entry point adds only Claude Code's reviewers; the shared procedure is authored once under `.agents/`.

## Claude Code reviewers

- **Native layer (Stage 3):** the built-in `code-review` skill, invoked through the Skill tool with
  `<effort> <base>..<head>`, adding ` -- <scoped paths>` for a bounded scope. Never pass
  `--comment` or `--fix`; the calling skill owns both.
- **Security layer (Stage 6):** the built-in `security-review` skill. It takes no target and diffs the
  working tree against `origin/HEAD`'s merge-base, so use it only when the checkout is clean at the candidate
  head, scope is `all`, and `<base>` equals `git merge-base origin/HEAD <head>`. Otherwise use the
  `security` lens.
