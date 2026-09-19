# base-agents

Read `README.md` before changing repository structure.

`.agents/skills/` owns shared skill behaviour. `.claude/skills/` and the skill/resource trees under
`plugins/base/` are generated; run `pwsh .agents/sync-generated.ps1` after authored changes and require
`pwsh .agents/sync-generated.ps1 -Check` before delivery. Exception: both
`plugins/base/.claude-plugin/plugin.json` and `plugins/base/.codex-plugin/plugin.json` are authored
manifest inputs until the planned P2 source-layout migration.

A utility skill must not depend on a manually assembled, machine-local file the plugin does not ship.
See [`PACKAGING.md`](PACKAGING.md).

This repository owns common agent behavior, shared engineering process, and machine utilities.
`plan-artifacts` supplies the common maintained-plan contract without requiring an engineering lifecycle.
Stack standards and product policy remain with their scope plugins. Further runtime migration and the
base/engineering/machine split are separate work; do not copy product-specific enforcement here.
