---
name: sync-plugins
description: Bring this CLI's tj-agents plugins up to date and into the running session. Run it yourself, without asking, whenever plugins look outdated - a skill or hook is missing or behaves like an older version, or a plugin PR just merged - or when asked to sync, reload, refresh or update the plugins.
kind: utility
domain: machine
---

# Sync plugins

Read the [canonical shared definition](../../../.agents/machine/utility/sync-plugins/SKILL.md).
This entry point adds only Codex's mechanism.

## Codex

Codex has no in-session reload. When this session needs the change now, checkpoint and transfer the
authorized work through `workflow:handoff` and `machine:handoff-codex`. The handoff opens and confirms
exactly one fresh Codex session in the same worktree; it must carry the active goal, authority, and next
action before that successor writes. Do this without asking the user to exit or run a resume command.

New sessions load the installed plugins on their own. A successful launcher submission proves startup,
not pickup: preserve the handoff receipt and report fresh-session acknowledgement separately.
