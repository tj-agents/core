---
name: sync-plugins
description: Bring this CLI's tj-agents plugins up to date and into the running session. Run it yourself, without asking, whenever plugins look outdated - a skill or hook is missing or behaves like an older version, or a plugin PR just merged - or when asked to sync, reload, refresh or update the plugins.
kind: utility
domain: machine
---

# Sync plugins

Read the [canonical shared definition](../../.agents/machine/utility/sync-plugins/SKILL.md).
This entry point adds only Codex's mechanism.

## Codex

Sync reloads hook runtime settings in the existing Codex daemon through its native configuration API,
then verifies every required hook definition and its trust state for the calling conversation's exact
checkout. It connects to the existing daemon without starting a replacement, changing hook trust or
closing other sessions. A failed live reload fails sync; a fresh-process inventory alone is insufficient.

Runtime hook reload does not replace instruction text already in model context. If the conversation
needs updated instructions, or its native process cannot be reloaded, preserve the current conversation
and follow the canonical same-conversation resume procedure with its exact ID and absolute directory.
New sessions load current instructions through normal startup.
