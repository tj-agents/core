---
name: commit
description: Turn the working tree into clean, logical git commits — survey staged, unstaged and untracked state, slice the changes into coherent per-workstream commits with honest messages derived from the actual diff, keep move-only renames out of rewrite commits, exclude junk and say what was excluded, and verify the resulting shape. Covers why a non-empty index is a signal rather than an accident, why a stale commit-plan artifact must be checked against the real tree, and the plan checkpoint a plan-managed slice carries. Use whenever the user asks to commit work, tidy the tree into commits, or wants a readable history rather than one mega-commit.
domain: process
---

# Committing the working tree as curated slices

Turn whatever is in the working tree into a history a reviewer can read one commit at a time. The job is
curation, not `git add -A && git commit`.

[`committing`](../committing/SKILL.md) is *when* to commit and why the default is to commit rather than leave
work loose; this doc is *how* to shape the commits once that trigger fires. When the user has asked for one
commit of everything, [`commit-all`](../commit-all/SKILL.md) is the procedure instead — they have opted out of the
survey and slicing below, and running it anyway is the ceremony they declined.

## Step 0 — survey before touching anything

```
git status --short
git diff --cached --stat                    # already staged
git diff --stat                             # unstaged modifications
git ls-files --others --exclude-standard    # untracked
git log --oneline -5                        # the repo's message style
git branch --show-current
```

- **Never commit on the default branch.** Branch first, per [`git-branching`](../git-branching/SKILL.md), unless the
  user explicitly says otherwise.
- **A non-empty index is a signal, not an accident.** If a prior session deliberately staged a curated set,
  treat it as its own commit candidate. Do not `git add` over it and fuse it with unrelated work.
- **Check for commit-plan artifacts before inventing structure** — a `*COMMIT_PLAN*.md`, a note in the
  repository's own guidance, a plan file referenced in the session. Then **verify its claims against the
  actual tree**: plans go stale, and a directory it says was moved may have been moved back. Follow what
  still holds and say what did not.

## Step 1 — slice by workstream, not by directory accident

One commit per coherent story, each readable standalone: a feature or refactor, an unrelated workstream that
merely shares the tree, the fixes from a debugging session, a tooling or guidance change.

- **Keep move-only renames separate from rewrites** where the tree allows it cheaply — a fused rename+rewrite
  commit destroys diff readability. Do not reconstruct history archaeologically once the intermediate states
  are gone; note the fusion in the message instead.
- Stage each slice by explicit pathspec (`git add <paths>`), never `git add -A`, unless the remaining tree
  genuinely is one slice.
- **One file can carry two workstreams** — a staged base with an unstaged fix on top. Committing the index
  first, then staging the file again, splits them correctly.

## Step 2 — exclude junk, and say what you excluded

Untracked files get reviewed, not blanket-added. What must not enter history: a stray lockfile where no
manifest exists, scratch logs, build output, editor or agent state directories, machine-local locks, temp
scripts. Leave them untracked and **name what was excluded and why** — the user may overrule. If a scaffolding
file says of itself that it must not be committed, honour that.

## Step 3 — messages

- **Subject:** imperative, roughly 72 characters or fewer, saying what the commit does. Match the repo's
  existing style from the `git log --oneline` above.
- **Body:** the why and the non-obvious consequences, derived from **the actual diff** — read it rather than
  writing from memory of the session. Numbers and root causes beat adjectives: *"READPAST error 650, 1359
  occurrences"* carries what *"fixed flaky tests"* does not. The reasoning belongs here and not in the code as
  running commentary, which is the point [`committing`](../committing/SKILL.md) makes.
- **Never add an AI-attribution trailer** — no co-author line, no "generated with" line, for any agent.
- Write a multi-line message through a single-quoted here-string in PowerShell, or `-m` with real newlines in
  a POSIX shell. Never a literal `\n`.

## Step 4 — the approval gate, and when it is already satisfied

Default: show the per-commit plan — slices, files, messages — and wait for explicit approval before running
`git commit`.

Skip the wait when the user has **already** told you to commit in this exchange. That instruction *is* the
approval, and re-asking after it is noise.

## Step 5 — commit and verify

When a plan-managed slice crosses one of the material transitions in the checkpoint standard, update and
compact its ledger before staging, record the evidence as `this commit`, and include it in that substantive
slice. Natural local commits that do not cross a material transition need no ledger rewrite. **Never create a
recursive follow-up commit whose only purpose is to write its own SHA.**

- Commit each slice and capture the hash.
- **If a pre-commit hook fails, fix the cause.** Never `--no-verify`, never bypass signing.
- After the last commit, `git status --short` must be clean, or every remaining entry deliberately excluded
  and explained. `git log --oneline -<n>` confirms the shape.
- Report hash, subject and file count per commit, plus what was left uncommitted and why.

## Anti-patterns

- One mega-commit of a mixed tree when the slices are obvious and cheap.
- Slices so fine they demand `git add -p` archaeology nobody asked for.
- Generated noise inside a code commit — lockfile churn from an aborted install, a stray last-run log.
- Editing the user's staged index without saying so.
- A message describing the session — *"fixed the thing we discussed"* — instead of the change.
