# Repo-declared agent configuration — progress

Plan: `REPO_DECLARED_CONFIG_PLAN.md`
Status: planned; no phase started.

## Current state (2026-09-23)

- Plan authored and landed on `main`; no implementation branch exists yet.
- This PC still has user-scope plugins and marketplaces in `~/.claude/settings.json`,
  including `concertable@agent-standards`. `tj-agents/core` is not installed in Claude.
- `sandbox-hwid` routes resolve for Claude and Codex after cpp-agents v0.3.0 adoption, but that
  relies on user-scope installs, not repository-declared config.

## Next Steps

Start phase 1 in a fresh worktree from `origin/main`: inventory the hooks in
`Concertable/agent-standards` `plugins/concertable/hooks` and their tests, classify each as
generic harness or Concertable-specific, and move the generic ones into core with their tests.
Record the inventory and classification here before moving code.
