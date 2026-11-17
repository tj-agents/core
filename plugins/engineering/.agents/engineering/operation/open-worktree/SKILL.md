---
name: open-worktree
description: Create, reuse, inspect or close a checkout for active work - an isolated worktree claimed for its session when a concurrent writer needs one. Use when selecting or managing a worktree.

kind: operation
domain: process
lane: L7
---

# Checkout isolation for active work

Owns deterministic worktree creation, its session claim and safe closure. `engineering:branching` owns
when work needs its own checkout and the existing-work lookup that runs before creating one: continue an
open PR or unmerged branch for the same area instead of starting fresh. Creation is setup, never the
deliverable: when the invocation carries a task, continue it in the new checkout by absolute path.

| Intent | Procedure |
|---|---|
| Sequential work in an available checkout | Verify no writer, build, monitor or session owns it, preserve its work, then switch under `engineering:branching` |
| Concurrent writer, necessary isolation or an explicit request | **Create**, below |
| Read-only inventory | `git worktree list --porcelain`, then `git -C <worktree> status --porcelain` for each |
| Close a merged PR's worktree | `engineering:merge`'s worktree sweep |
| Clear dead worktrees in bulk | `engineering:prune-worktrees` |

Before creating a checkout or restoring its dependencies, check free space and existing build output.

## Create

Create through the shared script, never by typing `git worktree add`. Use the repository's capitalized
`<Type>/<Name>` and never a second casing of an existing branch: a case-insensitive filesystem cannot hold
both, and the remote then breaks fetch for everyone.

```text
python -B <skill-directory>/scripts/create_worktree.py Feature/BrowserCredentials    # Windows
python3 -B <skill-directory>/scripts/create_worktree.py Feature/BrowserCredentials   # Linux/macOS
Result: <repository-root>/.worktrees/Feature-BrowserCredentials exists and is claimed for the current
agent session through tj session claim-worktree; JSON reports branch, path, HEAD, base and base SHA.
```

The script fetches with pruning and starts from the existing local branch, the existing remote branch or
the fetched remote default; `--from <ref>` names another start point. `<repository-root>/.worktrees/` is
the only supported location. It needs the installed `tj` command; outside an agent session the claim
succeeds without an owner, and a refused claim fails creation while leaving the checkout for its owner to
resolve. Read the JSON instead of re-deriving the path, verify a clean status and use absolute paths from
then on.

Tracked `.agents` and `.claude` content arrives with the checkout. Never copy or junction guidance
directories into it: stale untracked copies shadow plugin skills, and a deletion through a link reaches the
main checkout's real files. Unlink an existing link before removing a tree.

Report the branch, absolute path, HEAD, base and whether the attached task continued.
