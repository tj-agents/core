---
name: unmerged
description: Inventory every local branch + worktree and say what's genuinely left to merge vs. safe to bin — then do the safe cleanup. Classifies branches into truly-unmerged (has new content), squash-merge ghosts (content already in master under a different SHA — the bulk of branch clutter), and fully-merged; cross-references open PRs; surfaces uncommitted work stranded in worktrees; flags stale platform-sync branches; then deletes the dead ones with a case-collision guard so it never nukes a branch a worktree still holds. Use when Tommy says "/unmerged", "what's left to merge", "what code is still unmerged", "clean up my branches", "why do I have so many branches", or "prune merged branches". Works in any repo; personal git/gh only.

kind: utility
domain: machine
---

Answer "what's actually left to merge, and what's just clutter?" — then clear the clutter safely.

The trap this skill exists to avoid: **`git branch --merged` lies under a squash-merge workflow.** A
branch whose commits were squash- or rebase-merged into the main branch lands under a *new* SHA, so its
tip is never an ancestor of master and `--merged` calls it unmerged forever. Most of a long branch list
is these **ghosts** — the work IS shipped, the ref is just litter. The skill classifies by *content*
(`git cherry`), not ancestry, so ghosts are correctly identified as deletable.

## Detect the main branch first

```bash
main=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#origin/##'); main=${main:-master}
git fetch origin --prune --quiet 2>/dev/null
```

## Classify every local branch (one Bash call)

For each branch, `git cherry <main> <branch>` marks each commit `+` (content NOT in main) or `-`
(content already in main, i.e. squash/cherry-equivalent). That's the real signal.

```bash
for b in $(git for-each-ref --format='%(refname:short)' refs/heads/); do
  [ "$b" = "$main" ] && continue
  ahead=$(git rev-list --count "$main".."$b" 2>/dev/null)
  if [ "${ahead:-0}" -eq 0 ]; then cls="MERGED(ancestor)"; new=0
  else
    new=$(git cherry "$main" "$b" 2>/dev/null | grep -c '^+')
    if [ "$new" -eq 0 ]; then cls="GHOST(squash-merged)"; else cls="UNMERGED"; fi
  fi
  age=$(git log -1 --format='%cr' "$b" 2>/dev/null)
  printf '%-46s %-22s new=%-4s %s\n' "$b" "$cls" "$new" "$age"
done | sort -k2
```

- **MERGED(ancestor)** — tip is in main. Dead ref, delete.
- **GHOST(squash-merged)** — `new=0` but tip isn't an ancestor: content shipped under another SHA. **Dead
  ref, delete** — this is the bulk of the clutter and the thing `--merged` misses.
- **UNMERGED** (`new>0`) — genuinely carries content not in main. This is the *real* answer to "what's
  left to merge." Keep; report each with what it is.

## Then, for the UNMERGED set only, add context (one Bash call)

```bash
# open PRs, keyed by head branch
gh pr list --state open --json number,headRefName,title,isDraft,mergeStateStatus \
  --jq '.[] | "PR #\(.number)\t\(.headRefName)\t\(if .isDraft then "draft" else "ready" end)\t\(.mergeStateStatus)\t\(.title)"' 2>/dev/null
```

- Match each UNMERGED branch to an open PR by head ref. **UNMERGED + open PR** = in-flight, the top of
  the "left to merge" list. **UNMERGED + no PR** = either genuine WIP or an abandoned experiment — judge
  by age (days = live, months = probably dead) and commit subjects; never auto-delete these.
- **Concertable-only:** `chore/platform-sync-*` branches below the current pin are superseded — list the
  live one, flag the rest as stale. (Old sync branches often show as GHOST already.)

## Worktrees — check for uncommitted work BEFORE judging anything deletable

A branch can look thin while an entire feature sits uncommitted in its worktree. Never delete a branch,
or call a worktree dead, without checking its tree.

```bash
git worktree list --porcelain | grep '^worktree ' | sed 's|^worktree ||' | while read -r wt; do
  br=$(git -C "$wt" symbolic-ref --quiet --short HEAD 2>/dev/null || echo "(detached)")
  dirty=$(git -C "$wt" status --porcelain 2>/dev/null | wc -l)
  printf '%s\tbranch=%s\tuncommitted=%s\n' "$wt" "$br" "$dirty"
done
```

- **Uncommitted files in a worktree = at-risk work.** Surface it loudly and by name (`git -C <wt> status
  --short`); it's more urgent than any branch, because nothing but that disk holds it. Never delete/clean
  a worktree with a dirty tree without explicit say-so.
- A **detached-HEAD** worktree usually means its branch was deleted out from under it (see the case-
  collision guard) — verify its HEAD is in main (`git merge-base --is-ancestor <sha> origin/$main`) so
  no work is lost, then it's a dead worktree.

## The case-collision guard — the footgun that WILL bite on Windows

Windows' filesystem is case-insensitive, so `Refactor/Foo` and `refactor/foo` are the **same ref file**.
Deleting the lowercase twin removes the ref the uppercase worktree is pinned to → that worktree drops to
detached HEAD and breaks. Before deleting ANY branch:

- **Never delete a branch that is checked out in a worktree** (any casing). Build the set of
  worktree-held branches from the worktree list above and exclude them from deletion — matched
  **case-insensitively**.
- If two local branches differ only by case, treat them as one and delete neither automatically — name
  the collision and let Tommy resolve it.

## Delete the dead refs (only after the guard)

Collect MERGED + GHOST branches, minus anything a worktree holds (case-insensitive), then:

```bash
# $b is safe: content in main AND not held by any worktree
git branch -d "$b"     # -d refuses if git thinks it's unmerged — GHOSTs need -D
```

`git branch -d` will refuse GHOSTs ("not fully merged") because it checks ancestry, not content. For a
branch **confirmed GHOST by `git cherry` above** (`new=0`), `git branch -D` is safe and correct — the
content is provably in main. Do the ancestor-merged ones with `-d`, the confirmed ghosts with `-D`, and
say which is which in the report. Don't blanket-`-D`.

## Dead worktrees & their leftover directories

After removing a worktree branch, the worktree itself may need `git worktree remove --force <path>`
then `git worktree prune`. Two platform gotchas, both real on this setup:

- **Windows MAX_PATH:** `node_modules`/`obj` trees blow past 260 chars, so `git worktree remove` and
  `Remove-Item` both fail with "Filename too long". The working delete is PowerShell with the long-path
  prefix: `Remove-Item -LiteralPath "\\?\$dir" -Recurse -Force`. If the sandbox classifier blocks the
  recursive delete, **don't fight it** — hand Tommy the exact command to paste, listing only dirs
  confirmed git-unregistered with content in main.
- Removing a worktree does **not** delete its branch, and vice-versa. Reconcile both: `git worktree
  list` for live trees, then the branch classifier for refs.

## Report

Lead with the answer to "what's left to merge" — the UNMERGED set only, nothing else up top:

**🔧 Left to merge** (most-actionable first: open ready PR → recent WIP → uncommitted-in-worktree):
one line each — branch · PR#/none · age · one-line what · what's blocking or the next step.

**🗑 Cleaned up** — count of MERGED + GHOST deleted, with the ghost count called out (that's the
"where did all these come from" answer: *squash-merged, ref never pruned*). List names only if asked.

**⚠️ Needs a human** — only if found: case-collision pairs, an uncommitted worktree, a months-old
UNMERGED branch with no PR (abandoned?), a stale/red platform-sync. Skip the heading if empty.

**Directory cleanup** — only if dead worktree dirs remain that the sandbox couldn't delete: the ready-
to-paste `\\?\` PowerShell block, dirs confirmed safe.

## Rules

- **Classify by content, never by `--merged` alone.** The whole point is catching squash-merge ghosts;
  a skill that just runs `git branch --merged` would miss most of the clutter and mislabel it as work.
- **Safety is absolute: never delete a branch a worktree holds (any casing), never delete UNMERGED,
  never touch a dirty worktree, never `-D` a branch not proven ghost by `git cherry`.** When unsure,
  list it under "needs a human" rather than deleting.
- Deletion is local-only (`git branch -d/-D`). This skill never deletes remote branches or closes PRs —
  those are the merge/PR flow's job. Read-only until the classification is done; destructive only on
  the proven-dead set.
- `gh` may be absent / repo non-GitHub — PR context degrades quietly; carry on git-only and say PR state
  was unavailable rather than inventing it.
- Keep it tight. The headline is the UNMERGED list; the cleanup is a count, not a wall of branch names.
