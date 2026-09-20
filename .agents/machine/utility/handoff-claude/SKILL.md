---
name: handoff-claude
description: Open an independent unmanaged Claude Code window in an exact repository or worktree with a prepared prompt and the full native Claude Code terminal UI. Use when asked to open Claude, open another Claude instance, hand work to a second Claude, or run something in a separate Claude window.

kind: utility
domain: machine
route: infer
---

# Claude Code handoff

The sibling of `handoff-codex`, for handing work to a second Claude Code rather than to Codex. For
opening a CLI the user drives themselves, with no prepared prompt, use `open-claude` instead. Either
harness can run either launcher — both only spawn a Windows Terminal tab, so neither depends on the
harness it is invoked from. What the prompt itself must contain is the `handoff` skill's subject, not
this one's.

Write the complete handoff prompt to a UTF-8 file before launching. Never relay a substantial prompt
through nested command strings or place its contents directly in the Windows Terminal invocation.

Resolve the exact repository or worktree directory the request concerns. Do not substitute another
checkout.

## Model selection

This launcher is a dumb transport — it never chooses a model itself, and it packages no external
resolver. Pass `-Model` only when the caller already knows which one to use: the user named a specific
model or tier explicitly, or the calling skill/workflow carries its own checked-in model-selection policy
(for example a `lanes` contract, where the calling repository ships one) and has already resolved it
before reaching this launcher. Never invent a selection policy here, and never default to the most
capable or most expensive model just because none was specified.

Launch with `scripts/launch-claude.ps1`, beside this file:

```powershell
& '<skill-directory>\scripts\launch-claude.ps1' -WorkingDirectory '<absolute-checkout-path>' -PromptPath '<absolute-prompt-path>' -Title '<short-title>'
```

Add `-Model '<model-id>'` only when a model was resolved as above. Omitting it lets `claude.exe` fall
back to its own configured default — the same behavior an interactively launched session gets.

Add `-DangerouslySkipPermissions` **only when the user asks for it in that request**. It disables every
permission prompt in the new window, so it is never a default and never inferred from the repository
being Tommy's own.

The launcher starts the native `claude.exe` directly as the Windows Terminal tab process. Do not replace
it with the npm/NVM `claude` shim, `claude.cmd`, `claude.ps1`, `node.exe`, or an intermediate PowerShell
command — the same launch paths that produced a degraded monochrome, non-interactive TUI for Codex.

The terminal invocation and the parent-session environment scrub belong to `scripts/agent-cli.ps1` under
`resources/machine/utility/scripts`, shared with `open-claude` and `handoff-codex`. Its comments carry the
reasoning for the `--window 0` tab targeting, the cleared session variables and the forced colour
variables; change that behaviour there, not here, and read it before altering any of them.

This is an unmanaged handoff. Do not invoke Agent Workboard, pass Workboard tokens, bind the session to
Workboard state, or imply that the new window will checkpoint workflow status.

Open only one Claude tab per requested handoff. After launch, report the target checkout and prompt file.
