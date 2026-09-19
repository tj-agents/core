---
name: commit-push
description: Commit the intended current changes and push the verified commit to the current branch. Use when Tommy explicitly requests both operations.

kind: utility
domain: machine
---

# Commit and push

Read the repository instructions first. Inspect the branch, staged state, unstaged diff, untracked files, and
recent commit style before staging anything.

Stage only the intended coherent paths. Preserve an existing curated index, exclude generated junk and
machine-local files, and never use `git add -A` unless the user explicitly asked to commit the entire tree
and the complete status was reviewed first.

Follow the repository's commit policy and message format. Use an `AB#` work-item prefix only when that
repository's own instructions require it. Never add an AI-attribution trailer.

Run the relevant targeted checkpoint before committing. Commit without bypassing hooks, push the current
branch once, fetch it, and require the remote-tracking ref and any open PR head to equal the local commit.
Never force-push unless the user explicitly requests it.

On success, report the commit hash and that the exact head was pushed. On failure, diagnose and fix the
actual cause; never report success from the command exit code alone.
