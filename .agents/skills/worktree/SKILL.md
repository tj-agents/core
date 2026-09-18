---
name: worktree
description: Spin up / list / tear down an isolated git worktree per PR, so parallel branches never step on each other's single working tree (e.g. a stray AGENTS.md edit bleeding into an unrelated refactor). Creates the worktree INSIDE the repo at <repo>/.worktrees/<Branch-flattened> off fresh origin default, respecting the repo's capitalized <Type>/<Name> convention and matching any existing branch casing, then wires the new checkout's .agents skills and .Codex settings so local agent setup carries over. Use when Tommy says "worktree", "/worktree", "spin up a worktree", "new worktree for <Branch>", "isolate this PR", "list worktrees", or "remove the worktree for <Branch>". Personal repos (plain git / gh) — not the work Azure-DevOps flow.

kind: operation
domain: machine
---

# worktree

Give every in-flight PR its **own** working tree, so two branches can't corrupt each other through the
single shared checkout. Worktrees live **inside the repo folder** — **`<repo>/.worktrees/<Branch>`**,
with `/` in the branch flattened to `-`. Never a sibling `<repo>.worktrees/` dir at the same root: that
scatters one repo across two top-level entries and breaks every "the repo is one folder" assumption.
`create` writes `/.worktrees/` into `.git/info/exclude` so the nested checkouts stay out of `git status`.
Run everything below via the available shell/terminal tool from the repo root. No preamble — do the thing
and report the final state.

Three modes, dispatched on the first arg: **`create <Branch>`**, **`list`**, **`remove <Branch>`**.

> **Footgun — never nest worktrees under `.Codex/worktrees/`.** That path is reserved by the Codex
> Code harness for its own ephemeral agent worktrees; manual worktrees there collide with it and land
> as stray gitlinks that break submodule-aware checkouts (mirror.yml). `.worktrees/` only.

## If the invocation carries a task, the worktree is step one, not the whole job

`/worktree <task description>` (a bug to fix, a feature to build) is **not** the same invocation as a
bare `/worktree create <Branch>`. This skill's script only stands up the checkout — creating it is
never the end of the turn when a task came with it. After `create` finishes, immediately keep working
**in this same session**, targeting the new worktree path with absolute paths in every tool call (Read,
Edit, Bash, PowerShell all accept a path outside the current working directory — nothing requires `cd`
to persist, and nothing requires a fresh session). Do the actual work now: investigate, fix, build, test,
commit — the same "don't ask, act" default as everywhere else in this repo. Pick a branch name yourself
from the task if the user didn't name one.

"Open a NEW Codex session there" in the `create` output is informational for Tommy — it's how
*he* can tail the work in a second window if he wants — it is never an instruction for the agent that
just ran `create` to stop and wait. Stopping after `create` when a task was attached is the exact
failure this section exists to prevent.

## The lifecycle convention — merge as you go, then remove

**Merge each PR the moment it goes green; don't batch at the end.** A worktree that lingers after its
PR could have merged just drifts against `master` and the platform-sync bot, which is the exact pain
this skill exists to avoid. The loop is: `create` → work → open PR → **merge as soon as it's green**
(the `merge` skill) → `remove`. Don't let worktrees pile up.

## create — `worktree create <Type>/<Name>`

Adds a worktree for `<Branch>` at `<repo>/.worktrees/<Branch-flattened>`, branched off **fresh** `origin`
default, then links in local `.agents` skills and snapshots `.Codex/settings.local.json` for a fresh checkout.

```bash
BRANCH="$1"   # e.g. Refactor/DomainStereotypeLayout-Phase3
[ -n "$BRANCH" ] || { echo "usage: worktree create <Type>/<Name>"; exit 1; }
root=$(git rev-parse --show-toplevel)
DEF=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@'); DEF=${DEF:-master}
git fetch origin --quiet

# Reuse an existing branch of the same name in ANY casing (Windows case-insensitive refs collide).
# Case-insensitive whole-string match via awk — NOT `grep -iF`, which silently matches nothing on
# MSYS GNU grep 3.0; awk also avoids treating a branch's '.' as a regex wildcard.
EXIST=$(git for-each-ref --format='%(refname:short)' refs/heads refs/remotes/origin \
  | sed 's@^origin/@@' | grep -vx HEAD \
  | awk -v b="$BRANCH" 'BEGIN{lb=tolower(b)} tolower($0)==lb {print; exit}')
if [ -n "$EXIST" ]; then
  [ "$EXIST" != "$BRANCH" ] && echo "NOTE: reusing existing branch casing '$EXIST' (you asked for '$BRANCH')."
  BRANCH="$EXIST"; START=""                       # check out existing branch, don't -b
else
  TYPE="${BRANCH%%/*}"
  [ "$TYPE" = "$BRANCH" ] && { echo "ERROR: '$BRANCH' has no <Type>/<Name> prefix (Feature/, Refactor/, Bug/, Fix/…)."; exit 1; }
  [ "${TYPE:0:1}" = "$(printf %s "${TYPE:0:1}" | tr '[:lower:]' '[:upper:]')" ] \
    || { echo "ERROR: type prefix must be Capitalized (never a lowercase variant): try '${TYPE^}/…'."; exit 1; }
  START="origin/$DEF"                             # new branch off fresh default
fi

WT="$root/.worktrees/${BRANCH//\//-}"
mkdir -p "$(dirname "$WT")"
grep -qx '/.worktrees/' "$root/.git/info/exclude" 2>/dev/null || printf '/.worktrees/\n' >> "$root/.git/info/exclude"
if [ -z "$START" ]; then git worktree add "$WT" "$BRANCH"; else git worktree add "$WT" -b "$BRANCH" "$START"; fi || exit 1

# Wire .agents skills: tracked skills arrive with the checkout; junction ONLY the local-only ones
# (untracked skill dirs), and snapshot settings.local.json so the worktree session keeps your
# approved permissions instead of re-prompting. Junctions (dir) need no admin; files are copied.
mkdir -p "$WT/.agents/skills"
for d in "$root"/.agents/skills/*/; do
  [ -e "$d" ] || continue          # empty glob (repo has no local skills)
  name=$(basename "$d")
  [ -e "$WT/.agents/skills/$name" ] && continue
  MSYS_NO_PATHCONV=1 cmd /c mklink /J "$(cygpath -w "$WT/.agents/skills/$name")" "$(cygpath -w "$d")" >/dev/null \
    && echo "linked local skill: $name"
done
if [ -f "$root/.Codex/settings.local.json" ] && [ ! -e "$WT/.Codex/settings.local.json" ]; then
  cp "$root/.Codex/settings.local.json" "$WT/.Codex/settings.local.json"; echo "copied settings.local.json (snapshot)"
fi

echo "=== worktree ready ==="; echo "  branch: $BRANCH"
echo "  path:   $WT"; echo "  base:   ${START:-<existing branch>}"
echo "Open a NEW Codex session there:  cd \"$WT\""
```

## list — `worktree list`

```bash
git worktree list
```

The main checkout is line 1. `<repo>/.worktrees/…` entries are yours (this skill).
`.Codex/worktrees/agent-…` entries are the harness's ephemeral agent worktrees — **not** managed here;
leave them alone.

## remove — `worktree remove <Type>/<Name>`

Tear a worktree down **after its PR merged**. Refuses an unmerged branch unless you pass `force` as the
2nd arg. Unlinks the `.agents` junctions first so deletion can never recurse through them into the main
checkout's real skill files, then removes + prunes.

```bash
BRANCH="$1"; FORCE="$2"
[ -n "$BRANCH" ] || { echo "usage: worktree remove <Type>/<Name> [force]"; exit 1; }
root=$(git rev-parse --show-toplevel)
DEF=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@'); DEF=${DEF:-master}
WT=$(git worktree list --porcelain | awk -v b="refs/heads/$BRANCH" '$1=="worktree"{p=$2} $1=="branch"&&$2==b{print p}')
[ -n "$WT" ] || { echo "no worktree registered for branch '$BRANCH' — check: git worktree list"; exit 1; }

# Merged gate: tip is an ancestor of origin/DEF, OR its PR is MERGED. Don't nuke unmerged work.
git fetch origin --quiet
MERGED=0
git merge-base --is-ancestor "$BRANCH" "origin/$DEF" 2>/dev/null && MERGED=1
if [ "$MERGED" != 1 ]; then
  state=$(gh pr view "$BRANCH" --json state -q .state 2>/dev/null); [ "$state" = "MERGED" ] && MERGED=1
fi
if [ "$MERGED" != 1 ] && [ "$FORCE" != "force" ]; then
  echo "REFUSING: '$BRANCH' isn't merged into origin/$DEF and its PR isn't MERGED."
  echo "Merge the PR first (the convention), or re-run: worktree remove '$BRANCH' force"; exit 1
fi

# Stand in the MAIN checkout before deleting — NEVER inside the tree being removed. Windows refuses to
# delete a directory that is a process's current directory; that is the #1 cause of orphaned worktree
# folders (git drops the admin entry, the folder can't be deleted, and it lingers forever).
main_co=$(git worktree list --porcelain | awk '/^worktree /{print $2; exit}')
cd "$main_co" 2>/dev/null || cd /

# Unlink our junctions (Git Bash sees them as -type l) BEFORE removing — rmdir drops the link only.
find "$WT/.agents" -type l 2>/dev/null | while read -r j; do
  MSYS_NO_PATHCONV=1 cmd /c rmdir "$(cygpath -w "$j")" >/dev/null 2>&1 && echo "unlinked: ${j#$WT/}"
done

git worktree remove --force "$WT" 2>/dev/null
git worktree prune
# Removal can drop the admin entry yet leave the folder (Windows lock / a shell cwd'd inside). Finish
# the delete, then VERIFY — never report success while the folder survives, or it becomes an orphan.
if [ -d "$WT" ]; then
  rm -rf "$WT" 2>/dev/null || MSYS_NO_PATHCONV=1 cmd /c rmdir /s /q "$(cygpath -w "$WT")" >/dev/null 2>&1
fi
if [ -d "$WT" ]; then
  echo "!! STILL PRESENT: $WT — a live process holds a handle. Close that session/editor, then re-run."
else
  echo "=== removed worktree + folder gone: $WT ==="
fi
git branch -d "$BRANCH" 2>/dev/null && echo "deleted merged local branch: $BRANCH" \
  || echo "kept local branch '$BRANCH' (not fully merged into current HEAD, or already gone)"
git worktree list
```

## Rules

- **Inside the repo, never a sibling dir.** `<repo>/.worktrees/<Branch-flattened>` — one repo is one
  top-level folder, and `create` adds `/.worktrees/` to `.git/info/exclude` so it stays out of `git
  status`. A sibling `<repo>.worktrees/` at the same root is the banned layout. Still clear of the
  harness-reserved `.Codex/worktrees/`.
- **Match existing branch casing.** If a branch of the same name exists in any casing, reuse that exact
  ref — never create a second casing (Windows can't hold both; it breaks `fetch`/`pull` for everyone).
  Only when creating a genuinely new branch, enforce the Capitalized `<Type>/` prefix.
- **Branch off fresh `origin` default**, not stale local — `create` fetches first. Keeps new worktrees
  from starting already-drifted.
- **Only link the local-only `.agents` skills.** Tracked skills come with the checkout; this junctions
  just the untracked skill dirs and snapshots `settings.local.json`. Never junction the whole `.agents`
  (it may already exist in the checkout) — the link would fail or shadow tracked content.
- **Never remove an unmerged worktree** without an explicit `force`. Merge the PR first; that's the
  point of the merge-as-you-go convention.
- **Unlink junctions before deleting.** Belt-and-braces even though `rm`/`rmdir` are junction-safe here
  — a stray follow-through would delete the main checkout's real skill files.
- **Delete from the main checkout, then verify the folder is gone.** Never run removal with a shell
  cwd'd inside the worktree — Windows then can't delete it and orphans the folder (the pile-up). Always
  force-delete any leftover tree and confirm it's gone rather than trusting `git worktree remove`'s exit.
- Report the final branch/path/base on create; the surviving `git worktree list` on remove.
```



