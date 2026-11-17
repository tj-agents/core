---
name: pull
description: Pull the current branch and, when the pull fails, diagnose and fix the cause - blocking changes, conflicts, divergence, no upstream or detached HEAD. Use to pull or recover a failed pull.

kind: operation
domain: process
lane: L7
---

# Pulling, and recovering a failed pull

Owns updating the current branch and nothing else. When the question is also whether the branch is still
live or the default-branch view is stale, use `engineering:sync-checkout`.

## Steps

1. Run `git pull`.
2. **If it succeeds**, report the result in one line — files changed, or already up to date — and stop.
3. **If it fails**, read the error and fix the actual cause:
   - **Local uncommitted changes blocking the merge** — offer to stash, pull, then restore, resolving any
     conflicts the restore raises.
   - **Merge conflicts** — resolve them in the conflicting files, then complete the merge.
   - **Diverged branches, non-fast-forward** — rebase or merge, whichever suits the situation.
   - **No upstream tracking branch** — set it, or pull with an explicit remote and branch.
   - **Detached HEAD, or the wrong branch** — surface it. Do not guess which branch was meant.
4. Re-run the pull to confirm it lands clean.
5. Explain in one or two sentences what caused the failure and what you did about it.

## Notes

- Keep it lightweight: pull, fix only if needed, explain briefly.
- **Nothing destructive without asking** — no hard reset, no force-anything, no discarding local work.

```text
git pull -> error: Your local changes to src/map.py would be overwritten by merge.
git stash && git pull && git stash pop    # after offering it
Report: "Local edits to src/map.py blocked the merge; stashed, pulled 3 commits and restored them."
```
