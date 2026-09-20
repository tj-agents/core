---
name: prune-worktrees
description: Sweep ALL git worktrees at once and delete the dead ones — the bulk counterpart to the per-branch `worktree remove`. Classifies every worktree by content (merged / squash-ghost / genuinely unmerged), refuses anything dirty, detached-unsafe, or still carrying work, then tears down the provably-dead ones properly — unlinking .Codex junctions first so deletion can't recurse into the main checkout's real skill files, handling Windows MAX_PATH, pruning admin state, sweeping orphaned leftover folders a removed worktree left behind, and dropping the orphaned branch. Use when Tommy says "prune worktrees", "/prune-worktrees", "delete unused worktrees", "clean up my worktrees", "why do I have so many worktrees", "get rid of these worktrees", or "remove all the dead worktrees". Works in any repo; personal git/gh only. For ONE named worktree use `worktree remove`; for branch-ref clutter use `unmerged`.

kind: utility
domain: process
---

# prune-worktrees

Read and follow the [canonical shared definition](../../../.agents/engineering/utility/prune-worktrees/SKILL.md) in full.
This entry point supplies only Claude discovery metadata; the shared procedure is authored once under `.agents/`.
