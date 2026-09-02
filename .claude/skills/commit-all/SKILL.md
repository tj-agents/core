---
name: commit-all
description: Commit the ENTIRE working tree in a single commit — no survey, no slicing, no exclusions, because the user has explicitly opted out of curation. Covers the one judgment call worth pausing for (secrets, large binaries, machine-local agent state), why a failing pre-commit hook is fixed rather than bypassed, and the plan checkpoint that rides into the same commit. Use whenever the user wants everything committed at once — commit all, commit everything, one commit, just commit it all, stage everything and commit.
domain: process
---

# Committing the whole tree in one commit

Stage everything and make one commit. This is the deliberate opposite of
[`commit`](../commit/SKILL.md)'s survey-and-slice flow: the user has opted out of curation, so do not survey, do not
slice, and do not hold anything back.

Reach for this when the instruction is *commit all*, *commit everything*, *one commit*, *just commit it all*,
*stage everything and commit*. [`committing`](../committing/SKILL.md) still owns *when* committing is the right
move at all.

## The flow

For plan-managed work, apply the checkpoint procedure first only when this commit crosses a material
transition, recording its evidence as `this commit`. `git add -A` then carries the update in the one requested
substantive commit.

```
git branch --show-current    # must NOT be the default branch
git add -A
git commit -m "<one-line summary of the whole change>"
git log --oneline -1         # confirm it landed
git status --short           # must be clean afterwards
```

That is the entire procedure. No status survey first, no per-file dump, no per-workstream messages — that
ceremony is exactly what the user declined by reaching for this rather than [`commit`](../commit/SKILL.md).

## What still holds

- **Never commit on the default branch.** If you are on it, branch first per
  [`git-branching`](../git-branching/SKILL.md), then stage and commit.
- **Never `--no-verify`**, and never bypass commit signing. A failing pre-commit hook is a cause to fix, not a
  step to skip.
- **No AI-attribution trailer**, for any agent.
- **Pushing is out of scope.** This procedure only commits; [`push`](../push/SKILL.md) pushes.

## The one judgment call

`git add -A` is all-in by design. Pause only to flag — in one line, never by silently dropping it — when the
stage would obviously sweep in something that must never be in history:

- secrets, credentials, or an environment file holding live values;
- large build output or binaries;
- machine-local agent or editor state, including tracked worktree gitlink churn.

Name it and let the user decide. Otherwise trust the instruction and commit everything: **when unsure, commit
— they asked for all.**

## Message and report

One imperative line summarising the overall change, matched to the repo's `git log --oneline` style and derived
from the actual diff rather than from memory of the session. When the tree genuinely spans unrelated things, a
summary line plus a two-to-four-bullet body listing them is fine — but it is still one commit.

When a material plan checkpoint was due, confirm it landed *in* that commit. Do not create a second commit
solely to replace `this commit` with its SHA. Report the hash, subject and file count, and
confirm `git status` is clean — or name the single thing you flagged and why it was held back.
