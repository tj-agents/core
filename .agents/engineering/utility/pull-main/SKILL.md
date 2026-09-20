---
name: pull-main
description: Sync the current repo's local main with origin without losing work — stash any working changes, switch to main, fetch + pull --ff-only, then restore the stash. Skips the stash/restore entirely when the tree is clean. Use when Tommy says "pull main", "sync main", "/pull-main", or wants local main brought up to date while keeping current changes.

kind: utility
domain: process
---

# pull-main

Bring local `main` up to date with `origin/main`, carrying any current working changes back afterward. Run everything via the available shell/terminal tool from the repo root. No preamble — just do it and report the final state.

## Behavior

1. If the working tree is dirty, stash it (tracked + untracked, ignoring `.gitignore`d files). If it's clean, **skip** stashing and **skip** the later pop.
2. Switch to the default branch (`main`).
3. `git fetch`, then `git pull --ff-only`.
4. If (and only if) you stashed in step 1, `git stash pop` to restore the changes.

## Run this

```bash
MAIN=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@'); MAIN=${MAIN:-main}
STASHED=0
if [ -n "$(git status --porcelain)" ]; then
  git stash push -u -m "pull-main autostash" && STASHED=1
fi
git switch "$MAIN" 2>/dev/null || git switch -c "$MAIN" "origin/$MAIN"
git fetch origin
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
echo "=== on $(git rev-parse --abbrev-ref HEAD) @ $(git rev-parse --short HEAD) ==="
git status --short
```

## Rules

- **Only pop the stash this skill created** — it's the newest entry, made seconds earlier. Never blind-pop when you didn't stash; the repo may hold unrelated stashes.
- **Never discard work.** If `pull --ff-only` fails (local main diverged) or the pop conflicts, stop and report. Never force, reset over, or hand-resolve it.
- **A pop conflict must not leave markers on disk.** The stash is retained on conflict, so the work is safe; restore the tracked tree and report it unapplied. Conflict markers left in a file that something later *executes* — a hook, a script — break every subsequent session, and the failure surfaces nowhere near this command.
- Report the final branch, short HEAD sha, and whether changes were restored.
