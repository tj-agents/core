---
name: handoff-codex
description: Open an independent unmanaged Codex tab in an exact repository or worktree with a prepared prompt, an optional caller-chosen model and effort, and the full native Codex terminal UI. Use when asked to open Codex, hand work to it, obtain a second opinion from it, or run a prompt against a specific Codex tier.

kind: utility
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

## Model selection

Pass `-Lane L1`–`L5` and the launcher resolves the model *and its reasoning effort* from the canonical
lane tables it ships under `resources/lanes` — the `engineering:lanes` ladder, and the repo's only
model-name owner, so no caller has to know a model id and a retiering is one edit in one authored file.
The pair matters here: a Codex model is priced and paced by both. An explicit `-Model` or
`-ReasoningEffort` still wins for whichever half the user named outright. Supply none and the CLI keeps
its own configured default, exactly as an interactively launched session would.

**The lane is the caller's judgement, and the launcher never guesses it** — a transport that inferred a
lane from the prompt would quietly decide the cost of every handoff. Choose by reversibility, blast
radius, ambiguity and verifiability — never by how hard the work feels:

| Lane | For |
|---|---|
| `L1` | Irreversible work at the top of the ladder, where a mistake cannot be taken back. |
| `L2` | Open-ended judgement at the top of the ladder, where the answer is not yet known. |
| `L3` | Ordinary specified work that a compiler or a test suite will catch. |
| `L4` | Mechanical work whose shape is already decided. |
| `L5` | Clerical work with a small input and no judgement to make. |

`-Frontier` selects the tier above the ladder from the same table, model and effort together. **Pass it
only when the user explicitly asked for that tier or its model by name.** No lane resolves to it —
frontier spend is the user's provenance to grant, never a reward for a hard-looking task — and it rejects
`-Lane` or `-Model` beside it. `-ReasoningEffort` is the one flag it still accepts, winning over the
tier's own effort, for a user who named the pace as well as the tier.

A calling skill or workflow that ships its own resolved selection may still pass `-Model` and `-ReasoningEffort` directly;
that wins over `-Lane`. What is no longer acceptable is inventing a model id at the call site.

Launch with `scripts/launch-codex.ps1`, beside this file:

```powershell
& '<skill-directory>\scripts\launch-codex.ps1' -WorkingDirectory '<absolute-checkout-path>' -PromptPath '<absolute-prompt-path>' -Title '<short-title>'
```

Add `-Lane '<L1..L5>'` (or `-Frontier`) to have the launcher resolve model and effort, or `-Model
'<model-id>'` and `-ReasoningEffort '<level>'` for values the user named. Omitting them all lets
`codex.exe` fall back to its own configured default — the same behavior an interactively launched
session gets.

Use `-BypassHookTrust` for Tommy's personal repositories. Omit it for an untrusted checkout or when the
user has not authorized repository hooks.

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
