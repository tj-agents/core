# core

Shared agent behavior, engineering process, and machine utilities for Codex and Claude.
The canonical repository is [`tj-agents/core`](https://github.com/tj-agents/core).
Select `base@tj-agents`, `engineering@tj-agents` and `machine@tj-agents` from
[`tj-agents/marketplace`](https://github.com/tj-agents/marketplace).
The repository publishes a minimal `base` package and optional `engineering` and `machine` packages.
Stack standards remain in their stack plugins; Concertable policy stays with Concertable.
The repository also owns explicit PowerShell profile and CLI session-recovery installation.

`engineering:skill-authoring` owns skill selection triggers, names, and sizing; the
[`template:check` validator](https://github.com/tj-agents/template) owns required skill content and layout
validation. `engineering:docs` owns the generic guidance-writing convention.

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
The [shared recording contract](.agents/engineering/resources/problem-records.md) routes future bugs,
mistakes, debt, features and tasks to Work Items. `work-items:write-issue` classifies a recording request
and delegates to the corresponding specific writer; failure does not fall back to root problem-register
files. The problem address workflows reuse the existing repair lifecycle.
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

Use `machine:hook-control` for reversible Codex hook controls on the active user profile.
Add `--scope project --project <repository>` for a trusted repository's `.codex/config.toml`.
The utility requires Python 3.11+. `off` writes the native
[`features.hooks = false` gate](https://learn.chatgpt.com/docs/hooks#turn-hooks-off), which prevents ordinary
lifecycle hooks from starting, including hooks introduced by later plugin updates. `on` restores the
previous gate value or absence; it preserves individually disabled hooks and trust metadata. Plugins and
skills remain enabled. A higher-priority project, profile, command-line or managed setting may override
the selected layer; status describes saved settings, and reopening Codex is required to rely on the change.
Internal host cleanup hooks and the separate legacy `notify` command are outside this gate.

The packages have no release line or compatibility promise: machines follow each publisher's `main`
through automatic updates (see [Machine setup and updates](#machine-setup-and-updates)). Selection stays an
independent user and repository setting; adding a marketplace does not select its full roster.

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

Pass `--no-daemon` to an interactive Codex launch on Windows to avoid the shared daemon's visible hook
child consoles.

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

## Machine setup and updates

Run once per machine, and again whenever you like; it changes nothing that is already set:

```powershell
./setup.ps1          # Windows (pwsh or Windows PowerShell)
pwsh ./setup.ps1     # Linux
```

It turns on Claude's own auto-update for every marketplace an enabled plugin comes from, removes the
retired `claude`/`codex` profile launcher, and schedules `plugin_autoupdate.py` hidden at logon and hourly
(Task Scheduler on Windows, crontab on Linux). Each run checks every Codex git marketplace that an enabled
plugin comes from with one `git ls-remote`, and upgrades the marketplace and re-adds its enabled plugins only
when the revision changed. Nothing runs when `claude` or `codex` starts.

Published package bytes reach `main` after the post-merge `regenerate` job. Running sessions keep what they
loaded; new sessions pick up the update. `install.ps1` still wires the Windows `shell/` profile.

### Recover from a faulty installed hook

A hook repair reaches a machine after it merges, the `regenerate` job publishes it to `main`, and the next
automatic update installs it. On Codex, a changed package digest changes the hook definition, so the hook
needs trust review again. A running session keeps the hook bytes it loaded; start a new session.

Never edit an installed plugin cache, disable hooks, or rewrite continuation state to clear the block.

Use `machine:plugin-selection` to give a repository its own plugin selection.

Codex does not load agent definitions directly from plugins. When engineering is selected, the startup
preflight updates its shared agents in the active Codex profile. The installer preserves unowned filename
collisions and locally changed owned files; Claude loads the package's `agents/` payload directly.
