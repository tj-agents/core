---
name: sync-checkout
description: Bring the checkout up to date - fetch and prune, repair a stale origin/HEAD, retire the current branch if its PR shipped, or merge the default into a live branch. Use to sync or refresh the checkout.

kind: operation
domain: process
lane: L7
---

# Bringing the checkout up to date

Owns making the local checkout match the remote, including whether the current branch is still live.
`engineering:pull` only updates the current branch.

1. `git fetch origin --prune --quiet`. Pruning drops refs for remote branches deleted on merge, which is
   what makes `[gone]` detectable.
2. Resolve the default branch from the remote, never by assuming `main` or `master`, and repair a stale
   cached `origin/HEAD`.
3. `git status --porcelain` must be clean. If not, stop and offer `engineering:commit` or a stash.
4. Act on the current branch:
   - **Default branch:** `git pull --ff-only origin "$actual"` and report what arrived.
   - **Feature branch with no PR, a `MERGED` or `CLOSED` PR, or `[gone]`:** it is dead. Switch to the
     default, fast-forward it and delete the branch with `git branch -d`, which refuses unmerged work, plus
     `git push origin --delete <branch>` when the remote branch survives. Report which PR merged. Before calling a branch with no PR dead, confirm it has an `origin/<branch>`:
     brand-new local work looks identical through `gh pr view`. A branch the repository's guidance names as
     persistent is never deleted.
   - **Open PR:** live work; stay on it. When behind the default and clean, merge it, never rebase, since
     the history is pushed and possibly reviewed. On a conflict, stop and name the files.
5. List other `[gone]` branches (`git branch -vv | grep ': gone]'`) without deleting them.

```text
actual=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name)
cached=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#origin/##')
[ "$actual" != "$cached" ] && git remote set-head origin -a
git rev-list --left-right --count "origin/$actual"...HEAD   # "<behind>  <ahead>"; behind > 0 -> git merge "origin/$actual"
```

This never force-pushes, force-deletes or rewrites pushed history; the merge in step 4 is the only history
change, and only on the current branch.
