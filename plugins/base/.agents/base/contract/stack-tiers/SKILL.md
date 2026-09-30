---
name: stack-tiers
description: Why the base, engineering and machine packages apply in every project while a stack tier applies only where its stack is present, and how a tier repository declares that itself in a shipped `tier.json` instead of being wired into each consuming repository or configured per machine. Use when adding or changing a tier declaration, adding a stack tier repository to the corpus, correcting a detection rule that judged a project wrong, or explaining why a stack standard was blocked here.
kind: contract
domain: behavior
---

# Stack tiers

The corpus is layered. `base`, `engineering` and `machine` are stack-agnostic process, method and
behavior, so they are **ubiquitous**: they apply in every project, on every machine. `dotnet`, `react`
and `cpp` are **stack tiers**. A stack tier applies only where that stack is present, because its
standards describe code an unrelated project does not contain — applying them there is not a wasted
read, it is a wrong answer.

## The condition ships with the tier, never with the consumer or the machine

Neither host has conditional plugin loading. A plugin manifest declares `defaultEnabled` and
`dependencies` but no condition, and the two native knobs — `enabledPlugins` and `skillOverrides` —
are settings, at scopes that are either machine-local or written into each consuming repository.

Both of those are the wrong shape for a generic standard. Wiring a repository in means the standard is
installed repo by repo rather than applying everywhere by default; putting the rule in a machine's own
settings means a fresh machine does not have it. So each tier carries its own condition as `tier.json`
at the root of its plugin payload, and `base` ships the gate that reads whatever declarations are
installed. A tier repository cloned later is gated the moment it is installed, with no change to
`base`.

## Declaring a tier

```json
{
  "schema_version": 1,
  "tier": "dotnet",
  "stack": ".NET",
  "applies": "stack-present",
  "owner_repository": "tomjseery/dotagents",
  "detect": { "globs": ["*.sln", "*.csproj"], "files": ["global.json"] }
}
```

[`tier.schema.json`](tier.schema.json) is the contract. `applies` is `always` for a ubiquitous package
or `stack-present` for a stack tier. `detect` holds `files` (repository-relative paths), `globs`
(filenames at any depth), `content` (a `glob` whose text matches a `pattern`) and, at `schema_version`
2, `remote` (regexes against the origin identity `owner/name`, for a tier scoped to an organisation's
repositories); any one match means the stack is present. Prefer a marker the stack cannot exist
without — a project file, not a folder name someone chose.

Plugin and marketplace identity are taken from the installed path, so a declaration cannot claim to be
a plugin it is not, and the skill prefix the gate blocks is always the plugin's real name.

`owner_repository` exempts the tier's own authoring repository. `dotagents` contains no .NET, so
without it the gate would refuse to read the standards being edited there.

## What the gate does

[`scripts/tier_gate.py`](scripts/tier_gate.py) runs at two moments. At `SessionStart` it states which
tiers apply in this project, and prints nothing when no stack tier is installed. At `PreToolUse` it
blocks invoking a skill belonging to a tier whose stack is absent — Claude's `Skill` call by its
qualified name, and Codex's shell read of that tier's `SKILL.md`, which is the same event in the other
host's shape.

`--conventions` lists, per applicable tier, the conventions its installed payload ships — the skills
whose front matter declares `kind: contract`. A review loads exactly that: the applicable tiers'
rules, resolved from the installed cache with nothing wired into the reviewed repository.

## The payload shape is enforced, not remembered

[`scripts/check_tier_payload.py`](scripts/check_tier_payload.py) verifies a tier repository's
generated `plugins/` output: `tier.json` present and schema-valid in every payload declared by
`.agents/plugins/payloads.json`, no undeclared payload directory, every `skills/*/SKILL.md` carrying
`name:` and one-word `kind:` front matter, and `INDEX.md`/`selection.json` naming exactly the shipped
skills. Every tier repository runs it in its own CI, so drift fails that repository's build instead of
silently shipping a tier the gate cannot see or conventions the review cannot find.

The gate does not remove a tier's skills from the session listing; no host mechanism can do that
without per-repository or per-machine settings. It stops them being applied, not being offered.

A project the detection judges wrong is a defect in that tier's `detect`, and the fix belongs in the
tier's own repository. `AGENTS_TIER_OVERRIDE=<tier>[,<tier>]` forces a tier applicable for one session;
it is an escape hatch for the moment of being wrong, never the way a project selects a tier.
