# Split docs-and-debt into one skill per responsibility

## Authorization and ownership

Bounded standards-defect side workstream under the standing authorization in
`engineering:session-guidance`. Tommy called the bundling out ("docs and debt, why is it doing two things
at once? ... that's probably a tech debt") and explicitly chose to launch this Claude session for it
(the Codex CLI is installed, but its handoff launcher is Windows-only until PR #137). Authorized: implement, test,
open the PR and merge once this repository's gates pass. Installing into other scopes stays gated.

Worktree: `/home/tommy/projects/tj-agents/core/.worktrees/SplitDocsAndDebt` (yours alone)
Branch: `Refactor/SplitDocsAndDebt`, rebuilt on `origin/main` at `38550a7` on 2026-10-11 (first stacked on
`Docs/DirectionChangeConventions`; see Unstacking below).
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

- **Two owners: `docs` and `write-debt`.** First decided as three (`guidance-ownership`, `debt-records`,
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
  - `engineering:write-debt` (`.agents/engineering/convention/write-debt/`): the "Tech debt" section.
- **Debt skills named for their two jobs.** First named `debt-records` to avoid `tech-debt` beside the
  `techdebt` workflow; Tommy rejected both names: the two skills are writing debt and addressing debt. The
  recording convention is `engineering:write-debt` (never released, so no alias) and the resolution workflow
  `techdebt` is renamed `engineering:address-debt`. `engineering:skill-authoring` (#176) gives a one-to-one
  rename an alias, but the router checks proof against the old bare name, so an alias that changes it
  deadlocks a route (found in review; fixed separately by `Fix/RenameAliasRouting`). `techdebt` therefore
  stays as a routing-only compatibility entry, with its removal recorded in `.agents/engineering/TECH_DEBT.md`.
- **The debt convention stays separate from the `address-debt` workflow.** Recording is consumed during any
  work that leaves a problem unfixed; `address-debt` is the resolution workflow loaded only when working debt
  down. `SKILL_KINDS.md` requires a separate owner for independently consumed responsibilities. `address-debt`
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

## Final decision (2026-10-11)

Tommy: no stubs. `docs-and-debt` and `techdebt` are deleted outright. The alias table maps
`docs-and-debt` → `engineering:docs` and `techdebt` → `engineering:address-debt` (`base:` and
`engineering:` forms); a route naming the old `techdebt` resolves through the alias once #197
(`Fix/RenameAliasRouting`) carries renamed bare names through proof. The `docs` name is kept despite
`anthropic-skills:docs`, also Tommy's decision; this repository always writes `engineering:docs`. Earlier
decisions below about compatibility entries are superseded.

## Delivery

- PR: https://github.com/tj-agents/core/pull/173, now based on `main`.
- Unstacking (2026-10-11): #173 was stacked on #168 only because #168 also edited `docs-and-debt`; that cost
  six rebases and left #173 waiting on an unrelated PR. Tommy called it out. #173 was rebuilt on `main` by
  splitting `main`'s `docs-and-debt` text (`backup/SplitDocsAndDebt-stacked` keeps the stacked history
  locally). #168's owner moves its new paragraphs into `engineering:docs` (direction change) and
  `engineering:write-debt` (noticed problems) when it rebases.
- Continuation: the Linux machine has no cross-exit continuation adapter, so waits are owned by this
  session.

## Side workstream

- Tommy flagged that no standard governs how a skill is authored. Launched as a bounded side workstream:
  `.worktrees/SkillAuthoringConvention`, branch `Docs/SkillAuthoringConvention`, goal
  `plans/skill-authoring-convention/GOAL.md`, Claude at lane L3 (launcher submission confirmed; pickup is
  recorded in that goal). This goal does not own it.
- Review of the `address-debt` rename found that the skill router cannot follow an alias that changes a
  skill's bare name. Launched as a bounded side workstream: `.worktrees/RenameAliasRouting`, branch
  `Fix/RenameAliasRouting`, goal `plans/rename-alias-routing/GOAL.md`, Claude at lane L4. It will message
  this session when merged, so `techdebt` can become an alias if #173 is still open.

## Transfer checkpoint — 2026-10-11

Tommy explicitly requested a Codex handoff to finish and merge this split, then stop for the day.
Claude predecessor: `9c9d6521-ab19-404a-85b9-56f63635ff4c`, kitty tab `Split docs-and-debt`, window 4.
Its transcript ended at the monthly usage limit after the PR-check watcher succeeded at 14:20 UTC;
its visible terminal is idle. Do not resume that Claude writer while the Codex successor owns this goal.
Ownership transfers to one native Codex successor in this exact worktree. The transferring session
will make no further deliverable writes after launcher submission.

Observed delivery state: PR https://github.com/tj-agents/core/pull/173 is OPEN, base `main`, head
`a12811eb4dce4e9383ab2fedcbdd8ba1c6f737d3`; guard, verify-linux and verify-windows all succeeded.
The worktree is clean. Review watermark is `7a029f73b963c12547bd59d7958673da40f042b5`;
the following commit records that review. Claude reported 1062 + 1052 tests and all generation checks
passing. Review and CI evidence must be checked against the actual delivery candidate.

Main has since received PR #204 and generated commit `1406d04c`. It added core-adoption debt,
self-session host-side execution guidance in peer-cli and a merge pointer, and already removed the
stale Linux-plan link from CODE_CONVENTIONS.md. Preserve those changes when synchronizing; the separate
Linux-link docs PR mentioned in the old Next Steps is no longer needed. This does not add automatic
plugin installation or change close.py runtime behavior.

PR #197 (RenameAliasRouting) remains OPEN. The existing review records its dependency as an accepted
finding under Tommy's no-stubs decision. Read that disposition and current source before delivery;
do not silently merge another owner's PR or reintroduce compatibility stubs.

Handoff lane: L4 — the split design is settled; remaining work includes ordinary integration/review
judgment and validated delivery. Native Codex profile now has base, engineering and machine installed,
with 13 hooks enabled/trusted and this predecessor registered. Fresh successor registration still needs
observation; launcher submission alone does not prove it.

## Next Steps

Scope: finish this existing goal through PR #173 merge and linked-worktree cleanup; do not take on
core installation automation, marketplace naming, or unrelated workstreams.

1. Acknowledge Codex pickup in this goal with your native session identity before deliverable changes.
   Inspect the clean branch, PR #173, canonical review and current base. Read the applicable repository
   and merge/review instructions. Preserve Tommy's final decision: `engineering:docs`,
   `engineering:write-debt`, `engineering:address-debt`, and no docs-and-debt/techdebt stubs.
2. Follow the merge workflow's synchronization and review policy for the newer main changes. Preserve
   PR #204's guidance/debt and migrate any newly introduced references to the split owners if required.
   Complete any necessary focused validation and incremental review, commit/push coherently, and prove
   the exact PR head is the intended candidate. Keep generated plugins uncommitted.
3. When the actual candidate's gates pass, merge PR #173 through the authorized repository merge path.
   Tommy has explicitly authorized merge; do not stop to ask again. If a real delivery gate cannot be
   resolved within this scope, record its concrete resolver/resume condition and report it honestly.
4. Confirm the merge and generated package publication, then finish Step 5 cleanup for this linked
   worktree using the supported host-side path when process namespaces hide the native CLI. Retain
   PID/start-time and exact terminal identity checks. Remove the canonical review only after merge.
   Report the merged PR and cleanup outcome. Do not initiate unrelated work or broad machine shutdown.

Done when: PR #173 is merged to main and this delivery worktree/session cleanup is verified, or a
concrete unresolved delivery gate is recorded with the exact resumption condition.
