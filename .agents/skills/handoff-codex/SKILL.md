---
name: handoff-codex
description: Open an independent unmanaged Codex tab in an exact repository or worktree with a prepared prompt, policy-routed model and effort, and the full native Codex terminal UI. Use when asked to open Codex, hand work to it, obtain a second opinion from it, or run a prompt against a specific Codex tier.

kind: operation
domain: machine
route: infer
---

# Codex handoff

The sibling of `handoff-claude`, for handing work to Codex rather than to a second Claude Code. Either
harness can run either launcher — both only spawn a Windows Terminal tab, so neither depends on the
harness it is invoked from. What the prompt itself must contain is the `handoff` skill's subject, not
this one's.

Write the complete handoff prompt to a UTF-8 file before launching. Never relay a substantial prompt
through nested command strings or place its contents directly in the Windows Terminal invocation.

Resolve the exact repository or worktree directory the request concerns. Do not substitute another
checkout.

## Route before launch

Route declaration: infer `reversibility`, `blast`, `ambiguity`, `verifiability`, and task `tags` from the
delegated task. Set `authorization=frontier` only when the user explicitly requested the frontier/top tier
or a checked-in workflow declaration supplied it; never infer that authorization from size, difficulty,
ambiguity, or importance.

Immediately before launch, run `~/.claude/routing/route.py` with those parameters and parse its JSON output.
Do not choose, remember, or substitute a model or effort. The launch binding is exactly:

```powershell
$route = python (Join-Path $env:USERPROFILE '.claude\routing\route.py') @routeArguments | ConvertFrom-Json
& '<skill-directory>\scripts\launch-codex.ps1' -WorkingDirectory '<absolute-checkout-path>' -PromptPath '<absolute-prompt-path>' -Title '<short-title>' -Model $route.codex_model -ReasoningEffort $route.codex_effort -BypassHookTrust
```

Treat a missing resolver, failed resolver, invalid JSON, or absent `codex_model`/`codex_effort` field as a
hard stop. Re-route each separate handoff; an earlier result on the same plan is not reusable.

Launch with `scripts/launch-codex.ps1`, beside this file:

```powershell
& '<skill-directory>\scripts\launch-codex.ps1' -WorkingDirectory '<absolute-checkout-path>' -PromptPath '<absolute-prompt-path>' -Title '<short-title>' -Model $route.codex_model -ReasoningEffort $route.codex_effort -BypassHookTrust
```

Use `-BypassHookTrust` for Tommy's personal repositories. Omit it for an untrusted checkout or when the
user has not authorized repository hooks.

`-Model` and `-ReasoningEffort` are mandatory routed inputs for this skill. They come only from the resolver
fields above; the launcher remains a dumb transport and the caller owns routing.

## Which executable it starts, and why the choice is not free

It starts a **native** `codex.exe` directly as the Windows Terminal tab process. Do not replace it with
the npm/NVM `codex` shim, `codex.cmd`, `codex.ps1`, `node.exe`, or an intermediate PowerShell command:
those launch paths have produced a degraded monochrome/non-interactive TUI.

There is more than one native `codex.exe` on a machine, and **the newest file is not the newest build**:

- The npm package ships a vendored native binary per platform under its own `node_modules`; the thing on
  PATH is only a JavaScript entry point in front of it. The launcher takes the binary, not the entry point.
- The desktop app caches each downloaded runtime in a hash-named directory and *adds* rather than
  replaces, so that folder accumulates stale payloads indefinitely.

So the launcher enumerates both sources, asks each candidate for `--version`, and picks the highest
**version**, ranking a prerelease below the release it precedes. It replaces two defects, not one: the
old launcher searched only the desktop cache, so the npm build was never a candidate at all, and within
that cache it ranked by `LastWriteTime` — landing on 0.151.0-alpha.7.1. Date-ranking stays wrong even
once both sources are searched, because a freshly downloaded alpha's file is newer than the release it
precedes.

**The model roster is gated on the CLI version.** The stale build could not offer the current roster whatever
the account was entitled to. That is why the launcher fails loudly below `-MinimumVersion` (default
`0.154.0`, the oldest build observed to carry the current roster) rather than quietly running an old one. If it refuses, run
`npm install -g @openai/codex@latest` — do not lower the floor to get past it.

It opens as a **new tab in the current Windows Terminal window**, not a new OS window — the `wt.exe`
invocation passes `--window 0`, WT's documented sentinel for "the window that most recently had focus."
This is not the same as omitting `--window` entirely: `windowingBehavior` is unset in this machine's WT
settings, so the *default* behavior with no `--window` flag at all is `useNew` — always a new window.
`--window 0` is the only thing that overrides that default; do not "simplify" this back to no flag, or to
`--window new`, which forces the opposite. Handing off several related tasks against the same repository
means several tabs in this one window, not several windows.

## The parent session's environment must not leak

A Claude Code parent exports variables that make a child render plain and behave as a managed nested
session. Two treatments are needed, not one:

Everything is **cleared**; nothing is forced. `NO_COLOR`, `TERM`, the session-binding set `CLAUDECODE`,
`CLAUDE_CODE_CHILD_SESSION`, `CLAUDE_CODE_ENTRYPOINT`, `CLAUDE_CODE_SESSION_ID`, `CLAUDE_PID`, the
`CLAUDE_CODE_MESSAGING_*` pair, and the `WORKBOARD_*` pair.

**`TERM` is cleared here and forced in `handoff-claude`, and that difference is deliberate.** Claude Code
exports `TERM=xterm-256color`, which suits a Node CLI reading `supports-color`. Codex is a Rust/crossterm
binary, and on native Windows an unset `TERM` is what selects the console's truecolor path — handing it a
POSIX terminfo name instead caps the palette at 256 colours and visibly wrecks the theme. `COLORTERM` is
not set on this machine either, so there is nothing for the leaked `TERM` to be overridden by. Do not
"align" the two launchers; the runtimes differ, so the correct handling differs.

Only variables observed in a real parent session are listed. Codex's own exported session state has not
been read from one, so nothing is cleared on a guess.

This is an unmanaged handoff. Do not invoke Agent Workboard, pass Workboard tokens, bind the session to
Workboard state, or imply that Codex will checkpoint workflow status.

Open only one Codex tab per requested handoff. After launch, report the target checkout, the prompt file,
and the `codex-cli` version the launcher printed.
