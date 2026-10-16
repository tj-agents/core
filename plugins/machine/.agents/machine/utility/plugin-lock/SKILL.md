---
name: plugin-lock
description: Create or bump a repository's plugin lock and generate its Claude and Codex plugin settings. Use when adopting plugins for a repository or stack, moving repositories to another marketplace tag, or auditing a machine before removing old user-level plugin settings.

kind: utility
domain: machine
route: infer
---

# Plugin lock

The commands below show Windows paths and use `python` in Windows PowerShell. On Linux/macOS, use
`python3` with POSIX paths and the same script arguments.

A repository commits `.agents/plugins.lock.json`, `.claude/settings.json` and `.codex/config.toml`. A fresh
clone then installs exactly the plugins it selects, pinned to its declared immutable marketplace revisions, without
depending on any machine's user settings. User scope holds only `base`, `engineering` and `machine`, the
bootstrap that creates repositories.

## The lock

```json
{"schema_version": 3,
 "marketplaces": {
   "tj-agents": {"repository": "tj-agents/marketplace", "revision": "v1.0.0"},
   "agents":    {"repository": "Concertable/agents",    "revision": "<full commit>"}},
 "plugins": ["base@tj-agents", "engineering@tj-agents", "machine@tj-agents",
             "dotnet@tj-agents", "concertable@agents"]}
```

A lock names each marketplace it installs from and selects plugins as `<plugin>@<marketplace>`. A marketplace
knows nothing about the repositories that use it; only the consuming repository's lock combines them. The
`tj-agents` marketplace, when selected, must be `tj-agents/marketplace`; another marketplace must be a GitHub
repository owned by `tj-agents` or `Concertable`, its key is the name that marketplace declares for itself, and
every declared marketplace must supply at least one plugin. `revision` is a `vN.N.N` tag or a full lowercase
commit. The lock must include one complete Core triplet: `base`, `engineering` and `machine` from
`tj-agents`, or from the `base-agents` producer pinned to `tj-agents/core`. Mixed Core identities fail
validation. Stack dependencies remain explicit. The schema is `catalog/plugins.lock.schema.json`.

## Adopt a stack

```powershell
python -B '<skill-directory>\scripts\adopt_plugins.py' --root C:\path\to\repository `
  --stack dotnet --marketplace-revision v1.0.0 --mode preview
```

A stack (`dotnet`, `azure`, `react`, `cpp-gcc`, `cpp-msvc`, `win32`, `neovim`, `rust`, `github-actions`,
`plugin-repository`) resolves to its `tj-agents` plugins through `scripts/plugin_roster.json`, so nobody guesses which
plugins a project type needs. Repeat `--stack`, or add `--plugin <name>`. Core and each plugin's required
plugins are always added, existing selections and the existing revision are kept, and a new lock needs
`--marketplace-revision`. `preview` lists the changed files, `write` applies them together, and `check`
exits nonzero on drift, which is what CI runs. An unknown stack or plugin is rejected with the valid choices.

## Preserve a producer Core installation

For a project using Core's producer identity, select it explicitly and pin its producer marketplace:

```text
python -B <skill-directory>/scripts/adopt_plugins.py --root <repository> --core-marketplace base-agents --marketplace base-agents=tj-agents/core@<immutable-revision> --mode write
```

On Linux/macOS use `python3`. Later extensions preserve this choice. New aggregate locks retain the
existing default and require `--marketplace-revision`; a stack plugin selected from the aggregate
also needs that pin. Explicit conversion replaces only the old Core triplet, retaining other plugins
and marketplace pins. An old marketplace is removed only if it supplies no remaining plugin. This
writes project settings only. It never changes user installations or disables a differently named
global copy; inspect actual host selections before conversion and keep one identity enabled.

## Generate settings from an existing lock

```powershell
python -B '<skill-directory>\scripts\repo_config.py' --root C:\path\to\repository --mode write
```

`--lock` defaults to `<root>/.agents/plugins.lock.json`. The generator owns Claude's marketplace,
enabled-plugin and `permissions.allow` keys and Codex's marketplace and plugin tables plus
`.codex/rules/agent-harness.rules`; other project settings stay. Existing Claude allow entries outside the
declared harness must move into `.agents/repository-harness.json` first. Project scope also rejects
machine-specific absolute paths (Windows drive and UNC paths, `/home/<user>`, `/Users/<user>`, `/mnt/<drive>`)
anywhere in the committed `.claude/settings.json`, `.codex/config.toml` or `.codex/hooks.json`, in every mode,
reporting `file:line`. Replace such a path with a repository-relative one, or move the setting to an
uncommitted local file. `machine_paths.py --root <checkout>` runs that scan alone.

For per-clone adoption pass `--scope local`, which writes `.claude/settings.local.json`, `.codex/config.toml`,
optional `.codex/rules/agent-harness.rules` and `.agents/repo-capabilities.local.json` ownership state, keeps
exact Git exclusions, preserves unrelated selections and approvals, and refuses tracked targets, changed
owned settings and links that escape the root. Local settings need Python 3.11 or newer.

A plugin from another marketplace is added as `--plugin <plugin>@<marketplace>` together with
`--marketplace <marketplace>=<owner>/<repository>@<revision>`, for example
`--plugin concertable@agents --marketplace agents=Concertable/agents@<full commit>`. It is kept on later runs.

## Move repositories to another marketplace tag

```powershell
python -B '<skill-directory>\scripts\bump_plugin_lock.py' --revision v1.1.0 `
  --root C:\path\to\one --root C:\path\to\two --mode preview
```

`--marketplace <name>` moves a marketplace other than `tj-agents`. It previews by default. `--mode write`
rewrites that marketplace's revision in each lock and regenerates its settings; a
repository that fails validation is left unchanged and the others still proceed.

## Audit a machine

After every repository carries its own settings, audit the machine before removing old user-profile behavior:

```powershell
python -B '<skill-directory>\scripts\verify_machine.py' --home C:\Users\name --repository C:\path\to\project
```

The verifier is read-only and needs Python 3.11 or newer. Repeat `--repository` for each project; it checks
project Codex agents and local marketplace sources in Codex and Claude settings. GitHub marketplace
declarations are allowed. It reports user-scope plugin selections, marketplaces, hooks, notifications,
instruction files, agent settings, and loose agents or skills. `--json` gives stable finding codes. Exit
status 1 means findings or an inspection failure remain. Output never includes configuration values.
