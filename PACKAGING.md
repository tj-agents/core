# Packaging

A utility skill must work the moment its marketplace plugin is installed on a supported machine.
Installing the plugin is the whole delivery mechanism — no manually assembled, machine-local file may be
a precondition for a skill to run.

## The rule

**A repository-owned runtime dependency ships inside the skill that needs it.** If a skill's
instructions or its script read a file this repository authored — a helper script, a data table, a
policy document — that file lives under `.agents/skills/<name>/`, beside `SKILL.md`, so
`sync-generated.ps1`'s sibling-copy carries it into every generated plugin copy automatically (see
`AGENTS.md` and the header of `sync-generated.ps1`). A skill that names a path it does not ship is a
skill that only ever worked on the machine where someone happened to build that path by hand.

**Resolve a shipped dependency relative to the skill's own installed location, never the caller's.** A
script uses `$PSScriptRoot` (or an explicit sibling path) to find its own resources. `SKILL.md` prose
uses the `<skill-directory>` placeholder the invoking agent substitutes with wherever the skill was
actually installed. Neither may resolve through `$env:USERPROFILE`, `$HOME`, `~`, the caller's current
working directory, or a hardcoded username — those vary by machine and by installer, and a path built
from one is not a path the plugin delivered.

**A genuine external prerequisite is named and checked, never assumed.** Something this repository does
not and should not own — another harness's CLI, an OS feature — is documented explicitly in the skill
that needs it, with a check that fails loudly and names what is missing (`launch-codex.ps1`'s
`-MinimumVersion` gate on the Codex CLI is the model to follow). It is never silently required by
instructions alone, and a missing prerequisite is never worked around by inventing a replacement policy
or silently degrading behavior — the failure must be visible and correct.

## Why

`base-agents` installs onto machines that were not the one it was authored on. A skill whose
instructions require a file nobody packaged — a resolver, a policy table, a config — worked by accident
on the machine that happened to have it, and breaks silently everywhere else the marketplace plugin is
the only thing installed. `handoff-claude` and `handoff-codex` shipped exactly this defect: both
required `~/.claude/routing/route.py`, a file this repository never packaged and that had no
authoritative implementation anywhere to package — the launch scripts already accepted model parameters
directly, so the unshippable dependency was pure liability. The fix removed the requirement rather than
inventing a policy to satisfy it (see the `handoff-claude`/`handoff-codex` `SKILL.md` "Model selection"
sections) and this document is the standing rule so the next utility skill does not reintroduce the same
shape of bug.

## What to check when adding or reviewing a utility skill

- Every path a skill's instructions or scripts read that this repository authored is a sibling file
  under that skill's own directory.
- Every such reference resolves relative to the skill's installed location (`$PSScriptRoot`,
  `<skill-directory>`), never the caller's home, working directory, or username.
- Any reference to something this repository does not ship is named as an external prerequisite and
  guarded by a check with a clear failure message — not merely asserted in prose.
- `pwsh .agents/sync-generated.ps1 -Check` passes, confirming the generated plugin copies actually
  contain what the skill's instructions reference.
