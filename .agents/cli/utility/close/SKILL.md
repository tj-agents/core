---
name: close
description: Close only this CLI client after the final reply, preserving unfinished work. Use when the user asks to close or dismiss the CLI; use cli:closeout to finish the workflow and then close.
kind: utility
domain: cli
route: infer
---

# Close this CLI

Close this session's verified frontend process when explicitly asked. Unfinished work, open pull requests,
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

Close only a verified frontend, preserving shared backends, other clients and the containing terminal.
Worktree sharing does not prevent independent closure. Never terminate a process tree or infer ownership
from a process name, inherited token or initial resume argument. Missing or ambiguous ownership leaves
the CLI open with a refusal. Closure requires verified frontend exit.

Managed Codex launches record native submitted-input IDs in a private temporary file and match the latest
one against native thread history. A new input or recorded view switch invalidates the pending close.
Arming freezes that input, native turn and rollout identity. The watcher reads native `task_complete`
for that exact turn and rechecks the binding immediately before signaling; stale or unavailable Stop-hook
turn state does not prevent refresh closure. A newer native turn, peer input, abort or changed rollout
cancels closure. Agent Store is never changed to manufacture idle evidence.
The launcher removes its recording when the frontend exits. Unmanaged clients without this evidence
remain open; report the exact managed resume command. In-harness subagents return to their parent and
have no separate CLI to close. Archiving a thread alone does not establish client exit.

`cli:closeout` owns workflow completion followed by closure and proof-guarded cleanup.
`machine:peer-cli` closes other sessions.

```text
User: "Close this CLI; I'll come back to the unfinished PR later."
Action: arm literal closure, report the unfinished PR, and end the turn. Leave its branch and checkout intact.
```
