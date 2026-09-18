# base-agents

Read `README.md` before changing repository structure.

`.agents/skills/` owns shared skill behaviour. `.claude/skills/` and everything under `plugins/base/` are
generated; run `pwsh .agents/sync-generated.ps1` after authored changes and require
`pwsh .agents/sync-generated.ps1 -Check` before delivery.

The repository is the machine layer only. Engineering workflows, hooks, routes, rules, lanes, and stack
standards belong to their scope plugins and must not be copied back here.