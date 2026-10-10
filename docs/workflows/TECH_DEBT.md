# Workflow runtime debt

## Slice retirement checks the broader goal's completion

The runtime's `checkpoint --state complete` calls the canonical goal's full completion check, even
when its bound slice PR is merged and a workflow handoff records a pending successor. This conflicts
with the documented foreground slice transition: the owner cannot complete while the broader goal
correctly retains unfinished acceptance. A foreground parent can retire the merged slice's scheduler
and binding, preserve its blocked owner receipts, and initialize the next slice against the same goal.

Resolve when slice retirement verifies its exact merged PR/head and handoff without declaring the
broader goal complete, and tests preserve pending successor acceptance across the foreground transition.

## PR preflight misclassifies an incremental review base

`delivery-preflight` passes its final incremental review descriptor to `review-reconcile` against `origin/main`. An incremental descriptor's base is the prior reviewed commit, so an unchanged `origin/main` can be reported as `base-changed-relevant-evidence` when the prior commit touched a path in the incremental pass. The core Windows hook PR reproduced this false blocker; preparing a cumulative base-to-head descriptor let preflight verify the already reviewed chain.

Resolve when preflight reads the canonical work order's continuous completed review passes, reconciles the original remote base against the full reviewed path and rule set, and tests an incremental pass with unchanged, disjointly moved, and relevantly moved remote bases.

## The strategic workflow stage is pinned below planning's lane

L1 now owns planning and design, but the workflow contract's `strategic` stage (architecture, major planning) is still derived from L3 in `.agents/workflows/hosts/*.json` and `STAGE_LANES`. Draft #39 repins the same stages for Codex, so the two changes would collide.

Resolve when `strategic` is derived from L1 on both hosts, `STAGE_LANES` and the host pins agree, and the workflow contract tests pass.

## Non-review workflows run helpers from the reviewed repository

The review family resolves `workflow_ops.py`, `tier_gate.py` and `docs_reachability.py` from the installed
engineering plugin root, so it runs in a repository with no `.agents/`. `plan-execution`, `feature`, `bugfix`,
`merge`, `merging`, `open-pr`, `pr-preflight`, `remote-validation` and `persistent-delivery` still name
`python .agents/workflows/workflow_ops.py`, which exists only inside core.

Resolve when each of those skills names `<engineering>/workflows/workflow_ops.py --root <repository-root>`
and the `test_review_native_layer.py` repository-helper check covers them.

## Workflow skill resolution still assumes the former flat layout

The `skills` operation defaults lifecycle names to `.agents/skills/<name>/SKILL.md`. Core now owns `feature` under `.agents/engineering/workflow/feature/`, so recording the lifecycle by name fails before producing its identity record. This predates the Sol 6.1 update and is independent of lane resolution.

Resolve when lifecycle discovery uses the canonical scope/kind layout and regression coverage proves `skills --lifecycle feature` records the shipped owner in both source and installed package layouts.

## Codex keeps a merge-cleanup obligation after a failed merge

`merge_cleanup_gate.py` records its obligation at PreToolUse, before `gh pr merge` runs. Claude reports a
failed merge through PostToolUseFailure and never blocks Stop on an unconfirmed obligation, but Codex has no
result event, so after a failed or rejected merge it nags once every 10 minutes until `--clear` or the
7-day reconcile drops the obligation.

**Resolution condition.** Codex publishes a tool-result or failure event that hooks can consume; wire the
gate's failure handler to it and delete the obligation when the merge reports no success.

## Review routing requires the write-time opt-in

`review-prepare` names the skills a review owes only through `.agents/skill-routes.json`, and carrying that
table also opts the repository into the write-time router and the red-run gate. The router blocks every
write while any routed skill is unresolved or plugin discovery fails. Core therefore carries no table, so a
review of a changed `SKILL.md` is not required to load `engineering:skill-authoring`; the description and
`AGENTS.md` are its only discovery.

Resolve when a route can apply at review time alone, without opting the repository into write-time routing
or the red-run gate, and core routes authored `SKILL.md` paths to `engineering:skill-authoring` through it,
with a test that `review-prepare` names the skill for such a path.
