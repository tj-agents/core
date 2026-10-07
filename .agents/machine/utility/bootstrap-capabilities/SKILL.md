---
name: bootstrap-capabilities
description: Preview, apply or verify an exact project capability lock in an isolated Codex or Claude profile. Use when installing the repository's selected agent plugins, checking a reproducible installation, or diagnosing lock/catalog drift.

kind: utility
domain: machine
route: infer
---

# Bootstrap locked capabilities

## Generate repository host settings

Keep `.agents/capabilities.lock.json` in the project. Select `base`, `engineering`, and `machine`
from `base-agents` alongside the project's stack plugins. Commit the selected owners' release
records as `.agents/catalog/catalog.json` when selecting plugins outside core. Generate host
settings from that catalog and the lock:

```powershell
python -B '<skill-directory>\scripts\repo_config.py' `
  --lock C:\path\to\project\.agents\capabilities.lock.json --mode write
```

CI uses the same command with `--mode check`; it exits nonzero if either generated file drifts.
Each GitHub source must match the owner in its catalog release. The generator
owns Claude's marketplace, enabled-plugin, and `permissions.allow` keys, plus Codex's
marketplace and plugin tables and `.codex/rules/agent-harness.rules`. Existing Claude allow
entries outside the declared harness must be moved into `.agents/repository-harness.json`
before generation. Other project settings remain in place. Release commits are selected by
the lock, while host settings pin the corresponding GitHub marketplace revision and plugin
selection.

For per-clone adoption, pass an explicit root and local scope. Local settings generation
requires Python 3.11 or newer. Preview lists every changed output without writing:

```powershell
python -B '<skill-directory>\scripts\repo_config.py' `
  --root C:\path\to\checkout --scope local `
  --lock C:\path\to\checkout\.agents\capabilities.lock.json --mode preview
```

Use the same arguments with `--mode write` to apply or `--mode check` to detect drift.
Local mode writes `.claude/settings.local.json`, `.codex/config.toml`, optional
`.codex/rules/agent-harness.rules`, and `.agents/repo-capabilities.local.json` ownership
state. It preserves unrelated native selections, settings and existing approvals, removes
stale grants it added, and restores prior Claude values when owned selections become stale.
Changed owned settings and collisions with unmanaged Codex tables fail before writing.
Keep the ownership state with the clone; deleting it prevents safely updating existing
managed Codex configuration or rules.

All output paths, including Git exclusions, are checked against each other and the lock,
catalog and repository overlay by canonical path and file identity before mutation. Multiply
linked output files are rejected. Local mode rejects tracked targets and links that escape
the explicit root, including links above missing output files. A failed write restores the
attempted outputs to their prior bytes so approvals and ownership remain paired on retry.
For a Git checkout, it maintains exact file exclusions through
`git rev-parse --git-path info/exclude`; linked worktrees use their actual shared exclusion
file with separate blocks owned by each checkout. Explicit non-Git workspace roots are supported
without exclusions. Locks and catalogs remain read inputs; this command does not compose them
or change their tracking. A later adoption caller can use `plan(..., prospective_paths=[...])`
or `preflight_paths(...)` to validate its own prospective lock, catalog and receipt paths.
The default `--scope project` retains the existing project settings contract.

After each repository has adopted its generated project settings, audit the machine before removing
old user-profile behavior:

```powershell
python -B '<skill-directory>\scripts\verify_machine.py' --home C:\Users\name --repository C:\path\to\project
```

The verifier is read-only and requires Python 3.11 or newer for TOML inspection. Repeat
`--repository` for each project being migrated; it checks project Codex agents and local
marketplace sources in Codex and Claude settings. GitHub marketplace declarations are allowed.
It reports user-scope plugin selections, marketplaces, hooks, notifications, instruction files,
agent settings, and loose agents or skills. Codex's recorded hook trust hashes and built-in marketplaces are
runtime state and are not reported. Use `--json` for stable finding codes, paths, settings, and
clean or drift status. Exit status 1 means findings or an inspection failure remain. Output
never includes configuration values.

Use the packaged Python entry point. The lock and composed catalog are project-owned; core's
bundled catalog covers only core packages. `--profile` is the actual Codex or Claude configuration
directory, not a label.

```powershell
python -B '<skill-directory>\scripts\bootstrap_capabilities.py' `
  --lock C:\path\to\project\.agents\capabilities.lock.json `
  --harness codex `
  --profile C:\path\to\isolated-codex-home `
  --mode preview
```

The modes have deliberately different authority:

- `preview` validates catalog closure, lock selections, exact commits, required skills and prerequisites.
  It prints the planned native operations and changes nothing. `--report` may write that report explicitly.
- `apply` maintains only the catalog marketplaces and plugins selected in the lock. It clones installation-owned
  checkouts at the locked commits, registers those local marketplaces and installs/enables the selected plugins.
  When a managed release or repository source changes, it journals the prior and target identities before
  touching the checkout, accepts only the recorded old or new commit while resuming, refreshes installed plugin
  bytes, verifies their versions and digests, and only then finalizes managed state. It never removes an unrelated
  marketplace, plugin or setting.
- `verify` is offline-safe. It does not fetch, install, update or refresh. It verifies checkout commits, package
  digests, completed managed state, and the host's installed versions and package digests, then emits a report.

The bootstrap uses argument arrays for Git and host CLIs. A failed operation leaves completed checkouts and
host registrations in place and records the failing step; rerunning `apply` resumes from observable state.
Exit zero means the selected mode completed. Invalid locks, cycles, missing prerequisites, drift and partial
application exit nonzero.

## Compose immutable source catalogs

Use `compose_catalog.py` before lock selection when combining source owners. Its input is an
explicit JSON object with `schema_version: 1` and a non-empty `sources` list. Each source declares
`repository` (`owner/repo`), an absolute local `checkout`, a full lowercase commit SHA,
`plugins` (canonical package names), and `version_plugin` (one selected package):

```json
{
  "schema_version": 1,
  "sources": [{
    "repository": "example/capabilities",
    "checkout": "C:/sources/capabilities",
    "commit": "0123456789abcdef0123456789abcdef01234567",
    "plugins": ["base", "compiler"],
    "version_plugin": "base"
  }]
}
```

```powershell
python -B '<skill-directory>\scripts\compose_catalog.py' `
  --input C:\path\to\sources.json --platform windows
```

The composed v1 catalog is printed to stdout; the composer writes no files.
`--platform` defaults to the current platform. Source-owned catalog entries
supply platforms, executable prerequisites, status and digest exclusions when present; otherwise
the entry records only that consumption platform and no additional declared executable
prerequisites. Those defaults describe the supplied catalog, without establishing owner support.

The composer reads immutable Git blobs, so working-tree edits cannot change its output. It checks
the GitHub origin, both native marketplace/package identities, actual `N.N.N` package versions
supported by catalog v1, shipped skills, required harness declarations and their hook payloads. Top-level `selection.json`
prerequisites/dependencies must agree with harness plugin requirements; local names qualify to
the package's own marketplace in both dependency edges and emitted harness declarations.
Skill-level library requirements do not become plugin edges.
Unresolved dependencies, contradictory owners, cycles and linked payloads fail before output.
Each package keeps its own native version. The selected anchor supplies only the release grouping
version; the full commit and `sha256-tree-v1` payload digest identify the snapshot. Composition
requires every inspected Git object to be locally available, disables Git lazy fetching, and
performs no fetch, snapshot execution, lock selection, installation or profile changes. Git must
support `--no-lazy-fetch`; unsupported versions fail before inspecting snapshot objects.

## Catalog and digest contract

The bundled catalog uses `sha256-tree-v1`: sort package files by forward-slash relative path, then hash each
path, a NUL, its byte length, a NUL, and its bytes. Symlinks are rejected. A plugin may declare narrow
`digest_excludes`; the machine package excludes only `catalog/catalog.json`, whose own digest field would
otherwise be self-referential. Schemas and every other bootstrap resource remain covered.

A lock records full lowercase 40-character source commits. Catalog revisions accept semantic
`vN.N.N` release tags or exact lowercase 40-character commit SHAs. A SHA revision must equal
the lock and managed-state commit before preview or mutation. `apply` fetches tags through their
tag refs and SHAs directly, then verifies the revision identifies the locked commit object.
Branches, abbreviated or uppercase SHAs, object expressions, and tag-object SHAs are rejected.
Offline verification uses the same identity checks; version strings alone never select content.
Existing tag recovery retains its recorded prior/target checks. Matching legacy release and
commit records may acquire the catalog SHA; ambiguous legacy identity remains an error.

Do not use this utility to refresh a normal profile opportunistically. Use an isolated profile for projects that
select incompatible releases, and keep authentication/trust decisions separate from package installation.
