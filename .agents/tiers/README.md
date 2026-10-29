# Tier declarations

Every standards plugin ships a `tier.json` at its payload root. `base`, `workflow`,
`engineering` and `docs` apply to every project. A stack plugin declares `stack-present` and the markers that
identify its stack. The base package's `hooks/tier_gate.py` reads installed declarations at
SessionStart and blocks use of a stack skill when its stack is absent.

The declaration format is defined by [tier.schema.json](../schemas/tier.schema.json). All publishers
and readers use this one current format. Unknown fields and malformed predicates are rejected.
`detect.file` names a repository-relative path, `detect.glob` matches filenames at any depth,
`detect.content` matches a pattern inside files selected by a glob, and `detect.remote` matches
a regex against the origin identity `owner/name`. Use a marker intrinsic to the stack, such as a
project file. To apply a stack's standards in its authoring repository too, declare that explicitly:

```json
{"any": [{"file": "pyproject.toml"}, {"remote": "^tj-agents/python$"}]}
```

The gate gets plugin and marketplace identity from the installed path. Each plugin answers from the
first cache that has it, the running host's first, and from the version that cache's
`installed_plugins.json` names; a cache with no registry falls back to its newest version. Correct a
bad declaration in its owning stack repository. Host skill listings can still show blocked
skills; the PreToolUse gate prevents their application.

Reviews load only the skills selected by the reviewed repository's route table for changed paths.
When one valid employer declaration applies, a selected `<stack>:<name>` resolves to
`<employer>-<stack>:<name>` if that plugin and skill are installed. Otherwise it stays
`<stack>:<name>`. The employer name is the declaring plugin name. The same resolution governs
route queries, review, invocation checks, and session context. A company plugin can mirror a stack
skill under the same name to replace that whole skill; no section merge occurs.
When several employer declarations match, no replacement is selected until the ambiguity is resolved.

`hooks/check_tier_payload.py` enforces the shipped payload shape a tier repository must generate:
`tier.json` present and schema-valid in every payload declared by `.agents/plugins/payloads.json`
(a repository authored directly as its payloads carries no payloads.json and is checked against
every `plugins/` directory instead),
no undeclared payload directory, every `skills/*/SKILL.md` carrying `name:` and one-word `kind:`
front matter, and `INDEX.md`/`selection.json` naming exactly the shipped skills. Every tier
repository runs it in its own CI, so drift fails that repository's build instead of silently
shipping a tier the gate cannot see or conventions a review cannot find.

## Predicates and employer scope

`detect` contains one positive predicate. `all` and `any`
compose predicates; `file`, `glob`, `content`, and `remote` keep the repository detection above.
`remote_host` compares an exact origin hostname case-insensitively, normalizing a final DNS dot. It
accepts HTTP(S), SSH and Git URLs and `user@host:path` SCP origins. Local paths, `file:` origins,
malformed origins and missing or unreadable origins do not match. Hostnames are literal DNS names;
URLs, ports, patterns and wildcards are invalid predicate values. Combine host and owner matching
with `all` when an organisation must be bound to its Git host; `remote` matches
owner/name behavior without a host restriction.
`fact` requires scoped evidence and `context` compares a scoped string (`equals`) or list of
strings (`contains`). Unknown facts, missing contexts and malformed branches produce diagnostics
and prevent selection, including inside an otherwise matching `any`.

An employer plugin declares a gated tier and the slug of its own shipped context skill:

```json
{
  "tier": "example-employer",
  "applies": "stack-present",
  "detect": {"all": [{"remote_host": "git.example.test"}, {"remote": "^example-company/"}]},
  "employer": {"context_skill": "communication-context"}
}
```

`context_skill` is a lowercase local skill slug, not a qualified name or path. The payload must
ship readable `skills/communication-context/SKILL.md` with matching `name:` and lowercase
`kind:` front matter. Its resolved path must stay inside that payload. The payload checker and
runtime validate this contract. Employer metadata requires
`applies: "stack-present"` with an ordinary positive detection predicate.

The gate derives the reserved `employer` fact from valid installed employer declarations whose
predicates genuinely match this project. A missing or malformed declaration, missing or invalid
context skill, orphaned payload or caller-supplied
`employer` fact cannot establish employer applicability. Employer predicates cannot reference
`fact: "employer"` directly or within nested `all`/`any`.

A generic work tier can depend on this fact:

```json
{
  "tier": "work",
  "applies": "stack-present",
  "detect": {"fact": "employer"},
  "session_context": "Before drafting a human message, load the matching work:ask-* skill and clip the draft."
}
```

`session_context` is an optional nonblank single line on a tier. SessionStart emits it
only when that tier applies, including valid `always` tiers. It lists each genuinely matched
employer's qualified context skill and exact installed `SKILL.md` path. Multiple matching employers
are all reported; consuming workflows must resolve that ambiguity before choosing employer-specific
contacts. No employer names are built into core and no per-repository settings or files are required.
The existing Claude skill invocation and Codex cached skill-read gates refuse the work tier in
personal projects. This gates application; hosts can still show blocked skills in their listings.
