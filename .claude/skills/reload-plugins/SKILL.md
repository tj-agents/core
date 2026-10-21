---
name: reload-plugins
description: Load the latest published tj-agents plugins into this CLI, named after Claude Code's native /reload-plugins. Use when a skill or hook is missing or out of date after a merge, or when asked to reload, refresh or update the plugins.
kind: utility
domain: machine
---

# Reload plugins

Read the [canonical shared definition](../../../.agents/machine/utility/reload-plugins/SKILL.md).
This entry point adds only Claude Code's native mechanism.

## Claude Code

Run the shared script with `--host claude` yourself, never hand that step to the user. A new session loads
the result on its own; ask the user for `/reload-plugins`, which an agent cannot run, only when this
session must use the change now.
