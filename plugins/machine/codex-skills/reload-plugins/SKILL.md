---
name: reload-plugins
description: Load the latest published tj-agents plugins into this CLI, named after Claude Code's native /reload-plugins. Use when a skill or hook is missing or out of date after a merge, or when asked to reload, refresh or update the plugins.
kind: utility
domain: machine
---

# Reload plugins

Read the [canonical shared definition](../../.agents/machine/utility/reload-plugins/SKILL.md).
This entry point adds only Codex's mechanism.

## Codex

Codex has no native plugin reload, so run the shared script with `--host codex`. It upgrades each
selected marketplace and re-adds its plugins. Codex then loads them in a new session, so tell the user to
start one.
