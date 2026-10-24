---
name: background-listener
description: Run one deterministic command in the background and return its result through the current host completion notification. Use when waiting for a build, test, CI monitor or other deferred result while continuing work or parking the turn.
kind: utility
domain: machine
---

Read the [shared background listener](../../../../.agents/machine/utility/background-listener/SKILL.md).

For a surface exposing Bash `run_in_background`, run the exact command with that option enabled and
retain the returned task ID. Keep the session available for its native completion notification. On
`<task-notification>`, retrieve that task's result once and resume its owner through the shared contract.
Do not repeatedly call TaskOutput while waiting. Use another native background primitive only when
the current surface documents its completion callback.

```text
Bash command: the authorized command or deterministic watcher
run_in_background: true
Returned task ID: retain with the current task and working directory
Completion notification: read that task's output once, report the result and continue
```

Background Bash belongs to the live session and ends when Claude exits. Existing user notification
settings handle alerts; a separately launched `claude -p` context is not a callback to this conversation.
