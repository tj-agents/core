---
name: open-cli
description: Bring back any Claude or Codex CLI session from a session id, a topic or a directory, without choosing the host. A session that is still running has its existing terminal tab focused; a closed one is reopened in its own host and recorded directory. Use when asked to open, reopen, resume, switch to, find the window of or bring back a CLI, agent or conversation.

kind: utility
domain: machine
route: infer
---

# Open a CLI session

The caller names the session, never the host. `agent_recovery.py reopen` searches Claude and Codex history,
picks the one session, then either focuses its live tab or reopens it with the host's own launcher. The
host adapters [`open-claude`](../open-claude/SKILL.md) and [`open-codex`](../open-codex/SKILL.md) remain
the launch primitives it calls; do not use them to answer a user request that names a session.

Run with `python` on Windows or `python3` on Linux/macOS:

```sh
python -B '<skill-directory>/../../resources/machine/scripts/agent_recovery.py' reopen --target '<session-id | topic | directory>'
```

- `--target` is an exact native session id, a case-insensitive topic matched against ids, tab titles and
  messages, or an existing directory whose sessions are searched. An exact id wins over a topic.
- More than one match is refused with the candidates listed. Pass the exact id, or `--latest` to take the
  most recently active match when the user asked for "the last one".
- `--host claude|codex` only narrows a search; it is never required.
- `--prompt` or `--prompt-path` seeds a reopened session's first turn and is ignored when a live tab is
  focused. Follow the [task recovery context](../../resources/task-recovery.md) for recovery prompts.
- `--claude-history-root` and `--codex-history-root` select an alternate profile.

The JSON result carries `action`: `focused` for a verified-live session and `opened` for a reopened one.

## Live sessions are focused, never duplicated

A session whose recorded process is verified live is never launched a second time, because two writers on
one conversation corrupt it. Its registered terminal tab is focused instead (Windows Terminal, tmux, kitty).
If the tab cannot be focused the command fails and names why; report that to the user rather than
reopening. A session whose liveness is unknown is refused until the user confirms it has no live writer, then
pass `--confirm-closed`. Never retry after an ambiguous terminal result (exit 3).
