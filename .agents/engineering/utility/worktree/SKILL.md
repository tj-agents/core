---
name: worktree
description: Create, list or remove a worktree through the canonical open-worktree lifecycle. Select checkouts for active execution and isolation, reuse them for sequential work, and close completed worktrees promptly. Use for worktree commands or an explicit isolated-checkout request.

kind: utility
domain: process
---

# Worktree commands

Use [engineering:open-worktree](../../operation/open-worktree/SKILL.md) for checkout selection, creation,
inspection and safe closure. `engineering:git-branching` owns sequential delivery and required stacks.
An extra checkout serves active execution or isolation needs; branch count does not select checkout count.

| Invocation | Canonical operation |
|---|---|
| `create <Branch>` or a task requiring isolation | Verify ownership and create the needed checkout through `open-worktree` |
| `list` | Inspect registered worktrees and status through `open-worktree` |
| `remove <Branch>` | Follow `open-worktree` closure/retirement rules and preserve unfinished work |

When the invocation includes a task, continue the authorized work in the selected checkout in the same
session. Creation is setup; the task continues under its owning workflow.
