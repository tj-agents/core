# core

Shared agent behavior, engineering process, and machine utilities for Codex and Claude.
The canonical repository is [`tj-agents/core`](https://github.com/tj-agents/core); the marketplace ID remains `base-agents`.
The repository publishes a minimal `base` package and optional `engineering` and `machine` packages.
Stack standards remain in their stack plugins; Concertable policy stays with Concertable.
The repository also owns explicit PowerShell profile and CLI session-recovery installation.

`base:plan-artifacts` makes substantive plans maintained Markdown files, including outside a repository.
The richer planning workflows are selected engineering conventions, not prerequisites for standalone plans.
The packaged SessionStart hook emits the same canonical contract to both hosts. Python 3.9+ must be available
as `python` on PATH. Enable and trust the hook in the host before claiming automatic delivery; installation
alone is insufficient. The skill documents an explicit generated native-instruction fallback.

The split packages form the **2.1.5** release. Existing 1.x consumers and fresh installations select all
three packages. `base` remains the common behavior package, while `engineering` and `machine` stay
separate owners; all three install by default so `base:cd` always has its handoff workflow and launcher
closure.

## Layout

- `.agents/` is the canonical host-neutral source. Base, engineering and machine ownership is expressed
  below it alongside shared workflows, hooks, schemas, tests and resources.
- `.codex/` contains only Codex entry points and host configuration. `.claude/` contains only Claude
  entry points and host configuration. Their skills reference canonical `.agents/` definitions rather
  than maintaining copied instruction bodies.
- [`SOURCE_LAYOUT.md`](SOURCE_LAYOUT.md) defines this source/adapter/distribution boundary.
- [`SKILL_KINDS.md`](SKILL_KINDS.md) defines the shared open taxonomy used by every agent marketplace repo.
- [`PACKAGING.md`](PACKAGING.md) is the rule that a utility skill's runtime dependencies ship with it.
- `.agents/catalog/catalog.json` records immutable cross-repository releases and package digests. The generated
  [`CAPABILITIES.md`](CAPABILITIES.md) is its human-readable index; project selections live in one
  `.agents/capabilities.lock.json` governed by the shipped lock schema.
- `plugins/*` is generated distribution output assembled from canonical shared definitions and the
  selected host adapter. Nothing under it is an authored source.
- `shell/` owns the PowerShell profile, one concern per file.
- `cli-session-recovery/` owns save/restore scripts and their regression suite.
- install.ps1 installs the PowerShell profile; cli-session-recovery provides its own installer.

Run `pwsh .agents/sync-generated.ps1` after changing a skill and
`pwsh .agents/sync-generated.ps1 -Check` before delivery.

When package bytes change, refresh the local catalog digests before generation:

```powershell
python -B scripts/update_catalog_digests.py
pwsh .agents/sync-generated.ps1
```

The `machine:bootstrap-capabilities` skill previews, applies and verifies exact project locks through native
Codex or Claude plugin commands. It uses installation-owned Git checkouts at full locked commits and isolated
`CODEX_HOME` or `CLAUDE_CONFIG_DIR` profile paths. Preview changes nothing; verify is offline-safe; apply only
adds the selected catalog marketplaces and plugins. It never performs an unconditional marketplace refresh.

Catalog releases use immutable semantic tags. Codex manifests carry matching package versions; Claude remains
commit/tag based until its dependency/version behavior has a separately verified gate. `sha256-tree-v1` hashes
the sorted package paths, lengths and bytes. The machine package excludes only its embedded
`catalog/catalog.json` from its own digest to avoid a self-reference; its schemas, bootstrap and all other
resources remain covered.

## Install

```powershell
.\install.ps1
```

Use `-WhatIf` to inspect and `-VerifyOnly` to verify without changing the machine. Session-recovery runtime
data, transcripts, credentials, and identifiers remain outside the repository.

## Install / update the default plugins

GitHub is authoritative; a machine's installed copies of `base@base-agents`,
`engineering@base-agents`, and `machine@base-agents` are expected to be exactly what
the latest commit on `main` generated into `plugins/<package>/`. Every skill's own scripts and resources travel
inside that generated package (see `PACKAGING.md`), so registering the marketplace and installing/updating
the plugins is the entire supported procedure — never hand-place a script or resolver on a machine to make
a skill work.

Claude Code:

```
/plugin marketplace add tj-agents/core
/plugin install base@base-agents
/plugin install engineering@base-agents
/plugin install machine@base-agents
```

After a new commit lands on `main`, pick it up with:

```
/plugin marketplace update base-agents
```

Codex: adding the marketplace (`.agents/plugins/marketplace.json`) installs all three packages
automatically; each declares `INSTALLED_BY_DEFAULT`. Refresh Codex's copy of the marketplace the same way
to pick up a new commit.

Codex does not load agent definitions directly from plugins. After installing or updating the marketplace,
install the engineering package's shared agents once into the active Codex profile. The installer defaults
to `CODEX_HOME` and then `~/.codex`; `-CodexHome` selects an explicit alternate profile. Preview is the
default, apply and verify are separate deterministic operations:

```powershell
$codexProfile = if ($env:CODEX_HOME) {
    $env:CODEX_HOME
} else {
    Join-Path ([Environment]::GetFolderPath('UserProfile')) '.codex'
}
$engineeringRelease = Get-ChildItem -Directory (Join-Path $codexProfile 'plugins/cache/base-agents/engineering') |
    Sort-Object { [version]$_.Name } |
    Select-Object -Last 1
$agentInstaller = Join-Path $engineeringRelease.FullName 'scripts/install-codex-agents.ps1'

& $agentInstaller -CodexHome $codexProfile
& $agentInstaller -CodexHome $codexProfile -Apply
& $agentInstaller -CodexHome $codexProfile -Verify
```

To migrate a repository that received older base-agents copies, add
`-MigrateProjectRoot <repository> -Apply`. The installer verifies the profile copies before removing only
files whose content matches the shipped base-agents history; a colliding filename with different content is
preserved. Deprecated `-ProjectRoot` remains a migration alias so existing automation gets the safe profile
cut-over instead of a parameter-binding failure. Profile ownership is recorded in
`agents/.base-agents-delivery.json`: upgrades and `-Uninstall -Apply` replace or remove only files whose
content still matches that record. An unowned collision or a locally modified owned file is preserved and
reported as an actionable error instead of being overwritten. Use `-Uninstall` to preview profile cleanup.
Claude continues to load the package's `agents/` payload directly and needs no copied `.claude/agents` tree.
