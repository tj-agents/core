---
name: persistent-workflow
description: Select Codex continuation for authorized work whose next decision may outlive this session.
kind: workflow
domain: process
---

Read the [shared continuation workflow](../../.agents/engineering/workflow/persistent-workflow/SKILL.md) and `engineering:persistent-delivery` first. They own goal identity, exact delivery binding, repair, review and authorization.

Use a Scheduled Task attached to the owning Codex conversation when the current surface can actually create, update, wake and remove it. Keep the initialized owner and canonical goal as its identity. Otherwise use the supported adapter at `scripts/delivery_continuation.py` after runtime initialization and foreground claim: Linux uses a reachable systemd user manager; Windows uses ScheduledTasks through inbox Windows PowerShell. It runs a fresh headless `codex exec` context in the bound worktree; it is not a return to this chat.

The adapter supports `register`, `remove`, `list`, and `wake`. Register only after initialization and claim; yield the foreground lease before waiting. On Linux/macOS invoke it with `python3`; on Windows invoke it with `python`. Registration requires an explicit absolute native executable (`--host-executable`) unless the owner already pins one. Linux timers do not change lingering or extend execution beyond the existing login/user-manager scope. Unsupported platforms or unavailable scheduler prerequisites are explicit capability gates. Continue independent authorized work in the foreground and report the recoverable checkpoint.

Fresh repair and review work follows the roles and lane selection in the shared contracts. Reuse the declared L4 lane for ordinary continuation; do not hardcode a model or imply authenticated host acceptance from source packaging.
