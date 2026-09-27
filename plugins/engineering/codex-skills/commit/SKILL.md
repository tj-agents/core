---
name: commit
description: Turn the working tree into clean, logical git commits — survey staged, unstaged and untracked state, slice the changes into coherent per-workstream commits with honest messages derived from the actual diff, keep move-only renames out of rewrite commits, exclude junk and say what was excluded, and verify the resulting shape. Covers why a non-empty index is a signal rather than an accident, why a stale commit-plan artifact must be checked against the real tree, and the plan checkpoint a plan-managed slice carries. Use whenever the user asks to commit work, tidy the tree into commits, or wants a readable history rather than one mega-commit.

kind: operation
domain: process
model: gpt-6-luna
---

# Committing the working tree as curated slices

Read and follow the [canonical shared definition](../../.agents/engineering/operation/commit/SKILL.md) in full.
This entry point supplies only Codex discovery metadata; the shared procedure is authored once under `.agents/`.
