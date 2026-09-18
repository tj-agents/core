---
name: prune-worktrees
description: Sweep ALL git worktrees at once and delete the dead ones — the bulk counterpart to the per-branch `worktree remove`. Classifies every worktree by content (merged / squash-ghost / genuinely unmerged), refuses anything dirty, detached-unsafe, or still carrying work, then tears down the provably-dead ones properly — unlinking .Codex junctions first so deletion can't recurse into the main checkout's real skill files, handling Windows MAX_PATH, pruning admin state, sweeping orphaned leftover folders a removed worktree left behind, and dropping the orphaned branch. Use when Tommy says "prune worktrees", "/prune-worktrees", "delete unused worktrees", "clean up my worktrees", "why do I have so many worktrees", "get rid of these worktrees", or "remove all the dead worktrees". Works in any repo; personal git/gh only. For ONE named worktree use `worktree remove`; for branch-ref clutter use `unmerged`.

kind: operation
domain: machine
---

# prune-worktrees

Answer "which of these worktrees are dead, and can I bin them?" — then bin exactly those.

Sibling skills, so you pick the right one: **`worktree`** is per-worktree lifecycle (create/list/remove
one by name). **`unmerged`** classifies and deletes *branch refs*. **This** is the bulk *worktree*
sweep — many trees, one pass, disk actually reclaimed.

The trap this exists to avoid: a worktree looks disposable because its branch looks merged, but the
tree holds **uncommitted work nothing else on earth has a copy of**, or its branch was squash-merged so
`--merged` misreports it. Classify by content and by tree state, never by the directory name or vibes.

## 1. Detect main, refresh refs

```bash
main=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#origin/##'); main=${main:-master}
git fetch origin --prune --quiet 2>/dev/null
git worktree prune          # always safe: drops admin entries whose directory is already gone
```

## 2. Inventory + classify every worktree (one Bash call)

`git cherry` marks each commit `+` (content NOT in main) or `-` (already in main under another SHA —
the squash-merge ghost). That, plus the dirty count, decides everything.

```bash
git worktree list --porcelain | awk '/^worktree /{print $2}' | while read -r wt; do
  br=$(git -C "$wt" symbolic-ref --quiet --short HEAD 2>/dev/null || echo "(detached)")
  dirty=$(git -C "$wt" status --porcelain 2>/dev/null | wc -l)
  untracked=$(git -C "$wt" status --porcelain 2>/dev/null | grep -c '^??')
  if [ "$br" = "(detached)" ]; then
    sha=$(git -C "$wt" rev-parse HEAD 2>/dev/null)
    git merge-base --is-ancestor "$sha" "origin/$main" 2>/dev/null && cls="DETACHED-safe" || cls="DETACHED-UNSAFE"
  else
    ahead=$(git rev-list --count "origin/$main".."$br" 2>/dev/null)
    if [ "${ahead:-0}" -eq 0 ]; then cls="MERGED"
    else
      newc=$(git cherry "origin/$main" "$br" 2>/dev/null | grep -c '^+')
      [ "$newc" -eq 0 ] && cls="GHOST" || cls="UNMERGED(new=$newc)"
    fi
  fi
  case "$wt" in *"/.Codex/worktrees/agent-"*) kind=HARNESS;; *) kind=USER;; esac
  printf '%s\t%s\t%s\t%s\tdirty=%s\tuntracked=%s\t%s\n' \
    "$wt" "$kind" "$br" "$cls" "$dirty" "$untracked" "$(git -C "$wt" log -1 --format='%cr' 2>/dev/null)"
done
```

The **first** line of `git worktree list` is the main checkout — it is never a candidate, whatever its
state. Cross-reference open PRs for anything UNMERGED:

```bash
gh pr list --state open --json number,headRefName,mergeStateStatus,isDraft \
  --jq '.[] | "PR #\(.number)\t\(.headRefName)\t\(if .isDraft then "draft" else "ready" end)\t\(.mergeStateStatus)"' 2>/dev/null
```

## 3. The gates — a worktree is DEAD only if it clears every one

Delete only when **all** hold. Any failure ⇒ it goes in the report, not the bin.

1. **Not the main checkout.** Line 1 of the worktree list, always excluded.
2. **Clean tree** — `dirty=0`. Uncommitted work is at-risk work; nothing but that disk holds it.
   Untracked files count as dirty (a stray plan/investigation `.md` is often the only copy).
3. **Content is in main** — `MERGED`, `GHOST`, or `DETACHED-safe`. `UNMERGED(new>0)` is real work and
   is **never** auto-removed, no matter how old.
4. **No open PR** on its branch. An open PR means in-flight, regardless of merge state.
5. **HARNESS worktrees** (`.Codex/worktrees/agent-*`) — harness-owned ephemeral agent trees. Only ever
   candidates when clean AND content-in-main AND **stale (>1 day)**; a recent one may belong to a
   *running* agent and removing it breaks that agent mid-flight. Report them as their own group.

`force` as an arg relaxes gate 3 **only** (never 1, 2, or 4), and only for a worktree Tommy names
explicitly — never as a blanket sweep.

## 4. Remove each dead worktree — junctions FIRST

```bash
WT="$1"; BR="$2"
# Junctions (Git Bash sees them as -type l) point at the MAIN checkout's real skill dirs.
# Unlink before deleting or a follow-through deletes your actual skills. rmdir drops the link only.
find "$WT/.Codex" -type l 2>/dev/null | while read -r j; do
  MSYS_NO_PATHCONV=1 cmd /c rmdir "$(cygpath -w "$j")" >/dev/null 2>&1 && echo "  unlinked: ${j#$WT/}"
done
git worktree remove --force "$WT" 2>/dev/null && echo "  removed: $WT" || echo "  RETRY-NEEDED: $WT"
```

**Windows MAX_PATH.** `node_modules`/`obj`/`bin` trees blow past 260 chars and `git worktree remove`
fails with "Filename too long". The delete that works is PowerShell with the long-path prefix, then
prune the now-orphaned admin entry:

```powershell
Remove-Item -LiteralPath "\\?\C:\path\to\worktree" -Recurse -Force
```

```bash
git worktree prune     # reconciles admin state after any manual directory delete
```

If the sandbox blocks the recursive delete, **don't fight it** — hand Tommy one ready-to-paste block
listing only dirs already confirmed dead, and say the admin entries are pruned once he runs it.

## 5. Then drop the orphaned branch

Removing a worktree does **not** delete its branch. Reconcile both — a stranded ref is the clutter
`unmerged` would otherwise have to clean up later.

```bash
git branch -d "$BR" 2>/dev/null && echo "  deleted branch: $BR" \
  || { git branch -D "$BR" && echo "  deleted ghost branch: $BR"; }
```

`-d` refuses a GHOST ("not fully merged") because it checks ancestry, not content. `-D` is safe **only**
for a branch proven GHOST by `git cherry` in step 2. Never blanket-`-D`.

> **Case-collision guard (Windows).** `Refactor/Foo` and `refactor/foo` are the same ref file. Never
> delete a branch any *surviving* worktree holds, matched **case-insensitively** — deleting the twin
> drops that worktree to detached HEAD. If two branches differ only by case, delete neither; name it.

## 6. Sweep orphaned leftover folders (the actual pile-up)

`git worktree list` only shows *registered* worktrees, so steps 1–5 are **structurally blind** to the
folders that actually pile up: a removed worktree whose **directory was left behind** — admin entry
pruned, tree still on disk. That is the Windows "can't delete a directory a process is cwd'd in" failure,
and nothing above can see it. Catch it by diffing on-disk folders against the registered set:

```bash
root=$(git worktree list --porcelain | awk '/^worktree /{print $2; exit}')   # main checkout
reg=$(git worktree list --porcelain | awk '/^worktree /{print $2}')
for base in "$root/.worktrees" "$(dirname "$root")/$(basename "$root").worktrees"; do
  [ -d "$base" ] || continue
  for d in "$base"/*/; do d="${d%/}"; [ -e "$d" ] || continue
    printf '%s\n' "$reg" | grep -qxF "$d" && continue           # still registered → not an orphan
    br=$(basename "$d" | sed 's#-#/#')                          # slug -> branch (Type/Name)
    if git show-ref --verify --quiet "refs/heads/$br" && ! git merge-base --is-ancestor "$br" "origin/$main" 2>/dev/null; then
      echo "  ✋ ORPHAN KEPT — branch '$br' not merged; verify no uncommitted work, then delete by hand: $d"
    else
      cd "$root"                                                # never delete a tree you're standing in
      rm -rf "$d" 2>/dev/null || MSYS_NO_PATHCONV=1 cmd /c rmdir /s /q "$(cygpath -w "$d")" >/dev/null 2>&1
      [ -d "$d" ] && echo "  ⚠️ ORPHAN LOCKED (a live process holds it): $d" || echo "  🗑 orphan folder removed: $d"
    fi
  done
done
```

A true orphan has no valid worktree admin, so step 2's classifier never sees it — this folder-vs-registered
diff is the only thing that catches it. Auto-remove **only** when its branch is merged or already gone
(committed work is then safe in refs). An unmerged orphan is **kept and reported**: a leftover tree with a
dead `.git` can't be checked for uncommitted work, so it needs a human's eye before deletion.

## Report

**🗑 Pruned** — one line each: path · branch · why it was dead (merged / ghost / stale agent tree).
Finish with disk reclaimed if easily had (`du -sh` before, or just the count).

**✋ Kept** — the interesting half, most-urgent first:
- **uncommitted work** — path + `git -C <wt> status --short` output, by name. Loudest item; nothing but
  that disk holds it.
- **unmerged content** — branch · `new=N` commits · age · open PR or none · the next step (merge it, or
  it's abandoned and wants an explicit call).
- **open PR / in-flight** — leave it, say which PR.
- **harness agent trees still live** — recent ones skipped on purpose.

**⚠️ Needs a human** — only if found: case-collisions, `DETACHED-UNSAFE`, a MAX_PATH dir needing the
paste-block. Skip the heading when empty.

Keep it tight — the pruned list is a count plus names, the kept list is where the judgment goes.

## Rules

- **Safety is absolute: never the main checkout, never a dirty tree, never `UNMERGED` content, never a
  branch with an open PR, never a branch a surviving worktree holds.** Unsure ⇒ report it, don't bin it.
- **Classify by content, not ancestry.** `git branch --merged` misses squash-merge ghosts entirely; a
  sweep built on it would both miss clutter and mislabel shipped work as unmerged.
- **Untracked files make a tree dirty.** Scratch investigation markdown is routinely the only copy of
  an afternoon's thinking — treat `??` exactly like modified.
- **Unlink `.Codex` junctions before any delete.** Belt-and-braces even where `rm` is junction-safe:
  one follow-through takes out the main checkout's real skill files.
- **Harness `.Codex/worktrees/agent-*` trees are not yours by default.** Stale + clean + shipped only,
  and always reported as a separate group so it's obvious what was touched.
- Local-only. This never deletes remote branches, never closes PRs, never pushes. Read-only until the
  classification is done; destructive strictly on the proven-dead set.
- **Orphan folders are the real pile-up.** A removed worktree whose directory was left behind is
  invisible to `git worktree list`; step 6 catches it by diffing on-disk folders against the registered
  set, and auto-deletes only when the branch is merged/gone (keeps + reports an unmerged one).
- `gh` may be missing or the repo non-GitHub — degrade quietly, carry on git-only, and say PR state was
  unavailable rather than inventing it.
