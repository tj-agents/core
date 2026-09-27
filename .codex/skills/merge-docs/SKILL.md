---
name: merge-docs
description: Land a documentation or meta-only change as its own fast PR, bypassing the merge queue and its end-to-end gate through the sanctioned admin merge, because a diff with zero runtime blast radius has nothing for that gate to prove. Covers the in-scope path list that is a hard precondition rather than a hint, why a comment-only edit to a CI workflow still fails it, the docs review that is the only gate such a change gets and the pure-close-out exemption from it, the skip label that keeps a queue fallback cheap, and confirming no publish fired. Use when the user says merge docs, docs pr, or wants markdown, agent-instruction, plan or skill changes shipped without the full queue — and route anything touching runtime, package, schema, deployment or test-selection paths to the queue instead.

kind: workflow
domain: process
model: gpt-6-luna
---

# Landing a meta-only change

Read and follow the [canonical shared definition](../../../.agents/engineering/workflow/merge-docs/SKILL.md) in full.
This entry point supplies only Codex discovery metadata; the shared procedure is authored once under `.agents/`.
