# Packaging

A repository-owned runtime dependency must work when its owning plugin is installed on a supported machine.
Installation is the delivery mechanism; no manually assembled machine-local file may be required.

Every published standards package owns a committed harness manifest listing the plugins,
marketplaces, hook entry points, and host permissions its skills and workflows require. Adding
or changing any of those requirements updates that package's manifest in the same change.
The package owner checks its manifest against authored sources and shipped hook wiring; consumers
check generated project settings against the selected packages' declarations. Core does not
maintain another package owner's package declarations or harness manifest.

## Ownership

A skill-local helper, template, or policy file lives beside its canonical `SKILL.md` under `.agents/`.
Generation carries those siblings into the canonical package tree and into both generated host discovery
entries, so `<skill-directory>` keeps working after installation.

A resource shared by several skills stays under its canonical owner in `.agents/` and requires explicit
source/destination mappings in `.agents/plugins/sources.json`. A consuming package embeds the canonical
bytes beneath its own package root; each mapping names that destination package. Generated copies have
one authored owner and are covered by each package fingerprint. Runtime references may not cross into
another plugin or depend on the author checkout.

```json
{"plugin":"workflow","source":".agents/dependencies/agent/.agents/agent-store/runtime","destination":".agents/agent-store/runtime"}
```

Workflow loads this embedded store implementation from its own package. Agent Store owns the source,
schema and transaction contract.

Resolve shipped files relative to the installed skill or package. Scripts use `$PSScriptRoot`, their own
file location, or an explicit package-root input. Instructions use `<skill-directory>`. They do not resolve
repository-owned code through `$env:USERPROFILE`, `$HOME`, `~`, the caller's current directory, or a
hardcoded username.

A genuine external prerequisite, such as a host CLI or operating-system feature, is named and checked. A
missing prerequisite must fail clearly. It is not replaced with an invented policy or silently ignored.

Package verification uses `sha256-tree-v1`: hash each sorted forward-slash package-relative path, NUL, byte
length, NUL and file bytes. Reject symlinks. The generated
publication fingerprint identifies the authored rolling-main inputs while plugin digests are refreshed.

## Why

A skill that refers to an unpackaged helper works only on a machine where that path happens to exist.
The handoff launchers previously depended on an unshipped `~/.claude/routing/route.py`; removing that
dependency fixed the immediate defect. This contract prevents the same failure while allowing a deliberately
shared helper, such as the history reader, to ship once through an explicit mapping.

## Review checks

- Every repository-owned runtime path resolves to a skill-local sibling or a declared shared resource.
- Generated host entries contain skill-local resources required through `<skill-directory>`.
- Shared resources remain inside their owning plugin.
- External prerequisites are explicit and fail with a useful message.
- `pwsh .agents/sync-generated.ps1 -Check` passes.
- `python -B scripts/sync_harness_manifests.py --check` passes for this repository's packages.
