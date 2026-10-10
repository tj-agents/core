# Direction changes become standing conventions

## Authorization and ownership

Bounded standards-defect side workstream under the standing authorization in
`engineering:session-guidance`, explicitly requested by Tommy ("future code should be written to those
standards ... so this doesn't happen again"). Authorized: implement, test, open the PR and merge once
this repository's gates pass. Installing into other scopes stays gated. Another session owns the Linux
port; its worktrees and PRs (#137, #166) are read-only here.

Worktree: `/home/tommy/projects/tj-agents/core/.worktrees/DirectionChange`
Branch: `Docs/DirectionChangeConventions`, from `origin/main` at `21b482c`
Lane: L2, run locally (L1 routes to Codex, whose launcher is not ported to Linux; #137).

## Defect

The Linux port decided that shipped code moves from PowerShell to Python, but recorded that only in its
plan. A plan governs only its own work, so other sessions kept writing Windows-only PowerShell (peer-cli's
`finish.ps1`/`close.ps1`), and the merge cleanup gate then depended on it. PR #166 adds the specific
platform rule; no standard required a direction decided in a plan or task to become a standing
convention. The nearest rule, `plans`' phase-end checkpoint, fires only at a phase boundary and does not
say the rule must reach the repository's always-loaded conventions.

## Decisions

- Owner: `engineering:docs-and-debt`, under "Sort a rule by the cost of missing it", because a direction
  is project-specific and silently costly to miss. It applies to every repository consuming engineering.
- Pointers, one sentence each, where the decision or dependency actually happens: `plan-authoring` (a plan
  that decides a direction lands the convention with it), `plan-execution` (the first slice in a direction
  lands a missing convention), `review` Stage 4 and `docs-review` Rules (check it), and
  `session-guidance` (always-loaded trigger for task-level decisions outside a plan).
- No machine check: detecting a direction change is semantic, so review is the enforcement.
- Added at Tommy's request: every noticed problem is fixed, handed off to an owner whose goal ends in a
  merged fix, or recorded in a `TECH_DEBT.md` entry merged to the default branch. Owner: `docs-and-debt`'s
  Tech debt section; `session-guidance` now covers every defect, not only material ones. Folded into this
  PR because it edits the same two files, which the handoff standard forbids offloading.
- `base:plan-artifacts` stays unchanged: guidance-corpus ownership is an engineering convention, and a
  base copy would be a second home.

## Steps

- [x] Owner text in `docs-and-debt` and description trigger.
- [x] Pointers in `plan-authoring`, `plan-execution`, `review`, `docs-review`, `session-guidance`.
- [x] Problem-recording rule in `docs-and-debt`; `review-lifecycle` and `address-review` point at it.
- [x] Local gates: both Python suites, `sync-generated.ps1 -Check` after local regeneration, catalog,
  harness and reachability checks.
- [ ] Docs review to a clean incremental pass, exact-head CI (`verify`, `verify-linux`), merge #168
  through `engineering:merge-docs`.
- [ ] After merge: retire this goal and the review work order in a docs-only closeout, and finish merge
  Step 5 for this worktree.

## Current progress

- PR: https://github.com/tj-agents/core/pull/168. Both Python suites green locally before each push
  (802 + 985 tests at `bf43af5`); generated, tier, catalog, harness and reachability checks pass.
  Exact-head CI run 37949300554 passed `guard`, `verify` and `verify-linux` at `bf43af5`.
- Docs review: full pass plus incremental passes, recorded in `reviews/Docs-DirectionChangeConventions.md`
  (its watermark is the review state); every retained finding fixed with its commit noted. Later passes began contradicting earlier fixes; the parent
  dropped those with reasons recorded in the work order.
- Tommy flagged that `docs-and-debt` bundles two jobs. With his explicit choice of Claude (Codex cannot
  launch on Linux), side session `splitdocsanddebt-24` runs at L3 in `.worktrees/SplitDocsAndDebt`, stacked
  on this branch (goal `plans/split-docs-and-debt/GOAL.md` there). It has acknowledged and rebases after
  each parent change; message it after every further parent commit.
- Found while answering why Codex cannot launch: `agent_cli.py` finds Codex on POSIX only via PATH,
  and agent shells here lack `~/.npm-global/bin`. Routed to the #137 owner (`core-46`), which accepted it
  and the missing Windows-only note in `handoff-codex` as required fixes before #137 merges.

## Next Steps

Finish the current incremental docs-review pass over the latest head, then wait for #168's exact-head
`verify` and `verify-linux`, merge through `engineering:merge-docs` (guidance and process tests only),
tell `splitdocsanddebt-24` to retarget its stacked PR to `main`, retire this goal and the work order in a
docs-only closeout, and finish merge Step 5 for this worktree.
