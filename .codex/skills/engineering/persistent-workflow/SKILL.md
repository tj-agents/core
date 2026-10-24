---
name: persistent-workflow
description: Select Codex continuation for authorized work whose next decision may outlive this session.
kind: workflow
domain: process
---

Read the [shared continuation workflow](../../../../.agents/engineering/workflow/persistent-workflow/SKILL.md) and `engineering:persistent-delivery` first. They own goal identity, exact delivery binding, repair, review and authorization.

## Listener in this conversation

When the current surface documents background `functions.exec` cells, `tools.write_stdin` and `notify`,
start the bound monitor through its process tool, then attach one awaited relay to its returned
`session_id`. Replace `12345` below with that exact ID. The relay stays silent on empty reads and forwards
material output or process termination; it creates no second monitor or model polling loop.

```js
const sessionId = 12345;
for (;;) {
  try {
    const update = await tools.write_stdin({session_id: sessionId, chars: "", yield_time_ms: 30000});
    const terminal = update.exit_code !== undefined;
    const hasOutput = typeof update.output === "string" && update.output.trim() !== "";
    if (hasOutput || terminal) notify({output: update.output, terminal, exit_code: update.exit_code});
    if (terminal) break;
  } catch (error) {
    notify({terminal: true, error: String(error)});
    break;
  }
}
```

Use only the current surface's documented background-cell syntax and keep the relay awaited. Do not
infer idle-turn wake from these API names or from output collected with `functions.wait`; apply the
shared notification acceptance condition. Standalone Codex CLI does not inherit this surface's tools.
Native async hook output and the CLI's outbound `notify` setting do not start an idle conversation turn.
An existing exact-thread app-server connection can use `machine:followup-codex` only within that utility's
identity, authorization and delivery-verification contract. Queue submission alone is not notification
acceptance; do not start a daemon, resume a session or change host configuration to invent a route.

## Durable work after this conversation

Use a Scheduled Task attached to the owning Codex conversation when the current surface can actually create, update, wake and remove it. Keep the initialized owner and canonical goal as its identity. Otherwise use the supported adapter at `scripts/delivery_continuation.py` after runtime initialization and foreground claim: Linux uses a reachable systemd user manager; Windows uses ScheduledTasks through inbox Windows PowerShell. It runs a fresh headless `codex exec` context in the bound worktree; it is not a return to this chat.

The adapter supports `register`, `remove`, `list`, and `wake`. Register only after initialization and claim; yield the foreground lease before waiting. On Linux/macOS invoke it with `python3`; on Windows invoke it with `python`. Registration requires an explicit absolute native executable (`--host-executable`) unless the owner already pins one. Linux timers do not change lingering or extend execution beyond the existing login/user-manager scope. Unsupported platforms or unavailable scheduler prerequisites are explicit capability gates. Continue independent authorized work in the foreground and report the recoverable checkpoint.

Fresh repair and review work follows the roles and lane selection in the shared contracts. Reuse the declared L4 lane for ordinary continuation; do not hardcode a model or imply authenticated host acceptance from source packaging.
