# Repo-declared agent configuration — progress

- Plan: `plans/repo-declared-config/REPO_DECLARED_CONFIG_PLAN.md`
- Roadmap: `plans/repo-declared-config/REPO_DECLARED_CONFIG_ROADMAP.md`
- Roadmap item: `repo-declared-config/migrate-agent-state`
Status: phase 1 in progress; full repo-declared migration remains open (2026-09-28).

PR #48 merged at `1f7a928` and Codex hook snapshots (#59) at `531c0fd`; `v2.1.15` is the latest
release. Neither refreshes Claude before plugin load. Active slices: `Fix/ClaudeStandardsSync`
([`CLAUDE_STANDARDS_SYNC.md`](CLAUDE_STANDARDS_SYNC.md)) and `Fix/CodexStandardsSync`, each in its own
worktree under `core\.worktrees\Fix-CodexHookRefresh\`.
Tommy authorized end-to-end implementation, PR delivery and merging on 2026-09-27.

## Current state (2026-09-27)

- The plan covers per-machine migration and retirement of duplicated shared hooks and agents.
- This PC (first machine):
  - All four canonical repositories are cloned under
    `C:\Users\tommy\source\repos\tj-agents\{core,cpp,react,dotnet}`.
  - The old `base-agents` checkout has uncommitted work/live worktrees and is not retired.
  - Claude has core plus `concertable@agents` at user scope, so product hooks still load in
    unrelated repositories.
  - Claude user settings retain `tomjseery/*` sources, plugins and global Concertable trust text;
    migrate those declarations into their owning repositories.
  - `~/.codex/agents` holds the ten shared Codex agents installed by core's engineering
    package (owned via `.base-agents-delivery.json`); Codex cannot load agents from plugins, so
    the plan must decide how this stays repository-declared.
- `sandbox-hwid` (first consumer): routes resolve for Claude and Codex after cpp-agents v0.3.0
  adoption, but through user-scope installs.
- On this PC, Codex's failing user-scope `notify` entry and temporary plugin-cache junctions
  were removed. Core 2.1.12 is installed; a live-session update still needs a repository-owned
  repair and acceptance test. No local cache alias is supported.
- The phase-2 generator derives both host configs from a lock and owner-authored catalog,
  requires core's plugins, validates GitHub sources against release owners, and checks drift.
- Merged current `origin/main` (which released 2.1.12 and added native plugin activation checks).
  Reconciled the router: moved skills require explicit aliases, so disabled plugins stay
  unavailable. Core's Windows hook smoke test passes. The `codex.CMD` probe and shared hook
  runner use `CREATE_NO_WINDOW`; live-session popup acceptance remains pending.
- Concertable migration cannot delete duplicates wholesale: product hooks import its router
  and its generator emits shared agents. Settle those boundaries before cutover.
- Core now has a read-only machine verifier under `bootstrap-capabilities`. Focused tests pass;
  on this PC it finds 34 own-agent profile entries (2 settings groups, 5 marketplaces,
  15 plugins, 12 loose agents/skills). Host-bundled runtime marketplaces are excluded.
  No user-scope cleanup is safe until the corresponding consumers adopt project settings.
- Tommy authorized the whole repo-declared configuration plan through every repository's
  normal merge path. The plan now explicitly includes standards-owned harness manifests,
  generated project permission rules, CI enforcement of manifest/config drift, phase-2-first
  adoption in winwrap and sandbox-hwid, and a permanent always-on authoring rule. The separate
  `plans/conditional-skill-routes/` plan owns route conditionality and does not replace this
  plan's harness-installation contract.
- Tommy corrected the ownership boundary on 2026-09-27: core must not name or synchronize
  other standards repositories. Its catalog now holds only its own release; consumers commit
  the selected owners' records and the generator reads those without a source roster.

## Phase 1 inventory (2026-09-23)

Source: `Concertable/agent-standards` `origin/main` at `eae6cc6`. GitHub now redirects that
repository to `Concertable/agents`, which is the name its README and `standards_currency.py` use.
Its authored hooks live in `.agents/hooks/` (shared), `.claude/hooks/` and `.codex/hooks/`;
`plugins/concertable/hooks/` is its generated payload.

**Finding: the harness is already in core; phase 1 retires Concertable's duplicates.** Core's
`engineering` plugin ships and wires the skill router, every delivery gate and the ten lane/workflow
agents for both hosts. With `concertable` also enabled, each gate runs twice. **The copies have
diverged in both directions since 2026-09-20**, so a duplicate is deleted from concertable only
after its Concertable-ahead changes are ported into core; otherwise those fixes are lost. Beyond
that, only generic pieces core lacks move.

### Already in core — converge, core becomes the only copy

| Hook | State vs core | Action |
|---|---|---|
| `compact_output_gate`, `forge_poll_gate`, `git_auth_scope_gate`, `plan_handoff_stop`, `plan_handoff_stop_launcher`, `worktree_cleanup_gate` | identical | none in core; concertable drops its copy |
| `hook_runtime` | concertable ahead: `run_command`, `NETWORK_COMMAND_TIMEOUT_SECONDS` | port into core |
| `merge_review_gate`, `red_run_gate`, `delivery_binding_gate`, `persistent_workflow_merge_gate` | concertable ahead: `gh`/`git` calls through `run_command` with timeouts; `red_run_gate` lists `invocable_name` | port into core |
| `skill_router` | both ahead. Concertable: `invocable_name`, `_mask_quoted`, `_readable_skill`, `announce_drift`, `currency_failure`. Core: `skill_aliases`, `deleted_targets`, `unresolved_existing_deny_hits` | three-way merge in core |
| `plan_graph` | concertable's copy imports `prelaunch_conventions` (product policy); core's is generic | keep core |
| `docs_reachability` | core newer | keep core |

Tests follow their hook: identical tests need nothing; `test_hook_runtime`,
`test_delivery_bind_paths` and `test_standing_authorization` are generic and missing from core;
diverged tests (`test_skill_router`, `test_red_run_gate`, `test_merge_review_gate`,
`test_delivery_binding_gate`, `test_lane_tables`, `test_workflow_*`, `test_goal_preflight`,
`test_plan_graph`, `test_docs_reachability`, `lane_expectations` fixture) merge with their hook.

### Generic, not in core — deferred to phase 3, stays in Concertable until then

| Hook | Role | Note |
|---|---|---|
| `standards_currency` (+ test) | SessionStart currency check; also used by the router's `currency_failure` | hard-codes `Concertable/agents` manifest URL; key it to the owning marketplace's repository |
| `standards_enforcement_gate` (+ test) | commit/push/PR boundary gate driven by route `enforcement` rules | mechanism is generic; rules stay in each repository's routes |
| `.claude/hooks/claude_marketplace_refresh` (+ `test_claude_marketplace_refresh`, `test_claude_settings_path`) | Claude SessionStart `plugin marketplace update` for managed plugins | reads the machine install roster; phase 2 replaces that input with the repository's declared plugins, phase 3 extends it into self-heal |

### Not moved

| Hook | Classification | Reason |
|---|---|---|
| `always_on_instructions`, `dev_rules` (+ tests) | Concertable-specific content | injects `standards/process/ALWAYS_ON_INSTRUCTIONS.md` and the product rule catalogue; core's `session-guidance` SessionStart already covers the generic injection mechanism |
| `prelaunch_conventions` | Concertable-specific | product pre-launch policy used by concertable's `plan_graph` and route generator |
| `ci_change_classifier` (+ test) | Concertable-specific | concertable's own CI helper; not wired as a hook |
| `.claude/hooks/claude_marketplace_autoupdate` | retire | writes user-scope `extraKnownMarketplaces` in `~/.claude/settings.json`, which the plan's rule forbids; generated repository settings (phase 2) replace it |
| `.codex/hooks/codex_delivery` (+ test) | generic, deferred | installs Codex agents into `~/.codex/agents`; core already has `install-workflow-agents.ps1`. Decide in phase 2 with the open Codex-agents question |
| `test_hook_manifests`, `test_gen_skill_routes`, `test_capability_selection` | Concertable-specific | test concertable's own manifests, route generator and capability selection |
| `test_plugin_pruning` | generic, check | compare with core's `prune_plugin_cache` coverage before moving |

### Agents and skills in `plugins/concertable`

| Item | State vs core `engineering` | Action |
|---|---|---|
| `agents/*.md` (10) | duplicates. Concertable ahead: rung-specific `description`s (L1 "Irreversible work…", L5 "Clerical work…") and `kind`. Core ahead: `tools` | port descriptions and `kind` into core's authored agent source, then retire |
| `codex-agents/*.toml` (10) | duplicates. Same descriptions; core ahead with `sandbox_mode` | port descriptions, then retire |
| `skills/persistent-workflow` (+ `codex-skills`) | duplicate of `engineering:persistent-workflow`; core is the newer canonical form | retire |
| `skills/always-on-instructions`, `skills/reset-test-explorer`, and every other skill | Concertable-product or .NET/React stack contracts | stay |

### Additional authored-source audit (2026-09-26)

The shared lanes and workflow contract/runtime/role/fixture blobs match this core branch.
Core is ahead on other workflow files; Concertable's explicit UTF-8 decoding was ported with
a non-ASCII test. Its `kind: lens` differs from core's `kind: review`. Its Codex project-agent
installer differs from core's profile delivery; phase 2 must settle repository-owned delivery.

| Source | Classification | Action |
|---|---|---|
| `.agents/plugins/marketplace.json`, `payloads.json`, `install-roster.json`, `install-helpers.ps1` | Concertable product marketplace and its local installer | keep marketplace payload; retire local roster/install behavior after repo config adoption |
| `scripts/provision-agents.ps1`, `provision-project-capabilities.ps1`, `start-concertable-agent.ps1` | product provisioning and host launch built around local capability state | replace with core generator/bootstrap and repository declarations in phase 2; do not copy to core |
| `scripts/docker-health.ps1` | Concertable product test infrastructure | keep with Concertable |
| `scripts/worktrees.ps1`, `delivery-continuation.ps1` | generic mechanisms coupled to Concertable delivery policy | compare against core's worktree and workflow delivery utilities before retirement; not a hook duplicate |
| `.claude/.codex` hook wiring and agents | generated/product adapters containing the duplicate shared hooks and ten agents already inventoried | retire shared entries only after core is enabled in the project; keep product hooks |
| `standards/process`, `standards/rules`, `standards/dotnet`, `standards/react`, `.agents/skills` | Concertable product and stack contracts | keep product rules; compare named .NET/React skills against scope repos during consumer adoption |
| `.agents/routes`, profile, enforcement and standards manifest | Concertable repository policy | migrate its capability selection to repo-declared config; never move its rules into core |

The shared-name `.agents/skills` in Concertable and `tj-agents/dotnet`/`react` have no
byte-identical source files; names alone are insufficient evidence for deletion. They require
behavioral comparison when the Concertable consumer is migrated.

## Next Steps

**Goal: every capability has exactly one copy.** Remove all duplication between `Concertable/agents`
and the tj-agents repositories (`core`, `dotnet`, `react`). Concertable keeps only
Concertable-product content; core contains no Concertable reference in code, names, URLs or wording
(user decision, 2026-09-23). The currency gate, enforcement gate and marketplace refresh are **not**
moved into core; phase 3 rebuilds currency as self-heal.

Scope: whole plan: core-owned generic harness and repo-declared configuration for every consumer and machine.
Current slice: Claude pre-load standards refresh (`Fix/ClaudeStandardsSync`).
Adopt owner catalogs and generated settings in winwrap and sandbox-hwid before tagging a release with
the core-only bundled catalog; main-tracking installs already carry it since PR #48.
Remaining scope: consumer config, self-heal, live-update safety, machine verifier, and adoption everywhere.
Done when: both hosts pass the plan's acceptance checks in every consumer and the verifier reports no
machine-local behavioural state on each machine.

Completed on this branch: shared hook timeouts and Windows no-console launches; quote-aware and
foreign-path-safe router writes; explicit moved-skill aliases; red-run invocation names; lane metadata;
UTF-8 workflow output; and the first lock-to-host-config generator. The Concertable authored-source
inventory above distinguishes generic duplicates from product content. The merged hook suite passed
625 tests with 8 skips; package sync, plan graph, and committed-head catalog checks passed. The
repository suite's Windows shell test passed on focused rerun after sandbox denial and one transient
PowerShell startup timeout.

The core branch now has three authored harness manifests, a source-digest and hook-wiring
validator, catalog/package harness copies, composed Claude permissions and Codex rules, a consumer
catalog lookup beside the lock, and no hard-coded non-core marketplace roster in runtime source.
The core catalog contains only `base-agents`; each other standards owner must publish and check its
own release records. Focused validation: 31 bootstrap integration tests, 6 config tests, 4 harness
tests, 16 source-layout tests and the Windows shell hook regression passed. The 632-test shared
runtime suite had one failure because its fixture copied the catalog before the final digest refresh;
that exact workflow-generation test passed when rerun against the refreshed catalog. The other
631 completed without failure (8 skipped). PR #48's first exact-head CI found that the new source
digest varied between LF and CRLF checkouts; it now normalizes text line endings. Its next CI
found a Windows 8.3 temp-path alias in the new digest tests; the walker now resolves its root.
Both have regression tests; local drift checks pass. Review, push, and CI remain.

1. Done: PR #48 merged the core-only catalog and harness slice. Do not tag a release with it until the
   first consumers have committed their own composed catalogs.
2. Add owner-authored release and harness records in each selected standards repository, then adopt
   the generator and manifests in winwrap and sandbox-hwid first. Commit generated
   Claude/Codex config plus consumer drift checks, and prove the Claude launcher allow rule in a
   real trusted auto-mode session; record any host limitation honestly.
3. In a fresh `Concertable/agents` worktree from `origin/main`, select the released `base`,
   `engineering`, and `machine@base-agents` alongside `concertable` in project settings. Then remove
   its duplicated hooks, ten agents in both host forms, and `persistent-workflow` skill. Preserve
   product-only rules, hooks, and stack contracts. Compare its generic worktree and delivery scripts
   with core utilities before retiring them. Verify each host loads one copy of every shared gate,
   lane, and skill.
4. Add the repository-owned repair path for missing or stale skills. Keep plugin refresh
   safe for a live session, including stale hook paths and invisible Windows child processes.
   Claude's pre-load refresh and 14-day orphan window are delivered by `Fix/ClaudeStandardsSync`;
   Codex's equivalent is owned by `Fix/CodexStandardsSync`.
5. Adopt the other consumers named in the plan. After each host passes,
   remove obsolete user-scope behavioral entries on this PC, run the machine verifier, and record
   acceptance. Repeat the same procedure on every other machine until the plan closes.
