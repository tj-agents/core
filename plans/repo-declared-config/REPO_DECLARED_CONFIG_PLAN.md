# Repo-declared agent configuration

## Problem

Agent behaviour currently depends on machine-local state, so the same repository behaves
differently on different machines and drifts on this one. Observed on 2026-09-23 in
`sandbox-hwid`:

- Routes named `cpp:*`/`msvc:*`/`win32:*` skills that only Codex had, through a local
  marketplace override in `.codex/config.toml`. Claude had only legacy user-scope plugins,
  so the skill router blocked every write.
- The `cpp-agents` marketplace lacked `autoUpdate` in Claude's user config; the others had it.
- The SessionStart check reported standards current while no route resolved.
- A plugin installed mid-session could not be used until a restart.
- `concertable@agent-standards` is enabled at user scope, so Concertable product skills and the
  generic harness hooks it happens to carry load in every repository.

## Rule

Everything that affects agent behaviour is committed in a repository. A machine holds only
derived caches (downloaded plugins) and credentials. Cloning a repository on any machine gives
identical behaviour.

## Design

1. **Core owns the generic harness** for Claude and Codex: skill router, SessionStart check,
   delivery gates (merge-review, forge-poll, red-run, plan-handoff), the lane and workflow
   agents, and self-heal. Core's `engineering` package already ships the router, the gates and
   the agents; `concertable@agent-standards` (`Concertable/agent-standards`,
   `plugins/concertable`) carries duplicates of them. Retire those duplicates so concertable keeps
   only Concertable-product skills and rules. Order: the Concertable repositories first declare
   the concertable marketplace (which depends on core), then the duplicates are deleted, so
   they are never without lanes or gates.
2. **Generated repo config.** A core generator reads a repository's `.agents/` profile and
   routes and writes its `.claude/settings.json` and `.codex/config.toml` declaring only the
   repository's domain marketplace (GitHub sources, no local sources). A repository never names
   core, lanes or core's agents directly: every child marketplace (cpp, react, dotagents,
   concertable) depends on core, so core arrives transitively. Consumer CI fails when these
   drift from the generator.
3. **Self-heal.** When a route's skill is missing, stale or not loaded, core's hook updates the
   declared GitHub marketplace, installs the pinned release, injects the skill's `SKILL.md`
   through hook output and records that as the session proof, so no restart is needed.
   - Only repository-declared GitHub sources and released versions; never local paths,
     provisioning scripts or unreleased branches.
   - Running it twice does nothing extra; it runs once per desync, logs one line, and blocks
     only when repair is impossible, saying why.
   - The existing router already reads transcript proof (Claude `Skill` results, Codex `exec`
     reads); extend it so injected content counts.
   - Confirm whether Codex hooks can inject mid-session. If not, repair at SessionStart and
     say so plainly.
4. **Machine cleanup, per machine, after adoption.** Inventory, then remove:
   - `~/.claude/settings.json` user-scope `enabledPlugins` and `extraKnownMarketplaces`.
   - Codex user-config equivalents, `~/.codex/agents` and `~/.codex/skills`; move anything
     still needed into a repository.
   - Per-repository local marketplace overrides.
   Core ships a read-only verifier that reports remaining machine-local behavioural state, so
   every machine can be checked the same way.

## Marketplaces come only from tj-agents

The generic canonical repositories are `tj-agents/core`, `tj-agents/cpp`, `tj-agents/react` and
`tj-agents/dotnet`. The September 26 authorization additionally selects `Concertable/agents`
only for Concertable consumers. Generated repository configuration uses its domain's GitHub
source; the generator refuses other sources and consumer CI checks it.
Marketplace IDs stay stable (`base-agents`, `cpp-agents`, `react-agents`, `dotagents`), so
existing installs keep resolving; only the source changes.

Stale sources observed on this PC (2026-09-23): `tomjseery/dotagents`, `tomjseery/react-agents`
and `Concertable/agent-standards` in `~/.claude/settings.json`; `tj-agents/core` was not
installed in Claude at all.

Build the generator and verifier on `machine:bootstrap-capabilities`, which already previews,
applies and verifies exact project locks through native plugin commands; extend it rather than
adding a second installer.

## Per-machine migration

This plan stays open until every machine has converged, so the procedure lives here.

1. Clone the canonical repositories side by side under `~/source/repos/tj-agents/`: `core`,
   `cpp`, `react`, `dotnet`. Retire older checkouts with other names (`base-agents`,
   `cpp-agents`, `dotagents`, `react-agents`) only after the user has moved or discarded any
   uncommitted work in them.
2. Run core's machine verifier (phase 4) and record what it reports in the ledger.
3. Remove the user-scope marketplaces and plugins it reports, once the repositories on that
   machine declare their own.
4. Rerun the verifier; it must report nothing. Record the machine as converged in the ledger.

Paste this into a new Claude or Codex session on each machine:

```text
cd ~/source/repos/tj-agents/core
Pull main. Read plans/repo-declared-config/REPO_DECLARED_CONFIG_PLAN.md and
plans/repo-declared-config/REPO_DECLARED_CONFIG_PROGRESS.md and do what the ledger's
`## Next Steps` says; then follow the plan's "Per-machine migration" for this machine.
```

## Scope of this plan

The September 26 authorization supersedes the original sandbox-only adoption scope. Adopt
`cpp/windows/{winwrap,sandbox-hwid}` and the Concertable repositories. The cpp, react, dotnet
and Concertable marketplaces must supply core transitively. Other product consumers remain
follow-ups. Remove machine settings only after replacement delivery passes native-host tests.

## Independent audit implementation

Extend the existing `bootstrap_capabilities.py` entry point with `--mode audit`. It accepts
the existing required `--harness` and `--profile`, plus repeatable `--repository` paths, and
requires no lock, catalog, network or host CLI. Existing preview/apply/verify retain their
lock requirement. Audit parses Claude JSON or Codex TOML, reports user plugin/marketplace
settings, user-authored skills and agents, repository agent copies and local marketplace
overrides. Host-provided `.system` skills and downloaded plugin caches are derived state.
Malformed or unreadable inputs fail explicitly without returning their contents. Audit never
repairs or deletes anything; `--report` is the sole optional write.

The deciding entry-point branch is:

```python
report = audit_configuration(arguments) if arguments.mode == "audit" else execute(arguments)
```

Reports use the existing JSON envelope with `findings` containing diagnostic code, path and
setting name, never setting values. Exit zero means no findings; findings or read errors exit
one. Tests use isolated profiles to prove read-only behavior, rejection of malformed settings,
detection of disabled as well as enabled plugin entries, and preservation of bootstrap modes.
This audit can ship while transitive loading is being established; it does not satisfy the
separate plugin-write prevention or migration acceptance gates.

## Acceptance, for Claude and Codex each

1. With empty user plugin config, sessions in winwrap, sandbox-hwid and the adopted Concertable
   repositories load their domain and core's skills, hooks and agents transitively. A routed
   write succeeds in a C++ consumer and a Concertable consumer.
2. Uninstalling a route's plugin mid-session, then writing, succeeds after one logged repair
   with no restart (or, for a host that cannot inject, one SessionStart repair and a plain
   notice).
3. Sessions in winwrap and sandbox-hwid load no Concertable skills or hooks.
4. The machine verifier reports no machine-local behavioural state on this PC.

## Phases

0. Prove transitive delivery in the installed hosts before consumer changes or cleanup.
1. Port missing generic harness behavior to core, adopt Concertable declarations, retire its
   duplicate generic delivery, routing and gates; release.
2. Repo-config generator and consumer drift check; release.
3. Self-heal in the router and SessionStart for both hosts; release.
4. Adopt the authorized consumers; back up and clean this PC; run acceptance and the audit.
5. Enforce absence of repository agent writes and user-scope plugin enablement. Keep per-machine
   migration open until each available machine is verified, recording unavailable machines.
