# Packaging

A repository-owned runtime dependency must work when its owning plugin is installed on a supported machine.
Installation is the delivery mechanism; no manually assembled machine-local file may be required.

## Ownership

A skill-local helper, template, or policy file lives beside its canonical `SKILL.md` under `.agents/`.
Generation carries those siblings into the canonical package tree and into both generated host discovery
entries, so `<skill-directory>` keeps working after installation.

A resource shared by several skills stays under `.agents/` and requires an explicit source/destination
mapping in `.agents/plugins/sources.json`. The mapping names one owning plugin. Runtime references may not
cross into another plugin or depend on the author checkout.

Resolve shipped files relative to the installed skill or package. Scripts use `$PSScriptRoot`, their own
file location, or an explicit package-root input. Instructions use `<skill-directory>`. They do not resolve
repository-owned code through `$env:USERPROFILE`, `$HOME`, `~`, the caller's current directory, or a
hardcoded username.

A genuine external prerequisite, such as a host CLI or operating-system feature, is named and checked. A
missing prerequisite must fail clearly. It is not replaced with an invented policy or silently ignored.

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
