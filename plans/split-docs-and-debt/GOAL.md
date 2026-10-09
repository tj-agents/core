# Split docs-and-debt into one skill per responsibility

## Authorization and ownership

Bounded standards-defect side workstream under the standing authorization in
`engineering:session-guidance`. Tommy called the bundling out ("docs and debt, why is it doing two things
at once? ... that's probably a tech debt") and explicitly chose to launch this Claude session for it
(Codex is not installed on this Linux machine; its launcher port is PR #137). Authorized: implement, test,
open the PR and merge once this repository's gates pass. Installing into other scopes stays gated.

Worktree: `/home/tommy/projects/tj-agents/core/.worktrees/SplitDocsAndDebt` (yours alone)
Branch: `Refactor/SplitDocsAndDebt`, stacked on `Docs/DirectionChangeConventions` at `7900a30`
Parent PR: the open PR whose head is `Docs/DirectionChangeConventions`
(`gh pr list --head Docs/DirectionChangeConventions`). Another session owns it and its worktree
`.worktrees/DirectionChange`; read only. The Linux-port session owns #137 and #166; read only.
Lane: L3. The skill names, the compatibility treatment and the boundary with the existing `techdebt`
workflow are unresolved design choices; the rename itself is then mechanical.

## Defect

`.agents/engineering/convention/docs-and-debt/SKILL.md` owns three unrelated concerns under one name:
guidance-corpus ownership (one rule one home, reachability, machine checks, sorting a rule by the cost of
missing it, and the new "A change of direction is a standing rule" section from the parent PR), tech-debt
recording (`TECH_DEBT.md` placement and deletion), and throwaway working markdown. The name hides the
guidance half, so a session deciding where a rule belongs, or deciding a refactor, does not think to load
it, and a guidance rule added there looks like a tech-debt change.

## Completion expectation

1. Read `AGENTS.md`, `README.md`, `SOURCE_LAYOUT.md`, `SKILL_KINDS.md`, `PACKAGING.md`, the current
   `docs-and-debt` skill, the `techdebt` workflow and `engineering:git-branching`.
2. Decide and record here: the new skill names (one guidance-ownership convention, one tech-debt
   convention), where throwaway working markdown belongs, whether the debt convention stays separate from
   the `techdebt` workflow, and how `engineering:docs-and-debt` consumers keep working (check the
   catalog's published release and compatibility commitments before removing a published skill name).
3. Move the sections without rewriting their rules, update both host entry points (`.codex/skills/`,
   `.claude/skills/`), `.agents/plugins/sources.json` and harness manifests as the generators require, and
   every reference (about 29 files). Rename definition of done: `grep -rniE "docs-and-debt"` over authored
   sources returns zero outside an explicit written allowlist.
4. Validate: both Python suites with `< /dev/null`, local `python -B scripts/update_catalog_digests.py`
   and `pwsh .agents/sync-generated.ps1` then `-Check`, tier payload, catalog `--check`, harness
   `--check`, `docs_reachability.py`. Leave `plugins/*` and catalog digest changes uncommitted.
5. Review with `engineering:review` (the diff touches package manifests, so not docs-review), open a
   stacked PR with base `Docs/DirectionChangeConventions`. Do not merge before the parent merges; then
   retarget to `main`, re-validate and merge through `engineering:merge`, and finish its Step 5 for this
   worktree.
6. Record the PR URL and outcome here.

## Decisions (step 2)

- **Three owners, not two.** Throwaway working markdown is neither guidance nor debt and is summoned by
  its own trigger (creating a scratch analysis or handoff note), so it is a third convention rather than a
  section bolted onto either half. `base:plan-artifacts` was rejected as its home: it is an always-loaded
  base policy about plans, and moving the rule there would grow base context and change package ownership.
  - `engineering:guidance-ownership` (`.agents/engineering/convention/guidance-ownership/`): "Describe the
    intended behavior", "One rule, one home" with its subsections, "Make it machine-checked", "Sort a rule
    by the cost of missing it" including "A change of direction is a standing rule".
  - `engineering:debt-records` (`.agents/engineering/convention/debt-records/`): the "Tech debt" section.
    Not named `tech-debt`, which would sit one hyphen from the `techdebt` workflow.
  - `engineering:working-docs` (`.agents/engineering/convention/working-docs/`): "Throwaway working markdown".
- **The debt convention stays separate from the `techdebt` workflow.** Recording is consumed during any
  work that leaves a problem unfixed; `techdebt` is the resolution workflow loaded only when working debt
  down. `SKILL_KINDS.md` requires a separate owner for independently consumed responsibilities. `techdebt`
  keeps pointing at the recording standard, now by its new name.
- **Compatibility.** Published releases through `v2.1.15` ship `engineering:docs-and-debt`, and the
  `skills` alias table in `.agents/plugins/compatibility.json` maps one old name to one new name, so it
  cannot express a split. `docs-and-debt` therefore stays as a thin `convention` compatibility entry whose
  body only routes to the three owners (no rule text), with "remove after 2027-04-09" in its description,
  following the `gpp:gpp-scaffold` precedent. The `base:docs-and-debt` alias keeps resolving to it. Its
  removal is recorded in `.agents/plugins/TECH_DEBT.md` with that date as the resolution condition.
- **Rename allowlist** (`grep -rniE "docs-and-debt"` over authored sources, excluding `plugins/`):
  the compatibility entry's three files (`.agents/engineering/convention/docs-and-debt/SKILL.md`,
  `.codex/skills/docs-and-debt/SKILL.md`, `.claude/skills/docs-and-debt/SKILL.md`), the
  `base:docs-and-debt` alias in `.agents/plugins/compatibility.json`, its debt entry in
  `.agents/plugins/TECH_DEBT.md`, the authored `.agents/catalog/catalog.json` skill roster, this goal, and historical
  plans/reviews that record past work (`plans/direction-change-conventions/`, owned by the parent PR,
  `plans/outcome-verified-completion/`, `plans/pr-ownership/`, `reviews/`).

## Progress

- Steps 1–3 done: the split, host entry points, catalog roster, references and compatibility entry landed
  in "Split docs-and-debt into guidance, debt and working-doc conventions". The branch was rebased twice
  onto the parent (`3f9ab37`, then `724e5b5`) and the parent's revised recording and direction-change text
  re-moved into `debt-records` and `guidance-ownership`; its new `review-lifecycle` and `address-review`
  pointers were retargeted at `debt-records`.
- Step 4 passed at `39588f6` (both suites, generation `-Check`, tier payload, catalog and harness `--check`,
  `docs_reachability.py`); re-run on the rebased candidate before the PR.
- Step 5: first review pass over `3f9ab37..39588f6` is in `reviews/Refactor-SplitDocsAndDebt.md`
  (6 findings, changes requested); fixes applied after the rebase.

## Next Steps

Scope: whole goal through merge and cleanup.
Current slice: commit the review fixes, re-validate, incremental review of the rebased candidate.
Remaining scope: stacked PR on `Docs/DirectionChangeConventions`, merge after the parent lands, Step 5
cleanup of this worktree.
Done when: the split is merged to `main` and this worktree is cleaned up.

Continue at Completion expectation step 4 on the rebased candidate.
