# Workflow runtime debt

## Skill registration still assumes the old flat source layout

`workflow_ops.py skills --lifecycle plan-execution` looks for
`.agents/skills/plan-execution/SKILL.md`, which no longer exists in core's canonical layout.
The repo-declared configuration work loaded the actual workflow body directly and retained
the remaining native workflow operations. Resolve when skill registration discovers canonical
scoped skill paths and tests both source and installed package layouts.

## Inspection truncates the first unstaged path

The Git helper strips leading whitespace from porcelain output before `inspect` removes its
three-character status prefix. An initial ` M plans/...` therefore becomes `lans/...` in
`dirty_paths`. Direct Git status was used to verify this branch. Resolve when porcelain parsing
preserves status bytes and tests an initial unstaged path, staged path and path containing spaces.

## PR preflight misclassifies an incremental review base

`delivery-preflight` passes its final incremental review descriptor to `review-reconcile` against `origin/main`. An incremental descriptor's base is the prior reviewed commit, so an unchanged `origin/main` can be reported as `base-changed-relevant-evidence` when the prior commit touched a path in the incremental pass. The core Windows hook PR reproduced this false blocker; preparing a cumulative base-to-head descriptor let preflight verify the already reviewed chain.

Resolve when preflight reads the canonical work order's continuous completed review passes, reconciles the original remote base against the full reviewed path and rule set, and tests an incremental pass with unchanged, disjointly moved, and relevantly moved remote bases.
