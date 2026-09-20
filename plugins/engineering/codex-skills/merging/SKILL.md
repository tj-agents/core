---
name: merging
description: Landing a PR safely through a GitHub merge queue — synchronize once immediately before final review, preserve that exact reviewed head when unrelated base commits land, then confirm the queue outcome with the reconnect-safe shared monitor. It resolves to exactly one of four terminal states (merged, a failed check, conflicted-so-auto-merge-was-silently-disabled, or green-but-never-admitted), never retries or toggles a genuine failure, never swallows query errors, and distinguishes a failed merge-group run from a PR-state glitch; it also owns only the generated downstream version-bump PR causally produced by that merge. Use after enabling auto-merge, when a PR seems stuck, when a merge-queue run fails, or before starting new work on a possibly-broken base.

kind: contract
domain: process
---

# Merging

Read and follow the [canonical shared definition](../../.agents/engineering/contract/merging/SKILL.md) in full.
This entry point supplies only Codex discovery metadata; the shared procedure is authored once under `.agents/`.
