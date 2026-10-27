# core

Core authors and publishes the `base`, `workflow`, `engineering` and `docs` plugins for Codex and Claude, from
[`tj-agents/core`](https://github.com/tj-agents/core) through
[`tj-agents/marketplace`](https://github.com/tj-agents/marketplace).

- `base` is always-on agent behavior: routing, project setup, solution assessment and paired agent files.
- `workflow` is goal and plan ownership: plans, runs, resumption, status and handoff.
- `engineering` is the software lifecycle: features, bug fixes, review, committing, PRs and merging.
- `docs` is how pages people read are laid out.

Core does not own agent sessions, recovery, refresh or machine installation (`tj-agents/agent`), CLI and OS
mechanics such as closing terminals or the clipboard (`tj-agents/cli`), plugin generation and checks
(`tj-agents/template`), or stack standards (their stack repositories). Agent runtime reaches Core only as the
staged, git-ignored `.agents/dependencies/` export.

Marketplace owns the canonical plugin roster and dependency graph in
[`plugins.json`](https://github.com/tj-agents/marketplace/blob/main/plugins.json). Do not edit plugin names
or dependencies in Core.

`engineering:skill-authoring` owns skill selection triggers, names, and sizing; the
[`template:check` validator](https://github.com/tj-agents/template) owns required skill content and layout
validation. `engineering:docs` owns the generic guidance-writing convention.

Global architecture and cross-repository designs live in [`tj-agents/docs`](https://github.com/tj-agents/docs)
(private; organization access required). Core-specific implementation plans and operational documentation
stay here; shared plans link to their source owners.

`workflow:plan-artifacts` makes substantive plans maintained Markdown files, including outside a repository.
`base:agent-files` keeps `AGENTS.md` and `CLAUDE.md` paired with one shared instruction source.
[`base:project-setup`](.agents/base/policy/project-setup/SKILL.md) owns standards selection for new
repositories and new technology stacks, including the personal/work scope question.
[`base:solution-assessment`](.agents/base/policy/solution-assessment/SKILL.md) owns the once-per-idea
assessment of existing capabilities and solutions; [`workflow:run`](.agents/workflow/workflow/run/SKILL.md)
owns continued goal ownership and carries that recorded decision forward.
The richer planning workflows are selected engineering conventions, not prerequisites for standalone plans.
Known bugs, mistakes and debt follow the selected problem-record profile.
The [recording contract](.agents/workflow/resources/problem-records.md) routes remote work-item
operations to the repository's explicitly selected profile. Personal owns GitHub records; Infonetica owns
Azure Boards records and native type policy. Agent publishes the shared SQLite registry as Agent Store;
Core publishes generic work status as Workflow and reusable engineering lifecycles as Engineering.
Installing Engineering does not select or install a recording
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


The packages have no release line or compatibility promise: machines follow each publisher's `main`
through automatic updates. Selection stays an
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

An explicit `design` value overrides `all`, and omitted members default to `false`; an empty
`auto_approve` object disables design approval. When enabled, an agent may make and record routine design
or convention choices within work already authorized by the user. It does not override an explicit user
reservation, task scope, stricter repository rule, or any merge, publication, installation, or permission
gate. Source verification does not establish installed-host trust or acceptance.

## Layout

- `.agents/` is the canonical host-neutral source for Base, Workflow, Engineering and Docs.
- `.codex/` contains only Codex entry points and host configuration; `.claude/` contains only Claude entry
  points and host configuration. Their skills reference canonical `.agents/` definitions.
- [`SOURCE_LAYOUT.md`](SOURCE_LAYOUT.md) defines the source, adapter and distribution boundary.
- [`SKILL_KINDS.md`](SKILL_KINDS.md) defines the shared skill taxonomy.
- [`PACKAGING.md`](PACKAGING.md) is the rule that a utility skill's runtime dependencies ship with it.
- `.agents/plugins/plugins.json` records Core's package definitions and digests. The generated
  [`CAPABILITIES.md`](CAPABILITIES.md) is its human-readable index.
- `plugins/*` is generated distribution output assembled from canonical shared definitions and the
  selected host adapter. Nothing under it is an authored source.

A PR carries authored sources only. CI's guard job rejects generated paths, PR CI regenerates its own
workspace before testing, and the post-merge `regenerate` job commits the refreshed `plugins/*`,
plugin digests, marketplace bridges and `CAPABILITIES.md` to main. To refresh a local tree for tests,
run the same two commands and leave their output uncommitted:

```powershell
python -B scripts/update_plugin_digests.py
pwsh .agents/sync-generated.ps1
```

The Windows and Linux test suites run only on a PR labelled `ci:full`; every other PR and main run
selection, the generated-path guard and guidance examples. With the label, `scripts/ci_selection.py`
(Python 3.9+) classifies the PR's own change from its merge base. Inert prose runs the documentation
reachability check. Changes to mapped problem-record and handoff-transfer code run their regression modules on Windows and Linux, with generation and packaging
checks. Changed test modules include their import consumers. Unknown paths, shared infrastructure,
executable guidance, binary changes, unresolved ranges and broad changes run the full matrix. Adding or
removing the label reevaluates selection.

`ci-required` runs after selection, the generated-path guard and both platform jobs. It fails if
classification or any selected job fails, disappears or is cancelled, or skips on a `ci:full` PR. Configure branch protection
to require this check when enabling server-side enforcement. Existing all-checks merge validation also
consumes its result. Selection never cancels a prior run or transfers a previous head's test success.

Repositories select plugins with `agent:plugins`, and machines are installed by Agent's `install`; see
[`tj-agents/agent`](https://github.com/tj-agents/agent).

Plugin roster entries have no release or manifest version. `sha256-tree-v1` hashes the sorted package paths,
lengths and bytes of each package.
