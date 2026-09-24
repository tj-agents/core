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

## Model selection

Pass `-Lane` and the launcher resolves the model from `model-lanes.json`, the table it ships beside the
shared library, so no caller has to know a model id and a retiering is one edit in one file. `-Model`
still wins for a model the user named outright. Supply neither and the CLI keeps its own configured
default, exactly as an interactively launched session would.

**The lane is the caller's judgement, and the launcher never guesses it** — a transport that inferred a
lane from the prompt would quietly decide the cost of every handoff. Choose it from the work:

| Lane | Model | For |
|---|---|---|
| `L0` | `claude-fable-5` | Frontier deliberation: a foundational design decision or deep option synthesis. **Only when the user explicitly asks for it** — never inferred from difficulty, ambiguity or scope. |
| `L1` | `claude-opus-5` | Complex reasoning: architecture, diagnosis, review, security, irreversible or service-wide change. |
| `L2` | `claude-sonnet-5` | Everyday engineering. The default when nothing selects another lane. |
| `L3` | `claude-haiku-4-5-20251001` | Mechanical work already decided, caught by a compiler or a test. |

A calling skill or workflow that ships its own resolved selection may still pass `-Model` directly;
that wins over `-Lane`. What is no longer acceptable is inventing a model id at the call site.

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
`resources/machine/scripts`, shared with `open-claude` and `handoff-codex`. Its comments carry the
reasoning for the `--window 0` tab targeting, the cleared session variables and the forced colour
variables; change that behaviour there, not here, and read it before altering any of them.

This is an unmanaged handoff. Do not invoke Agent Workboard, pass Workboard tokens, bind the session to
Workboard state, or imply that the new window will checkpoint workflow status.

Open only one Claude tab per requested handoff. After launch, report the target checkout and prompt file.
