---
name: incremental-review
description: Select and run the canonical isolated review workflow over only commits added after the canonical work order's completed watermark, appending one frozen pass and moving the marker only after parent synthesis. Use for new commits since a prior full or staged review, including remediation commits that require a fresh watermark.

kind: workflow
domain: process
---

# Incremental review selector

Read and follow the [canonical shared definition](../../../.agents/engineering/workflow/incremental-review/SKILL.md) in full.
This entry point supplies only Codex discovery metadata; the shared procedure is authored once under `.agents/`.
