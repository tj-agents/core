# Codex hook refresh and stack workflow

## Objective
Deliver a focused core follow-up stacked on PR #48 (`Refactor/RepoDeclaredConfigHarnessMove`) that repairs Codex skill-routing recovery, makes the stacked-PR workflow discoverable as `engineering:stack`, and removes the exposed `base:stack-tiers` skill while preserving tier gating.

## Authorization and checkout
Tommy explicitly authorized a stacked follow-up on PR #48 and a fresh Codex handoff. He then asked to get rid of `stack-tiers`. Work only in `C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-CodexHookRefresh` on `Fix/CodexHookRefresh`. The verified parent head at creation is `279790686f21ddc062230798fd462fe2b978354d`; PR #48 is open and targets `main`. This worktree was clean at creation. Do not edit the existing PR #48 worktree or Concertable Party Foundation worktree. The previous Party Foundation continuation was launched separately.

## Evidence and scope
- PR #48 declares/generates the core harness, but its plan `plans/repo-declared-config/REPO_DECLARED_CONFIG_PLAN.md` leaves consumer adoption and live session refresh for later phases. Current Codex route failure still tells the agent to read the whole skill and retry. Determine whether host hooks can inject refreshed content mid-session; otherwise implement a supported SessionStart repair path and describe the real host limit.
- Claude has a marketplace-refresh SessionStart path. Establish the exact Codex/Claude consistency gap from source and a reproducible probe before editing. A failed hook must have a useful repair path; do not silently bypass the gate.
- `base:stack-tiers` is currently listed as a skill, but its folder also contains `tier_gate.py` and `tier.schema.json`. The gate runs in Claude and Codex hooks. Tommy wants the **skill** removed. Relocate the runtime/schema and any necessary authoritative tier contract so tier enforcement remains intact; remove its skill exposure/catalog/selection entries and update references and generated outputs. The reason for its existence was to document the tier gate and house its script, not a stacked-PR procedure.
- `engineering:stack` should name the stacked PR workflow. Inspect existing `engineering:git-branching`, `open-worktree`, PR and merge guidance, then add a discoverable `stack` entry/route without conflating it with tier gating. Keep the useful existing guidance and avoid duplicate authored bodies.
- Open PR #58 is about verified delivery of messages to existing Codex sessions, not hook refresh. PR #55 adds command routes and identifies a possible conflict with PR #48's early exit; do not accidentally absorb those unrelated branches. Recheck their state if relevant.

## Completion
Use meaningful tests for recovery and tier gating, run `pwsh .agents/sync-generated.ps1` and its `-Check` gate, refresh/check catalog digests as required, and follow core's review and PR workflow. Commit in logical units, push and open a plain GitHub stacked PR targeting `Refactor/RepoDeclaredConfigHarnessMove`. Report exact behavior, limits, and PR link. Do not merge either PR merely because this worktree exists. If the skill naming and runtime fix need separate PRs, preserve the parent stack and use separate focused layers.

## Next Steps
1. Read `AGENTS.md`, `README.md`, this goal, PR #48's plan, and relevant hook/skill generation sources. Verify parent PR state and current branch status.
2. Remove the exposed `stack-tiers` skill while preserving the tier gate; add the stacked-PR `engineering:stack` skill; diagnose and implement the Codex refresh repair.
3. Validate, review, commit, push and open the correctly based stacked PR; update this goal with evidence and outcome.

Handoff lane: L3, because host recovery behavior requires open-ended investigation and a verified implementation.

## Current checkpoint (2026-09-28)

- PR #48 is open against `main`; this branch starts at its recorded head `279790686f21ddc062230798fd462fe2b978354d` and was current with `origin/Refactor/RepoDeclaredConfigHarnessMove` when checked.
- Delivery slice: one focused child PR for tier runtime relocation, the `engineering:stack` discovery entry, and Codex hook recovery. Base: `Refactor/RepoDeclaredConfigHarnessMove`; head: `Fix/CodexHookRefresh`. The three changes share the generated package and hook manifests. Reassess the size before review.
- The exposed `stack-tiers` directory contains the tier gate's script and schema. Move those to shared runtime/resources; keep tier hook wiring and test behavior.
- The router currently blocks missing skills with a restart instruction and asks Codex to read a skill file before retry. Codex's documented `PreToolUse` hook output supports model-visible `additionalContext`, but a blocked write must be retried after receiving it. Verify actual host output behavior before claiming live recovery.
- Remaining: implement, run focused tests and generated/catalog gates, review, commit, push, and open the child PR. Do not merge either PR.

## Implementation checkpoint (2026-09-28)

- Removed the `base:stack-tiers` skill and its Codex/Claude discovery entries. The tier gate remains in `.agents/hooks/tier_gate.py`; its schema and contract moved to `.agents/schemas/` and `.agents/tiers/`. Both host manifests still invoke the gate from the generated base package.
- Added `engineering:stack` as a thin discoverable entry that routes stacked PR work to the existing branching, worktree, PR, and merge procedures.
- Refreshed harness manifests, catalog digests, and generated packages. `test_stack_tiers`, `test_hook_contract`, `test_harness_manifests`, `test_engineering_hooks`, `test_source_layout`, `test_catalog_digests`, `test_codex_windows_hook_commands`, `test_base_router`, `test_plan_artifacts`, and `skill-packaging.tests.ps1` passed. Harness, catalog, and generated package checks passed.
- Codex's documented `PreToolUse` hook can emit `additionalContext`, but a denied write still needs a retry. Automatic approval review rejected both a newest-cache-version dispatcher and an unverified executable snapshot in `PLUGIN_DATA`, citing arbitrary code selection and integrity risk. Tommy approved an integrity-checked snapshot. The generated Codex hook command now binds to the exact package tree hash, saves that package in `PLUGIN_DATA`, and checks the hash on every invocation. It runs the saved copy after its initial verification, so cache deletion cannot race a hook invocation; it fails closed on a modified copy.
- The removed-cache-path probe passed for a base SessionStart and PreToolUse hook. The probe also changed a saved dependency and observed exit code 2 with an integrity failure. All three package commands bind to their normalized package trees; the Windows hook test passed through PowerShell, pwsh, and cmd. Focused 37-test hook, harness, and tier suite plus the four snapshot/Windows tests passed. Harness, catalog, and generated package checks passed. A live Codex marketplace update and host trust review have not been observed in this worktree; the remaining gate is a real installed-host acceptance run after this package is released and trusted.
- Mid-session routed skill injection remains unresolved. An isolated Codex CLI probe of combined `deny` and `additionalContext` never reached its hook because the local process policy blocked the tool call. The router still blocks until a successful skill load is proven; `.agents/plugins/TECH_DEBT.md` records the host-level proof and pinned-install repair needed before this can safely change.
- The final focused suites and generation checks passed. Commits `ba5742e`, `edac04b`, and `f16d796` were pushed on `Fix/CodexHookRefresh`. Draft PR [#59](https://github.com/tj-agents/core/pull/59) is open with base `Refactor/RepoDeclaredConfigHarnessMove` and head `f16d7961b7f8980fafd0cf34b9a996991d7e3449`. Its `verify` check was in progress when observed.
- The first PR CI run failed two `test_plan_artifacts` assertions: the test still expected a direct Codex script command and invoked the new verified loader from a package path outside its cache layout without `PLUGIN_DATA`. Updated the fixture to exercise the generated command in a valid cache layout; the eight focused plan-artifact, snapshot, and Windows-command tests pass locally.
- Next: push the test correction and monitor the new exact-head PR check to completion, then run installed-host acceptance after the package is released and trusted. The routed-skill injection proof remains tracked in `.agents/plugins/TECH_DEBT.md`. Do not merge either PR.
