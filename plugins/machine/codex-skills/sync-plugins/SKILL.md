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

Sync attempts native hook reload for the calling conversation's exact checkout. If live reload is
unavailable, including a standalone `--no-daemon` client absent from the shared daemon, it automatically
arms verified closure and same-conversation resumption through the existing relaunch watcher. A shared
daemon lookup is not proof that a standalone client adopted anything. Required hook trust is verified
before arming; execution is verified in the fresh managed client.

When the result is `relaunch: armed`, preserve the checkpoint and end the turn so the watcher can resume
this exact conversation automatically. No user-run restart or `continue` is required. Runtime reload
does not replace instructions already in model context; fresh native startup performs session adoption.
