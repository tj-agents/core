# base-agents

Read `README.md` before changing repository structure.

`.agents/` is the only canonical home for host-neutral capability definitions, workflow contracts,
shared hooks, schemas, tests and resources. Logical base, engineering and machine ownership lives below
that directory; it must not be recreated as authored top-level source trees.

`.codex/` contains Codex-only entry points, adapters, agent definitions and configuration. `.claude/`
contains Claude-only equivalents. Authored host manifests and hook wiring live under
`.agents/plugins/manifests/` and are mapped explicitly by `.agents/plugins/sources.json`. A host entry
point references its canonical definition in `.agents/` and adds only genuine host differences; never
copy a shared instruction body into either host tree as another authored source.

`plugins/*` is generated distribution output, never an authored source tree. Run
`pwsh .agents/sync-generated.ps1` after authored changes and require
`pwsh .agents/sync-generated.ps1 -Check` before delivery. See [`SOURCE_LAYOUT.md`](SOURCE_LAYOUT.md).

A utility skill must not depend on a manually assembled, machine-local file the plugin does not ship.
See [`PACKAGING.md`](PACKAGING.md).

This repository owns common agent behavior, selected engineering process and machine utilities.
`plan-artifacts` supplies maintained plans without requiring an engineering lifecycle. Stack standards,
product profiles and product-specific enforcement remain with their scope owners. Shared runtime recovery
and host acceptance remain part of P2; source generation alone does not establish adoption.
