---
name: stack
description: Maintain a required stack when work must build on an unmerged PR. Covers the concrete reason for overlap, verified parent branches, parent-targeted child PRs, cumulative validation and prompt bottom-up landing. Sequential delivery and checkout allocation follow git-branching.
kind: operation
domain: process
lane: L4
---

# Stacked pull requests

`engineering:git-branching` owns the decision to overlap dependent work. Sequential delivery is the
default; use this procedure whenever a PR must build on an unmerged parent. Record the concrete reason
the child must proceed before the parent lands in the existing plan or ledger. Preserve the full goal,
parent/head identities, slice sizes and validation gates there.

Create each dependent branch from its recorded parent's verified current tip. Use
`engineering:open-worktree` only when active execution needs another checkout; inactive layers can remain
Git branches. Use `engineering:open-pr` to open every child against its immediate parent branch. Review
the child-only delta and validate its cumulative tree. Every unmerged PR dependency uses this relationship.

Keep the stack limited to necessary active work and land each ready, authorized parent promptly.

Land from the bottom up through the repository's selected merge workflow. After a parent lands,
verify the child's new base and diff. If the forge does not retarget it correctly, replay only
the child's commits onto the new base using the recorded old parent tip, then rerun affected
checks. Do not merge a child into an unmerged parent's branch and call it landed.
