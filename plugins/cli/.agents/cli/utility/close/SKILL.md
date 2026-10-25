---
name: close
description: Close only this CLI tab after the final reply, preserving unfinished work. Use when the user asks to close or dismiss the CLI; use cli:closeout to finish the workflow and then close.
kind: utility
domain: cli
route: infer
---

# Close this CLI tab

Close this session's exact terminal tab when explicitly asked. Unfinished work, open pull requests,
pending checks and approvals do not prevent literal closure. Preserve the session for later resumption;
do not merge, complete a workflow, remove a checkout, run a worktree sweep, or close another CLI.
Honor an explicit keep-open request. A question about closure is not a request to close.

As your last command, run:

```text
python -B <skill-directory>/scripts/close_session.py arm      # Windows
python3 -B <skill-directory>/scripts/close_session.py arm     # Linux/macOS
```

Give a concise final reply with any unfinished work and end the turn. The detached watcher waits for
the reply to finish and about three seconds of idle time. A new prompt cancels closure. Arming is not
proof of closure: the receipt is `~/.agents-state/session-close/<session-id>.json`.

Close only a verified exact terminal target. Never terminate a shared backend or infer tab ownership
from a process name or a stale title. Missing or ambiguous ownership leaves the CLI open with a refusal.
Closure requires both the exact tab to disappear and its dedicated frontend to exit.

`cli:closeout` owns workflow completion followed by closure and proof-guarded cleanup.
`machine:peer-cli` closes other sessions.

```text
User: "Close this CLI; I'll come back to the unfinished PR later."
Action: arm literal closure, report the unfinished PR, and end the turn. Leave its branch and checkout intact.
```
