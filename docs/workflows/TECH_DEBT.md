# Workflow runtime debt

## PR preflight misclassifies an incremental review base

`delivery-preflight` passes its final incremental review descriptor to `review-reconcile` against `origin/main`. An incremental descriptor's base is the prior reviewed commit, so an unchanged `origin/main` can be reported as `base-changed-relevant-evidence` when the prior commit touched a path in the incremental pass. The core Windows hook PR reproduced this false blocker; preparing a cumulative base-to-head descriptor let preflight verify the already reviewed chain.

Resolve when preflight reads the canonical work order's continuous completed review passes, reconciles the original remote base against the full reviewed path and rule set, and tests an incremental pass with unchanged, disjointly moved, and relevantly moved remote bases.

## The L1 lane agent has no user-authorization gate

The handoff launchers refuse `-Lane L1` without `-UserAuthorizedLane`, but a delegating agent can still select the generated `lane-l1` agent directly, so a subagent dispatch is not held to L1's reservation for critical design decisions.

Resolve when selecting a lane agent whose rung carries `requires_user_authorization` is refused without the user's explicit authorization on both hosts, with a test.
