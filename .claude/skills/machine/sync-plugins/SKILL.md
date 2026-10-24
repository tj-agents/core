---
name: sync-plugins
description: Bring this CLI's tj-agents plugins up to date and into the running session. Run it yourself, without asking, whenever plugins look outdated - a skill or hook is missing or behaves like an older version, or a plugin PR just merged - or when asked to sync, reload, refresh or update the plugins.
kind: utility
domain: machine
---

# Sync plugins

Read the [canonical shared definition](../../../../.agents/machine/utility/sync-plugins/SKILL.md).
This entry point adds only how Claude Code adopts the result.

## Claude Code

Nothing reloads plugins inside a running Claude process, so when this session runs an older copy of a
plugin than the one now installed, the script relaunches the conversation itself. It arms the
`cli:close` watcher; once this session has exited, a detached watcher resumes it with
`claude --resume <session-id>` in its own directory through the `machine:open-cli` launcher, re-passing
the `--settings`, `--mcp-config`, `--plugin-dir`, `--add-dir`, permission and model flags resume does not
restore. Directories added in-session with `/add-dir` are not restored.

When its JSON reports `"relaunch": "armed"`, give a short final reply and end the turn; the fresh process
continues the work. `--no-relaunch` keeps this session unchanged.
