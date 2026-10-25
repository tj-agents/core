# core

Shared agent behavior, engineering process, and machine utilities for Codex and Claude.
The canonical repository is [`tj-agents/core`](https://github.com/tj-agents/core).
Select `base@tj-agents`, `agent-store@tj-agents`, `machine@tj-agents`, `workflow@tj-agents` and `engineering@tj-agents` from
[`tj-agents/marketplace`](https://github.com/tj-agents/marketplace).
The repository publishes Base, Agent Store, Machine, Workflow and Engineering packages. Agent Store owns recorded
execution/session state; Machine observes and operates native hosts; Engineering owns code work and delivery.
Stack standards remain in their stack plugins; Concertable policy stays with Concertable.
The repository also owns explicit PowerShell profile and CLI session-recovery installation.

## Required setup on every machine

For authorized machine setup or Core delivery, the agent owns this procedure through execution and
verification, including post-merge publication, setup and sync. Run the supported commands, repair failed
steps and report observed results; handing Tommy commands to execute does not complete work the agent
can perform. A genuinely user-owned credential or native trust action retains its existing control;
keep the remaining deployment work owned and resume it when that dependency is resolved.

Installing the plugins or cloning this repository does **not** complete machine setup. From a current
primary Core checkout, run the full setup on each PC before relying on automatic plugin refresh:

```powershell
# Windows, from the Core checkout
./setup.ps1
./setup.ps1 --check
```

```bash
# Linux, from the Core checkout
./setup.sh
./setup.sh --check
```

Both commands must finish successfully. A permissions-only `--step` run is a scoped repair, not full
setup. Full setup owns the event channel, publisher configuration, launch runtime, shell profiles and
catch-up. Wrapper files alone do not prove the event channel is configured.

Open a fresh terminal so its profile loads. In PowerShell, `Get-Command claude,codex` must resolve the
managed functions; in bash/zsh, `type claude codex` must show the managed shell functions. Verify the
installed launch check without starting an agent, from a repository that selects its standards:

```powershell
python -B "$HOME/.agents-state/bin/launch_check.py" --host codex --project (Get-Location).Path
python -B "$HOME/.agents-state/bin/launch_check.py" --host claude --project (Get-Location).Path
```

On Linux, use `python3` and `--project "$PWD"`. Setup is complete only when the full `--check` exits zero,
both fresh-terminal launch checks succeed, and required hooks execute successfully. A version string or
an `unconfigured` update check is not completion evidence. If setup or verification fails, keep ordinary
work blocked, diagnose the failed step and rerun the supported setup; do not silently continue on stale
machine state. [Machine setup and updates](#machine-setup-and-updates) explains the owned steps and scope.

After a Core change merges, wait for the post-merge regeneration job to publish its packages on `main`,
update the primary Core checkout, then rerun the full setup and verification above to deploy machine
runtime changes. Normal `claude` and `codex` launches check for published updates automatically. For an
immediate explicit refresh from the Core checkout, run:

```powershell
./sync.ps1 --verify
```

```bash
./sync.sh --verify
```

`machine:sync-plugins` owns adoption in a running session, including resuming the same conversation when
native reload is unavailable. The agent runs explicit sync whenever an immediate refresh is needed.

`engineering:skill-authoring` owns skill selection triggers, names, and sizing; the
[`template:check` validator](https://github.com/tj-agents/template) owns required skill content and layout
validation. `engineering:docs` owns the generic guidance-writing convention.

Global architecture and cross-repository designs live in [`tj-agents/docs`](https://github.com/tj-agents/docs)
(private; organization access required). Core-specific implementation plans and operational documentation
stay here; shared plans link to their source owners.

`workflow:plan-artifacts` makes substantive plans maintained Markdown files, including outside a repository.
`base:agent-files` keeps `AGENTS.md` and `CLAUDE.md` paired with one shared instruction source.
[`base:idea-initialization`](.agents/base/policy/idea-initialization/SKILL.md) owns the once-per-idea
assessment of existing capabilities and solutions; [`workflow:run`](.agents/workflow/workflow/run/SKILL.md)
owns continued goal ownership and carries that recorded decision forward.
The richer planning workflows are selected engineering conventions, not prerequisites for standalone plans.
Known bugs, mistakes and debt follow the selected problem-record profile.
The [recording contract](.agents/workflow/resources/problem-records.md) routes remote work-item
operations to the repository's explicitly selected profile. Personal owns GitHub records; Infonetica owns
Azure Boards records and native type policy. Core publishes the shared SQLite registry as Agent Store, generic work status as Workflow, and reusable
engineering lifecycles as Engineering. Installing Engineering does not select or install a recording
profile. Missing selection retains unsent facts with a resolver and resume condition; historical Markdown
registers remain evidence only.
Packaged SessionStart hooks deliver context and PreToolUse hooks gate routed writes. Their Python 3.9+
interpreter follows the host manifest: Codex uses `python3` on Linux/macOS and `python` on Windows; Claude's
current manifest uses `python` on all platforms. Keep the configured executable on PATH. Codex skips new or
changed plugin hooks until they are reviewed and trusted in `/hooks`; a fresh missing-marketplace write
probe is required before claiming enforcement.
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

## Agent Store ownership

[Agent Store inspection](.agents/agent-store/utility/inspect/SKILL.md) reads recorded work items,
sessions, owners and external references without creating or migrating the database. Its JSON labels
process liveness as unobserved. Machine's native recovery checks processes and worktrees before opening
a session; the store serializes ownership changes and preserves the existing schema and identities.

The store runtime is authored once under `.agents/agent-store/runtime/`. Agent Store, Machine and
Engineering receive generated package-local copies through the [resource contract](PACKAGING.md).
A package never imports a sibling plugin installation. Machine's hooks remain the native event adapters.

```text
Machine -> Base + Agent Store
Engineering -> Base + Agent Store + Machine
Agent Store inspection -> existing sessions.db, read-only JSON
```

These are source package relationships. The central marketplace roster and native installation must
also contain a package before a selected host can discover it; successful source generation is not
installed activation.

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

An explicit `design` value overrides `all`, and omitted members default to `false`; an empty
`auto_approve` object disables design approval. When enabled, an agent may make and record routine design
or convention choices within work already authorized by the user. It does not override an explicit user
reservation, task scope, stricter repository rule, or any merge, publication, installation, or permission
gate. Source verification does not establish installed-host trust or acceptance.

## Layout

- `.agents/` is the canonical host-neutral source. Base, Agent Store, Machine, Workflow and Engineering ownership is expressed
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
- setup.ps1 and setup.sh install the machine runtime and shell profiles; cli-session-recovery provides its own installer.

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
Selections can combine `tj-agents` and `Concertable` marketplaces without revision pins.

Catalog packages have no release or manifest version. `sha256-tree-v1` hashes
the sorted package paths, lengths and bytes. The machine package excludes only its embedded
`catalog/catalog.json` from its own digest to avoid a self-reference; its schemas, bootstrap and all other
resources remain covered.

## Machine setup and updates

Core's portable permission preference is an enum in `.agents/settings.json`:

```json
{"configuration":{"core":{"permissions":"bypass"}}}
```

`bypass` is the default, including when the setting is omitted. `standard` opts into normal native
permission checks. Machine setup installs the preference into both user profiles. Cloning Core carries the
declaration; running its existing setup applies the same defaults on another Windows or Linux machine.

| Shared mode | Claude user-profile `permissions.defaultMode` | Codex `approval_policy` | Codex `default_permissions` |
|---|---|---|---|
| `bypass` | `bypassPermissions` | `never` | `:danger-full-access` |
| `standard` | `default` | `on-request` | `:workspace` |

Claude 2.1.257+ ignores bypass in project and local settings. Repository generation therefore inherits
Claude's installed user default for `bypass`, and emits `default` for the supported `standard` project
override. It never treats a committed bypass value as effective activation. Codex supports either mode
in trusted repository settings. Run the same machine setup after cloning on another machine; no
machine-specific permission list or hand-edited host profile is needed.

Run setup with `--step "native permission defaults"` for only this repair, or add `--check` to inspect
drift without writing. Existing model, plugin, hook and trust settings are preserved. The mapping migrates
legacy Codex sandbox keys instead of combining incompatible configuration formats. Managed host policy,
initial project trust and an explicit session selection remain authoritative; changing a default does
not change an already-running restricted session. Merge authorization is configured separately.

The desktop app can retain a local host-mode override separately from `config.toml`. Setup removes
that saved local override so new desktop chats follow the configured permission profile, including
repository-specific `standard` settings. Remote host preferences and existing chat permissions remain
intact. Close Codex Desktop before running this setup step from a terminal, then reopen it. Setup
refuses to rewrite the app state while the app is running, because its cached state could undo the change.
For example, a saved `guardian-approvals` mode must not keep new chats restricted after Core installs
`bypass`; clearing that override lets the configured `:danger-full-access` profile take effect.

Native settings: [Codex](https://developers.openai.com/codex/config-reference/),
[Claude Code](https://code.claude.com/docs/en/permissions).

Follow [Required setup on every machine](#required-setup-on-every-machine) for the full installation and
fresh-terminal verification. Rerunning setup converges on the same channel and launch configuration.

Repeat `--step` to select existing setup steps for a scoped repair. They retain their declared order
and always include required preconditions. Selecting shell profiles also includes their launch-check
runtime dependency. `--check` inspects that same selection without applying it:

```text
./setup.ps1 --check --step "launch-check runtime" --step "shell profiles"  # Windows
./setup.sh --check --step "launch-check runtime" --step "shell profiles"   # Linux
```

The full setup enables Claude's native auto-update, copies the launch-check runtime to `~/.agents-state/bin` and
adds `claude` and `codex` functions to the PowerShell profiles (and `~/.bashrc` or `~/.zshrc` on
Linux) inside one marked block, keeping a `.pre-tj-agents.bak` copy. Nothing runs in the background.

After native installations are verified, setup also runs each selected plugin's declared `requires.setup` helper.
Its `setup --check` is always read-only; ordinary setup may converge a ready installation, while a browser or human
enrollment helper runs only with explicit `./setup.ps1 --onboard` or `./setup.sh --onboard`. `--onboard` and
`--check` are mutually exclusive. Explicit sync also converges selected setup; use `./sync.ps1 --onboard`
or `./sync.sh --onboard` for enrollment. `--verify-only` checks without applying setup and rejects `--onboard`.

Each `claude`, `codex`, handoff and open launch runs `launch_check.py` first: one non-blocking ntfy.sh
poll for events since the saved cursor; offline it starts anyway. Events name the publishing repositories.

Repository-required standards are a separate, blocking check. Before starting the native host,
the shell and handoff launchers compare every identity in `.agents/plugins.json` with that host's
enabled native installations for the exact project. A missing, disabled, broken or wrong-project
installation refuses the launch with the required identities. An unavailable verifier also refuses
the launch. This does not depend on a Python, .NET or other stack-specific route, and another host's
cached files are insufficient. The write router repeats admission before discovering plugin routes,
so a missing plugin cannot silently remove its own standards from enforcement. Read-only diagnosis
remains available. Offline optional update polling does not invalidate already verified installations.

Claude inventory receives launch-specific settings, setting sources and plugin paths. Codex's native
inventory does not apply session activation overrides, so selected repositories refuse CLI profile,
feature and non-model configuration overrides that cannot be verified. Persist those settings in the
repository configuration instead. Model and reasoning overrides remain available; help, version and
native maintenance commands remain available to repair an installation.

For example, selecting `example@tj-agents` while it is absent from Codex's inventory prevents a
Codex launch and file writes even if its `tier.json` and routes are entirely missing. Repair the
selection/install and start a fresh session; copying a Claude cache directory does not satisfy it.

A GitHub query per repository reads its head and each plugin directory's tree into `~/.agents-state/plugin-heads.json`,
both hosts update in parallel, and the cursor advances once both succeed. A failed host retries on the next
launch; a cursor older than ntfy's retention compares every publisher instead. Every launch except `codex` then compares
this project's Claude installs with the recorded heads from local files only, and updates an install only
when its plugin directory differs at the head; each install is tried at most once per head, so a failure waits
for the next head. A project install is skipped when a nested worktree's install below it is listed first,
because Claude's CLI then updates the nested one. Codex re-adds a plugin only when its directory changed. Without GitHub content, both compare commits.
`machine:sync-plugins` runs the same check in a running session.

Main-branch callers publish events through the shared
`tj-agents/github-actions/.github/actions/machine-events` publisher. Setup reuses or creates the
unguessable `MACHINE_EVENTS_TOPIC` Actions variable on core, configures the same variable for active
repositories in tj-agents, Concertable and tomjseery, and saves it in `~/.agents-state/machine-events.json`.
The same value is stored as an Actions secret for callers, so public run logs mask it.
The topic is an untrusted public hint channel; it contains only repository names and change categories.
No administrative GitHub credential is stored in Actions.

Setup ends with one catch-up through `machine_events.py`, which re-reads GitHub and invokes the
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
loaded; follow `machine:sync-plugins` for adoption and the required recovery verification.

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
automatic update installs it. Codex launch and refresh verify published package contents, apply trust only
to verified current hook hashes, and read back required-hook readiness. Failed readiness blocks ordinary
work; native plugin maintenance remains available for recovery. A running session keeps the hook bytes it
loaded. Use `machine:sync-plugins` to recover, and verify the affected hooks actually execute successfully.
If native reload is unavailable, resume the same conversation by its exact session ID and directory.
Keep ownership and leave the conversation open for that user action; do not launch a successor merely
to change directory or reload hooks. `base:cd` owns the native directory-change fallback.

Never edit an installed plugin cache, disable hooks, or rewrite continuation state to clear the block.

## Repository plugin selection

Use `machine:plugin-selection` to commit `.agents/plugins.json`, `.claude/settings.json` and
`.codex/config.toml`. Claude declares `extraKnownMarketplaces` with `autoUpdate: true` and
`enabledPlugins`. Codex declares `[marketplaces]` and `[plugins]` in trusted project configuration.
Native admission, installation, credentials and caches remain host responsibilities.

Shell, handoff, open and recovery launchers use the shared launch check before starting the native CLI.
They do not independently generate packages or rewrite repository configuration. Handoff startup
acknowledgement and recovery pickup verification remain separate from refresh and required-hook
readiness. Running sessions retain the instructions and hook definitions they already loaded.

On Codex 0.163.0-alpha.1, declarations make a plugin discoverable but do not install it in an empty
profile. `codex plugin add <plugin>@<marketplace>` installs the native cache and writes a user enabled
entry. An installed cache can subsequently load solely from trusted project declarations. Generated
settings alone do not prove fresh-machine installation. See the current
[cutover acceptance record](plans/repo-declared-config/CUTOVER.md).

The [machine setup and update flow](#machine-setup-and-updates) owns automatic launch checks and explicit
refresh. Codex's native `plugin add` commands maintain required user installation entries; repository
settings remain the authored selection. Codex currently provides no cache-only install scope.

Codex does not load agent definitions directly from plugins. Core setup owns their profile installation;
Claude loads the package's `agents/` payload directly. Codex launch and refresh verify required hook trust
as described under [faulty-hook recovery](#recover-from-a-faulty-installed-hook).
