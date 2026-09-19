---
name: pr-preflight
description: Read-only readiness gate answering whether the current branch is clear to open or enqueue a PR right now, run before you do. Checks it is a real capitalized Type/Name branch rather than the default one, that the local is not behind its own remote or tracking a deleted one, that it is current with base, that all code is committed while docs may ride uncommitted, whether a PR already exists, that no generated version-bump PR is explicitly red while healthy or pending automation remains out of scope, that no published-package cut-over is half-done, and that the targeted local checkpoint was run rather than a full solution build — then reports GREEN with the next command or every blocker with its exact fix. Changes no state beyond a fetch. Use when the user asks whether they can PR this, are clear to PR or merge, or wants a check before opening or landing one.

kind: operation
domain: process
model: gpt-5.6-luna
---

# Is this branch clear to PR?

Read and follow the [canonical shared definition](../../.agents/engineering/operation/pr-preflight/SKILL.md) in full.
This entry point supplies only Codex discovery metadata; the shared procedure is authored once under `.agents/`.
