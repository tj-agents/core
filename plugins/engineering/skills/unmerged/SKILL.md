---
name: unmerged
description: Inventory every local branch + worktree and say what's genuinely left to merge vs. safe to bin — then do the safe cleanup. Classifies branches into truly-unmerged (has new content), squash-merge ghosts (content already in master under a different SHA — the bulk of branch clutter), and fully-merged; cross-references open PRs; surfaces uncommitted work stranded in worktrees; flags stale platform-sync branches; then deletes the dead ones with a case-collision guard so it never nukes a branch a worktree still holds. Use when Tommy says "/unmerged", "what's left to merge", "what code is still unmerged", "clean up my branches", "why do I have so many branches", or "prune merged branches". Works in any repo; personal git/gh only.

kind: utility
domain: process
---

# open PRs, keyed by head branch

Read and follow the [canonical shared definition](../../.agents/engineering/utility/unmerged/SKILL.md) in full.
This entry point supplies only Claude discovery metadata; the shared procedure is authored once under `.agents/`.
