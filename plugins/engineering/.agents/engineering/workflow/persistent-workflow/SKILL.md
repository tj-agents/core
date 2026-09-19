---
name: persistent-workflow
description: Keep an authorized remote delivery owned across delayed checks using the selected host's supported continuation capability and one exact delivery identity.
kind: workflow
domain: process
---

# Persistent delivery continuation

Load `engineering:persistent-delivery` for binding, review, repair, authorization and terminal behavior.
Use this workflow when remote work has a future decision that needs an active continuation. Ordinary
foreground implementation remains with its current owner. The `.codex/` and `.claude/` adapters supply their host-specific continuation mechanisms and
reference this shared ownership contract. Host-only resources remain with the corresponding adapter.

Preserve one delivery identity and one continuation. Confirm the host's actual capability before
claiming unattended progress, bind it to the exact repository/head/worktree, and remove only this owner's
continuation when its authorized chain reaches terminal state. An unsupported host must report the
missing capability and keep a recoverable checkpoint. Installing this plugin never creates a task.
