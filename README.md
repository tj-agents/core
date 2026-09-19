# base-agents

Shared agent behavior, engineering process, and machine utilities for Codex and Claude.
The combined `base@base-agents` package includes the common maintained-plan contract and the already
restored process skills. The later base/engineering/machine split is not implemented here. Stack standards
remain in their stack plugins; Concertable policy and its remaining enforcement runtime stay with Concertable.
The repository also owns explicit PowerShell profile and CLI session-recovery installation.

`base:plan-artifacts` makes substantive plans maintained Markdown files, including outside a repository.
The richer planning workflows are selected engineering conventions, not prerequisites for standalone plans.
The packaged SessionStart hook emits the same canonical contract to both hosts. Python 3.9+ must be available
as `python` on PATH. Enable and trust the hook in the host before claiming automatic delivery; installation
alone is insufficient. The skill documents an explicit generated native-instruction fallback.

The candidate Codex package version is **1.2.0**. Claude retains commit-based refresh (no fixed version)
until release gates are introduced. Consequently Claude `plugin validate --strict` currently reports its
missing-version warning, also present at the 1.1.0 baseline; ordinary manifest validation must still pass.

## Layout

- `.agents/` is the canonical host-neutral source. Base, engineering and machine ownership is expressed
  below it alongside shared workflows, hooks, schemas, tests and resources.
- `.codex/` contains only Codex entry points and host configuration. `.claude/` contains only Claude
  entry points and host configuration. Their skills reference canonical `.agents/` definitions rather
  than maintaining copied instruction bodies.
- [`SOURCE_LAYOUT.md`](SOURCE_LAYOUT.md) defines this source/adapter/distribution boundary.
- [`SKILL_KINDS.md`](SKILL_KINDS.md) defines the shared open taxonomy used by every agent marketplace repo.
- [`PACKAGING.md`](PACKAGING.md) is the rule that a utility skill's runtime dependencies ship with it.
- `plugins/*` is generated distribution output assembled from canonical shared definitions and the
  selected host adapter. Nothing under it is an authored source.
- `shell/` owns the PowerShell profile, one concern per file.
- `cli-session-recovery/` owns save/restore scripts and their regression suite.
- install.ps1 installs the PowerShell profile; cli-session-recovery provides its own installer.

Run `pwsh .agents/sync-generated.ps1` after changing a skill and
`pwsh .agents/sync-generated.ps1 -Check` before delivery.

## Install

```powershell
.\install.ps1
```

Use `-WhatIf` to inspect and `-VerifyOnly` to verify without changing the machine. Session-recovery runtime
data, transcripts, credentials, and identifiers remain outside the repository.

## Install / update the `base` plugin

GitHub is authoritative; a machine's installed copy of `base@base-agents` is expected to be exactly what
the latest commit on `main` generated into `plugins/base/`. Every skill's own scripts and resources travel
inside that generated package (see `PACKAGING.md`), so registering the marketplace and installing/updating
the plugin is the entire supported procedure — never hand-place a script or resolver on a machine to make
a skill work.

Claude Code:

```
/plugin marketplace add tomjseery/base-agents
/plugin install base@base-agents
```

After a new commit lands on `main`, pick it up with:

```
/plugin marketplace update base-agents
```

Codex: adding the marketplace (`.agents/plugins/marketplace.json`) installs `base` automatically — its
declared policy is `INSTALLED_BY_DEFAULT`. Refresh Codex's copy of the marketplace the same way to pick up
a new commit.
