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

## Active work is prematurely treated as a handoff

During the system-role projection correction, questions and follow-up corrections to the same feature repeatedly led toward a handoff even after Tommy asked to continue in the existing session. Preparing another context displaced authorized implementation and review work. The continuation policy already preserves the current goal; the unresolved failure is applying that ownership through conversational steering and the handoff selector.

Resolve when continuation and handoff selection preserve the current owner for an implementation question, review correction, or explicit "continue here", and regression cases demonstrate that only an explicit transfer request or an applicable execution-transfer requirement changes ownership. A request to note process debt must retain the active feature's owner and respect the user's chosen order of work.

## Applicable domain standards are missed before implementation and review

The system-role feature loaded build, style, naming, DI and integration-test standards, but omitted the available DDD/domain-value owners before designing reconciliation behavior and missed the unique-set carrier contract. Business behavior consequently stayed in the API projector, and tuple uniqueness was represented by collection/list contracts. A completed general review did not catch the missing standards; the user had to identify them.

Investigation on 2026-10-09 reproduced concrete coverage gaps. Installed tier detection identifies .NET but delivers the tier identity, not the DDD contract body. Codex has `features.hooks = false` and disabled router hook entries, so the read-before-write gate is inactive. The authz feature worktree has no `.agents/skill-routes.json`; the main checkout has a private excluded generated table. Installed `skill_router.find_repo_root` walks beyond the nested worktree to that parent table, while `workflow_ops.route_findings` returns no requirements when the current worktree has no table. Thus editing and frozen review do not resolve the same requirements. The installed router has no shipped fallback registry.

The .NET generator routes a production API projector to style and naming only. Its Domain-folder row adds `domain-design`, whose body points to DDD and value owners, but neither `domain-ddd` nor `domain-values` is a required route. Business logic initially placed in an API folder therefore avoids the domain route entirely. Tier-convention review lists the available domain owners but still relies on the agent to select and read them; this session failed that obligation. Existing helper skill-resolution debt also interferes with the intended installed-package identity record.

Related delivery: core PR116 (scoped project facts and standards contexts) merged on 2026-10-08 and explicitly deferred source ownership and host activation. `core/.worktrees/Feature-StandardsSourceOwnership` retains uncommitted source ownership implementation and tests, with no PR for that branch. Dotnet PR35 (the skill-route generator, with cris-authz registered) merged on 2026-10-05; its own contract says registry emission becomes live only when shipped beside the installed router. These are related foundations, not evidence of an active DDD loading requirement.

Resolve when the .NET owner declares DDD/value requirements for the selected DDD service profile across API and Domain production changes; core resolves that profile consistently for the actual checkout in editing and frozen review, and records successful contract loading before design/first write. Regression coverage must include a nested fresh worktree, an API projector containing business behavior, a consumer with private or absent routes, and review using the same requirement identities. After the separate hook-repair owner restores supported activation, a trusted fresh-session probe must deny a relevant write without load proof and allow it after successful reads. Preserve the intentionally disabled hooks during this investigation; source tests, generated manifests, tier listings and compilation alone do not prove host enforcement or application of the standards.

Tommy also clarified an outstanding naming decision: injected collaborator identifiers retain their responsibility suffix, while their subject may be shortened when unambiguous (`IRelationshipTupleStore relationshipStore` when there is one store). The loaded `dotnet:naming-collaborators` currently requires the full subject and role. The .NET plugin owns that standard update; core owns preserving and routing this user clarification. Keep the full subject where shortening would introduce ambiguity. Resolve this follow-up when the owning .NET naming standard reflects the clarification and its examples cover both contexts, without duplicating the canonical rule in core.
