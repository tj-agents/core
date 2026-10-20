---
name: reload-plugins
description: Load the latest published tj-agents plugins into this CLI, named after Claude Code's native /reload-plugins. Use when a skill or hook is missing or out of date after a merge, or when asked to reload, refresh or update the plugins.
kind: utility
domain: machine
---

# Reload plugins

Read the [canonical shared definition](../../.agents/machine/utility/reload-plugins/SKILL.md).
This entry point adds only Claude Code's native mechanism.

## Claude Code

Claude Code installs marketplace updates itself. Ask the user to type `/reload-plugins`, the built-in
command that loads them into this session; an agent cannot run a slash command. When the newest published
plugins are not installed yet, run `claude plugin marketplace update` first, then ask for
`/reload-plugins`.
