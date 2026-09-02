---
name: pull
description: Pull the latest changes for the current branch, and when the pull fails diagnose the cause, fix it, and explain briefly what was wrong — uncommitted changes blocking the merge, conflicts, a diverged branch, a missing upstream, or a detached HEAD. Nothing destructive without asking. Use whenever the user wants to pull, pull latest, get the latest changes, or recover from a failed pull.
domain: process
---

# Pulling, and recovering a failed pull

Pull the latest changes for the current branch. When it fails, find the cause, fix it, and explain what was
wrong in a sentence or two.

This is the narrow operation: it updates the branch you are on and nothing else. When the question is also
*"is this branch still live, and is my view of the default branch stale?"*, [`sync-checkout`](../sync-checkout/SKILL.md) is the
procedure.

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
