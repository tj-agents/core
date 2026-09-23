# Repo-declared agent configuration — progress

Plan: `REPO_DECLARED_CONFIG_PLAN.md`
Status: planned; no phase started.

## Current state (2026-09-23)

- The plan is on `main`, amended with the tj-agents-only source rule and the per-machine
  migration procedure. No implementation branch exists yet.
- This PC (first machine):
  - All four canonical repositories are cloned under
    `C:\Users\tommy\source\repos\tj-agents\{core,cpp,react,dotnet}`.
  - The older `C:\Users\tommy\source\repos\base-agents` checkout is 87 commits behind with
    uncommitted `plan-artifacts` edits and live worktrees; it is not retired.
  - `~/.claude/settings.json` still has user-scope plugins and marketplaces, including
    `concertable@agent-standards` and `tomjseery/*` sources for `dotagents` and
    `react-agents`. `cpp-agents` lacks `autoUpdate`. `tj-agents/core` is not installed in Claude.
  - `~/.codex/agents` holds the ten shared Codex agents installed by core's engineering
    package (owned via `.base-agents-delivery.json`); Codex cannot load agents from plugins, so
    the plan must decide how this stays repository-declared.
- `sandbox-hwid` (first consumer):
  - Routes resolve for Claude and Codex after cpp-agents v0.3.0 adoption, but through
    user-scope installs.
  - It still has ten untracked Codex agent files in `.codex/agents/` (`lane-l1`..`lane-l5`,
    `workflow-*`). Their naming differs from core's shipped set; identify their origin before
    removal, and remove only through core's installer migration path
    (`-MigrateProjectRoot`), which preserves unmatched content.

## Next Steps

Start phase 1 in a fresh worktree from `origin/main`: inventory the hooks in
`Concertable/agent-standards` `plugins/concertable/hooks` and their tests, classify each as
generic harness or Concertable-specific, and move the generic ones into core with their tests.
Record the inventory and classification here before moving code. Phase 3 (self-heal: automatic
marketplace refresh and in-session skill injection for Claude and Codex) follows the generator
in phase 2.
