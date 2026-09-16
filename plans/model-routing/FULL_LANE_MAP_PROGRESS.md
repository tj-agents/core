# Full model and effort lane map progress

- Plan: `plans/model-routing/FULL_LANE_MAP_PLAN.md`
- Roadmap: `plans/model-routing/MODEL_ROUTING_ROADMAP.md`
- Roadmap item: `model-routing/full-lane-map`
- Worktree: `C:\Users\TommySeery\source\repos\base-agents`
- Branch: `Feature/Model-Routing`
- PR: not opened
- Dependency/package gates: machine routing policy is outside the repository and must be updated in the same session
- Last reconciled: 2026-09-16 from the implemented routing guard, generated payloads, machine policy, and focused tests

## Current state

Implementation, review remediation, and local validation are complete in the current candidate. It contains
routed handoffs, route declarations for every delegating skill, runtime and repository-scan enforcement,
mandatory routed inputs for Workflow v2, model-free generated agent defaults, generated payloads, tests,
and this plan corpus.

## Next Steps

Push the stable candidate once, open the GitHub PR, and own exact-head CI and merge to terminal.

## Completed work

- Resolved repository ownership, generated-file boundaries, hook packaging, CI, and handoff launcher contracts.
- Updated the machine policy and routing guide so L0/L1/L2/L3 map to Astra/Sol/Terra/Luna and their distinct
  Claude peers.
- Routed both handoff launchers and made each handoff infer its lane from the delegated task.
- Added route declarations and enforcement for handoffs, review lenses, workflow calls, and native agent
  dispatch, including missing-model and missing-effort rejection.
- Aligned Workflow v2 strategic/review, implementation, and mechanical roles with L1, L2, and L3.
- Removed Workflow v2's duplicate model table and generated role defaults; host preparation now requires
  externally resolved model, effort, and lane values.
- Addressed all canonical review findings through commits `2e2932c`, `9b1f0df`, `943347f`, and this commit.

## Verification

Full CI-equivalent validation passes: 443 hook tests with one platform skip, Workflow v2 verification, the
repository routing scan, and generated-file verification. Representative resolver calls return all four
distinct lane pairs.

## Reviews

Canonical work order `reviews/Feature-Model-Routing.md` is complete and approved; it owns the exact current
watermark. All three findings are resolved and no finding remains open.

## Decisions, discoveries, blockers, and deviations

- The frontier lane is opt-in through an authorization parameter whose value may come only from the user's
  explicit request or a durable workflow declaration; ordinary ambiguity, judgement, blast, and design tags
  never select it.
- Claude and Codex each use one distinct model per lane.
- Enforcement detects literal assignment shapes rather than carrying a duplicate model roster.
- Codex CLI metadata ranks Sol as the reliable workhorse, Terra as the balanced coding model, and Luna as
  fast and affordable; `gpt-6-pro` is absent from the current picker metadata and remains unmapped.
