---
name: committing
description: Commit completed reversible work at natural local boundaries, and push separately only when a stable candidate needs remote validation, a real handoff, or a meaningful published checkpoint. Covers safe staging, tests before commit, batching related review fixes into one verified push, exact-head remote verification, and why finished work must not remain loose. Use whenever a chunk of work goes green, when deciding whether a local commit needs publishing, or when finished work belongs in a different PR than the current branch.

kind: contract
domain: process
---

# Committing and pushing

Read and follow the [canonical shared definition](../../../.agents/engineering/contract/committing/SKILL.md) in full.
This entry point supplies only Claude discovery metadata; the shared procedure is authored once under `.agents/`.
