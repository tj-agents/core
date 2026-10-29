---
name: commit-all
description: Commit the ENTIRE working tree in a single commit — no survey, no slicing, no exclusions, because the user has explicitly opted out of curation. Covers the one judgment call worth pausing for (secrets, large binaries, machine-local agent state), why a failing pre-commit hook is fixed rather than bypassed, and the plan checkpoint that rides into the same commit. Use whenever the user wants everything committed at once — commit all, commit everything, one commit, just commit it all, stage everything and commit.
model: claude-haiku-4-5
metadata:
  tj-agents-kind: operation
  tj-agents-domain: process
---

# Committing the whole tree in one commit

Read and follow the [canonical shared definition](../../../../.agents/engineering/skills/commit-all/SKILL.md) in full.
This entry point supplies only Claude discovery metadata; the shared procedure is authored once under `.agents/`.
