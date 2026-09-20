---
name: open-pr
description: Open or update the pull request for the current branch with the forge's own CLI once a stable substantive candidate needs remote validation. Covers the read-only readiness gate, continuing actionable work after opening instead of stopping by default, drafting the title and body from committed history, keeping required attribution, why end-to-end labels belong to merge, and that marking a draft ready is not merge authorization. Use when the user says open a PR, raise a PR, create the PR, or PR this. Landing it is the merge procedure's job.

kind: operation
domain: process
model: gpt-5.6-terra
---

# Opening a pull request

Read and follow the [canonical shared definition](../../.agents/engineering/operation/open-pr/SKILL.md) in full.
This entry point supplies only Codex discovery metadata; the shared procedure is authored once under `.agents/`.
