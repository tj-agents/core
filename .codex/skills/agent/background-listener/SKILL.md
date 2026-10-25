---
name: background-listener
description: Run one deterministic command in the background and return its result through the current host completion notification. Use when waiting for a build, test, CI monitor or other deferred result while continuing work or parking the turn.
kind: utility
domain: process
---

Read the [shared background listener](../../../../.agents/agent/utility/background-listener/SKILL.md).

Use the current surface's native background completion primitive when available. When the surface
provides background `functions.exec` cells, `tools.write_stdin` and `notify`, start the command through
its process tool and attach one awaited relay to the returned `session_id`. Replace `12345` below with
that exact handle. Running reads stay inside the relay; command output is bounded until completion.

```js
const sessionId = 12345;
let output = "";
let truncated = false;
for (;;) {
  try {
    const update = await tools.write_stdin({session_id: sessionId, chars: "", yield_time_ms: 30000});
    const chunk = typeof update.output === "string" ? update.output : "";
    truncated ||= output.length + chunk.length > 8192;
    output = (output + chunk).slice(-8192);
    if (update.exit_code !== undefined) {
      notify({session_id: sessionId, output, truncated, terminal: true, exit_code: update.exit_code});
      break;
    }
  } catch (error) {
    notify({session_id: sessionId, output, truncated, terminal: true, error: String(error)});
    break;
  }
}
```

Use the documented background-cell syntax and keep the relay awaited; cells do not share local
variables. The callback returns the result to the owner, which reports it through the normal Codex turn
and existing user notification settings. Do not repeatedly call `functions.wait` or `write_stdin` from
model turns to discover completion. Standalone CLI surfaces do not inherit hosted tool APIs; apply the
shared capability result when their available tools provide no completion callback.
