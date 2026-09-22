---
name: open-claude
description: Open a Claude Code CLI in a new Windows Terminal tab on an exact directory, optionally resuming a known session, with the full native colour TUI. Use when asked to open a Claude CLI, open a terminal running Claude, or reopen/resume a past conversation in its own window.

kind: utility
domain: machine
route: infer
---

# Open a Claude CLI

Opens an interactive Claude Code session the user drives themselves. Its sibling `handoff-claude` is for
delegating prepared work to a second Claude; this one is for putting a terminal in front of the user.
Both share `scripts/agent-cli.ps1` under `resources/machine/scripts`, which owns the terminal
invocation and the environment scrub.

Never open a Claude CLI by typing `claude` into a PowerShell command, `pwsh -Command`, `claude.cmd`,
`claude.ps1`, `node.exe`, or any other intermediate process. Those resolve to the npm/NVM shim, which
runs the TUI through an extra process and degrades it to a monochrome, non-interactive window. Use this
launcher, which starts the native `claude.exe` as the tab process.

Resolve the exact directory the request concerns and do not substitute another checkout.

```powershell
& '<skill-directory>\scripts\open-claude.ps1' -WorkingDirectory '<absolute-path>' -Title '<short-title>'
```

- `-Resume '<session-id>'` reopens a specific past session; `-Continue` reopens the most recent one for
  that directory. A session resumes only from the directory it was started in, so pass the session's own
  `cwd` as `-WorkingDirectory`.
- `-Prompt '<short instruction>'` seeds a first turn. For anything substantial write a file and pass
  `-PromptPath` instead; never relay a long prompt through a nested command string.
- `-Model '<model-id>'` only when the user named one or a checked-in selection policy already resolved
  it. Omitted, `claude.exe` uses its own configured default.
- `-DangerouslySkipPermissions` only when the user asks for it in that request.

It opens as a new tab in the current Windows Terminal window. Open one tab per request, and report the
directory and any session id afterwards.

## One tab, and never a second

The launcher **throws** on failure and prints `Launched claude handoff tab '<title>' …` on success. Those
are the only two outcomes.

**Never verify a launch by listing processes, and never re-run the launcher because one looked absent.**
A tab takes seconds to appear and a process listing is trivially misread — an unsorted `Select-Object
-First 3` is enough to miss the newest one. Re-running puts two agents on the same task in the same
repository, which is worse than no handoff at all: they collide on the same files with neither aware of
the other.

If the launcher printed its confirmation, the handoff happened. Report it and stop. If it threw, say so;
do not retry blind.
