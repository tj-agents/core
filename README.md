# core

Shared agent behavior, engineering process, and machine utilities for Codex and Claude.
The canonical repository is [`tj-agents/core`](https://github.com/tj-agents/core).
Select `base@tj-agents`, `engineering@tj-agents` and `machine@tj-agents` from
[`tj-agents/marketplace`](https://github.com/tj-agents/marketplace).
The repository publishes a minimal `base` package and optional `engineering` and `machine` packages.
Stack standards remain in their stack plugins; Concertable policy stays with Concertable.
The repository also owns machine setup: `./setup.ps1` or `./setup.sh` is the one entry point.

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
Known bugs, mistakes and debt are [GitHub issues](https://github.com/tj-agents/core/issues).
The [recording contract](.agents/engineering/resources/problem-records.md) routes remote work-item
operations to the repository's explicitly selected profile. Personal owns GitHub records; Infonetica owns
Azure Boards records and native type policy. Core owns the shared SQLite agent execution/session registry
and reusable engineering lifecycles. Installing Engineering does not select or install a recording
profile. Missing selection retains unsent facts with a resolver and resume condition; historical Markdown
registers remain evidence only.
Packaged SessionStart hooks deliver context and PreToolUse hooks gate routed writes. Their Python 3.9+
interpreter follows the host manifest: Codex uses `python3` on Linux/macOS and `python` on Windows; Claude's
current manifest uses `python` on all platforms. Keep the configured executable on PATH. Codex skips new or
changed plugin hooks until they are reviewed and trusted in `/hooks`; a fresh missing-marketplace write
probe is required before claiming enforcement. The host coverage limit is tracked in
[core#402](https://github.com/tj-agents/core/issues/402). The `base:agent-files` skill documents a generated native-instruction
fallback.
Codex hook commands use a per-session temporary snapshot preseeded for the running session's hooks.
This lets those hooks keep running after a plugin update replaces an inactive package cache entry.
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
- `setup.ps1` and `setup.sh` wrap `.agents/machine/scripts/setup_machine.py`, which installs the profile,
  the hidden Git Bash proxy and everything else this machine needs.

### Windows CLI hook windows

Pass `--no-daemon` to an interactive Codex launch on Windows to avoid the shared daemon's visible hook
child consoles.

If coordinator discovery fails, Codex plugin maintenance remains available through the normal command
on Windows and Linux. Install the current coordinator with:

```text
codex plugin marketplace add https://github.com/tj-agents/marketplace.git
codex plugin add machine@tj-agents
```

Claude Code can open a visible Git Bash window for each hook. On Windows, setup builds the included
GUI-subsystem Bash proxy in the main checkout's `shell/` with Clang or GCC when it is missing or older
than its source, and sets the user `CLAUDE_CODE_GIT_BASH_PATH` and `TJ_AGENTS_REAL_GIT_BASH` variables.
The profile loads it in new PowerShell sessions. The proxy forwards standard handles and the exit code
to the real Git Bash. If Git Bash lives outside `C:\Program Files\Git\bin\bash.exe`, set the user-level
`TJ_AGENTS_REAL_GIT_BASH` environment variable to its absolute path before running setup. Claude
processes that launch `git.exe` directly bypass this Git Bash workaround and require an upstream host fix.

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

Run setup from any checkout or worktree of this repository. Rerunning it converges: each step checks
first and writes only on drift, so a current machine is left untouched. `--check` reports drift, writes
nothing and exits 1 when something would change:

```text
./setup.ps1          # Windows (PowerShell)
./setup.sh           # Linux (bash and python3)
./setup.ps1 --check  # report drift only
```

Installed paths always point at the main checkout (the parent of `git rev-parse --git-common-dir`),
never the worktree that ran setup. In order, setup verifies the saved `gh` login, configures the event
channel and publishers, and enables Claude's native auto-update. It removes the retired machine event
listener task or systemd service and the former hourly plugin-autoupdate and merge-gates tasks or cron
entries, then copies the launch-check runtime to `~/.agents-state/bin`. It writes one
`# >>> tj-agents >>>` block into both PowerShell profiles on Windows, and into `~/.bashrc`, `~/.zshrc` or
the PowerShell profile that exists on Linux. The block defines the `claude` and `codex` functions and, on
Windows, loads the main checkout's `shell/profile.ps1`. It replaces older profile and launcher blocks in
place, keeps other lines, encoding and BOM, and keeps one `.pre-tj-agents.bak` copy of a changed profile.
On Windows setup then builds the hidden Git Bash proxy. On both
platforms it delivers Codex profile agents with `pwsh` when Codex is set up, catches up plugins and merge
policies for repositories whose default branch moved since the last catch-up, converges installed
packages' declared harness permissions (removing owned rules that are no longer declared), removes
retired Codex configuration and migrates the old agent delivery manifest. Nothing runs in the background.

Each `claude`, `codex`, handoff and open launch runs `launch_check.py` first: one non-blocking ntfy.sh
poll for events since the saved cursor. With none it starts the CLI immediately; offline it starts anyway.
With events it updates, on both hosts in parallel, only the marketplaces and enabled plugins that list or
publish the named repositories, and advances the cursor once both hosts succeed. A failed host retries on
a later launch, at most hourly. `machine:reload-plugins` runs the same check in a running session.

Main-branch callers publish events through the shared
`tj-agents/github-actions/.github/actions/machine-events` publisher. Setup reuses or creates the
unguessable `MACHINE_EVENTS_TOPIC` Actions variable on core, configures the same variable for active
repositories in tj-agents, Concertable and tomjseery, and saves it in `~/.agents-state/machine-events.json`.
The same value is stored as an Actions secret for callers, so public run logs mask it.
The topic is an untrusted public hint channel; it contains only repository names and change categories.
No administrative GitHub credential is stored in Actions.

Setup's catch-up runs `machine_events.py` once, which re-reads GitHub and invokes the
installed github-actions plugin's `merge-policy reconcile` for committed policy changes as Tommy's saved
`gh` account. Install that plugin before setup. Launches do not reconcile merge policy; run
`machine_events.py --repo <owner/name>` after a policy change.

A Codex upgrade first snapshots each installed hook package, so a running Codex session keeps calling the
hooks it started with. Only packages whose hook loader still reads the cache first wait for running Codex
sessions to exit.

Catch-up logs rotate at `~/.agents-state/machine-events.log`. Package regeneration jobs publish a second
hint after pushing generated packages because GitHub's own token cannot trigger another push workflow.
Repository enrollment is explicit: merge the uniform caller only into an approved personal repository.
The generic service scaffold does not generate it. GitHub Free's repository ruleset limitations still
apply to private repositories.

Published package bytes reach `main` after the post-merge `regenerate` job. Running sessions keep what they
loaded; new sessions pick up the update.

### Refresh and repository boundaries

An event refresh updates the installed bytes of plugins already selected by trusted project or user
configuration. Those shared tools can also serve employer projects that select them. A refresh does not
adopt the personal profile, generate project workflows or apply a merge policy to every project that uses
GitHub Actions. Running sessions retain their loaded instructions and hook snapshots.

The personal event publishers and automatic ruleset reconciliation are restricted to `tj-agents`,
`Concertable` and `tomjseery`. Hints request a GitHub re-read, and only a changed, committed
`.github/merge-policy.json` can trigger that repository's ruleset reconciliation. Publisher adoption is
owned by [github-actions:machine-events](https://github.com/tj-agents/github-actions/blob/main/.agents/github-actions/utility/machine-events/SKILL.md);
the policy writer also enforces its owner boundary before GitHub access.

Personal is for explicitly adopted personal projects only. A GitHub owner or permission to commit agent
configuration does not establish personal scope. Infonetica is work scope, including the
`tj-agents/infonetica` plugin source repository and all its worktrees; never select or inject Personal
there. Read the target repository's README.md and AGENTS.md before choosing its policy profiles.

Repository plugin adoption follows
[machine:plugin-selection](.agents/machine/utility/plugin-selection/SKILL.md). Employer-project agent
settings use its local scope and Git metadata exclusions. The local writer resolves the exact checkout
and `git rev-parse --git-path info/exclude`, including shared Git metadata for linked worktrees; it refuses
tracked local targets. A home directory, current branch or linked worktree is not permission to adopt a
personal profile. For example, a linked worktree of an employer repository still receives local agent
settings, with no personal publisher or personal merge rules.

Setup installs one launch check per machine user, independent of the checkout or worktree used to invoke it.
Launch checks and catch-up do not edit or remove worktrees. The separate
[merge cleanup workflow](.agents/engineering/workflow/merge/SKILL.md) owns worktree cleanup and its proof
requirements. The machine event fixtures cover both event and catch-up paths without launching agents.

### Recover from a faulty installed hook

A hook repair reaches a machine after it merges, the `regenerate` job publishes it to `main`, and the next
automatic update installs it. On Codex, a changed package digest changes the hook definition, so the hook
needs trust review again. A running session keeps the hook bytes it loaded; start a new session.

Never edit an installed plugin cache, disable hooks, or rewrite continuation state to clear the block.

## Repository plugin selection

Use `machine:plugin-selection` to commit `.agents/plugins.json`, `.claude/settings.json` and
`.codex/config.toml`. Claude declares `extraKnownMarketplaces` with `autoUpdate: true` and
`enabledPlugins`. Codex declares `[marketplaces]` and `[plugins]` in trusted project configuration.
Native admission, installation, credentials and caches remain host responsibilities.

Handoff, open and recovery launchers start the native CLI without refreshing plugins, generating
packages or rewriting host configuration. They retain handoff startup acknowledgement and recovery
pickup verification. Running sessions retain the instructions they already loaded.

On Codex 0.163.0-alpha.1, declarations make a plugin discoverable but do not install it in an empty
profile. `codex plugin add <plugin>@<marketplace>` installs the native cache and writes a user enabled
entry. An installed cache can subsequently load solely from trusted project declarations. Generated
settings alone do not prove fresh-machine installation. See the current
[cutover acceptance record](plans/repo-declared-config/CUTOVER.md).

Automatic updates belong to Claude's native updater and the background updater installed by `setup.ps1`.
The scheduled Codex updater also installs missing declared plugins after a repository has native trust.
Its native `plugin add` commands maintain the host's required user installation entries automatically;
repository settings remain the authored selection. Codex currently provides no cache-only install scope.
Nothing updates packages in the launch path.

For an explicit native refresh use `machine:reload-plugins`. Its default performs native marketplace
and plugin updates; remote revision verification is opt-in and prints progress. `/reload-plugins`
adopts updates in an open Claude session; start a new Codex session to load updated packages.

Codex does not load agent definitions directly from plugins. Setup delivers them to the Codex profile
with the engineering package's `scripts/install-codex-agents.ps1`; launcher startup no longer copies
agents or records hook trust. Native hook trust review still applies. Claude loads the package's
`agents/` payload directly.
