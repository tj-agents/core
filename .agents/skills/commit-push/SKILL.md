---
name: commit-push
description: Commit current changes and push to the current branch in one step. Use whenever Tommy says "commit and push", "commit this", or "push this". No preamble, no analysis.

kind: operation
domain: machine
---

Run exactly ONE tool call:

```powershell
git add -A; git commit -m @'
<message>

Co-Authored-By: Codex <noreply@anthropic.com>
'@; git push
```

Rules:
- Commit EVERYTHING — leave no working-tree change behind. Default to a single `git add -A` commit (stages tracked edits AND new files; node_modules/ and smoke-tests/ are gitignored, so `-A` never touches them). You MAY split into multiple logical commits if it genuinely helps — but then `git push` only ONCE, at the very end.
- Message: `AB#<ticket> <imperative summary>` — ticket from the current branch name (`AB#xxxxx/...`), summary from what was just changed in this session. Do NOT run `git status`, `git diff`, or `git log` first.
- On success, reply with one line: the commit hash and "pushed". Nothing else.
- Only investigate output if the exit code is nonzero.
