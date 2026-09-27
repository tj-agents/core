# Repository configuration host evidence

Observed on 2026-09-26, reconciled 2026-09-27. This is a prerequisite investigation, not
consumer acceptance or permission to remove existing delivery.

## Claude Code 2.1.282

The installed `C:\Users\TommySeery\.local\bin\claude.exe --version` reports `2.1.282`.
An isolated profile and Git consumer were created under the delivery worktree's ignored
`.claude-dependency-probe.tmp` directory. Its local fixture marketplace had a `domain` plugin
depending on `shared`; `shared` contained one skill and one agent. No normal profile was used.

```text
claude plugin marketplace add <fixture-marketplace> --scope project
claude plugin install domain@rdc-probe --scope project --json
claude plugin list --json
claude plugin details shared
```

All exited zero. Install reported `(+ 1 dependency: shared)`; list showed both plugins enabled
at project scope; details showed `Skills (1)` and `Agents (1)`. No user settings file appeared.
The consumer settings gained both `domain@rdc-probe` and `shared@rdc-probe` in `enabledPlugins`.
This does not establish a permanently domain-only consumer declaration, automatic installation
on clone, hook execution, GitHub sourcing, version locking or successful model invocation.

[Claude's dependency contract](https://code.claude.com/docs/en/plugin-dependencies) supports
plugin dependencies and requires the root marketplace to allow dependencies from other
marketplaces. A marketplace name is not its GitHub source declaration. Listing core packages
as pinned Git sources inside a domain marketplace still needs an end-to-end probe.

## Codex 0.157.0

The executable at
`C:\Users\TommySeery\.codex\packages\app-server-daemon\releases\0.157.0-x86_64-pc-windows-msvc\bin\codex.exe`
reports `codex-cli 0.157.0`. The separate Desktop executable under
`AppData\Local\OpenAI\Codex\bin\6ca77c4a9caa4eed` reports `0.151.0-alpha.7.1`.
The shell does not resolve a bare `codex` command. The exported experimental app-server schema
has no plugin agents or dependency fields. The exact release's upstream source confirms:

- [marketplace.rs](https://raw.githubusercontent.com/openai/codex/rust-v0.157.0/codex-rs/core-plugins/src/marketplace.rs):
  `Marketplace` and `MarketplacePlugin` describe a flat plugin list and local, Git or npm sources.
  Repository discovery recognizes `.agents/plugins/marketplace.json`. No dependency resolver
  brings in a second marketplace.
- [manifest.rs](https://raw.githubusercontent.com/openai/codex/rust-v0.157.0/codex-rs/core-plugins/src/manifest.rs):
  `RawPluginManifest` and its path resolver handle skills, MCP servers, apps and hooks. Adding
  `agents` or `dependencies` does not add a capability; the legacy parser ignores these keys.
- [loader.rs](https://raw.githubusercontent.com/openai/codex/rust-v0.157.0/codex-rs/core-plugins/src/loader.rs):
  `load_plugin` builds skill roots, MCP servers, apps and hook sources. It does not discover
  native agent role TOMLs from an installed plugin.

A domain marketplace can enumerate core packages as Git-sourced entries. That can deliver
skills and hooks without naming a second marketplace, but cannot extend the host's agent loader.
Core's existing profile installer supplies roles through `<CODEX_HOME>/agents`; the requested
deletion removes that supported delivery path.

## Required next proof

The inspected contract cannot register native roles through a plugin manifest. This alone does
not block the authorized plan: it explicitly anticipated the limitation and permits a solution
inside core and its child marketplaces. Native role registration is not an additional user requirement.

Investigate a packaged Codex dispatcher that consumes core's existing role and lane definitions
and invokes `codex exec` with per-run model, effort and developer instructions. Prove sandbox,
result validation and cancellation behavior before using it as the agent delivery mechanism.
This must not write role files into a profile or consumer repository. The existing host runtime
already models semantic dispatch; extend it rather than inventing a parallel orchestration system.
Do not claim plain skill text or hook injection has registered native agent types.

Consumer migration and cleanup still require successful native-host acceptance of the chosen
mechanism. The read-only audit is independent of that implementation work.

## Per-invocation role proof (2026-09-27)

A real Codex 0.157.0 `exec` probe consumed the generated core L7 role's model, effort and
developer instructions, using `--ephemeral`, `--sandbox read-only`, `--output-schema` and
`--config developer_instructions=<TOML string>`. It returned the exact token supplied only in
the developer instructions. The isolated profile had no config or agents directory; the Git
consumer had no `.codex/agents`. Only a temporary credential copy was supplied and it was deleted
afterward. Raw results are in the worktree's ignored `.codex-dispatch-probe.tmp`.

This proves a plugin-contained subprocess can supply the role without installing native role
files. It does not yet prove cancellation, writer leases, full workflow results or domain startup.
The config keys are present in the exact
[0.157.0 configuration source](https://raw.githubusercontent.com/openai/codex/rust-v0.157.0/codex-rs/config/src/config_toml.rs).

Additional fixture probes found:

- Removing the auto-installed Claude dependency's `enabledPlugins` entry disabled it and left
  the domain plugin with `dependency-unsatisfied`. A cache entry alone is insufficient.
- Codex read repository marketplace configuration after native project trust was set. Its
  app-server discovered a fixture plugin marked `INSTALLED_BY_DEFAULT`, but after `thread/start`
  it remained uninstalled and disabled. Adding an explicit domain plugin enablement changed
  the result to `enabled=true`, `installed=false`; `skills/list` still omitted the fixture skill.
  The profile held only native project trust, no plugin or marketplace tables. Home-only plugin
  CLI listing was not a repository-load proof.

Do not conclude that these observations rule out a generated domain bundle or plugin-contained
adapter. The original authorization requires investigating those paths inside the marketplace owners.

## Installation boundary (2026-09-27)

The exact release's [plugin CLI implementation](https://raw.githubusercontent.com/openai/codex/rust-v0.157.0/codex-rs/cli/src/plugin_cmd.rs)
separates listing from explicit `install_plugin` calls. `INSTALLED_BY_DEFAULT` is installation
policy metadata; it does not materialize an arbitrary repository-declared Git plugin at thread
startup. Native installation changes profile plugin state. No project-scoped install option was
found in the inspected CLI or app-server contract.

The successful per-invocation role proof therefore resolves role transport only. A fully cold
repository session still needs a supported way to install its declared domain plugin before any
plugin-owned hook or dispatcher can run. Existing cached installs must not be mistaken for this
cold-start acceptance. Domain package composition can address transitive payload delivery, but
cannot itself execute before that domain plugin has been materialized.
