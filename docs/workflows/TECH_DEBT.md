# Workflow runtime debt

## PR preflight misclassifies an incremental review base

`delivery-preflight` passes its final incremental review descriptor to `review-reconcile` against `origin/main`. An incremental descriptor's base is the prior reviewed commit, so an unchanged `origin/main` can be reported as `base-changed-relevant-evidence` when the prior commit touched a path in the incremental pass. The core Windows hook PR reproduced this false blocker; preparing a cumulative base-to-head descriptor let preflight verify the already reviewed chain.

Resolve when preflight reads the canonical work order's continuous completed review passes, reconciles the original remote base against the full reviewed path and rule set, and tests an incremental pass with unchanged, disjointly moved, and relevantly moved remote bases.

## The strategic workflow stage is pinned below planning's lane

L1 now owns planning and design, but the workflow contract's `strategic` stage (architecture, major planning) is still derived from L3 in `.agents/workflows/hosts/*.json` and `STAGE_LANES`. Draft #39 repins the same stages for Codex, so the two changes would collide.

Resolve when `strategic` is derived from L1 on both hosts, `STAGE_LANES` and the host pins agree, and the workflow contract tests pass.
