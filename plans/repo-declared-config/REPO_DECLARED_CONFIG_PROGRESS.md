# Repo-declared agent configuration — progress

- Plan: `plans/repo-declared-config/REPO_DECLARED_CONFIG_PLAN.md`
- Roadmap: `plans/repo-declared-config/REPO_DECLARED_CONFIG_ROADMAP.md`
- Roadmap item: `repo-declared-config/migrate-agent-state`
Status: phase 1 in progress; full repo-declared migration remains open (2026-09-27).

Branch: `Refactor/RepoDeclaredConfigHarnessMove`
Worktree: `C:\Users\tommy\source\repos\tj-agents\core\.worktrees\Refactor-repo-declared-config_harness-move`
PR: [tj-agents/core #48](https://github.com/tj-agents/core/pull/48), ready and mergeable.
CI `verify` passed at `284d014` (run `36318559193`); review watermark matches that head.
Tommy authorized end-to-end implementation, PR delivery and merging on 2026-09-27; the
authorization checkpoint below requires a fresh exact-head review and CI run. `v2.1.13`
remains unpublished.

## Current state (2026-09-26)

- The plan is on `main`, amended with the tj-agents-only source rule, the per-machine migration
  procedure and (PR #30) the retire-duplicates framing of phase 1.
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
- The phase-2 generator derives both host configs from a capability lock, requires core's
  plugins, rejects non-`tj-agents` sources, preserves unrelated settings, and supports
  `write`/`check`. Tests and package sync pass; adoption awaits the 2.1.13 release.
- Merged current `origin/main` (which released 2.1.12 and added native plugin activation checks).
  Reconciled the router: moved skills require explicit aliases, so disabled plugins stay
  unavailable. Core's Windows hook smoke test passes. The `codex.CMD` probe and shared hook
  runner use `CREATE_NO_WINDOW`; live-session popup acceptance remains pending.
- Concertable migration cannot delete duplicates wholesale: product hooks import its router,
  its generator emits shared agents, and the tj-agents-only source rule conflicts with enabling
  `concertable@agents`. Settle that boundary before cutover.
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
- Documentation review resolved the harness mechanism: per-plugin authored manifests feed the
  catalog and generated packages; `repo_config.py` composes selected requirements into Claude
  settings and Codex rules; digest, wiring, catalog and consumer-drift checks enforce the rule.
  This mechanism is designed but not yet implemented.

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

### Retirement order

### Additional authored-source audit (2026-09-26)

Compared `Concertable/agents` `origin/main` blobs with this core branch, then inspected every
divergent shared workflow file. All four `.agents/lanes` sources and the other shared workflow
contract, runtime, role, and fixture files have identical blobs. The divergent workflow files
are core-ahead except `workflow_ops.run_process`, where Concertable explicitly decodes UTF-8;
that fix is now in core with a non-ASCII output test. Concertable's `kind: lens` fixture/host
values differ from core's `kind: review`; the latter matches core's role taxonomy. Its Codex
project agent install and host probe differ from core's profile delivery; phase 2 must settle
repository-owned Codex agent delivery rather than copying either local installer.

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

1. Core releases with the ports above.
2. The Concertable repository enables core (`base`, `engineering`, `machine@base-agents`) plus
   `concertable` in its own project settings, so it is never without lanes or gates.
3. Only then delete the duplicates (both tables of hooks above, their wiring, the ten agents in
   both forms, and `persistent-workflow`) from `Concertable/agents`, keeping the "Not moved" product
   hooks and product skills.

## Next Steps

**Goal: every capability has exactly one copy.** Remove all duplication between `Concertable/agents`
and the tj-agents repositories (`core`, `dotnet`, `react`). Concertable keeps only
Concertable-product content; core contains no Concertable reference in code, names, URLs or wording
(user decision, 2026-09-23). The currency gate, enforcement gate and marketplace refresh are **not**
moved into core; phase 3 rebuilds currency as self-heal.

Scope: whole plan: core-owned generic harness and repo-declared configuration for every consumer and machine.
Current slice: implement the declared harness manifests, permission composition and enforcement
on the 2.1.13 core candidate; then re-review, publish it, and adopt winwrap and sandbox-hwid.
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

1. Implement `.agents/plugins/harness.schema.json`, the three core manifests, their validator and
   catalog/package sync, permission-aware `repo_config.py`, standing guidance, and focused tests on
   PR #48. Refresh exact-head review and CI, merge, publish 2.1.13, and verify the tag and digests.
2. Adopt the released generator and manifests in winwrap and sandbox-hwid first. Commit generated
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
5. Adopt the other consumers named in the plan. After each host passes,
   remove obsolete user-scope behavioral entries on this PC, run the machine verifier, and record
   acceptance. Repeat the same procedure on every other machine until the plan closes.
