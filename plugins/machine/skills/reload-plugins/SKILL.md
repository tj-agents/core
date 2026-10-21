---
name: reload-plugins
description: Load the latest published tj-agents plugins into this CLI, named after Claude Code's native /reload-plugins. Run it yourself, without asking, whenever plugins look outdated - a skill or hook is missing or behaves like an older version, or a plugin PR just merged - or when asked to reload, refresh or update the plugins.
kind: utility
domain: machine
---

# Reload plugins

Read the [canonical shared definition](../../.agents/machine/utility/reload-plugins/SKILL.md).
This entry point adds only Claude Code's native mechanism.

## Claude Code

Afterwards native `/reload-plugins` loads the change into this session, and only the user can type it.
Ask for it only when this session needs the change now; new sessions load it on their own.
