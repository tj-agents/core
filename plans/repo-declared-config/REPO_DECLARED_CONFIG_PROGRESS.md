# Repo-declared agent configuration progress

- Plan: `plans/repo-declared-config/REPO_DECLARED_CONFIG_PLAN.md`
- Roadmap: `plans/repo-declared-config/REPO_DECLARED_CONFIG_ROADMAP.md`
- Roadmap item: `repo-declared-config/migrate-agent-state`
- Worktree: `C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Feature-RepositoryOwnedLayout`
- Branch: `Feature/RepositoryOwnedLayout`
- PR: not opened for adoption
- Dependency/package gates: reconcile producer releases/catalogs and consumer state for the first adoption batch; native producer/host acceptance remains required
- Last reconciled: 2026-10-07; goal/session and worktree state supplied by current owner

## Current state

The original Repo-declared config owner, session `01a0dedd-012f-7b10-8d89-dde5869ded40` (PID 17300), is dead. Its attempted transfer was never acknowledged. Codex full-goal session `01a11794-26f3-7fb2-accb-0df87faa5180` now coordinates this existing adoption owner under the user's repository-layout authorization. No adoption PR exists; fleet completion has not been verified.

The repository-layout proposal is a dependency: [REPOSITORY_LAYOUT_PROPOSAL.md](../repository-layout/REPOSITORY_LAYOUT_PROPOSAL.md). Core's owner catalog contains only core releases; each producer owns its catalog and harness manifest. Consumer declarations and generated Claude/Codex settings must be committed and drift-checked. Do not tag a core-only catalog release for consumer adoption until the first `winwrap` and `sandbox-hwid` consumers have committed their composed catalogs.

Current first-consumer source inventory (2026-10-07; read-only, no adoption changes):

| Consumer | Observed checkout and declarations | Remaining gate |
|---|---|---|
| `cpp/windows/winwrap` | Primary `main` at `1355897c910b800ca516d315ffa68ccce26140c8`; code clean, existing root plan has historical delivery edits. Project host settings select `cpp`, `msvc`, `win32` from `cpp-agents`; no core selection, capability lock, composed catalog or drift check. | Reconcile exact core and C++ producer records, then create a bounded consumer adoption checkout. Preserve root plans and PLANNING.md. |
| `cpp/windows/sandbox-hwid` | Primary `main` at `f7f42813b446bba772ddc5de1b9e5ec8809c139e`; code clean; same stack-only settings and missing declaration artifacts. Legacy `sandbox-hwid.worktrees/Docs-TraceGuideCodePath` at `d58d763721ee07e18b6a43dd3144ff063052a2d4` remains registered. | Reconcile native owner and references before moving that checkout. Preserve root plans, technical routes and docs/next-session.md teaching contract. |

Both projects already keep plans in their repositories; the inspected files do not identify an active external goal to move. Neither tracked ignore file declares `.worktrees/`; the shipped allocator must establish its common-Git exclusion. Current project settings still rely on profile/global core roles and do not establish installed closure or host acceptance. Native session liveness was outside this inventory.

The inspected canonical `tj-agents/cpp` checkout lacks an owner catalog and harness-manifest directory. Its producer must supply and validate exact release/harness records before composing the first consumer catalogs; core must not invent those records. Allocator/guidance delivery, aggregate identity reconciliation, both-host acceptance and the existing credential-copy gate remain open.

Previously recorded machine inventory (2026-09-27; recheck before cleanup): canonical `core`, `cpp`, `react`, and `dotnet` checkouts exist. The old `base-agents` checkout has uncommitted work and live worktrees and is not retired. User-scope Claude state included Concertable and other marketplace/plugin/trust declarations; Codex had ten shared agents in `~/.codex/agents`. `sandbox-hwid` routes worked through user-scope installs. These are evidence to reconcile, not verified current state; do not remove machine state before consumer host acceptance.

Native role acceptance is still held on approval to copy credentials. Do not copy credentials before that gate clears. Concertable scope-isolation commit `3bcb527` remains unpushed on `Concertable/agents` branch `Fix/PluginScopeIsolation`; keep it separate from this core work. Core's machine-verifier continuation is implemented, but it does not establish native or consumer acceptance. The stale-snapshot diagnosis was fixed independently in PR #73; do not report old PR #60 as still open without checking.

The update-channel decision remains unresolved: immutable release pins do not advance on pushes; automatic review rejected changing generated refs to moving `main` because that would run unreviewed executable code. Keep the approved release-pinned behavior until an update channel is accepted. Native Claude/Codex acceptance, including live-session refresh safety, remains pending.

## Next Steps

Reconcile exact producer releases/catalogs and existing consumer state before the first `winwrap`/`sandbox-hwid` adoption batch. Confirm each producer's release identity, harness record and host requirements, then compare those with both consumers' current declarations and generated settings. Resolve producer/native acceptance gates before implementation. Do not claim consumer migration complete from core-side generation or verifier results.

Scope: whole plan: core-owned generic harness and repo-declared configuration for every consumer and machine.
Current slice: reconcile producer releases/catalogs and existing `winwrap`/`sandbox-hwid` consumer state before the first adoption batch.
Remaining scope: producer records, consumer config, self-heal, live-update safety, machine verifier acceptance, and adoption in every consumer and machine.
Done when: both hosts pass the plan's acceptance checks in every consumer and the verifier reports no machine-local behavioural state on each machine.

1. Verify the selected producers' exact releases, owner catalogs, harness manifests and native acceptance; preserve the credential-copy hold.
2. Reconcile `winwrap` and `sandbox-hwid` state; adopt owner catalogs, generated settings and drift checks only after producer/native gates clear. Prove the Claude launcher allow rule in a trusted auto-mode session and record any host limitation.
3. In a fresh `Concertable/agents` worktree from `origin/main`, select released `base`, `engineering`, and `machine@base-agents` beside `concertable`; then retire only verified shared duplicates while preserving product rules, hooks and stack contracts. Compare shared-name .NET/React skills behaviorally before deletion.
4. Add repository-owned repair and live-session cache safety; adopt every remaining consumer and machine, remove obsolete user-scope behavioral state only after host acceptance, and rerun the verifier until all plan acceptance criteria pass.

## Completed work

- Phase 1/core harness: PR #48 merged core-only catalog and generic harness; Codex hook snapshots #59; Claude pre-load refresh and plugin-owned typed launcher merged in #61/#63 with live PowerShell acceptance. These releases do not complete consumer adoption.
- Phase 2/core generator: lock-to-host-config generator, three authored harness manifests, owner-catalog validation, source/wiring checks, composed host permissions, and consumer drift support are present on the current branch. Source-owned manifests and policy scope remain authoritative; core must not own other standards repositories' release rosters.
- Machine verifier: parsed TOML, named profiles, hidden loose files, repository-local sources, redacted findings and read-only CLI were added in the 2026-09-29 continuation. This verifies inventory only; machine cleanup and native acceptance remain open.
- Dated source inventory (2026-09-23 to 2026-09-26; source was `Concertable/agent-standards` at `eae6cc6`, now `Concertable/agents`):

| Inventory | Recorded evidence and disposition |
|---|---|
| Shared hooks already in core | Identical: `compact_output_gate`, `forge_poll_gate`, `git_auth_scope_gate`, `plan_handoff_stop`, `plan_handoff_stop_launcher`, `worktree_cleanup_gate`; retain core copies. Port Concertable advances in `hook_runtime` (`run_command`, timeout), `merge_review_gate`, `red_run_gate` (`invocable_name`), `delivery_binding_gate`, `persistent_workflow_merge_gate`; three-way merge `skill_router` (Concertable: `invocable_name`, `_mask_quoted`, `_readable_skill`, `announce_drift`, `currency_failure`; core: `skill_aliases`, `deleted_targets`, `unresolved_existing_deny_hits`). Keep core `plan_graph` and `docs_reachability`.
| Associated tests | Generic missing tests: `test_hook_runtime`, `test_delivery_bind_paths`, `test_standing_authorization`. Merge diverged `test_skill_router`, `test_red_run_gate`, `test_merge_review_gate`, `test_delivery_binding_gate`, `test_lane_tables`, `test_workflow_*`, `test_goal_preflight`, `test_plan_graph`, `test_docs_reachability`, and `lane_expectations` fixture with their hooks.
| Generic, deferred to phase 3 | `standards_currency` (+ test; URL is Concertable-specific and must key off owning marketplace); `standards_enforcement_gate` (+ test; mechanism generic, rules remain consumer-owned); Claude `claude_marketplace_refresh` and settings tests (replace machine roster in phase 2, extend to self-heal in phase 3).
| Not moved / retire | Concertable-specific `always_on_instructions`, `dev_rules`, `prelaunch_conventions`, `ci_change_classifier` and their product tests stay. Retire `claude_marketplace_autoupdate` (writes forbidden user-scope marketplace state). Compare `codex_delivery` (+ test) with core agent delivery; compare `test_plugin_pruning` with core cache-pruning coverage. `test_hook_manifests`, `test_gen_skill_routes`, `test_capability_selection` remain Concertable-specific.
| Plugin agents and skills | Ten `agents/*.md` and ten `codex-agents/*.toml` duplicate core lanes; port rung descriptions and `kind` while retaining core `tools`/`sandbox_mode`, then retire. Retire duplicate `persistent-workflow`; keep product and .NET/React skills.
| Additional authored sources | Keep Concertable marketplace payload; retire local roster/install behavior after adoption. Replace product provisioning/launch scripts with declarations and core bootstrap, not copies in core. Keep Docker test infrastructure. Compare generic worktree/delivery scripts before retirement. Retire only shared generated hook/agent entries after core is enabled; keep product hooks/rules, stack contracts and repository policy in Concertable. Shared-name .NET/React skills are not byte-identical and require behavioral comparison.

## Verification

No current adoption verification. Historical core-candidate checks only: shared runtime suite 632 tests had one fixture-order failure; the workflow-generation test passed after catalog digest refresh, with 631 others passing and 8 skipped. Focused bootstrap/config/harness/source-layout and Windows shell checks were recorded passing. Exact-head CI found LF/CRLF source-digest variation and a Windows 8.3 temp-path alias; both received regression fixes. PR #73 independently fixed stale-snapshot diagnosis. These results do not prove current consumer or installed-host acceptance.

## Reviews

Current review state unknown; no reviewed-up-to watermark recorded for this adoption.

## Decisions, discoveries, blockers, and deviations

- Whole-plan implementation and normal per-repository merge delivery were authorized 2026-09-27. Repository-layout work has its separate current user authorization; see the linked proposal dependency.
- Each standards owner publishes its own release identity, source, digest and harness requirements. Consumers compose selected owner records; core must not synchronize a roster of other standards repositories.
- Phase 2 for `winwrap` and `sandbox-hwid` has priority. It does not waive producer release/catalog reconciliation or native acceptance.
- Native credential copying remains gated. The old `base-agents` checkout and unpushed Concertable scope-isolation work must be preserved until their owners resolve them.
- Keep immutable release pins pending an approved update channel. A marketplace cache refresh alone does not prove next-session cross-PC currency or live-session safety.
- Concertable removal requires project-scope enablement first; its product hooks import product policy and its generator emits shared agents. Preserve product-only rules/hooks and compare stack skills before removal.
