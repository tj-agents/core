---
name: bootstrap-capabilities
description: Preview, apply or verify an exact project capability lock in an isolated Codex or Claude profile. Use when installing the repository's selected agent plugins, checking a reproducible installation, or diagnosing lock/catalog drift.

kind: utility
domain: machine
route: infer
---

# Bootstrap locked capabilities

Use the packaged Python entry point. The lock is project-owned; the catalog is release-owned and ships
with this skill's plugin. `--profile` is the actual Codex or Claude configuration directory, not a label.

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
