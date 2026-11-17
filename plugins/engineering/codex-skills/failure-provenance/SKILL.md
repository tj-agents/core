---
name: failure-provenance
description: For a suspected flaky or timing failure, find the last genuine pass in CI job history, diff it against the failure and classify regression, budget race or flake. Use before fixing a suspected flake.

kind: contract
domain: process
---

# Provenance of a suspected flaky or timing failure

Read and follow the [canonical shared definition](../../.agents/engineering/contract/failure-provenance/SKILL.md) in full.
This entry point supplies only Codex discovery metadata; the shared procedure is authored once under `.agents/`.
