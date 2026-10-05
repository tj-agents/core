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

## Cross-PC currency requirement (Tommy, 2026-09-28)

After standards change on another PC and are pushed, the next Claude and Codex CLI sessions on every developer PC must load the current approved standards without manual cache repair. This requires a defined update channel, a startup refresh that completes before the host loads plugins, and acceptance runs in both installed hosts. The existing immutable release pins give repeatable behavior but do not advance after a push to `main`. Automatic approval review rejected changing all generated project marketplace refs to moving `main`, because it would execute code outside the reviewed release contract. Keep the pinned behavior until an approved update channel is chosen; do not report latest-push synchronization as complete from cache refresh alone.
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
   sources). Consumer CI fails when these drift from the generator. Each standards repository
   publishes its own release catalog and harness requirements; consumers commit a composed
   catalog covering the plugins they select.
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
   Claude's pre-load refresh and orphan-window evidence: [`CLAUDE_STANDARDS_SYNC.md`](CLAUDE_STANDARDS_SYNC.md).

## Priority and authorization (Tommy, 2026-09-27)

Machine-agnostic agent behaviour is the priority and is authorized end to end: implement,
test, open PRs and deliver through each repository's normal merge path. Tommy's requirement,
verbatim in substance: if the standards require certain harnesses, the standards declare them
and every consuming repository gets them committed. No reliance on local permissions or
user-scope installs. Concretely:

1. Each standards package (core, cpp, react, ...) declares the harness it requires — plugins,
   marketplaces, hooks and the permission rules its own workflows need — in a committed manifest.
2. The phase 2 generator composes those manifests for a repository's selected stacks and writes
   its committed `.claude/settings.json` and `.codex/config.toml`; consumer CI fails on drift.
3. Do phase 2 (including the permissions gap below) first for the C++ consumers
   (`cpp/windows/winwrap`, `sandbox-hwid`). Phase 1's Concertable ordering constraint still
   applies to Concertable; it does not block phase 2 elsewhere.
4. Keep the sibling plan `plans/conditional-skill-routes/` separate but compatible: routes stay
   the "which skills must be loaded" contract; this plan owns "which harness is installed".
5. **Make it a permanent, fundamental rule — not just this plan's outcome.** Codify it in core's
   always-on standing guidance (the instructions every standards-managed repository loads) and
   in the skill/package authoring guidance: *never add or change a skill, hook, workflow or
   marketplace package without, in the same change, updating the harness manifest it requires,
   so that every repository that pulls in that marketplace gets its harness updated.* The
   mechanism below is enforced, not remembered: a standards-repo CI check
   fails when a package's skills/hooks/workflows need harness (plugins, hooks, permissions) that
   its manifest does not declare, and consumer CI fails when a repository's committed settings
   drift from the generated harness. A machine's local configuration must never be what makes a
   standard work.

### Phase-2 harness manifest mechanism

Core owns the schema at `.agents/plugins/harness.schema.json`. Each standards repository owns one
manifest per published plugin at `.agents/plugins/harness/<plugin>.json`; core starts with
`base.json`, `engineering.json`, and `machine.json`. `scripts/sync_harness_manifests.py` validates
the manifests, and `scripts/update_catalog_digests.py` copies the validated `requires`
object into the matching plugin entry in `.agents/catalog/catalog.json`. The generated package also
ships the manifest as `plugins/<plugin>/harness.json`, so its package digest covers the declaration.
The catalog schema makes `harness` required for every current plugin release.

The manifest shape is fixed:

```json
{
  "schema_version": 1,
  "plugin": "base-agents/machine",
  "source_roots": [".agents/machine"],
  "requires": {
    "marketplaces": [{"id": "base-agents", "repository": "tj-agents/core"}],
    "plugins": ["base-agents/base", "base-agents/machine"],
    "hooks": [
      {"path": "hooks/example.py", "hosts": ["claude", "codex"]}
    ],
    "permissions": {
      "claude_allow": [
        "PowerShell(& *\\handoff-codex\\scripts\\launch-codex.ps1 *)",
        "PowerShell(& *\\handoff-claude\\scripts\\launch-claude.ps1 *)"
      ],
      "codex_prefix_rules": [
        {
          "pattern": ["example", "safe-subcommand"],
          "justification": "Required by the packaged workflow.",
          "match": ["example safe-subcommand --flag"],
          "not_match": ["example unsafe-subcommand"]
        }
      ]
    }
  }
}
```

`hooks[].path` is the package-relative generated destination and `hosts` is a non-empty subset of
`claude` and `codex`. Each Codex rule is an allow decision; the generator supplies
`decision = "allow"` and requires non-empty pattern, justification, match and not-match arrays.
The validator recomputes the expected hooks, plugins and marketplaces from the authored sources on
every run, so a wiring change makes `sync_harness_manifests.py --check` fail until the declaration
is updated; the earlier blanket `source_digest`/`source_excludes` tripwire was dropped as
consumerless. The validator also proves every declared hook is wired by
both host manifests where its `hosts` list requires that, every required plugin exists in the
catalog, and every marketplace repository matches its own release owner and GitHub source.
Core's authored catalog contains only core releases; each other standards repository maintains
its own release records and digest sync. A consumer combines the selected owner catalogs in
its committed `.agents/catalog/catalog.json`, passed to the generic bootstrap and config generator.
Core must not carry a roster, source map, or digest ledger for another standards repository.

`repo_config.py` reads the selected catalog plugins, unions their `requires` objects, and fails if
the committed capability lock omits a required plugin. It owns these generated fields and files:

- `.claude/settings.json`: `extraKnownMarketplaces`, `enabledPlugins`, and
  `permissions.allow`, sorted and deduplicated. Repository-specific additions use a committed
  `.agents/repository-harness.json` shaped as
  `{"schema_version": 1, "requires": {<same requires object>}}` and validated through the
  schema's `$defs/requires`; hand-edited values in those generated fields are drift.
- `.codex/config.toml`: the managed marketplace/plugin section already generated today.
- `.codex/rules/agent-harness.rules`: deterministic Starlark `prefix_rule` entries from
  `codex_prefix_rules`, including inline `match`/`not_match` examples. Empty declarations remove
  the generated file. Codex project rules load only for trusted projects and cannot safely express
  a machine-varying plugin-cache script path, so the machine launcher currently declares no Codex
  prefix rule; the existing hook/sandbox approval remains the honest minimum until a stable
  repository-relative command exists.

Claude's committed project `permissions.allow` supports `PowerShell(...)` rules and takes effect
after workspace trust. The phase-4 acceptance session must prove that the two launcher patterns
above satisfy the auto-mode classifier; if an `ask`/`deny` rule or managed policy still wins, record
that external policy as the minimal non-repository remainder instead of broadening the patterns.

The permanent prose rule lives in `PACKAGING.md` (package authoring) and the shipped
`base:plan-artifacts` standing contract. Enforcement lives in code: standards CI runs
`python -B scripts/sync_harness_manifests.py --check`, catalog/schema tests and
`pwsh .agents/sync-generated.ps1 -Check`; consumer CI runs `repo_config.py --mode check` and
host-config parsing tests. `test_harness_manifests.py` covers stale digests, missing hook wiring,
foreign marketplaces, absent required plugins and catalog drift; `test_repo_config.py` covers
multi-package composition, permission deduplication, preservation of unrelated settings, stale
generated-rule deletion, and check-mode drift.

Implementation-path standards: root `AGENTS.md` and `SOURCE_LAYOUT.md` govern the authored versus
generated split; `PACKAGING.md` governs shipped runtime closure; the existing Python and JSON style
in `repo_config.py`, `sync_plugin_packages.py`, and their tests governs the new validator and schema.
No stack-specific standard applies to these paths.

## Gap: permissions and auto-mode rules (observed 2026-09-27)

The design above covers plugins and marketplaces but not permission rules, which also change
agent behaviour per machine. In `cpp/windows/winwrap` on this machine, Claude Code's auto-mode
classifier denied the packaged `machine:handoff-codex` launcher (`launch-codex.ps1 ...
-BypassHookTrust`) as "Create Unsafe Agents". The same handoff works on Tommy's other machine,
where a user-scope allow rule presumably exists. The handoff skill is standard workflow, so
its launch permission must not depend on which machine runs it.

**Extend phase 2:** the generator also writes the permission allow rules that the standards'
own workflows need (at minimum the packaged handoff launchers) into the repository's
`.claude/settings.json`, and the equivalent Codex approval policy where one exists. The
machine verifier (phase 4) reports user-scope permission rules that duplicate or contradict
the generated ones. Confirm in a real session that a project-scope allow rule satisfies the
auto-mode classifier; if it does not, record the limitation and the minimal user-scope
remainder instead of claiming the machine is clean.

## Marketplace declarations belong to their owners

Each standards repository publishes its own release identity, GitHub source, package digests,
and harness requirements. Core publishes only `base-agents`. A consuming repository commits
the release records for its selected standards in `.agents/catalog/catalog.json` and checks
that catalog alongside its lock and generated host settings. The generic generator validates
that each source matches its release owner; it contains no list of other repositories.

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
