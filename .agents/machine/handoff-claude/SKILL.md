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

Pass `-Lane L1`–`L7` and the launcher resolves the model from the canonical lane tables it ships under
`resources/lanes` — the `engineering:lanes` ladder, and the repo's only model-name owner, so no caller has
to know a model id and a retiering is one edit in one authored file. `-Model` still wins for a model the
user named outright. Supply neither and the CLI keeps its own configured default, exactly as an
interactively launched session would.

**The lane is the caller's judgement, and the launcher never guesses it** — a transport that inferred a
lane from the prompt would quietly decide the cost of every handoff. Choose by design, stakes, ambiguity
and verifiability, from the hardest judgement inside the delegated work — never by how
hard the work feels, and never raised by a merge, push or publish at its end, which the delivery gates
govern:

| Lane | For |
|---|---|
| `L1` | Plans and design decisions of any size, where the work decides how something should be built. |
| `L2` | High-stakes judgement that is not design, where a wrong call is costly or hard to undo. |
| `L3` | Open-ended judgement that is not design, where the answer is not yet known. |
| `L4` | Ordinary specified work that a compiler or a test suite will catch, delivery included. |
| `L5` | Mechanical work whose shape is already decided. |
| `L6` | Bulk clerical work whose input is too large for the cheapest rung. |
| `L7` | Clerical work with a small input and no judgement to make. |

Choose the launch lane for the work assigned to this independent session. If the successor later reaches
a different phase, it can route bounded work to an appropriate lane agent while retaining ownership.
Completing a plan in the current owning session does not call for this launcher; continue the same
authorized work there, directly or with a bounded lane agent. Use the `engineering:plans` transfer
criteria to decide whether another session should own the work.

`-Frontier` selects the tier above the ladder from the same table. **Pass it only when the user
explicitly asked for that tier or its model by name.** No lane resolves to the tier — L1 prices the same
family an effort step below, and frontier spend is the user's provenance to grant, never a reward for a
hard-looking task — and it rejects `-Lane` or `-Model` beside it.

A calling skill or workflow that ships its own resolved selection may still pass `-Model` directly;
that wins over `-Lane`. What is no longer acceptable is inventing a model id at the call site.

Launch with `scripts/launch-claude.ps1`, beside this file:

```powershell
& '<skill-directory>\scripts\launch-claude.ps1' -WorkingDirectory '<absolute-checkout-path>' -PromptPath '<absolute-prompt-path>' -Title '<short-title>'
```

Add `-Lane '<L1..L7>'` (or `-Frontier`) to have the launcher resolve the model, or `-Model '<model-id>'`
for one the user named. Omitting all three lets `claude.exe` fall back to its own configured default —
the same behavior an interactively launched session gets.

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
