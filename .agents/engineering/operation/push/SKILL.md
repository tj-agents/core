---
name: push
description: Push a stable candidate and prove the remote carries it - the remote-tracking ref and any open PR head equal the pushed head. Diagnoses rejected or blocked pushes; never force-pushes unasked.

kind: operation
domain: process
lane: L7
---

# Push a verified head

Owns publishing a commit and proving it landed. `engineering:committing` owns when to push: commit locally
often, push stable candidates and real handoffs. A command returning success is not evidence; matching
refs are.

Resolve the owning branch and PR through `engineering:branching`; corrections made elsewhere are integrated
onto the owning branch first. Then push the exact head once and verify it:

```text
work_head=$(git rev-parse HEAD)
git push                                  # git push -u origin <branch> on a first push
git fetch origin <branch>
test "$(git rev-parse origin/<branch>)" = "$work_head"
test "$(gh pr view --json headRefOid --jq .headRefOid)" = "$work_head"   # only when a PR is open
Result: both comparisons pass, or the push is not reported as done.
```

When the push or a comparison fails, fix the actual cause and retry the same push once:

- **Rejected, remote has new commits:** `git pull --rebase`, resolve, push. When the rebase is unsafe or the
  conflicts are messy, stop and tell the user rather than force-pushing.
- **No upstream:** `git push -u origin <branch>`. **No remote:** say so; never invent one.
- **Authentication or permission failure:** report it for the user to fix; never retry in a loop.
- **Pre-push hook failed:** fix the cause. Never `--no-verify`, and never `--force` or
  `--force-with-lease`, unless the user explicitly asks.

Report one line when it went straight through; otherwise the problem, the fix and the final state, or what
blocks the push and what the user must do.
