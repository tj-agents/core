---
name: open-worktree
description: Create, inspect, or close one isolated git worktree so every in-flight delivery branch gets its own checkout and carries its plan and ledger. Covers the planning-only no-worktree exception, the worktree identity gate, starting at fetched origin/main, branch casing, flat folders, safe audit/close/retire, and stale guidance links. Use when the user wants a worktree created, a branch or PR isolated, worktrees listed, or one closed or retired.

kind: operation
domain: process
model: gpt-5.6-luna
---

# One checkout per in-flight branch

Read and follow the [canonical shared definition](../../../.agents/engineering/operation/open-worktree/SKILL.md) in full.
This entry point supplies only Codex discovery metadata; the shared procedure is authored once under `.agents/`.
