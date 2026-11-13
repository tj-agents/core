# Tier declarations

Every standards plugin ships a `tier.json` at its payload root. `base`, `workflow`,
`engineering` and `docs` apply to every project. A stack plugin declares `stack-present` and the markers that
identify its stack. The base package's `hooks/tier_gate.py` reads installed declarations at
SessionStart and resolves standards for repository paths before work begins.

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
bad declaration in its owning stack repository. Host skill listings can still show inapplicable
skills. Context tells the agent which standards govern a repository; it does not restrict filesystem access
or remove instructions already present in the conversation.

Reviews load only the convention and contract skills of applicable plugins that the repository's
`.agents/plugins.json` selects; the write gate requires only the `core` ones of the stack whose markers
match the file being written.
When one valid version 3 employer declaration applies, a selected `<stack>:<name>` resolves to
`<employer>-<stack>:<name>` if that plugin and skill are installed. Otherwise it stays
`<stack>:<name>`. The employer name is the declaring plugin name. The same resolution governs
route queries, review, and session context. A company plugin can mirror a stack
skill under the same name to replace that whole skill; no section merge occurs.
When several employer declarations match, no replacement is selected until the ambiguity is resolved.
The write gate evaluates no employer evidence, so it requires the selected stack's own skills.

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
`remote_host` compares an exact origin hostname case-insensitively, normalizing a final DNS dot. It
accepts HTTP(S), SSH and Git URLs and `user@host:path` SCP origins. Local paths, `file:` origins,
malformed origins and missing or unreadable origins do not match. Hostnames are literal DNS names;
URLs, ports, patterns and wildcards are invalid predicate values. Combine host and owner matching
with `all` when an organisation must be bound to its Git host; `remote` retains its legacy
owner/name behavior without a host restriction.
`fact` requires scoped evidence and `context` compares a scoped string (`equals`) or list of
strings (`contains`). Unknown facts, missing contexts and malformed branches produce diagnostics
and prevent selection, including inside an otherwise matching `any`.

An employer plugin declares a gated tier and the slug of its own shipped context skill:

```json
{
  "schema_version": 3,
  "tier": "example-employer",
  "applies": "stack-present",
  "detect": {"all": [{"remote_host": "git.example.test"}, {"remote": "^example-company/"}]},
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
contacts. No employer names are built into Core. Employer scope comes from installed declarations;
Personal additionally requires explicit repository adoption.

## Folders containing repositories

A repository or a directory inside it uses that repository's evidence. Nested repositories have their
own scope. A non-Git folder is scanned through ordinary directories and worktree wrappers, stopping at
each repository boundary. Repository, directory-entry and time limits bound the scan. An unreadable
or unexamined part of the folder makes the inventory incomplete.

Each repository is assessed with its own installed declarations, origin and adoption file:

| Folder contents | Shared organizational scope |
| --- | --- |
| Complete inventory; every repository matches an employer | Work; only employer identities common to every repository are shared |
| Complete inventory; every repository explicitly adopts Personal | Personal for those repositories |
| Complete inventory containing Work and Personal repositories | Mixed; neither profile applies to the whole folder |
| Incomplete inventory, unresolved or unclassified repositories, or no repositories | Undetermined; neither profile applies to the whole folder |

Personal adoption is a valid repository-local `.agents/plugins.json` selecting `personal@tj-agents`
from the `tj-agents/marketplace` repository. An installed `always` declaration, repository ownership,
override or missing employer match cannot establish adoption. An employer match combined with Personal
adoption is a scope conflict; Personal remains excluded.

Technical standards shared by a folder must apply independently to every discovered repository. A
non-Git project's own technical markers can establish its local stack without establishing Work or
Personal scope. Predicates never combine evidence from sibling repositories.

## Resolve target paths before applying standards

From mixed or undetermined folders, resolve every intended target repository before preparing an edit
or applying its standards. The installed Base resolver accepts repeatable paths and returns JSON:

```text
python -B <base-package>/hooks/tier_gate.py --path <first-target> --path <second-target>
```

Use `python3` on Linux and macOS. Paths may name existing files, new files or search directories. A new
file uses its nearest existing parent to find its owning repository. A search spanning repositories
retains the separate results; its anchor does not select one profile for every search result. Repeated
queries re-read ownership, origin, adoption and declarations. There is no remembered active repository.

Shell commands and other opaque tools require the explicit path query before the operation. Command
text, cwd and a previous query are not proof of the paths an operation accesses. Claude file mentions
and host operations without a supported typed path event also require explicit resolution. The write gate
covers typed write tools only; it does not observe or restrict shell writes.

## Write gate

Base's PreToolUse hook gates Claude `Edit`, `Write`, `MultiEdit` and `NotebookEdit` and every path in a
Codex `apply_patch` operation, including move destinations. It finds the target's repository by walking up
to the nearest `.git` and reads that repository's `.agents/plugins.json`. For each selected `stack-present`
tier whose `file`, `glob` or content-glob marker matches the target, it requires that plugin's `core` (or
unprofiled) convention and contract skills. Other stacks and other profiles are not required. A repository
without a selection, or a file no selected stack declares, is allowed silently.

The hook denies the write until the agent has read every required canonical `SKILL.md`. The denial names
the target and lists each missing `<plugin>:<name>` with its absolute canonical path; the agent reads those
files and retries. A Claude `Read` of a `SKILL.md` is recorded by a `Read` hook whose `if` condition keeps
ordinary reads from launching it. A Codex shell command is recorded for each installed stack standard whose
canonical path it names. The discovery entry under `skills/<name>/` does not count, because it only points
at the canonical file. Records are kept per session and agent under
`<AGENT_STATE_DIRECTORY|~/.agents-state>/standards-loaded/`; the PostCompact hook clears that agent's
record, so its next gated write requires the standards again. The gate and recorders use filesystem checks
only, never Git, and allow the write when they fail.

At SessionStart, a repository with a selection gets one line naming its gated stacks plus the session
context of its selected always-applicable plugins, without a repository assessment. Outside a Git
repository the hook prints nothing.
