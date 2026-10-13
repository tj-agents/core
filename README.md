# core

Shared agent behavior, engineering process, and machine utilities for Codex and Claude.
The canonical repository is [`tj-agents/core`](https://github.com/tj-agents/core); the marketplace ID remains `base-agents`.
The repository publishes a minimal `base` package and optional `engineering` and `machine` packages.
Stack standards remain in their stack plugins; Concertable policy stays with Concertable.
The repository also owns explicit PowerShell profile and CLI session-recovery installation.

Global architecture and cross-repository designs live in [`tj-agents/docs`](https://github.com/tj-agents/docs)
(private; organization access required). Core-specific implementation plans and operational documentation
stay here; shared plans link to their source owners.

`base:plan-artifacts` makes substantive plans maintained Markdown files, including outside a repository.
`base:agent-files` keeps `AGENTS.md` and `CLAUDE.md` paired with one shared instruction source.
[`base:idea-initialization`](.agents/base/policy/idea-initialization/SKILL.md) owns the once-per-idea
assessment of existing capabilities and solutions; [`base:goal-continuation`](.agents/base/policy/goal-continuation/SKILL.md)
owns continued goal ownership and carries that recorded decision forward.
The richer planning workflows are selected engineering conventions, not prerequisites for standalone plans.
Known workflow runtime debt: [docs/workflows/TECH_DEBT.md](docs/workflows/TECH_DEBT.md).
Observed agent mistakes and proposed corrections: [MISTAKES.md](MISTAKES.md).
Recorded defects default to `BUGS.md` when a repository has no declared problem-register owner.
`engineering:write-bug`, `write-mistake`, and `write-debt` share record semantics; their corresponding
address workflows reuse the existing repair lifecycle.
Packaged SessionStart hooks deliver context and PreToolUse hooks gate routed writes. Their Python 3.9+
interpreter follows the host manifest: Codex uses `python3` on Linux/macOS and `python` on Windows; Claude's
current manifest uses `python` on all platforms. Keep the configured executable on PATH. Codex skips new or
changed plugin hooks until they are reviewed and trusted in `/hooks`; a fresh missing-marketplace write
probe is required before claiming enforcement. The host coverage limit is tracked in
`.agents/plugins/TECH_DEBT.md`. The `base:agent-files` skill documents a generated native-instruction
fallback.
Codex hook commands retain an integrity-checked copy of their trusted plugin package in `PLUGIN_DATA`.
An active session can keep running its original hook scripts when a marketplace refresh removes the old
cache directory. A changed hook definition still requires Codex trust review before it runs.

Codex hook commands use a short readable Python authenticator instead of encoded executable source.
It checks the shipped snapshot verifier's SHA-256 before staging those authenticated bytes in a temporary
directory and loading the Python file. Python isolated mode prevents the caller's directory from supplying
bootstrap imports. The verified runtime then checks package identity, package bytes and snapshot bytes.
Codex [trusts the hook definition](https://github.com/openai/codex/blob/rust-v0.157.0/codex-rs/hooks/src/engine/discovery.rs),
so invoking a mutable verifier directly would allow it to skip its own checks. The inline authenticator
retains that boundary without Base64 or explicit `exec`. These checks do not protect against an attacker
who can modify the user's trusted configuration or race files inside the same user's temporary/snapshot
directories, and source tests do not establish antivirus acceptance.

Use `machine:hook-control` for reversible Codex hook controls. In a terminal with the machine launcher
loaded, `codex-hooks status`, `codex-hooks off` and `codex-hooks on` operate on the active user profile.
Add `--scope project --project <repository>` for a trusted repository's `.codex/config.toml`.
The utility requires Python 3.11+. `off` writes the native
[`features.hooks = false` gate](https://learn.chatgpt.com/docs/hooks#turn-hooks-off), which prevents ordinary
lifecycle hooks from starting, including hooks introduced by later plugin updates. `on` restores the
previous gate value or absence; it preserves individually disabled hooks and trust metadata. Plugins and
skills remain enabled. A higher-priority project, profile, command-line or managed setting may override
the selected layer; status describes saved settings, and reopening Codex is required to rely on the change.
Internal host cleanup hooks and the separate legacy `notify` command are outside this gate.

The split packages form the **2.1.16** release candidate. Existing 1.x consumers and fresh installations select all
three packages. `base` remains the common behavior package, while `engineering` and `machine` stay
separate owners; all three install by default so `base:cd` always has its handoff workflow and launcher
closure.

## Repository auto-merge

An engineering-enabled repository opts into guarded agent auto-merge in `.agents/settings.json`:

```json
{"configuration":{"core":{"auto_merge":true}}}
```

Omit `configuration.core.auto_merge`, or set it to `false`, to disable the capability. The setting only
permits the guarded workflow command to request GitHub auto-merge; it does not authorize a merge. Standing
or scoped merge authority, every stop class and hold label, exact-head checks, current independent review,
security review, and checkout identity must still pass. The guarded workflow rereads settings at execution
time, so disabling it after a delivery binding prevents arming auto-merge. See
[repository settings](docs/workflows/REPOSITORY_CONFIGURATION.md) for the complete contract.

## Repository routine design approval

`configuration.core.auto_approve` is separately `false` for every supported routine category when
absent. Its only currently supported category is `design`, including routine convention choices. A
design-only opt-in is:

```json
{"configuration":{"core":{"auto_approve":{"design":true}}}}
```

An all-categories opt-in is:

```json
{"configuration":{"core":{"auto_approve":{"all":true}}}}
```

An explicit `design` value overrides `all`, and omitted members default to `false`. The legacy
`configuration.core.auto_approve_design` boolean remains available only when `auto_approve` is absent;
an empty `auto_approve` object is authoritative and disables design approval. When enabled, an agent may
make and record routine design or convention choices within work already authorized by the user. It does
not override an explicit user reservation, task scope, stricter repository rule, or any merge,
publication, installation, or permission gate. Select a core release that understands the nested setting
before enabling it; older strict readers reject unknown core settings. Source verification does not
establish installed-host trust or acceptance.

## Layout

- `.agents/` is the canonical host-neutral source. Base, engineering and machine ownership is expressed
  below it alongside shared workflows, hooks, schemas, tests and resources.
- `.codex/` contains only Codex entry points and host configuration. `.claude/` contains only Claude
  entry points and host configuration. Their skills reference canonical `.agents/` definitions rather
  than maintaining copied instruction bodies.
- [`SOURCE_LAYOUT.md`](SOURCE_LAYOUT.md) defines this source/adapter/distribution boundary.
- [`SKILL_KINDS.md`](SKILL_KINDS.md) defines the shared open taxonomy used by every agent marketplace repo.
- [`PACKAGING.md`](PACKAGING.md) is the rule that a utility skill's runtime dependencies ship with it.
- `.agents/catalog/catalog.json` records this repository's immutable releases and package digests. The generated
  [`CAPABILITIES.md`](CAPABILITIES.md) is its human-readable index. Consumers selecting other standards
  commit a composed catalog of owner-published release records beside their capability lock.
- `plugins/*` is generated distribution output assembled from canonical shared definitions and the
  selected host adapter. Nothing under it is an authored source.
- `shell/` owns the PowerShell profile, one concern per file.
- `cli-session-recovery/` owns save/restore scripts and their regression suite.
- install.ps1 installs the PowerShell profile; cli-session-recovery provides its own installer.

### Windows CLI hook windows

On Windows, interactive Codex launches through the installed machine profile and Codex handoff tabs
use `--no-daemon` to avoid the shared daemon's visible hook child consoles. The option is applied to
interactive starts, resumes, and forks; Codex's batch and maintenance commands keep their normal
arguments. Reopen a terminal after updating the machine plugin so its profile launcher is current.
For an existing installation that cannot yet refresh the machine plugin, run
`pwsh shell/install-codex-no-daemon.ps1` to add the same behavior to both PowerShell profiles;
`-VerifyOnly` checks that local installation.

Claude Code can open a visible Git Bash window for each hook. On Windows, run
`pwsh shell/install-hidden-bash.ps1` once from this checkout. The installer builds the included
GUI-subsystem Bash proxy using Clang or GCC, configures `CLAUDE_CODE_GIT_BASH_PATH` for the user, and
loads it in new PowerShell sessions. Check it with `pwsh shell/install-hidden-bash.ps1 -VerifyOnly`.
The proxy forwards standard handles and the exit code to the real Git Bash. If Git Bash lives outside
`C:\Program Files\Git\bin\bash.exe`, set the user-level `TJ_AGENTS_REAL_GIT_BASH` environment variable
to its absolute path before running the installer. Claude processes that launch `git.exe` directly
bypass this Git Bash workaround and require an upstream host fix.

A PR carries authored sources only. CI's guard job rejects generated paths, PR CI regenerates its own
workspace before testing, and the post-merge `regenerate` job commits the refreshed `plugins/*`,
catalog digests, marketplace bridges and `CAPABILITIES.md` to main. To refresh a local tree for tests,
run the same two commands and leave their output uncommitted:

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
`engineering@base-agents`, and `machine@base-agents` are expected to be exactly what the post-merge
`regenerate` job last committed into `plugins/<package>/` on `main` (briefly the previous, still
self-consistent generation while that job runs). Every skill's own scripts and resources travel
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

Claude loads installed plugins at session start and `/plugin marketplace update` refreshes only the
catalog. Typing `claude` in Bash on Linux or PowerShell on Windows/Linux, `open-claude`, `handoff-claude` and session recovery run
`.agents/machine/scripts/claude_standards_sync.py` first, so a session started through them loads the
latest registered commit of every plugin the directory enables. The machine plugin's SessionStart hook
adds one marked block to the supported terminal profiles that resolves its own `claude` wrapper, so the wrapper
updates with the plugin and no checkout is pulled; set `BASE_AGENTS_CLAUDE_PROFILE=off` to opt out.
From a core checkout, run it directly:

```powershell
python -B .agents/machine/scripts/claude_standards_sync.py --project <directory>
```

The ordinary command refreshes enabled Claude packages. Except in `--check` mode, it also invokes best-effort
permission synchronization for Claude allowlist entries and their state sidecar, plus Codex prefix rules.

To deliberately consolidate authenticated legacy Claude profile aliases into `<plugin>@tj-agents`, preview the
profile change first. On Windows run:

```powershell
python -B .agents/machine/scripts/claude_standards_sync.py --project <directory> --migrate-profile --check
```

On Linux or macOS run the same command with `python3`. After reviewing the preview, omit `--check` to apply it.
The migration checks the supplied project and registered project/local plugin roots before changing the user profile;
it defers a selection when one of those roots preserves a conflicting legacy choice.

Codex treats `INSTALLED_BY_DEFAULT` as marketplace policy, not a CLI dependency resolver. Register the
marketplace, then install all three packages explicitly:

```powershell
codex plugin marketplace add tj-agents/core
codex plugin add base@base-agents
codex plugin add engineering@base-agents
codex plugin add machine@base-agents
```

Typing `codex` in Bash on Linux or PowerShell on Windows/Linux and using `handoff-codex` refreshes configured Git marketplaces and
enabled plugins before Codex loads them. The launcher then records native Codex hook trust only for
enabled plugins sourced from GitHub's `tj-agents` organisation, after checking the installed package
against its unchanged Git source. Other publishers and user/project hooks retain normal trust review.
Set `BASE_AGENTS_CODEX_HOOK_TRUST=off` to keep manual review for all hooks. The machine plugin's SessionStart hook adds a marked block
to the supported terminal profiles. That block resolves the active installed machine package at invocation time, so later
terminals load its `codex` wrapper without pulling this checkout. The first session after installing
the package wires the profiles; open a new terminal to use the wrapper. Set
`BASE_AGENTS_CODEX_PROFILE=off` to leave profiles alone. A project pinned to a release continues to
use that release until its committed selection changes.

### Recover from a faulty installed hook

A hook repair reaches a machine only after it merges and the `regenerate` job commits it to `main`. Until
then the installed copy matches `main` and is not stale. Packaged versions do not change per merge; the
refresh above re-caches same-version content, and on Codex the changed package digest changes the hook definition,
so it needs trust again. A running session keeps the hook bytes it loaded on either host and cannot adopt the repair.
To recover one blocked by a Stop hook, send `stop` or `pause` as the whole prompt so the continuation gate releases
the turn, then close it and start a new session through the `codex` or `claude` terminal wrapper,
`handoff-codex` or `handoff-claude`. Without a wrapper, refresh first:

```text
codex plugin marketplace upgrade
codex plugin add engineering@base-agents      # then trust the changed hook in /hooks
claude plugin marketplace update base-agents
claude plugin update engineering@base-agents
```

Never edit an installed plugin cache, disable hooks, or rewrite continuation state to clear the block.

Use a project capability lock and `machine:bootstrap-capabilities` when a cross-marketplace selection must
resolve and verify its complete dependency closure reproducibly.

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
