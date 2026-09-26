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
- On 2026-09-26, an active Codex session loaded hooks from `base-agents` 2.1.8, then a
  marketplace refresh removed that plugin cache path during the session. The hooks' script paths
  became stale. A machine-local `notify` command also launched a console executable from AppData
  and had a recorded Windows error 206. Neither a profile edit nor a cache junction is a durable
  repair for these failures.

## Rule

Everything that affects agent behaviour is committed in a repository. Core owns the generic
harness and its host adapters; consumer repositories declare which released capabilities they use.
A machine holds only derived caches, credentials and runtime data. Cloning a repository on any
machine gives identical agent behaviour without hand-edited user hook, plugin, agent, marketplace
or notification settings. A plugin refresh must not break hooks already loaded by a live session.

## Design

1. **Core owns the generic harness** for Claude and Codex: skill router, SessionStart check,
   delivery gates (merge-review, forge-poll, red-run, plan-handoff), the lane and workflow
   agents, and self-heal. Core's `engineering` package already ships the router, the gates and
   the agents; `concertable@agent-standards` (`Concertable/agent-standards`,
   `plugins/concertable`) carries duplicates of them. Retire those duplicates so concertable keeps
   only Concertable-product skills and rules. Order: the Concertable repository first enables
   core plus concertable in its own project settings, then the duplicates are deleted, so it is
   never without lanes or gates.
2. **Generated repo config.** A core generator reads a repository's `.agents/` profile and
   routes and writes its `.claude/settings.json` (`extraKnownMarketplaces` with GitHub sources
   plus `enabledPlugins`, always including core) and `.codex/config.toml` (same, no local
   sources). Consumer CI fails when these drift from the generator. Child marketplaces (cpp,
   react, dotagents) always pull in core.
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
   - User-scope hook and notification commands, temporary cache aliases and manually placed
     harness scripts. A desired notification belongs in a declared host adapter and must be
     launched without an unwanted console window; otherwise omit it.
   Core ships a read-only verifier that reports remaining machine-local behavioural state, so
   every machine can be checked the same way.
5. **Live-session cache safety.** Exercise a marketplace update while an old session is active.
   Keep the scripts used by that session callable until it ends, or have core's host adapter
   resolve the currently installed released package without a machine-specific path. The repair
   and its regression test live in core; never create a local junction as part of normal operation.

## Marketplaces come only from tj-agents

The canonical repositories are `tj-agents/core`, `tj-agents/cpp`, `tj-agents/react` and
`tj-agents/dotnet`. Every marketplace a generated repository config references must use one of
these GitHub sources; the generator refuses any other source and consumer CI checks it.
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

Adopt `sandbox-hwid` first, then every known consumer: cpp-agents, the Concertable repository,
dotagents, react-agents, winwrap, note-cli, icon-dropper and wifi-toggle. Discover any additional
consumer during the inventory and add it here. Adopt consumers one at a time with a green host
check before removing their user-scope fallback. Concertable must move
`concertable@agent-standards` to project scope before user-scope removal on any machine that works
on it. This plan closes only after all known consumers and machines pass the verifier; a single
consumer or PC is a checkpoint, not the end of the goal.

## Acceptance, for Claude and Codex each

1. With empty user plugin config, cloning `sandbox-hwid` and starting a session yields the
   declared plugins, and a C++ write succeeds.
2. Uninstalling a route's plugin mid-session, then writing, succeeds after one logged repair
   with no restart (or, for a host that cannot inject, one SessionStart repair and a plain
   notice).
3. A `sandbox-hwid` session loads no Concertable skills or hooks.
4. The machine verifier reports no machine-local behavioural state on each migrated PC.
5. A live Codex and Claude session continues to run its installed hooks across a marketplace
   update without stale-path failures or empty console windows.

## Phases

1. Move the generic harness hooks into core; release.
2. Repo-config generator and consumer drift check; release.
3. Self-heal in the router and SessionStart for both hosts; release.
4. Adopt in `sandbox-hwid`; clean this PC; run acceptance.
5. Adopt every remaining consumer and machine, remove user-scope behavioural state, and run the
   same acceptance checks after each migration.
