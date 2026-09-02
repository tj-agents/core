---
name: sync-checkout
description: Bring the whole local checkout up to date with reality, not just the current branch — fetch and prune, repair a stale origin/HEAD so the default branch is resolved rather than assumed, then detect whether the branch you are on already shipped (switch back to a clean default and delete it safely) or is still open (report drift and merge the default in when behind and clean). Covers why persistent branches are never auto-deleted, why merge and never rebase, and why brand-new local work looks identical to a shipped branch through one gh call. Use whenever the user wants to sync, sync with main, refresh the checkout, get up to date, or start a session on a clean current tree.
domain: process
---

# Bringing the checkout up to date

One procedure to make the local repository match reality: what is on the remote, and whether the branch you are
sitting on is still live or already shipped.

[`pull`](../pull/SKILL.md) only updates the current branch. This also asks **"is this branch even still needed?"** and
**"am I looking at a stale default-branch pointer?"** — the two questions that make a checkout quietly wrong
rather than merely behind.

## Step 1 — fetch and prune

```
git fetch origin --prune --quiet
```

Prune drops remote-tracking refs for branches deleted on the remote when their PR merged. Without it, the
`[gone]` detection in Step 4 cannot work at all.

## Step 2 — fix a stale `origin/HEAD`

A remote's default branch can be renamed without the local clone noticing, and every later step that compares
against "the default branch" then compares against the wrong one. Resolve the actual default from the remote
rather than assuming a name:

```
actual=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name)
cached=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#origin/##')
[ "$actual" != "$cached" ] && git remote set-head origin -a
```

Every later step means `$actual` when it says the default branch. **Never hard-code `main` or `master`.**

## Step 3 — the working tree must be clean before touching branches

```
git status --porcelain
```

If dirty, stop and report it. Do not merge, check out, or pull over uncommitted work. Offer
[`commit`](../commit/SKILL.md) or a stash rather than silently doing one.

## Step 4 — read the current branch's state and act on it

```
git rev-parse --abbrev-ref HEAD
git status -sb | head -1        # look for "[gone]"
```

**On the default branch already** — fast-forward it, report the commits pulled or *already up to date*, stop:

```
git pull --ff-only origin "$actual"
```

**On a feature branch** — find out whether its PR already shipped:

```
gh pr view --json number,state,url --jq '{number,state,url}' 2>&1
```

- **No PR found, or the PR is `MERGED`/`CLOSED`, or `git status -sb` showed `[gone]`:** the branch is dead — its
  work landed, or it was abandoned. Switch back to a clean default branch, then delete the dead branch with
  `-d`, which refuses unless it really is merged and so cannot eat unmerged work:

  ```
  git checkout "$actual" 2>/dev/null || git checkout -b "$actual" --track "origin/$actual"
  git pull --ff-only origin "$actual"
  git branch -d <old-branch>
  git push origin --delete <old-branch> 2>/dev/null || true
  ```

  Report which PR merged, by number and title, so the user knows *why* the branch is gone.

  **Exception — a persistent branch is never auto-deleted, even when it reports as merged.** Some branches are
  reused across passes rather than being per-PR. The rule is portable; **which branches those are is a value the
  repository's own guidance names**, not something this doc can list or a heuristic can infer. Leave one checked
  out as-is.

- **The PR is `OPEN`:** this is live work — do not switch away from it. Report drift against the default branch
  and close it when safe:

  ```
  git rev-list --left-right --count "origin/$actual"...HEAD    # "<behind>  <ahead>"
  ```

  - `behind` is 0 — nothing to do, report in sync.
  - `behind` above 0, tree clean (Step 3 proved this) — **merge, never rebase**, since rebasing rewrites a
    history that is already pushed and possibly reviewed:

    ```
    git merge "origin/$actual"
    ```

    On a clean merge, note that the branch is now current and that a rebuild is worth doing before relying on
    green CI. On a conflict, stop and surface the conflicting files. Do not resolve blindly.

## Step 5 — report other cleanup candidates, but do not touch them

```
git branch -vv | grep ': gone]'
```

Branches whose remote is gone but which are not the one you are on get **noted, not deleted** — deleting a
branch you are not sitting on was not asked for.

## Notes

- This never force-pushes, force-deletes, or rewrites already-pushed history. The merge in Step 4 is the only
  history-changing step, and only on the branch you are already on.
- Deleting the *current* dead branch is safe by construction, because `git branch -d` refuses an unmerged
  branch. Deleting *other* local branches is left to the user.
- When `gh pr view` errors because there is no PR and no upstream tracking at all, treat it as "no PR found" —
  but confirm the branch actually has an `origin/<branch>` to compare against before reporting it dead. Brand
  new local work looks identical to a shipped branch through that one command.
