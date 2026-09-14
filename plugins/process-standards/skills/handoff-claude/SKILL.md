---
name: handoff-claude
description: Open an independent unmanaged Claude Code window in an exact repository or worktree with a prepared prompt and the full native Claude Code terminal UI. Use when asked to open Claude, open another Claude instance, hand work to a second Claude, or run something in a separate Claude window.
domain: process
---

# Claude Code handoff

The sibling of `handoff-codex`, for handing work to a second Claude Code rather than to Codex. Either
harness can run either launcher — both only spawn a Windows Terminal tab, so neither depends on the
harness it is invoked from. What the prompt itself must contain is the `handoff` skill's subject, not
this one's.

Write the complete handoff prompt to a UTF-8 file before launching. Never relay a substantial prompt
through nested command strings or place its contents directly in the Windows Terminal invocation.

Resolve the exact repository or worktree directory the request concerns. Do not substitute another
checkout.

Launch with `scripts/launch-claude.ps1`, beside this file:

```powershell
& '<skill-directory>\scripts\launch-claude.ps1' -WorkingDirectory '<absolute-checkout-path>' -PromptPath '<absolute-prompt-path>' -Title '<short-title>'
```

Add `-DangerouslySkipPermissions` **only when the user asks for it in that request**. It disables every
permission prompt in the new window, so it is never a default and never inferred from the repository
being Tommy's own.

The launcher starts the native `claude.exe` directly as the Windows Terminal tab process. Do not replace
it with the npm/NVM `claude` shim, `claude.cmd`, `claude.ps1`, `node.exe`, or an intermediate PowerShell
command — the same launch paths that produced a degraded monochrome, non-interactive TUI for Codex.

It opens as a **new tab in the current Windows Terminal window**, not a new OS window — the `wt.exe`
invocation passes `--window 0`, WT's documented sentinel for "the window that most recently had focus."
This is not the same as omitting `--window` entirely: `windowingBehavior` is unset in this machine's WT
settings, so the *default* behavior with no `--window` flag at all is `useNew` — always a new window.
`--window 0` is the only thing that overrides that default; do not "simplify" this back to no flag, or to
`--window new`, which forces the opposite.

## The parent session's environment must not leak

A Claude Code session exports variables that make a child render plain and behave as a managed nested
session. Two different treatments are needed, not one:

- **Cleared** (set to nothing, not inherited): `NO_COLOR`, and the session-binding set `CLAUDECODE`,
  `CLAUDE_CODE_CHILD_SESSION`, `CLAUDE_CODE_ENTRYPOINT`, `CLAUDE_CODE_SESSION_ID`, `CLAUDE_PID`, the
  `CLAUDE_CODE_MESSAGING_*` pair, and the `WORKBOARD_*` pair. `NO_COLOR=1` alone makes the child black and
  white; the rest bind a child to the parent's session and messaging pipe.
- **Forced to an explicit value, never merely left unset**: `FORCE_COLOR=1` and `TERM=xterm-256color`. An
  automation-spawned `wt.exe`/`claude.exe` is not the interactive shell a human would have launched it
  from, so color/terminal-capability auto-detection cannot be trusted to land on a good value by itself —
  clearing `NO_COLOR` is necessary but was not sufficient on its own; leaving `TERM` blank risks a
  conservative dumb-terminal fallback instead of inheriting a real one.

`CLAUDE_CODE_GIT_BASH_PATH` is machine configuration, not session state, and is deliberately preserved.

This is an unmanaged handoff. Do not invoke Agent Workboard, pass Workboard tokens, bind the session to
Workboard state, or imply that the new window will checkpoint workflow status.

Open only one Claude tab per requested handoff. After launch, report the target checkout and prompt file.
