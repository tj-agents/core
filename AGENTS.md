# base-agents

Read `README.md` before changing repository structure.

`.agents/` is the only canonical home for host-neutral capability definitions, workflow contracts,
shared hooks, schemas, tests and resources. Logical base, engineering and machine ownership lives below
that directory; it must not be recreated as authored top-level source trees.

`.codex/` contains Codex-only entry points, adapters, agent definitions, hook wiring and configuration.
`.claude/` contains Claude-only equivalents. A host entry point references its canonical definition in
`.agents/` and adds only genuine host differences; never copy a shared instruction body into either host
tree as another authored source.

`plugins/*` is generated distribution output, never an authored source tree. Run
`pwsh .agents/sync-generated.ps1` after authored changes and require
`pwsh .agents/sync-generated.ps1 -Check` before delivery. See [`SOURCE_LAYOUT.md`](SOURCE_LAYOUT.md).

A utility skill must not depend on a manually assembled, machine-local file the plugin does not ship.
See [`PACKAGING.md`](PACKAGING.md).

This repository owns common agent behavior, shared engineering process, and machine utilities.
`plan-artifacts` supplies the common maintained-plan contract without requiring an engineering lifecycle.
Stack standards and product policy remain with their scope plugins. Further runtime migration and the
base/engineering/machine split are separate work; do not copy product-specific enforcement here.
