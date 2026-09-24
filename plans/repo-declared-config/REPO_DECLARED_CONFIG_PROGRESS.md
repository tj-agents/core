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
  - Claude now has `base`, `engineering` and `machine@base-agents` (source `tj-agents/core`)
    at user scope, and `concertable@agent-standards` is disabled at user scope, so Claude's
    lanes and gates come from core. This is an interim user-scope state until phase 4.
  - `~/.claude/settings.json` still has other user-scope plugins, `tomjseery/*` sources for
    `dotagents` and `react-agents`, and `cpp-agents` without `autoUpdate`. Its auto-mode
    environment text names `Concertable/concertable` as the trusted repo for every session;
    that belongs in the Concertable repository's project settings (user decision).
  - `~/.codex/agents` holds the ten shared Codex agents installed by core's engineering
    package (owned via `.base-agents-delivery.json`); Codex cannot load agents from plugins, so
    the plan must decide how this stays repository-declared.
- `sandbox-hwid` (first consumer): routes resolve for Claude and Codex after cpp-agents v0.3.0
  adoption, but through user-scope installs.

## Next Steps

Start phase 1 in a fresh worktree from `origin/main`: inventory `Concertable/agent-standards`
`plugins/concertable` (hooks, Claude agents, `codex-agents`, generic skills) against core's
`engineering` and `base` packages, and record here which items are duplicates of core and which
are Concertable-specific. Port anything generic that core lacks. Then, in the Concertable
repository, enable core plus concertable in its project settings, and only after that delete the
duplicates from `Concertable/agent-standards`. Phase 3 (self-heal: automatic
marketplace refresh and in-session skill injection for Claude and Codex) follows the generator
in phase 2.
