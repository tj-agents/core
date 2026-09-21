# Source ownership and host adapters

This repository has one shared source and two host-specific adapter trees.

## Canonical shared source

`.agents/` owns every host-neutral capability definition and its shared runtime material. The logical
base, engineering and machine packages are classifications inside `.agents/`; they are not authored
top-level repository trees. Shared workflow contracts, hooks, schemas, tests and resources also remain
under `.agents/`.

The release catalog and project-lock schemas live under `.agents/catalog/`. `CAPABILITIES.md` is generated
from that canonical catalog and is never edited as a second source.

A shared rule or procedure is written once. Neither host adapter may reproduce its body as an independently
maintained source.

## Host-specific source

`.codex/` contains only material whose shape or behavior is specific to Codex: skill entry points,
agent TOML and installation details. `.claude/` contains the corresponding Claude-only material.

Authored host manifests and hook wiring live under `.agents/plugins/manifests/`, with their Codex or
Claude identity explicit in the path. `.agents/plugins/sources.json` is the one source map used to
assemble those manifests with the host adapter and canonical capability definitions.

Each host skill entry point references one canonical definition under `.agents/` and may add only the
host-specific metadata or invocation mechanics required by that host. A host difference must be explicit;
shared prose returns to `.agents/`.

## Distribution output

`plugins/*` contains generated installable payloads. The build assembles canonical `.agents/` definitions,
the selected `.codex/` or `.claude/` adapter and all declared resources into a self-contained plugin.
Generated output is validated and may be committed for marketplace distribution, but it is never edited as
source.

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
