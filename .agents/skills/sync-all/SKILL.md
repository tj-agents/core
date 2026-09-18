---
name: sync-all
description: Bring EVERY git worktree up to date with the default branch in one pass — the bulk counterpart to `sync` (which only updates the main checkout). Fetches once, then for each worktree merges `origin/main` into its branch (or `pull --ff-only` when it IS the default branch), auto-stashing and restoring any working changes, and aborting cleanly on any conflict so no tree is ever left half-merged. Use when Tommy says "sync all", "/sync-all", "sync all worktrees", "bring every worktree up to date", "get all my worktrees current with main", or after a merge that everything else should rebase onto.

kind: utility
domain: machine
---

# sync-all

Answer "make every one of my worktrees current with `main`" — in one pass, without losing a scrap of
uncommitted work and without ever leaving a tree in a conflicted state.

Sibling skills, so you pick the right one: **`sync`** returns the *main checkout* to a clean, up-to-date
default branch (the thing you want right after your own PR merges). **This** is the bulk sweep across
*every* worktree — each feature branch gets `origin/main` merged in so nothing is left building on a
stale tree. **`prune-worktrees`** is the disposal counterpart (delete the dead ones).

Auto-detects `main` vs `master`. Run everything via the shell tool from any checkout of the repo. No
preamble — do it and report the per-worktree outcome.

## Behavior, per worktree

1. **Skip detached HEADs** — nothing to fast-forward a branchless tree onto; report and move on.
2. **Already current** (`HEAD..origin/main` is empty) — report `current`, touch nothing.
3. **Dirty tree** — stash tracked + untracked first, so the update runs on a clean tree; restore after.
4. **Update** — if the worktree IS on the default branch, `pull --ff-only`; otherwise `merge origin/main`.
5. **Conflict is never left on disk** — a merge conflict is `merge --abort`ed back to the pre-merge state
   and reported; a stash-pop conflict restores the tracked tree and reports the WIP as unapplied but safe
   in the newest stash entry. A pop conflict otherwise writes markers into files and keeps the stash, so
   "the WIP is safe" and "the tree is clean" are two different claims - only the first was ever true.

## Run this

```bash
main=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#origin/##'); main=${main:-main}
git show-ref --verify --quiet "refs/remotes/origin/$main" || main=master
git fetch origin --prune --quiet
git worktree list --porcelain | awk '/^worktree /{print $2}' | while read -r wt; do
  br=$(git -C "$wt" symbolic-ref --quiet --short HEAD 2>/dev/null || echo '(detached)')
  if [ "$br" = '(detached)' ]; then echo "⏭  detached   $wt"; continue; fi
  behind=$(git -C "$wt" rev-list --count "HEAD..origin/$main" 2>/dev/null)
  if [ "${behind:-0}" -eq 0 ]; then echo "✓  current    $br"; continue; fi
  stashed=0
  if [ -n "$(git -C "$wt" status --porcelain)" ]; then
    git -C "$wt" stash push -u -m 'sync-all autostash' >/dev/null && stashed=1
  fi
  if [ "$br" = "$main" ]; then
    git -C "$wt" pull --ff-only --quiet && res="✓  pulled $behind" || res="⚠  PULL FAILED (diverged) — manual"
  elif git -C "$wt" merge "origin/$main" --no-edit --quiet; then
    res="✓  merged $behind"
  else
    git -C "$wt" merge --abort; res="⚠  MERGE CONFLICT (aborted, unchanged) — manual"
  fi
  if [ "$stashed" = 1 ]; then
    if ! git -C "$wt" stash pop --quiet 2>/dev/null; then
      # A pop conflict writes markers into the tree and keeps the stash, so restoring loses nothing -
      # and it is the only way this loop's "no tree is ever left half-merged" claim is actually true.
      git -C "$wt" checkout --force HEAD -- . 2>/dev/null; git -C "$wt" reset --quiet
      res="$res + POP CONFLICT (restored clean; WIP UNAPPLIED, safe in newest stash)"
    fi
  fi
  echo "$res    $br"
done
```

## Rules

- **Never discard work.** Every mutation is a stash or a merge that aborts on conflict; nothing forces,
  resets, or discards. If a tree can't be updated cleanly, report it and leave it exactly as found.
- **Only pop the stash this skill created** — it's the newest entry, made seconds earlier in that same
  worktree. Never blind-pop a tree this run didn't stash.
- **A conflict is a report, not a fight.** `merge --abort` on merge conflict; on pop conflict restore the
  tree and leave the WIP in the stash. Do not attempt to resolve — hand it back by name. Never leave
  markers on disk: in a file something later executes, they break every subsequent session, far from here.
- **Local + fetch only.** Never pushes, never deletes a branch, never touches a PR. Bringing branches
  current is the whole job; publishing that is a separate, explicit step.
- Report one line per worktree — `current` / `merged N` / `pulled N` / the conflict state — then the
  count updated vs left for manual attention.
