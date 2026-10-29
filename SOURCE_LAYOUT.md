# Source ownership and host adapters

This repository has one shared source and two host-specific adapter trees.

## Canonical shared source

`.agents/` owns every Core host-neutral capability definition and its shared runtime material. Core owns
Base, Workflow, Engineering and Docs classifications inside `.agents/`; they are not authored top-level
repository trees. Agent, Agent Store, Codex, Claude and CLI source stays with its publisher. Core consumes
declared publisher exports from `.agents/dependencies/` while building its own packages.

Canonical skills use `.agents/<namespace>/skills/<subject>/SKILL.md`. Kind is frontmatter metadata,
independent of that path and the public identity. A nested subject path joins with hyphens, so
`skills/state/client/SKILL.md` publishes `<namespace>:state-client`; reject collisions with a flat
`skills/state-client/SKILL.md`. Use a subject family when useful, without mechanically grouping names
that share a word. Shared plugin-layout guidance belongs to `template:structure`; this document owns
Core's authored/native/distribution boundaries.

```text
.agents/engineering/skills/commit/SKILL.md
.codex/skills/engineering/commit/SKILL.md
.claude/skills/engineering/commit/SKILL.md
plugins/engineering/
```

The plugin roster and project-selection schemas live under `.agents/plugins/`. `CAPABILITIES.md` is generated
from that canonical plugin roster and is never edited as a second source.

A new package may be built before Marketplace publishes its entry when Core's package roster declares
Core as its owner. An existing Marketplace assignment to another publisher always takes precedence.

A shared rule or procedure is written once. Neither host adapter may reproduce its body as an independently
maintained source.

## Host-specific source

`.codex/` contains only material whose shape or behavior is specific to Codex: skill entry points
(`skills/<plugin>/<name>/SKILL.md`), agent TOML and installation details. `.claude/` contains the
corresponding Claude-only material.

Authored host manifests and hook wiring live under `.agents/plugins/manifests/`, with their Codex or
Claude identity explicit in the path. `.agents/plugins/sources.json` is the one source map used to
assemble those manifests with the host adapter and canonical capability definitions.

Each host skill entry point references one canonical definition under `.agents/` and may add only the
host-specific metadata or invocation mechanics required by that host. A host difference must be explicit;
shared prose returns to `.agents/`.

A plain host entry point repeats its canonical definition's name and description, projects kind and
domain under `metadata.tj-agents-kind` and `metadata.tj-agents-domain`, and has the fixed reference body.
Other house fields use the same `metadata.tj-agents-` prefix. Codex model and effort selections are house
metadata; Claude retains its supported native `model` field and projects house effort into metadata.
Only host-supported fields remain at the top level. The canonical lane remains the source of those
selections, not a native host field.

```yaml
name: docs
description: Keep repository guidance owned and reachable. Use when editing guidance.
metadata:
  tj-agents-kind: standard
  tj-agents-domain: process
```

A skill named in `extended_host_adapters` in `.agents/plugins/sources.json` is the explicit
exception on both hosts: its entry points keep the canonical name and projected kind/domain and link the canonical
definition exactly once, and may word their description and the rest of their body for their host
without restating shared prose. Generation does not compare that wording, so review an extended entry
point whenever its canonical definition changes. `pwsh .agents/sync-generated.ps1 -Check` fails on any
other drift.

## Distribution output

`plugins/*` contains generated installable payloads. The build assembles canonical `.agents/` definitions,
the selected `.codex/` or `.claude/` adapter and all declared resources into a self-contained plugin.
Generated output is validated and committed to main by CI's post-merge regeneration job for marketplace
distribution; it never changes in a pull request and is never edited as source.

Two host-native marketplace files are generated bridges: `.agents/plugins/marketplace.json` comes from
`.agents/plugins/manifests/codex/marketplace.json`, and `.claude-plugin/marketplace.json` comes from
`.agents/plugins/manifests/claude/marketplace.json`.

The supported flow is:

```text
.agents shared definition
        +
.codex or .claude host adapter
        ↓
plugins/<package> installable payload
```

Concertable and stack repositories consume released packages and keep their product or stack-specific
definitions with their own owners. They do not receive another authored copy of this repository's shared
instructions.
