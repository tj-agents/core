# Repo-declared agent configuration — progress

Plan: `REPO_DECLARED_CONFIG_PLAN.md`
Status: phase 1 in progress — inventory recorded; step 1 done.

Branch: `Refactor/repo-declared-config_harness-move`
Worktree: `C:\Users\tommy\source\repos\tj-agents\core\.worktrees\Refactor-repo-declared-config_harness-move`
PR: none yet.

## Current state (2026-09-23)

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

### Generic, not in core — move

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

1. Core releases with the ports above.
2. The Concertable repository enables core (`base`, `engineering`, `machine@base-agents`) plus
   `concertable` in its own project settings, so it is never without lanes or gates.
3. Only then delete the duplicates (both tables of hooks above, their wiring, the ten agents in
   both forms, and `persistent-workflow`) from `Concertable/agents`, keeping the "Not moved" product
   hooks and product skills.

## Next Steps

Continue phase 1 in this worktree, in this order, committing each coherent step with its tests:

1. Done: `hook_runtime.run_command` and the timeout-bearing `gh`/`git` calls in `merge_review_gate`,
   `persistent_workflow_merge_gate` and `delivery_binding_gate`, with `test_hook_runtime`. The hook
   suite's only failures are the two pre-existing `CanonicalEnvelopeShellTests`, which need a Git Bash
   this machine's test lookup does not find.
2. Three-way merge `skill_router`, `red_run_gate` and their tests (keep both sides' additions).
   Core first added the router on 2026-09-02 (`058e6e6`, extracted from Concertable); find that
   concertable revision as the merge base.
3. Move `standards_currency` and `standards_enforcement_gate` with tests; wire the enforcement gate
   in both hosts' `engineering-hooks.json`.
4. Move `claude_marketplace_refresh` (Claude-only, under `.claude/`) with tests; wire SessionStart.
5. Port the agent descriptions and `kind` into core's authored agent sources.
6. Add the missing generic tests; run the full hook suite and `pwsh .agents/sync-generated.ps1 -Check`.
7. Release core, then follow the retirement order above.

Phase 3 (self-heal: automatic marketplace refresh and in-session skill injection for Claude and
Codex) follows the generator in phase 2.
