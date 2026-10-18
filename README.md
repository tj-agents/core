# core

Shared agent behavior, engineering process, and machine utilities for Codex and Claude.
The canonical repository is [`tj-agents/core`](https://github.com/tj-agents/core).
Select `base@tj-agents`, `engineering@tj-agents` and `machine@tj-agents` from
[`tj-agents/marketplace`](https://github.com/tj-agents/marketplace).
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
Codex hook commands use a per-session temporary snapshot preseeded for the running session's hooks.
This lets those hooks keep running after a startup refresh replaces an inactive package cache entry.
New sessions create a fresh snapshot from the verified package; snapshots outside the plugin cache are
left in place. A changed hook definition still requires Codex trust review before it runs.

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

The packages have no release line or compatibility promise: each supported Claude and Codex launcher
refreshes and verifies the currently selected packages and their required dependencies from their
publishers' `main` branches before the native CLI starts. Selection stays an independent user and
repository setting; adding a marketplace does not select its full roster. An explicitly selected package
that has been removed from the current publisher roster blocks startup with an error until selection is
corrected. Initial native installation is bootstrap only; ongoing freshness requires a supported launcher.

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
publication, installation, or permission gate. Use a current core package that understands the nested setting
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
- `.agents/catalog/catalog.json` records current package definitions and package digests. The generated
  [`CAPABILITIES.md`](CAPABILITIES.md) is its human-readable index. Consumers select plugins in a
  committed `.agents/plugins.json` with qualified identities and a marketplace-to-repository map; selected
  approved publishers follow `main`.
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
The launcher checks that the installed Codex advertises this option and leaves `--remote` sessions alone;
older CLIs need an update to receive this Windows workaround.
The machine profile installer removes the superseded standalone no-daemon wrapper when refreshing a
profile, so the current launcher owns the launch path.

If coordinator discovery fails, Codex plugin maintenance remains available through the normal command
on Windows and Linux. Install the current coordinator with:

```text
codex plugin marketplace add https://github.com/tj-agents/marketplace.git
codex plugin add machine@tj-agents
```

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

PR CI uses `scripts/ci_selection.py` (Python 3.9+) to classify the complete base-to-merge change.
Inert prose runs the documentation reachability check. Changes to mapped problem-record, plugin-adoption,
lock-bump, machine-verification and handoff-transfer code run their regression modules on Windows and
Linux, with generation and packaging checks. Changed test modules include their import consumers.
Unknown paths, shared infrastructure, executable guidance, binary changes, unresolved ranges and broad
changes retain the full matrix. Main always runs the full matrix. Add the `ci:full` PR label to request
full coverage; adding or removing a label reevaluates selection.

`ci-required` runs after selection, the generated-path guard and both platform jobs. It fails if
classification or any selected job fails, disappears, is cancelled or skips. Configure branch protection
to require this check when enabling server-side enforcement. Existing all-checks merge validation also
consumes its result. Selection never cancels a prior run or transfers a previous head's test success.

The `machine:plugin-selection` skill creates a repository's `.agents/plugins.json` and generates the committed
Claude and Codex plugin settings from it, so a fresh clone installs exactly what it selects from rolling main.
Selections can combine `tj-agents` and `Concertable` marketplaces without revision pins. Adoption explicitly
migrates the old single- or multi-marketplace lock, preserving selections and removing its pins.
It also audits a machine for old user-level plugin settings.

Catalog packages have no release or manifest version. `sha256-tree-v1` hashes
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

Each supported Claude and Codex terminal, handoff, and recovery launcher runs a bounded startup preflight
before starting the native CLI. It follows the selected tj-agents packages and their required dependencies
to the publishers' current `main` commits, installs and verifies the exact package files and bytes, and
blocks startup if fetching, installation, trust, verification, or the overall deadline fails. A successful
native install alone does not establish freshness. Published package bytes become available after the
post-merge `regenerate` job commits generated packages to `main`; the updater follows what is currently
published there. Running sessions retain their already-loaded instructions.

Codex gives each launch temporary native marketplace names, catalogs and package paths while keeping
its normal user profile and logical plugin selections. Verified preparation releases the refresh lock
before starting the CLI, so an idle terminal can wait for its first prompt while another CLI refreshes.
Hook trust and copied plugin policy are supplied only to that child. Its temporary paths remain until
the child is confirmed exited; uncertain child liveness preserves them.

The updater accepts only the configured tj-agents source closure. Claude permissions are synchronized
only from the current verified selected-package closure. Codex hook trust follows that same verified
closure. Startup uses disposable native install settings so selection does not leak into global settings.
Codex's automatically installed shared agents update from the selected engineering package while
preserving unowned or locally changed filename collisions. See [PACKAGING.md](PACKAGING.md) for package
content rules.

Native installation is a one-time bootstrap for packages already selected by repository or user settings.
Use Claude's plugin UI or Codex's plugin commands to install only those selected packages. Registering a
marketplace or bootstrapping one package does not select the publisher's full roster. After bootstrap,
ongoing freshness requires a supported launcher preflight. Typing `claude` in Bash on Linux or
PowerShell on Windows/Linux, `open-claude`, `handoff-claude` and session recovery run the startup preflight
first, so a session started through them loads the verified current `main` content for the selected
packages and dependencies. The machine plugin's SessionStart hook
adds one marked block to the supported terminal profiles that resolves its own `claude` wrapper, so the wrapper
updates with the plugin and no checkout is pulled; set `BASE_AGENTS_CLAUDE_PROFILE=off` to opt out.
The startup preflight refreshes selected packages and dependencies and blocks launch on failure. Claude
permissions are updated only from that current verified package closure.

Typing `codex` in Bash on Linux or PowerShell on Windows/Linux and using `handoff-codex` runs the startup
preflight for selected tj-agents packages and dependencies before Codex loads them. The launcher then
records native Codex hook trust only for the current verified package closure. Other publishers and
user/project hooks retain normal trust review.
Set `BASE_AGENTS_CODEX_HOOK_TRUST=off` to keep manual review for all hooks. The machine plugin's SessionStart hook adds a marked block
to the supported terminal profiles. That block resolves the active installed machine package at invocation time, so later
terminals load its `codex` wrapper without pulling this checkout. The first session after installing
the package wires the profiles; open a new terminal to use the wrapper. Set
`BASE_AGENTS_CODEX_PROFILE=off` to leave profiles alone. Repository and user settings determine package
selection independently of freshness.

### Recover from a faulty installed hook

A hook repair reaches a machine after it merges and the `regenerate` job commits the published package bytes
to `main`. Before that publication, the startup preflight verifies the currently published package. On Codex,
a changed package digest changes the hook definition, so the hook needs trust review again. A running session keeps the hook bytes it loaded on either host and cannot adopt the repair.
To recover one blocked by a Stop hook, send `stop` or `pause` as the whole prompt so the continuation gate releases
the turn, then close it and start a new session through the `codex` or `claude` terminal wrapper,
`handoff-codex` or `handoff-claude`. The startup preflight refreshes and verifies the selected package set;
if that fails, the CLI remains blocked until the source or selection problem is corrected.

Never edit an installed plugin cache, disable hooks, or rewrite continuation state to clear the block.

Use `machine:plugin-selection` to give a repository its own plugin selection.

Codex does not load agent definitions directly from plugins. When engineering is selected, the startup
preflight updates its shared agents in the active Codex profile. The installer preserves unowned filename
collisions and locally changed owned files; Claude loads the package's `agents/` payload directly.
