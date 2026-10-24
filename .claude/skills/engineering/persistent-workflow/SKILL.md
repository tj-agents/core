---
name: persistent-workflow
description: Select Claude continuation for authorized work whose next decision may outlive this session.
kind: workflow
domain: process
---

Read the [shared continuation workflow](../../../../.agents/engineering/workflow/persistent-workflow/SKILL.md) and `engineering:persistent-delivery` first. They own goal identity, exact delivery binding, repair, review and authorization.

## Listener in this conversation

For a surface exposing the native Bash tool's `run_in_background` option, run the exact bound monitor
command with that option enabled and retain its returned task ID. Keep the session available for its
native completion notification and the user's existing alert settings. On `<task-notification>`, retrieve
that task's compact result once and
apply the shared wake/report contract. Do not run a second monitor or repeatedly call TaskOutput while
nothing has changed. A foreground shell started without background notification is not this listener.

```text
Bash command: the bound workflow_ops.py monitor command
run_in_background: true
Returned task ID: retain with the exact PR/head/run identity
Completion notification: read this task's result once, then report the next gate
```

Use another native monitor or channel only when the current surface documents it and the shared
notification contract is satisfied. Background Bash belongs to the live Claude session;
exiting the application ends that notification route. Source fixtures for task notifications do not
prove a live wake. A separately launched `claude -p` process does not notify this conversation.

## Durable work after this conversation

Claude `/goal`, `/loop`, monitors, channels and session restoration can continue or wake work only while their supported session is available. They do not continue after the application or terminal exits. For work that must continue across that boundary, use the supported adapter at `scripts/delivery_continuation.py`: Linux uses a reachable systemd user manager and Windows uses ScheduledTasks through inbox Windows PowerShell; it launches a fresh `claude -p` context in the initialized worktree.

The adapter supports `register`, `remove`, `list`, and `wake`. Register only after initialization and foreground claim; yield the foreground lease before waiting. Use `python3` on Linux/macOS and `python` on Windows; registration needs `--host-executable` with an absolute native path unless the owner already pins it. Linux timers do not change lingering or extend execution beyond the existing login/user-manager scope. If a scheduler prerequisite is unavailable, report the capability gate and checkpoint, then continue independent authorized work in the current session.

Fresh repair and review work follows the roles and lane selection in the shared contracts. Reuse the declared L4 lane for ordinary continuation; do not hardcode a model or imply authenticated host acceptance from source packaging.
