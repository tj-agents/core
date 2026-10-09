# Add a skill-authoring convention

## Authorization and ownership

Bounded standards-defect side workstream under the standing authorization in
`engineering:session-guidance`. Tommy called the gap out while the docs-and-debt split was in progress
(2026-10-09): "we should have a skills conventions im ngl, liek a meta skill for writing skills ... as ive
noticed u dont make skill in the right way." Authorized: implement, test, open the PR and merge once this
repository's gates pass. Installing into other scopes, publishing outside this repository and destructive
operations stay gated.

Worktree: `/home/tommy/projects/tj-agents/core/.worktrees/SkillAuthoringConvention` (yours alone)
Branch: `Docs/SkillAuthoringConvention`, from `origin/main` at `49c618c`.
Originating session: `.worktrees/SplitDocsAndDebt` (PR #173, stacked on #168). Read only; it keeps its own
goal. #168 (`.worktrees/DirectionChange`) is also read only.
Lane: L3. Owner, scope and the shape of the rules are unresolved design; the edits are then mechanical.

## Defect

No standard tells an agent how to author a skill. What exists is scattered and partial:

- `SKILL_KINDS.md` — the kind taxonomy and one sentence: "Use a separate owner when one body has two
  independently consumed responsibilities". Read literally, it pushed the docs-and-debt split into three
  skills, including a two-paragraph `working-docs`, before Tommy merged two of them back into
  `engineering:docs`.
- `SOURCE_LAYOUT.md` (canonical `.agents/` source, host entry points, generated `plugins/*`),
  `PACKAGING.md` (shipped resources), `engineering:lanes` (whether and which lane a skill declares),
  `engineering:docs` (one rule, one home — on #173, not yet on main; currently `engineering:docs-and-debt`).
- `tj-agents/kit` ships scaffolding templates and `check_skill_references.py`, not authoring rules.

Mistakes this session made that such a convention should have prevented, as evidence for the rules:

1. Splitting by trigger count instead of by subject, producing a skill too small to justify its discovery
   cost.
2. A name one hyphen from an existing skill (`tech-debt` beside `techdebt`, caught in time) and a name
   colliding with another installed plugin's skill (`docs` beside `anthropic-skills:docs`, handled by always
   writing `engineering:docs`).
3. A compatibility entry whose description repeated its replacements' trigger words, so description
   matching could pick the stub.
4. A skill-local `TECH_DEBT.md`, which generation copies into every package (recorded in
   `.agents/plugins/TECH_DEBT.md`).
5. Descriptions maintained by hand three times (canonical, `.codex/skills`, `.claude/skills`).

## Completion expectation

1. Read `AGENTS.md`, `README.md`, `SOURCE_LAYOUT.md`, `SKILL_KINDS.md`, `PACKAGING.md`, `engineering:lanes`,
   the current docs owner (`engineering:docs-and-debt` on main), and kit's `new-plugin` and `check` skills
   (`gh api repos/tj-agents/kit/...`). Check `anthropic-skills:skill-creator` only for ideas, not as an owner.
2. Decide and record here: the owner (a core convention skill, a section of an existing doc, or kit, which
   scaffolds every tj-agents plugin repository), its name (check every installed plugin for collisions),
   and its scope: when to create versus extend a skill, sizing and splitting by subject and consumption,
   naming, writing the description as the selection trigger, kinds (link `SKILL_KINDS.md`, never restate),
   lanes (link), host entry points and generation (link), skill-local resources, compatibility entries for
   renamed or split skills, and tests. Follow one rule, one home: link existing owners rather than
   restating them, and reconcile `SKILL_KINDS.md`'s separate-owner sentence with the new sizing rule in
   one place.
3. Implement it, with discovery: make sure the sessions that add or change a skill actually load it (route
   table, `AGENTS.md`, description trigger). Add a focused test where a rule is machine-checkable; consider
   whether description parity between canonical and host entries can be checked or generated instead of
   copied.
4. Validate: both Python suites with `< /dev/null`, local `python -B scripts/update_catalog_digests.py` and
   `pwsh .agents/sync-generated.ps1` then `-Check`, tier payload, catalog `--check`, harness `--check`,
   `docs_reachability.py`. Leave `plugins/*` and catalog digest changes uncommitted.
5. Review with `engineering:review` if packages or tests change, otherwise `engineering:docs-review`; open the
   PR against `main` and merge through `engineering:merge` or `engineering:merge-docs` as the diff requires;
   finish Step 5 for this worktree.
6. Record the PR URL and outcome here, and message the originating session (`.worktrees/SplitDocsAndDebt`)
   if the new convention changes how #173's skills should be shaped.

## Next Steps

Scope: whole goal through merge and cleanup.
Current slice: steps 1–2.
Remaining scope: implementation, validation, review, PR, merge, cleanup.
Done when: the convention is merged to `main` and this worktree is cleaned up.

Start at Completion expectation step 1.
