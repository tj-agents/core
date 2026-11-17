---
name: commit-all
description: Commit the entire working tree in one commit with no survey or slicing, pausing only for secrets, large binaries or machine-local state. Use for commit all, commit everything or one commit.

kind: operation
domain: process
lane: L7
---

# Commit the whole tree in one commit

Owns the one-commit path the user chose instead of `engineering:commit`'s curated slices.
`engineering:committing` owns when to commit at all.

```text
git branch --show-current    # must NOT be the default branch; branch first per engineering:branching
git add -A
git commit -m "<one-line summary of the whole change>"
git log --oneline -1         # confirm it landed
git status --short           # must be clean afterwards
```

Never `--no-verify` or bypass signing; fix a failing hook's cause. Attribution follows the harness. Pushing
is `engineering:push`'s job.

Pause only to flag, in one line, something that must never enter history: secrets or a live environment
file, large build output or binaries, machine-local agent or editor state. Let the user decide; otherwise
commit everything.

The message is one imperative line derived from the actual diff in the repository's `git log` style, plus
two to four bullets when the tree spans unrelated things. Report the hash, subject and file count, and that
`git status` is clean, or name what was held back and why.
