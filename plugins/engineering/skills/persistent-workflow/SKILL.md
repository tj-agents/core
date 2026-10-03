---
name: persistent-workflow
description: Select Claude continuation for authorized work whose next decision may outlive this session.
kind: workflow
domain: process
---

Read the [shared continuation workflow](../../.agents/engineering/workflow/persistent-workflow/SKILL.md) and `engineering:persistent-delivery` first. They own goal identity, exact delivery binding, repair, review and authorization.

Claude `/goal`, `/loop`, monitors, channels and session restoration can continue or wake work only while their supported session is available. They do not continue after the application or terminal exits. For work that must continue across that boundary, use the supported Windows adapter at `scripts/delivery-continuation.ps1`; it launches a fresh `claude -p` context in the initialized worktree.

The adapter supports `register`, `remove`, `list`, and `wake`. Register only after initialization and foreground claim; yield the foreground lease before waiting. If Windows or scheduler prerequisites are unavailable, report the capability gate and checkpoint, then continue independent authorized work in the current session.

Fresh repair and review work follows the roles and lane selection in the shared contracts. Reuse the declared L4 lane for ordinary continuation; do not hardcode a model or imply authenticated host acceptance from source packaging.
