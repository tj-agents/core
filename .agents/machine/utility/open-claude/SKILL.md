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
`resources/machine/scripts`, shared with `handoff-claude` and `handoff-codex`. The terminal claude
launcher (`claude-profile.ps1`) still uses the PowerShell `agent-cli.ps1` until its own Python port lands.

Never open a Claude CLI by typing `claude` into a shell command, an npm shim such as `claude.cmd`, or
`node.exe`, or any other intermediate process. Those resolve to the npm/NVM shim, which runs the TUI
through an extra process and degrades it to a monochrome, non-interactive window. Use this launcher,
which starts the native `claude` executable as the tab process.

Resolve the exact directory the request concerns and do not substitute another checkout.

```sh
python3 '<skill-directory>/scripts/open_claude.py' --working-directory '<absolute-path>' --title '<short-title>'
```

Use `python` on Windows, `python3` everywhere else. On Windows, `python3` is often the Microsoft Store
alias stub rather than a real interpreter, and it fails rather than running the launcher.

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

The launcher **exits non-zero** on failure and prints `Launched claude tab '<title>' …` on success.
`standards:` lines before them report the pre-launch plugin refresh, which never blocks the launch.

Exit code **3 is distinct from every other failure**: it means the terminal control command timed out
after the tab may already have opened, not that the launch definitely failed. Check the terminal for the
tab before doing anything else; never relaunch automatically on exit 3. Any other non-zero exit means the
launch did not happen.

**Never verify a launch by listing processes, and never re-run the launcher because one looked absent.**
A tab takes seconds to appear and a process listing is trivially misread — an unsorted `Select-Object
-First 3` is enough to miss the newest one. Re-running puts two agents on the same task in the same
repository, which is worse than no handoff at all: they collide on the same files with neither aware of
the other.

If the launcher printed its confirmation, the handoff happened. Report it and stop. If it exited
non-zero, say so; do not retry blind — and never retry on exit code 3 specifically, where a retry risks a
second tab for the same request.
