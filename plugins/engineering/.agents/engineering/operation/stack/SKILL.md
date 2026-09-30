---
name: stack
description: Create and maintain a dependent stack of focused GitHub pull requests. Use when a change needs stacked PRs, a child PR must target its parent branch, a parent changes after a child opens, or a stack must be landed from the bottom up.
kind: operation
domain: process
lane: L4
---

# Stacked pull requests

Use `engineering:git-branching` for slice boundaries, parent and head identities, sizing,
validation, and reconciliation after a parent changes. Keep the full goal and stack map in its
existing plan or ledger.

Use `engineering:open-worktree` to create each dependent branch from its recorded parent's
current tip and keep each branch in its own checkout. Use `engineering:open-pr` to open each
child PR with its immediate parent branch as the base. Review and validate each layer against
that parent and its cumulative tree.

Land from the bottom up through the repository's selected merge workflow. After a parent lands,
verify the child's new base and diff. If the forge does not retarget it correctly, replay only
the child's commits onto the new base using the recorded old parent tip, then rerun affected
checks. Do not merge a child into an unmerged parent's branch and call it landed.
