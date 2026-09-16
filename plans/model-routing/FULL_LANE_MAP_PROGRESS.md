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

The policy and repository implementation are complete in this candidate. It contains routed
handoffs, route declarations for every delegating skill, runtime and repository-scan enforcement, corrected
Workflow v2 lane peers, generated payloads, tests, and this plan corpus.

## Next Steps

Run the full CI-equivalent validation, create the immutable implementation commit, complete the canonical
review, address any findings, then push, open the PR, and own CI and merge to terminal.

## Completed work

- Resolved repository ownership, generated-file boundaries, hook packaging, CI, and handoff launcher contracts.
- Updated the machine policy and routing guide so L0/L1/L2/L3 map to Astra/Sol/Terra/Luna and their distinct
  Claude peers.
- Routed both handoff launchers and made each handoff infer its lane from the delegated task.
- Added route declarations and enforcement for handoffs, review lenses, workflow calls, and native agent
  dispatch, including missing-model and missing-effort rejection.
- Aligned Workflow v2 strategic/review, implementation, and mechanical roles with L1, L2, and L3.

## Verification

Focused routing-guard tests pass (13 tests); the repository scan is clean; Workflow v2 contract tests pass
(53 tests); generated files were regenerated successfully; representative resolver calls return all four
distinct lane pairs.

## Reviews

Not started; review follows the first immutable implementation candidate.

## Decisions, discoveries, blockers, and deviations

- The frontier lane is opt-in through an authorization parameter whose value may come only from the user's
  explicit request or a durable workflow declaration; ordinary ambiguity, judgement, blast, and design tags
  never select it.
- Claude and Codex each use one distinct model per lane.
- Enforcement detects literal assignment shapes rather than carrying a duplicate model roster.
- Codex CLI metadata ranks Sol as the reliable workhorse, Terra as the balanced coding model, and Luna as
  fast and affordable; `gpt-6-pro` is absent from the current picker metadata and remains unmapped.
