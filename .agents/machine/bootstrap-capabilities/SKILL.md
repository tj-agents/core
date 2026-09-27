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
owns Claude's marketplace and enabled-plugin keys and Codex's marketplace and plugin tables;
other project settings remain in place. Release commits are selected by the lock, while host
settings declare the corresponding GitHub marketplace and enabled plugins.

After each repository has adopted its generated project settings, audit the machine before removing
old user-profile behavior:

```powershell
python -B '<skill-directory>\scripts\verify_machine.py' --home C:\Users\name
```

The verifier is read-only. It reports user-scope plugin selections, marketplaces, hooks,
notification commands, and loose agents or skills. Codex's recorded hook trust hashes and host
preferences are runtime state and are not reported. Exit status 1 means findings remain.

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

## Catalog and digest contract

The bundled catalog uses `sha256-tree-v1`: sort package files by forward-slash relative path, then hash each
path, a NUL, its byte length, a NUL, and its bytes. Symlinks are rejected. A plugin may declare narrow
`digest_excludes`; the machine package excludes only `catalog/catalog.json`, whose own digest field would
otherwise be self-referential. Schemas and every other bootstrap resource remain covered.

A lock records full 40-character source commits. Catalog revisions are immutable release tags. `apply` resolves
the tag and refuses it unless it equals the lock's commit; version strings alone never select content.

Do not use this utility to refresh a normal profile opportunistically. Use an isolated profile for projects that
select incompatible releases, and keep authentication/trust decisions separate from package installation.
