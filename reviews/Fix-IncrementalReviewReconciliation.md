# Code review - Fix/IncrementalReviewReconciliation

**Review status:** `complete`
**Judgment:** `changes-requested`

**Reviewed up to commit:** `cdc58d8fafff65257b1fb0ebdc329d200a26231f`

## Review pass - 2026-10-07 - full

**Candidate base:** `a9988f52dc388fb4793733657366a94696f32da5`
**Candidate head:** `cdc58d8fafff65257b1fb0ebdc329d200a26231f`
**Candidate branch:** `Fix/IncrementalReviewReconciliation`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:17453b24fdddc5fbf9ca883463b1c88d7b164dba899e3d6b38f701bae1cd9def` `(3 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\_DX0yMLq6_6aPQrZQpFVDM\2Zv6ZHqIvCT5-JyXomRNka`
**Candidate bundle identity:** `sha256:b0d9a10402c8cd32e153daaad3b361575d248038f4ee6b6bd9936eab661c2622`
**Work-order path:** `reviews/Fix-IncrementalReviewReconciliation.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

Native L4 and fresh workflow L4 review. Worker verified44 ReviewTests and8 focused shared-runner regressions, including real Git ancestry and route invalidation. Generator, tier, digest and harness checks passed. Final synchronization integrates disjoint published changes at a9988f52.

### Findings

Native review and fresh workflow review independently confirm one regression. Fresh review verified immutable bundle hashes and reproduced it in real temporary Git history. Its redundant broad test rerun was interrupted; the prior44-test worker result remains the completed-suite evidence.

- [ ] R1 - MEDIUM - A rewritten or rolled-back stack parent can escape review invalidation (`.agents/workflows/workflow_ops.py:977-985`). The nonancestral fallback substitutes recorded trunk for any target; when the parent restores a reviewed file to its trunk contents, the trunk-to-parent diff hides that relevant change. Restrict fallback to a verified trunk target and preserve the recorded-parent comparison for stack targets. Add rollback and divergent rewrite regressions.

The conservative-history contract also needs a new-file fixture: missing or invalid recorded trunk evidence can otherwise appear unchanged because the new file exists in neither baseline. Verify this boundary in the same serial repair.
