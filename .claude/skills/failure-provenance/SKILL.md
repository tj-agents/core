---
name: failure-provenance
description: Establish when a failing test last genuinely passed and what was different then, from pipeline job history rather than any checked-in baseline, and classify the failure as a real regression, a budget/timing race, or a true flake before proposing a fix. Covers reading conclusions at job level because a green workflow says nothing when the job was skipped, finding the last real execution by paging workflow runs, diffing that run's configuration and duration against the local one, the three failure classes and the signature that distinguishes them, why a local baseline file is never evidence, and stating the headroom a fix buys instead of declaring victory. Use before fixing any test that "used to pass" or is suspected flaky, and again after the fix to say what margin it restored.

kind: contract
domain: process
---

# Establishing what changed since it last passed

Read and follow the [canonical shared definition](../../../.agents/engineering/contract/failure-provenance/SKILL.md) in full.
This entry point supplies only Claude discovery metadata; the shared procedure is authored once under `.agents/`.
