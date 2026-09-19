---
name: worktree
description: Spin up / list / tear down an isolated git worktree per PR, so parallel branches never step on each other's single working tree (e.g. a stray AGENTS.md edit bleeding into an unrelated refactor). Creates the worktree INSIDE the repo at <repo>/.worktrees/<Branch-flattened> off fresh origin default, respecting the repo's capitalized <Type>/<Name> convention and matching any existing branch casing, then wires the new checkout's .agents skills and .Codex settings so local agent setup carries over. Use when Tommy says "worktree", "/worktree", "spin up a worktree", "new worktree for <Branch>", "isolate this PR", "list worktrees", or "remove the worktree for <Branch>". Personal repos (plain git / gh) — not the work Azure-DevOps flow.

kind: utility
domain: process
---

# worktree

Read and follow the [canonical shared definition](../../../.agents/engineering/utility/worktree/SKILL.md) in full.
This entry point supplies only Codex discovery metadata; the shared procedure is authored once under `.agents/`.
