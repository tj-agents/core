---
name: sync
description: Go back to the repo's default branch and bring it up to date after a merge — stash any working changes, switch to the default branch (main/master, auto-detected), fetch --prune, pull --ff-only, restore the stash, and delete local branches whose remote was deleted on merge. Use when Tommy says "sync", "/sync", "sync main", "go back to main and pull", "back to master", or wants the local repo reset to a clean up-to-date default branch after a PR merged.

kind: operation
domain: machine
---

# sync

Return the repo to a clean, up-to-date default branch — the thing you want right after a PR merges. Auto-detects `main` vs `master`, never loses working changes, and cleans up the local feature branch whose remote was deleted on merge. Run everything via the available shell/terminal tool from the repo root. No preamble — do it and report the final state.

## Behavior

1. If the working tree is dirty, stash it (tracked + untracked). If clean, skip the stash and the later pop.
2. Switch to the default branch (auto-detected from `origin/HEAD`; falls back to `main` then `master`).
3. `git fetch --prune` (drops remote-tracking refs for branches deleted on merge), then `git pull --ff-only`.
4. If (and only if) step 1 stashed, `git stash pop` to restore the changes.
5. Delete local branches whose upstream is gone (`: gone]` in `git branch -vv`) — i.e. the feature branch that was merged and auto-deleted on the remote. Use `-d` (never `-D`) so git refuses any branch not fully merged into the default. Never touch the current/default branch.

## Run this

```bash
DEF=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@')
if [ -z "$DEF" ]; then
  git show-ref --verify --quiet refs/remotes/origin/main && DEF=main || DEF=master
fi
STASHED=0
if [ -n "$(git status --porcelain)" ]; then
  git stash push -u -m "sync autostash" && STASHED=1
fi
git switch "$DEF" 2>/dev/null || git switch -c "$DEF" "origin/$DEF"
git fetch origin --prune
git pull --ff-only
if [ "$STASHED" = 1 ]; then
  if ! git stash pop; then
    # A pop conflict WRITES conflict markers into the tree and KEEPS the stash. Leaving them is how a
    # half-merged main silently poisoned every later session: the markers landed in a hook file, and
    # python then died on `<<<<<<<` before running a line. The stash still holds the work, so restoring
    # tracked files loses nothing and is the only way to honour "never leave a tree half-merged".
    git checkout --force HEAD -- . 2>/dev/null
    git reset --quiet
    echo "POP CONFLICT: tree restored to $(git rev-parse --short HEAD); your changes are UNAPPLIED but"
    echo "safe as the newest entry in 'git stash list'. Re-apply with 'git stash pop' when ready to resolve."
  fi
fi
# Delete local branches whose remote was deleted on merge (upstream gone), never the default branch.
git branch -vv | awk '/: gone]/ {print $1}' | grep -vx "$DEF" | while read -r b; do
  git branch -d "$b" 2>/dev/null && echo "deleted merged branch: $b" || echo "kept (not fully merged): $b"
done
echo "=== on $(git rev-parse --abbrev-ref HEAD) @ $(git rev-parse --short HEAD) ==="
git status --short
```

## Rules

- **Only pop the stash this skill created** — it's the newest entry, made seconds earlier. Never blind-pop when you didn't stash.
- **Never discard work.** If `pull --ff-only` fails (local default diverged) or the pop conflicts, stop and report. Never force, reset over, or hand-resolve it.
- **A pop conflict must not leave markers on disk.** The stash is retained on conflict, so the work is safe; restore the tracked tree and report it unapplied. Conflict markers left in a file that something later *executes* — a hook, a script — break every subsequent session, and the failure surfaces nowhere near this command.
- **Branch deletion is `-d` only.** If git refuses because a branch isn't fully merged, leave it and report — never `-D`.
- Report the final branch, short HEAD sha, whether changes were restored, and any branches deleted.

