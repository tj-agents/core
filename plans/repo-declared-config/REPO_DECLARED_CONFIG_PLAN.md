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
   delivery gates (merge-review, forge-poll, red-run, plan-handoff) and self-heal. These
   currently ship in `concertable@agent-standards` (`Concertable/agent-standards`,
   `plugins/concertable/hooks`). Move them here; concertable keeps only Concertable-product
   skills and rules.
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
   Core ships a read-only verifier that reports remaining machine-local behavioural state, so
   every machine can be checked the same way.

## Scope of this plan

Adoption is **`sandbox-hwid` only**. Other consumers (cpp-agents, the Concertable repository,
dotagents, react-agents, winwrap, note-cli, icon-dropper, wifi-toggle) are follow-ups, adopted
one at a time after this plan closes. Concertable must move `concertable@agent-standards` to
project scope before user-scope removal on any machine that works on it.

## Acceptance, for Claude and Codex each

1. With empty user plugin config, cloning `sandbox-hwid` and starting a session yields the
   declared plugins, and a C++ write succeeds.
2. Uninstalling a route's plugin mid-session, then writing, succeeds after one logged repair
   with no restart (or, for a host that cannot inject, one SessionStart repair and a plain
   notice).
3. A `sandbox-hwid` session loads no Concertable skills or hooks.
4. The machine verifier reports no machine-local behavioural state on this PC.

## Phases

1. Move the generic harness hooks into core; release.
2. Repo-config generator and consumer drift check; release.
3. Self-heal in the router and SessionStart for both hosts; release.
4. Adopt in `sandbox-hwid`; clean this PC; run acceptance.
