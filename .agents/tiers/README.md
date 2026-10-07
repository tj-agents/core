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

## Version 3 predicates and employer scope

Version 3 uses one positive predicate instead of the legacy matcher arrays. `all` and `any`
compose predicates; `file`, `glob`, `content`, and `remote` keep the repository detection above.
`fact` requires scoped evidence and `context` compares a scoped string (`equals`) or list of
strings (`contains`). Unknown facts, missing contexts and malformed branches produce diagnostics
and prevent selection, including inside an otherwise matching `any`.

An employer plugin declares a gated tier and the slug of its own shipped context skill:

```json
{
  "schema_version": 3,
  "tier": "example-employer",
  "applies": "stack-present",
  "detect": {"remote": "^example-company/"},
  "employer": {"context_skill": "communication-context"}
}
```

`context_skill` is a lowercase local skill slug, not a qualified name or path. The payload must
ship readable `skills/communication-context/SKILL.md` with matching `name:` and lowercase
`kind:` front matter. Its resolved path must stay inside that payload. The payload checker and
runtime validate this contract. Employer metadata is supported only in version 3 and requires
`applies: "stack-present"` with an ordinary positive detection predicate.

The gate derives the reserved `employer` fact from valid installed employer declarations whose
predicates genuinely match this project. A missing or malformed declaration, missing or invalid
context skill, orphaned payload, owner-repository exemption, session override or caller-supplied
`employer` fact cannot establish employer applicability. Employer predicates cannot reference
`fact: "employer"` directly or within nested `all`/`any`. Version 3 selection does not use owner
exemptions or `AGENTS_TIER_OVERRIDE`; versions 1 and 2 retain their existing behavior.

A generic work tier can depend on this fact:

```json
{
  "schema_version": 3,
  "tier": "work",
  "applies": "stack-present",
  "detect": {"fact": "employer"},
  "session_context": "Before drafting a human message, load the matching work:ask-* skill and clip the draft."
}
```

`session_context` is an optional nonblank single line on a version 3 tier. SessionStart emits it
only when that tier applies, including valid `always` tiers. It lists each genuinely matched
employer's qualified context skill and exact installed `SKILL.md` path. Multiple matching employers
are all reported; consuming workflows must resolve that ambiguity before choosing employer-specific
contacts. No employer names are built into core and no per-repository settings or files are required.
The existing Claude skill invocation and Codex cached skill-read gates refuse the work tier in
personal projects. This gates application; hosts can still show blocked skills in their listings.