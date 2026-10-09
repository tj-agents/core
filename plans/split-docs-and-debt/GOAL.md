# Split docs-and-debt into one skill per responsibility

## Authorization and ownership

Bounded standards-defect side workstream under the standing authorization in
`engineering:session-guidance`. Tommy called the bundling out ("docs and debt, why is it doing two things
at once? ... that's probably a tech debt") and explicitly chose to launch this Claude session for it
(the Codex CLI is installed, but its handoff launcher is Windows-only until PR #137). Authorized: implement, test,
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

- **Two owners: `docs` and `debt-records`.** First decided as three (`guidance-ownership`, `debt-records`,
  `working-docs`); Tommy questioned separating the guidance and working-markdown halves, and they were
  merged into `engineering:docs`. Both govern where a repository's markdown lives and when it goes away;
  the working-markdown rule is two paragraphs, so a separate skill cost more in discovery than it saved,
  and `docs` names the guidance half the old name hid. A scratch note is sometimes written without any
  guidance work; loading the guidance rules then costs only context. `base:plan-artifacts` was rejected as
  the working-markdown home: it is an always-loaded base policy about plans. Another installed plugin owns
  `anthropic-skills:docs`, so this repository always writes the qualified `engineering:docs`.
  - `engineering:docs` (`.agents/engineering/convention/docs/`): "Describe the intended behavior", "One
    rule, one home" with its subsections, "Make it machine-checked", "Sort a rule by the cost of missing
    it" including "A change of direction is a standing rule", and "Throwaway working markdown".
  - `engineering:debt-records` (`.agents/engineering/convention/debt-records/`): the "Tech debt" section.
    Not named `tech-debt`, which would sit one hyphen from the `techdebt` workflow.
- **The debt convention stays separate from the `techdebt` workflow.** Recording is consumed during any
  work that leaves a problem unfixed; `techdebt` is the resolution workflow loaded only when working debt
  down. `SKILL_KINDS.md` requires a separate owner for independently consumed responsibilities. `techdebt`
  keeps pointing at the recording standard, now by its new name.
- **Compatibility.** Published releases through `v2.1.15` ship `engineering:docs-and-debt`, and the
  `skills` alias table in `.agents/plugins/compatibility.json` maps one old name to one new name, so it
  cannot express a split. `docs-and-debt` therefore stays as a thin `convention` compatibility entry whose
  body only routes to the two owners (no rule text), with "remove after 2027-04-09" in its description,
  following the `gpp:gpp-scaffold` precedent. The `base:docs-and-debt` alias keeps resolving to it. Its
  removal is recorded in `.agents/engineering/TECH_DEBT.md` (a skill-local debt file would ship in
  every generated package), resolved after that date once no `tj-agents` consumer still names the old skill.
- **Rename allowlist** (`git grep -nIi docs-and-debt -- . ':!plugins'`):
  the compatibility entry's three files (`.agents/engineering/convention/docs-and-debt/SKILL.md`,
  `.codex/skills/docs-and-debt/SKILL.md`, `.claude/skills/docs-and-debt/SKILL.md`), the
  `base:docs-and-debt` alias in `.agents/plugins/compatibility.json`, its debt entry in
  `.agents/engineering/TECH_DEBT.md`, the compatibility entry's test in
  `.agents/hooks/tests/test_process_standards.py`, the authored `.agents/catalog/catalog.json` skill roster, this goal, and historical
  plans/reviews that record past work (`plans/direction-change-conventions/`, owned by the parent PR,
  `plans/outcome-verified-completion/`, `plans/pr-ownership/`, `reviews/`).

## Progress

- Steps 1–3 done in "Split docs-and-debt into guidance, debt and working-doc conventions". The branch was rebased
  six times onto the moving parent; each rebase re-moved its revised recording and direction-change text into
  `debt-records` and `guidance-ownership`, and retargeted its new pointers (`review-lifecycle`,
  `address-review`, session-guidance, and two `test_process_standards.py` tests).
- Step 4 passes on the rebased head over parent `bf43af5`: 802 + 985 tests, generation `-Check`, tier
  payload, catalog and harness `--check`, `docs_reachability.py`, packaging tests.
- Step 5: `reviews/Refactor-SplitDocsAndDebt.md` was approved after five passes over the three-skill
  split; the merge into `engineering:docs` (Tommy's decision) is reviewed as a further incremental pass.

## Delivery

- PR: https://github.com/tj-agents/core/pull/173 (draft, base `Docs/DirectionChangeConventions`, stacked on
  #168). Body validated; delivery bound with no recorded standing merge authorization in the binding.
- Continuation: this Linux machine has no cross-exit continuation adapter (the supported one is Windows-only),
  so the waits are owned by the live session. #168's owner (`.worktrees/DirectionChange`) notifies this
  session when #168 changes or merges; each parent change is absorbed by rebasing and re-moving its text.

## Side workstream

- Tommy flagged that no standard governs how a skill is authored. Launched as a bounded side workstream:
  `.worktrees/SkillAuthoringConvention`, branch `Docs/SkillAuthoringConvention`, goal
  `plans/skill-authoring-convention/GOAL.md`, Claude at lane L3 (launcher submission confirmed; pickup is
  recorded in that goal). This goal does not own it.

## Next Steps

Scope: whole goal through merge and cleanup.
Current slice: merge `guidance-ownership` and `working-docs` into `engineering:docs` on #173, validate,
incremental review, push.
Remaining scope: after #168 merges, rebase onto `main`, retarget #173 to `main`, re-validate, mark ready and
merge through `engineering:merge`, then Step 5 cleanup of this worktree.
Done when: the split is merged to `main` and this worktree is cleaned up.

Continue at Completion expectation step 4 for the merged `docs` skill.
