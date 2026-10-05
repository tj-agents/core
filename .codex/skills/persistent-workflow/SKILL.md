---
name: persistent-workflow
description: Select Codex continuation for authorized work whose next decision may outlive this session.
kind: workflow
domain: process
---

Read the [shared continuation workflow](../../../.agents/engineering/workflow/persistent-workflow/SKILL.md) and `engineering:persistent-delivery` first. They own goal identity, exact delivery binding, repair, review and authorization.

Use a Scheduled Task attached to the owning Codex conversation when the current surface can actually create, update, wake and remove it. Keep the initialized owner and canonical goal as its identity. If that surface is unavailable on Windows, use the supported adapter at `scripts/delivery-continuation.ps1` after runtime initialization and foreground claim. It runs a fresh headless `codex exec` context in the bound worktree; it is not a return to this chat.

The adapter supports `register`, `remove`, `list`, and `wake`. Register only after initialization and claim; yield the foreground lease before waiting. Unsupported platforms or unavailable scheduler prerequisites are explicit capability gates. Continue independent authorized work in the foreground and report the recoverable checkpoint.

Fresh repair and review work follows the roles and lane selection in the shared contracts. Reuse the declared L4 lane for ordinary continuation; do not hardcode a model or imply authenticated host acceptance from source packaging.
