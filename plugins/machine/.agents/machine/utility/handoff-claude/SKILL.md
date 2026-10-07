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
harness can run either launcher — both only spawn a terminal tab, so neither depends on the
harness it is invoked from. What the prompt itself must contain is the `handoff` skill's subject, not
this one's.

Write the complete handoff prompt to a UTF-8 file before launching. Never relay a substantial prompt
through nested command strings or place its contents directly in the terminal invocation.

Resolve the exact repository or worktree directory the request concerns. Do not substitute another
checkout.

It opens a new tab in the terminal this process is running inside (Windows Terminal, tmux, kitty or
Konsole).

## One tab, and never a second

The launcher **exits non-zero** on failure and prints `Launched claude handoff tab '<title>' …` on success.
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
second tab for the same handoff.

## Model selection

Pass `--lane L1`–`L7` and the launcher resolves the model from the canonical lane tables it ships under
`resources/lanes` — the `engineering:lanes` ladder, and the repo's only model-name owner, so no caller has
to know a model id and a retiering is one edit in one authored file. `--model` still wins for a model the
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
After a small or medium plan, the current owner normally continues directly or with a bounded lane agent;
planning alone does not call for this launcher. After a massive plan that was a substantial design phase,
`engineering:plans` normally transfers execution to one fresh harness from a durable phased plan, even in
the same checkout. Apply its context criteria and judgment to cases between those sizes.

`--frontier` selects the tier above the ladder from the same table. **Pass it only when the user
explicitly asked for that tier or its model by name.** No lane resolves to the tier — L1 prices the same
family an effort step below, and frontier spend is the user's provenance to grant, never a reward for a
hard-looking task — and it rejects `--lane` or `--model` beside it.

A lane's effort travels with its resolved model (`--lane L4`, for example, resolves both a model and an
effort from the table) and reaches `claude --effort <level>` automatically — a lane always opens the
exact session that rung's model and effort pair describes. An explicit `--model` beating the lane means
no lane effort applies either, matching the model it would have paired with. Some rungs (Claude's `L7`)
price no effort at all, and the launcher passes none rather than inventing one.

`--effort '<low|medium|high|xhigh|max>'` is accepted only together with an explicit `--model`, for a
calling skill or workflow (or a user) that already knows the exact pace it wants for a model it named
outright — passing `--effort` alone, or beside `--lane`/`--frontier`, is rejected, because a lane or the
frontier tier already carries its own effort for whichever model it resolves, and an effort picked
without reference to a specific model is exactly the caller's-guess defect this restriction exists to
prevent. `engineering:handoff`'s obligation to preserve a user-selected model, effort or frontier request
is why this flag exists at all, not a general invitation to invent one.

A calling skill or workflow that ships its own resolved selection may still pass `--model` directly;
that wins over `--lane`. What is no longer acceptable is inventing a model id (or, per above, an
unpaired effort) at the call site.

Launch with `scripts/launch_claude.py`, beside this file:

```sh
python3 '<skill-directory>/scripts/launch_claude.py' --working-directory '<absolute-checkout-path>' --prompt-path '<absolute-prompt-path>' --title '<short-title>'
```

Use `python` on Windows, `python3` everywhere else. On Windows, `python3` is often the Microsoft Store
alias stub rather than a real interpreter, and it fails rather than running the launcher.

Add `--lane '<L1..L7>'` (or `--frontier`) to have the launcher resolve the model and, where the table
prices one, its effort, or `--model '<model-id>'` for a model the user named outright, optionally paired
with `--effort '<level>'` for that exact model (never with `--lane` or `--frontier`; see above). Omitting
them all lets the CLI fall back to its own configured default — the same behavior an interactively
launched session gets.

Add `--dangerously-skip-permissions` **only when the user asks for it in that request**. It disables every
permission prompt in the new window, so it is never a default and never inferred from the repository
being Tommy's own.

The launcher starts the native `claude` executable directly as the terminal tab process. Do not replace
it with the npm/NVM `claude` shim, `claude.cmd`, `claude.ps1`, `node.exe`, or an intermediate shell
command — the same launch paths that produced a degraded monochrome, non-interactive TUI for Codex.

The terminal invocation and the environment scrub belong to `scripts/agent_cli.py` under
`resources/machine/scripts`, shared with `open-claude`. `handoff-codex` still uses the PowerShell
`agent-cli.ps1` until its own Python port lands.

This is an unmanaged handoff. Do not invoke Agent Workboard, pass Workboard tokens, bind the session to
Workboard state, or imply that the new window will checkpoint workflow status.

Open only one Claude tab per requested handoff. After launch, report the target checkout and prompt file.
