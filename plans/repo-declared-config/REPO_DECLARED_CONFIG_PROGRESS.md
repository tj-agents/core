# Repo-declared agent configuration — progress

- Plan: `plans/repo-declared-config/REPO_DECLARED_CONFIG_PLAN.md`
- Roadmap: `plans/repo-declared-config/REPO_DECLARED_CONFIG_ROADMAP.md`
- Roadmap item: `repo-declared-config/migrate-agent-state`
Status: phase 1 in progress; full repo-declared migration remains open (2026-09-26).

Branch: `Refactor/repo-declared-config_harness-move`
Worktree: `C:\Users\tommy\source\repos\tj-agents\core\.worktrees\Refactor-repo-declared-config_harness-move`
PR: none yet.

## Current state (2026-09-26)

- The plan is on `main`, amended with the tj-agents-only source rule, the per-machine migration
  procedure and (PR #30) the retire-duplicates framing of phase 1.
- This PC (first machine):
  - All four canonical repositories are cloned under
    `C:\Users\tommy\source\repos\tj-agents\{core,cpp,react,dotnet}`.
  - The older `C:\Users\tommy\source\repos\base-agents` checkout is 87 commits behind with
    uncommitted `plan-artifacts` edits and live worktrees; it is not retired.
  - Claude now has `base`, `engineering` and `machine@base-agents` (source `tj-agents/core`)
    at user scope, and `concertable@agent-standards` is disabled at user scope, so Claude's
    lanes and gates come from core. This is an interim user-scope state until phase 4.
  - `~/.claude/settings.json` still has other user-scope plugins, `tomjseery/*` sources for
    `dotagents` and `react-agents`, and `cpp-agents` without `autoUpdate`. Its auto-mode
    environment text names `Concertable/concertable` as the trusted repo for every session;
    that belongs in the Concertable repository's project settings (user decision).
  - `~/.codex/agents` holds the ten shared Codex agents installed by core's engineering
    package (owned via `.base-agents-delivery.json`); Codex cannot load agents from plugins, so
    the plan must decide how this stays repository-declared.
- `sandbox-hwid` (first consumer): routes resolve for Claude and Codex after cpp-agents v0.3.0
  adoption, but through user-scope installs.
- User clarified that the goal is to remove machine-local hook, harness, plugin and agent
  configuration across all known consumers and machines, with core as the generic source owner.
  The plan now covers that full migration; `sandbox-hwid` is only the first adoption checkpoint.
- On this PC, Codex's failing user-scope `notify` entry was removed from `~/.codex/config.toml`.
  Temporary 2.1.8 plugin-cache junctions created during diagnosis were removed after the
  updater deleted their 2.1.11 targets. No local cache alias is a supported fix. The currently
  installed core plugin release is 2.1.12; a live-session update regression still needs a
  repository-owned repair and acceptance test.
- Core branch now includes a first phase-2 generator beside `bootstrap-capabilities`: it derives
  `.claude/settings.json` and `.codex/config.toml` from a committed capability lock, requires
  core's three plugins, rejects sources outside the four `tj-agents` repositories, preserves
  unrelated project settings, and has `write`/`check` modes. Its focused tests and package
  sync check pass. No consumer has adopted it yet; core's release catalog still pins 2.1.4.

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

Scope: whole plan: core-owned generic harness and repo-declared configuration for every known
consumer and machine in the plan.
Current slice: finish phase 1's duplicate audit and generic ports on this branch; include the
live-session cache-path failure in the subsequent host-adapter work.
Remaining scope: release core; retire Concertable duplicates; generate consumer config; add
self-heal and live-update safety; migrate each consumer and machine; remove local behavioural state.
Done when: every migrated host and consumer passes the plan's acceptance checks and the machine
verifier reports no local behavioural configuration.

Done already on this branch: inventory above; `hook_runtime.run_command` with timeout-bearing
`gh`/`git` calls in `merge_review_gate`, `persistent_workflow_merge_gate` and
`delivery_binding_gate`, plus `test_hook_runtime`. The hook suite's only failures are the two
pre-existing `CanonicalEnvelopeShellTests`, which cannot find Git Bash on this machine.

1. **Finish the audit.** The inventory above covers hooks, agents and two skills only. Compare
   everything else in Concertable's authored sources (`.agents/lanes` lane tables, `.agents/workflows`,
   `.agents/plugins` install roster/payloads, `scripts/`, `standards/`, `codex-skills`,
   `enforcement-rules.json`, `.claude/` and `.codex/` adapters) against core's `base`, `engineering` and
   `machine` sources and against `tj-agents/dotnet` and `tj-agents/react` (Concertable's .NET/React
   stack skills may duplicate those). Compare content, not names. Record each item as duplicate
   (which side is ahead), product-only, or generic-missing-from-core in the inventory above.
2. **Port Concertable-ahead generic fixes into core, rewritten in core's terms**, each commit with its
   tests: router commits `ff903b3` (quoted `>` is not a redirect; foreign paths; first writes),
   `26941b7` (settle foreign paths before any gate) and `f5d2b7e` (qualifier fallback; reconcile with
   core's `skill_aliases` from `45506cb`); `red_run_gate`'s `invocable_name`; the rung-specific lane agent
   `description`s and `kind` into core's authored agent sources for both hosts. Replay commit by commit
   (Concertable history since `7ab1028`); a three-way reconciliation against `c68ff55` gives 29 conflicts. Skip the
   currency-coupled commits (`62c3887`, `de88e59`, `ee7f228`). After source changes run
   `python -B scripts/update_catalog_digests.py`, `pwsh .agents/sync-generated.ps1` and
   `pwsh .agents/sync-generated.ps1 -Check`, and the hook suite
   (`python -B -m unittest discover -s .agents/hooks/tests -p 'test_*.py'`).
3. `/review` this branch, open the PR, merge and release core.
4. **In `Concertable/agents`** (its own worktree from `origin/main`; the local checkout
   `C:\Users\tommy\source\repos\agent-standards-fresh` is on another branch): first enable `base`,
   `engineering`, `machine@base-agents` plus `concertable` in the Concertable product repository's
   project settings, then delete every duplicate recorded above (hooks and their wiring, the ten agents
   in both forms, `persistent-workflow`, and whatever step 1 adds), keeping the "Not moved" product
   pieces. Verify a Concertable session in both hosts loads one copy of each lane, gate and skill.
5. Record the result here, then continue with phase 2 (repo-config generator).
