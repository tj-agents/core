Worktree: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-RefreshCliFastPath (branch Fix/RefreshCliFastPath)
Why: the Claude side of "get merged tj-agents standards into running sessions fast, event-driven" is committed here; the Codex side is yours.

Read plans/refresh-cli-fast-path/GOAL.md first. The Claude session that wrote it has stopped writing to this worktree; you are the only writer.

Your task, for Codex only, mirroring the Claude decisions in GOAL.md:
1. Verify Codex's real install and load path on this PC: how a launcher-bound session binds main
   (startup_binding / codex_runtime_binding), and what `codex plugin` natively offers for updating and
   reloading. Record it, as evidence, in GOAL.md.
2. Decide Codex's fast path. `refresh_cli.py` currently prints "codex: each launch binds current main" and
   does nothing for Codex unless `--full` is passed. Keep that if it is right, or replace it with Codex's
   best native mechanism. No new skill, no timer or polling: refresh is triggered by the merge
   (`engineering:merge` Step 6) and by launches only.
3. Codex has no in-process plugin reload; confirm or refute that against the installed CLI, and make the
   PR 311 gate's Codex adoption message accurate.
4. Tests for whatever you change; keep the existing suites green
   (tests/test_refresh_cli.py, tests/test_plugin_generation.py, tests/test_rolling_plugins.py).

Constraints: shared `.agents/` source is the single owner; `plugins/*` is generated and never committed.
Commit locally at natural boundaries. Do not push or open a PR: Tommy decides that. Update GOAL.md
Progress with what you verified and changed, then stop.
