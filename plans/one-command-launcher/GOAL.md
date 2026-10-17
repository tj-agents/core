# One-command launcher for runnable projects

Repair workflow: engineering:self-repair
Source owner: tj-agents/core (base or engineering policy; successor chooses the owning skill)
Callout: session 9d8cff7b-a0d2-4ecd-bc2b-e08b4e0d2ff7, callout id none issued (callout gate state absent),
prompt sha256 a47e7eb9b9b284d71674a0841602e6ed8d2414640a9617c8a185bdde667cd0b7

## Authorization

Standing standards-defect authority (`engineering:session-guidance`, `engineering:self-repair`) plus Tommy's
explicit request on 2026-10-17: "You should always set up like a quick and easy like script that I can just invoke
once and it will automate all of this crap. This should probably be in Core so it never happens again."
Covers this bounded Core repair through implementation, tests, review, PR, merge and publication once core's gates
pass. Does not cover installing into consuming repos or changing stack plugins (python, dotnet, react, ...).

## Observed mistake

- Project: `C:\Users\TommySeery\source\repos\marketplace-car-hunter` (new Python app, built 2026-10-17).
- After building it, the agent answered "how do I run this app?" with a list of manual steps: put uv on PATH,
  `uv sync`, copy `.env.example`, `playwright install chromium`, `car-hunter login`, `car-hunter run`.
- Tommy: "I'm not typing all of that. Why can't it just be quick and easy?"
- Cause: no Core rule says a runnable project must ship one idempotent command that bootstraps and starts it.
  The governing standard is missing, not violated. `python:scaffold` is also silent (separate repo, not in scope).
- Consumer fix already shipped: marketplace-car-hunter `run.ps1` + `run.cmd` (commit 01da009): finds or installs
  uv, `uv sync --locked`, creates `.env` from `.env.example`, installs Chromium only for browser commands, no args
  starts the dashboard and opens it, otherwise passes the command through.

## Expected completion

1. Record this as the next `M` entry in `MISTAKES.md` (per `engineering:write-mistake`), linking this goal.
2. Add the rule to the owning Core policy with minimum words. Proposed wording:
   "A runnable project ships one idempotent launcher at its root (`run.ps1` plus `run.cmd` on Windows, `run` on
   POSIX) that installs or locates its toolchain, syncs dependencies, creates local config from its example, and
   starts the app with no arguments, passing any arguments through to the app's CLI. Setup and run instructions
   lead with it; never answer 'how do I run this' with a manual step list."
3. Route it so it applies when a project is created or first made runnable (e.g. from `idea-initialization` or the
   scaffold-handoff step), not only when someone remembers. Core must not name stack plugins.
4. Regenerate packages, run core's tests, review, PR, merge.
5. Record in this goal a follow-up note that stack scaffolds (`python:scaffold` etc.) should generate the launcher,
   as a separate repair for those repos.

## Next Steps

1. Read this goal, `MISTAKES.md`, and the candidate owning policies (`.agents/base/policy/*`,
   `.agents/engineering/policy/session-guidance`), then acknowledge pickup below.
2. Do items 1–5 of Expected completion in this worktree on branch `Fix/OneCommandLauncher`.

## Progress

- 2026-10-17: goal created by the originating session; worktree
  `C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-OneCommandLauncher` from origin/main d347903e.
