---
name: commit
description: Turn the working tree into coherent per-workstream commits with messages from the actual diff, excluding junk and naming what was excluded. Use to commit work or tidy the tree into commits.

kind: operation
domain: process
lane: L7
---

# Commit the working tree as curated slices

Owns shaping the working tree into commits a reviewer can read one at a time. `engineering:committing`
owns when to commit; `engineering:commit-all` is the procedure when the user asked for one commit of
everything. When the work is authorized or the user asked to commit, commit without asking again.

1. **Survey.** `git status --short`, `git diff --cached --stat`, `git diff --stat`,
   `git ls-files --others --exclude-standard`, `git log --oneline -5` and `git branch --show-current`.
   Never commit on the default branch; branch first per `engineering:branching`. A non-empty index is a
   deliberate candidate, not an accident: do not fuse unrelated work into it.
2. **Slice by workstream.** One commit per coherent story, staged by explicit pathspec, never `git add -A`
   unless the tree is genuinely one slice. Keep move-only renames apart from rewrites when that is cheap.
   One file can carry two workstreams: commit the index first, then stage the file again.
3. **Exclude junk and say so.** Never stage ignored files. Leave stray lockfiles, scratch logs, build output,
   editor or agent state and machine-local locks untracked, and name what was excluded and why.
4. **Write messages from the diff.** An imperative subject of about 72 characters in the repository's
   `git log` style; a body with the why and non-obvious consequences, numbers and root causes over
   adjectives. Attribution follows the harness. Write multi-line messages with a single-quoted here-string in
   PowerShell or real newlines in a POSIX shell, never a literal `\n`.
5. **Commit and verify.** Never `--no-verify` or bypass signing; fix a failing hook's cause. Afterwards
   `git status --short` is clean or every remaining entry is a named exclusion.

```text
Tree: src/export.py + tests/test_export.py (CSV quoting), docs/setup.md (new step), run.log (scratch).
Commit 1: git add src/export.py tests/test_export.py -> "Quote CSV fields that contain commas"
Commit 2: git add docs/setup.md -> "Document the export setup step"
Excluded: run.log, a scratch log.
```

Report hash, subject and file count per commit, plus anything left uncommitted and why.
