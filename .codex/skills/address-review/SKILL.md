---
name: address-review
description: Serially resolve open findings in the canonical review work order without changing its frozen candidate, original finding text, severity, or completed pass judgment; verify and commit coherent fixes, then require a fresh incremental watermark. Use when the user explicitly asks to address findings or an implementation workflow already authorized review-and-fix.

kind: workflow
domain: process
model: gpt-6.1-sol
---

# Address a review serially

Read and follow the [canonical shared definition](../../../.agents/engineering/workflow/address-review/SKILL.md) in full.
This entry point supplies only Codex discovery metadata; the shared procedure is authored once under `.agents/`.
