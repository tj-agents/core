---
name: followup-codex
description: Send a follow-up or correction to an existing Codex session and verify recipient delivery. Use when asked to message another Codex session, check whether it received a follow-up, or recover from a queued message that did not arrive.
kind: utility
domain: machine
---

# Verified Codex follow-up

Use this only when the user authorized messaging the other session. Keep ownership of the current task.
For a child agent in the current conversation, use the host's native collaboration message tool instead.
This utility addresses an independent, already running Codex session; it does not perform a handoff.

Requires Python 3.9+, a native Codex executable with `app-server proxy` and the experimental direct-input
and paginated-history APIs, and an existing shared app-server daemon in the selected Codex profile.
The helper never starts a daemon, launches/resumes a session, edits Codex databases, changes configuration,
or injects terminal keystrokes. A standalone embedded TUI may have no reachable messaging endpoint.
Missing/older capabilities fail explicitly. Verified against the local 0.157.1 protocol schemas;
fixture validation is not proof that a particular live session is reachable.

1. Bind the exact thread UUID, expected working directory and Codex profile from the prior launch result
   or user-authorized session inspection. Never guess the newest conversation, a PID, or a window title.
2. Write the exact authorized message to a UTF-8 file. Choose a new receipt path outside version control
   and reuse it for this message. Do not put private message/history data into repository fixtures.
3. Invoke the shipped helper with properly quoted shell arguments. `--codex` accepts a native executable
   path, not a command string; supply the actual executable if the PATH entry is a shell shim.

```text
python -B "<skill-directory>/scripts/codex_followup.py" --codex "<codex-executable>" --timeout 20 send --thread <exact-uuid> --cwd "<expected-directory>" --codex-home "<selected-profile>" --message-file "<message-file>" --receipt "<receipt-file>"
```

The helper checks the server's thread identity, cwd, loaded membership and direct-input capability.
It steers the identified active turn using `expectedTurnId`, or starts a turn on the same loaded idle
thread. It preserves the recipient's model, permissions, working directory and configuration.
Before submission it exclusively creates a receipt containing a client message ID and message hash.
It then checks recipient history for that client ID. Receipt files are private runtime evidence.

Reusing a receipt only checks status; it never submits again. A disconnect or timeout after reserving a
receipt is uncertain delivery, not permission to retry with a fresh receipt. Check with:

```text
python -B "<skill-directory>/scripts/codex_followup.py" --codex "<codex-executable>" --timeout 20 status --receipt "<receipt-file>"
```

Report the returned status accurately:

- `delivered` (exit 0): the matching user message appears in the exact recipient's conversation. This
  proves delivery, not acknowledgment, execution, or completion. Claim acknowledgment only after an
  actual recipient response supports it.
- `accepted` or `unverified` (exit 2): delivery remains unproven. Report that plainly and retain the
  receipt. A missing queue entry, successful CLI exit, or timeout is not delivery evidence.
- `unavailable` or `rejected` (exit 2): report the reason. If no send was attempted, immediately give the
  authorized message as plain prose for the user to paste; do not claim it was sent or ask another
  permission question. If submission might have occurred, disclose that before any manual retry.

Do not substitute `codex queue` success for verified delivery. A queue entry can persist without the
recipient consuming it, particularly for an embedded session without a shared server. An older queued
message may still arrive later; do not silently enqueue or paste another copy. Do not repair transport by
starting a second owner, changing the recipient's profile, or restarting its terminal.
