# Repo-declared agent configuration — progress

- Plan: `plans/repo-declared-config/REPO_DECLARED_CONFIG_PLAN.md`
- Roadmap: `plans/repo-declared-config/REPO_DECLARED_CONFIG_ROADMAP.md`
- Roadmap item: `repo-declared-config/transitive-core`
- Worktree: `C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Feature-Repo-Declared-Config`
- Branch: `Feature/Repo-Declared-Config`
- Base: `origin/main` at `a7925eadfd7007e6923d1dbf4e13414ebfb9d648`
- PR: not opened
- Dependency/package gates: plugin-contained Codex dispatch needs native proof before migration.
- Last reconciled: 2026-09-27; audit review complete, cold-start evidence and overlapping PR discovered.

## Authorization

Tommy authorized the whole plan on September 26: domain marketplaces supply core transitively;
consumers never name core, lanes or its agents directly; remove machine-local agent settings
after replacement delivery works; Concertable loads only in Concertable repositories; retire its
duplicate delivery and add a guard. Commit, push and open PRs; merges follow each repository's
review gate. The current request explicitly resumed this plan through its Next Steps.

## Current state

The September 26 plan, ledger and roadmap were carried from the main checkout into this fresh
delivery worktree. It owns this audit and host investigation. Another migration owner was discovered
in PR #48; ownership of the shared plan and bootstrap generator needs reconciliation before
publishing further migration changes. The original sandbox-only scope was reconciled
with the newer winwrap and Concertable authorization.

`bootstrap_capabilities.py --mode audit` is implemented with focused tests and skill documentation.
It reads user plugin/marketplace declarations, user skills/agents, repository Codex agents and local
marketplace overrides, including Claude local settings. It performs no installation or cleanup.
Package generation and all 200 repository Python tests passed. The audit was committed as
`982eeb3e8aeb9883ce5cad71f941154b575b610c`; synchronization with main produced reviewed head
`93fd8054385e561b34a99f69b4db4d71d7247e1c`. Publication remains pending ownership reconciliation.

No normal machine configuration or consumer repository was changed. Migration and self-heal
have not been implemented. The audit does not supply the separate plugin-write prevention guard.

## Host findings

[HOST_EVIDENCE.md](HOST_EVIDENCE.md) owns the versions, native probe and exact upstream source links.
Claude 2.1.282 installed a local fixture dependency at project scope and exposed its skill and agent,
but wrote the dependency into project settings. Fresh-clone loading is not yet proven.
Codex 0.157.0 has neither plugin-agent loading nor a native marketplace dependency resolver.
Domain catalogs can enumerate core packages, but cannot make the native agent loader consume them.
A real isolated Codex `exec` successfully consumed core's L7 role via per-invocation developer
instructions/model/effort, with no profile config or agent files. A plugin-contained dispatcher is
therefore viable; its integration and repository-only plugin activation still need implementation
and proof. Native registration is not an added user requirement. Explicit repository plugin
enablement still left the Codex fixture uninstalled after native thread startup; its skill was
absent. The initial domain-plugin installation boundary remains unresolved.

## Machine inventory

Read-only audit on this PC reported:

- Codex: two user configuration tables (`plugins`, `marketplaces`), 13 user file entries,
  and 30 repository agent files.
- Claude: two user configuration tables (`enabledPlugins`, `extraKnownMarketplaces`) and
  one user file entry.
- No local marketplace overrides were reported among the existing requested consumer paths.
- `Concertable/concertable` is absent at the expected path. The other 12 Concertable registry
  entries and both C++ consumers were inspected. Other machines remain unverified.

Raw reports are in ignored `.machine-audit-codex.tmp` and `.machine-audit-claude.tmp` in this
worktree. Counts describe entries, not skill/role totals.

## Earlier machine record

The September 23 ledger described a separate checkout under `C:\Users\tommy`: all four
canonical repositories were present; an older `base-agents` checkout was 87 commits behind with
uncommitted plan-artifact changes and live worktrees. Claude had interim user-scope core installs,
stale domain sources, and auto-mode environment text naming Concertable globally. Codex used
profile-installed shared agents. That machine has not been reverified or marked converged. Retain
its old checkout until its work is preserved, and include the product-specific environment text
in eventual cleanup; the new audit does not inspect arbitrary environment values.

## Concurrent migration ownership

[PR #48](https://github.com/tj-agents/core/pull/48), branch
`Refactor/RepoDeclaredConfigHarnessMove`, was discovered during preflight. At inspected head
`fe46ff642d044fd4b5fca99e66904e0b2b36c504`, it ports shared hooks and adds a `repo_config.py`
generator under the same bootstrap skill, with a 2.1.13 release candidate. It also changes this
plan, ledger and roadmap. Its description requires consumers to name core's three plugins,
which conflicts with this session's newer domain-only authorization. Do not silently adopt that
policy or rewrite the other branch. Tommy was asked whether that session remains the owner or
this session should consolidate the migration. Audit code and host evidence remain preserved here.

## Concertable inventory

`Concertable/agents` was on `Fix/StandardsCurrencyAutoRefresh`, seven commits ahead of its tracking
branch. Do not modify or adopt that checkout's work. Its registry names agents, auth, b2b,
concertable, config, customer, docs, infra, payment, pipeline, platform-dotnet, search and system.
Generic generated hooks/workflows overlap core but many differ; semantic comparison is still needed.
Its `codex_delivery.py` and `codex-agents` remain pending retirement after replacement delivery.
Consumer stack profile drift (b2b/customer missing react versus the registry) remains to reconcile
during adoption. Core's separate hook activation work has now merged as PR #46.

## Verification

- 11 audit tests passed: read-only behavior, sanitized errors, disabled plugin detection,
  local source detection and CLI exit status.
- 31 existing capability-bootstrap tests passed.
- All 200 repository Python tests passed after synchronization with PR #46.
- PowerShell skill packaging tests passed; generated-file and paired AGENTS/CLAUDE checks
  also passed after synchronization with PR #47.
- Generated package and catalog checks passed.
- Native Claude fixture installation and component inventory succeeded; no model-session acceptance
  or Codex replacement delivery has been claimed.
- Existing workflow helper source-layout and porcelain parsing defects are recorded in
  `docs/workflows/TECH_DEBT.md`. Lifecycle instructions were loaded directly; test capture works.

## Reviews

`reviews/Feature-Repo-Declared-Config.md` records approval at
`93fd8054385e561b34a99f69b4db4d71d7247e1c`, with no actionable findings. Both configured review
agents were unavailable because their Spark model is unsupported for this account; the parent
completed both frozen lenses under the workflow fallback. The merge gate identified no
security-sensitive changed path. Later checkpoint-only documentation updates need incremental
review before publication.

## Next Steps

Scope: whole plan through all remaining phases and terminal delivery.
Current slice: reconcile ownership with PR #48 before publishing the completed read-only audit.
Remaining scope: native delivery gate, domain dependencies, Concertable deduplication, generator,
consumer adoption, self-heal, machine cleanup, plugin-write guard and per-machine acceptance.
Done when: authorized consumers load domain and core capabilities transitively in both hosts,
machine-local behavior is removed after acceptance, guards pass and delivery gates complete.

1. Resolve the requested ownership clarification for PR #48, then consolidate compatible source
   and plan changes without losing the domain-only requirement or the other owner’s work. Review
   the checkpoint documentation delta and publish the independent audit through the selected owner.
2. Prove a plugin-contained dispatcher using supported per-run Codex arguments and core's semantic
   role/lane definitions. The plan anticipated unsupported native plugin agents; native registration
   is not an added requirement. Keep ownership and investigate this adapter inside core before any
   decision to request changed constraints. Do not delete agent files before replacement acceptance.
3. Once proven, follow the remaining phases in fresh worktrees from fetched `origin/main`.
   Declare domains before deleting duplicate delivery. Back up profiles before cleanup and run
   real Claude/Codex sessions in winwrap and a Concertable consumer before declaring convergence.
