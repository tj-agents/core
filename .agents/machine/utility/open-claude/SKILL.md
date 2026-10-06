---
name: open-claude
description: Open a Claude Code CLI in a new terminal tab on an exact directory, optionally resuming a known session, with the full native colour TUI. Use when asked to open a Claude CLI, open a terminal running Claude, or reopen/resume a past conversation in its own window.

kind: utility
domain: machine
route: infer
---

# Open a Claude CLI

Opens an interactive Claude Code session the user drives themselves. Its sibling `handoff-claude` is for
delegating prepared work to a second Claude; this one is for putting a terminal in front of the user.
The terminal invocation and the environment scrub belong to `scripts/agent_cli.py` under
`resources/machine/scripts`. `handoff-claude` and `handoff-codex` still use the PowerShell
`agent-cli.ps1` until their own Python ports land.

Never open a Claude CLI by typing `claude` into a shell command, an npm shim such as `claude.cmd`, or
`node.exe`, or any other intermediate process. Those resolve to the npm/NVM shim, which runs the TUI
through an extra process and degrades it to a monochrome, non-interactive window. Use this launcher,
which starts the native `claude` executable as the tab process.

Resolve the exact directory the request concerns and do not substitute another checkout.

```sh
python3 '<skill-directory>/scripts/open_claude.py' --working-directory '<absolute-path>' --title '<short-title>'
```

On Windows, use `python` instead of `python3` if `python3` is not on PATH.

- `--resume '<session-id>'` reopens a specific past session; `--continue` reopens the most recent one for
  that directory. A session resumes only from the directory it was started in, so pass the session's own
  `cwd` as `--working-directory`.
- `--prompt '<short instruction>'` seeds a first turn. For anything substantial write a file and pass
  `--prompt-path` instead; never relay a long prompt through a nested command string.
- `--model '<model-id>'` only when the user named one or a checked-in selection policy already resolved
  it. Omitted, the CLI uses its own configured default.
- `--dangerously-skip-permissions` only when the user asks for it in that request.

It opens a new tab in the terminal you are running in (Windows Terminal, tmux, kitty or Konsole). Open
one tab per request, and report the directory and any session id afterwards.

## One tab, and never a second

The launcher **exits non-zero** on failure and prints `Launched claude tab '<title>' …` on success. Those
are the only two outcomes. `standards:` lines before them report the pre-launch plugin refresh, which
never blocks the launch.

**Never verify a launch by listing processes, and never re-run the launcher because one looked absent.**
A tab takes seconds to appear and a process listing is trivially misread — an unsorted `Select-Object
-First 3` is enough to miss the newest one. Re-running puts two agents on the same task in the same
repository, which is worse than no handoff at all: they collide on the same files with neither aware of
the other.

If the launcher printed its confirmation, the handoff happened. Report it and stop. If it exited
non-zero, say so; do not retry blind.
