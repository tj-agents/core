# Tier declarations

Every standards plugin ships a `tier.json` at its payload root. `base`, `engineering`, and
`machine` apply to every project. A stack plugin declares `stack-present` and the markers that
identify its stack. The base package's `hooks/tier_gate.py` reads installed declarations at
SessionStart and blocks use of a stack skill when its stack is absent.

The declaration format is defined by [tier.schema.json](../schemas/tier.schema.json). `detect.files` names
repository-relative paths, `detect.globs` matches filenames at any depth, `detect.content`
matches a pattern inside files selected by a glob, and (`schema_version` 2) `detect.remote` matches
regexes against the origin identity `owner/name`, for a tier scoped to an organisation's
repositories. Any match makes the stack present. Use a
marker intrinsic to the stack, such as a project file. `owner_repository` allows a standards
authoring repository to use its own skills without ordinary project markers.

The gate gets plugin and marketplace identity from the installed path. Each plugin answers from the
first cache that has it, the running host's first, and from the version that cache's
`installed_plugins.json` names; a cache with no registry falls back to its newest version. It exposes
`AGENTS_TIER_OVERRIDE=<tier>[,<tier>]` for a single session when detection is wrong. Correct a
bad declaration in its owning stack repository. Host skill listings can still show blocked
skills; the PreToolUse gate prevents their application.

`tier_gate.py --conventions` lists, per applicable tier, the conventions its installed payload
ships — the skills whose front matter declares `kind: contract` — with their installed paths.
A review loads exactly that: the applicable tiers' rules, resolved from the installed cache with
nothing wired into the reviewed repository.

`hooks/check_tier_payload.py` enforces the shipped payload shape a tier repository must generate:
`tier.json` present and schema-valid in every payload declared by `.agents/plugins/payloads.json`
(a repository authored directly as its payloads carries no payloads.json and is checked against
every `plugins/` directory instead),
no undeclared payload directory, every `skills/*/SKILL.md` carrying `name:` and one-word `kind:`
front matter, and `INDEX.md`/`selection.json` naming exactly the shipped skills. Every tier
repository runs it in its own CI, so drift fails that repository's build instead of silently
shipping a tier the gate cannot see or conventions a review cannot find.
