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
clone then installs exactly the plugins it selects, pinned to one `tj-agents/marketplace` revision, without
depending on any machine's user settings. User scope holds only `base`, `engineering` and `machine`, the
bootstrap that creates repositories.

## The lock

```json
{"schema_version": 2,
 "marketplace": {"repository": "tj-agents/marketplace", "revision": "v1.0.0"},
 "plugins": ["base", "engineering", "machine", "dotnet"]}
```

`revision` is a `vN.N.N` marketplace tag or a full lowercase commit. The lock must include `base`,
`engineering` and `machine`, and it lists a stack plugin's required plugins explicitly. The schema is
`catalog/plugins.lock.schema.json`.

## Adopt a stack

```powershell
python -B '<skill-directory>\scripts\adopt_plugins.py' --root C:\path\to\repository `
  --stack dotnet --marketplace-revision v1.0.0 --mode preview
```

A stack (`dotnet`, `azure`, `react`, `cpp-gcc`, `cpp-msvc`, `win32`, `neovim`, `rust`, `github-actions`,
`plugin-repository`) resolves to its plugins through `scripts/plugin_roster.json`, so nobody guesses which
plugins a project type needs. Repeat `--stack`, or add `--plugin <name>`. Core and each plugin's required
plugins are always added, existing selections and the existing revision are kept, and a new lock needs
`--marketplace-revision`. `preview` lists the changed files, `write` applies them together, and `check`
exits nonzero on drift, which is what CI runs. An unknown stack or plugin is rejected with the valid choices.

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

## Move repositories to another marketplace tag

```powershell
python -B '<skill-directory>\scripts\bump_plugin_lock.py' --revision v1.1.0 `
  --root C:\path\to\one --root C:\path\to\two --mode preview
```

It previews by default. `--mode write` rewrites each lock's revision and regenerates its settings; a
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
