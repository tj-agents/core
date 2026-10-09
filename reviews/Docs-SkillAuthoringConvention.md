# Code review — Docs/SkillAuthoringConvention

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `4d63fe82046f99aebd87651c8f35a6f1355ec983`  `(2026-10-09)`
**Judgment:** `changes-requested`

## Review pass — 2026-10-09 — full

**Candidate base:** `49c618c5204140629df7a78dd7f8e47a0bfe749f`
**Candidate head:** `4d63fe82046f99aebd87651c8f35a6f1355ec983`
**Candidate branch:** `Docs/SkillAuthoringConvention`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:150f88b807ff2652b7fe72bc65de176af224202b3fd519b3557107d4a89559a5` `(11 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/1YNaq4-UxodIoI1tf3dVbi/ITq8s8qMeeBeQFxq0E7EbQ`
**Candidate bundle identity:** `sha256:8e7232eb6aa01d2cb58847ac89c610a1fca7679e124a1c76f860a4421ab06875`
**Work-order path:** `reviews/Docs-SkillAuthoringConvention.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

Synchronization: one pre-review synchronization against `origin/main` (behind 0). Routed rules:
`engineering:skill-authoring`. Lenses: native-general (Claude Code `code-review`, medium), workflow (parent). Security layer: not required (no
security path in the frozen or trunk range).

### Findings

- [x] **F1 — HIGH — native-general** — `.agents/skill-routes.json:1`
  Carrying a route table opts all of core into write-time routing. `skill_router.py` (`missing_routed_skills`)
  blocks every write in the repository, not only `SKILL.md`, while any routed skill is unresolved or
  plugin discovery fails, and `red_run_gate.has_jurisdiction` then gates every red test run in core. Until
  a release ships `engineering:skill-authoring`, and on any host whose discovery fails, every session in
  core stops writing. Fix: remove the route table and its test; keep discovery in the description and
  `AGENTS.md`, and record the decision in the goal.
  Fixed: route table and its test removed; the goal records why.
- [x] **F2 — LOW — native-general, workflow** — `.agents/engineering/convention/skill-authoring/SKILL.md:48`
  "The generator ... rejects two names that are equal once their hyphens are removed" holds only for core's
  generator; kit's check has its own folder-naming rules and no such check, so a kit-layout author could
  rely on a check that does not exist. Fix: attribute the hyphen check to core's generator and name
  `kit:check`'s naming rules for kit-layout repositories.
  Fixed: the hyphen check is attributed to core's generator, and kit's rules are said not to catch it.
- [x] **F3 — LOW — native-general** — `AGENTS.md:26`
  The new instruction names a skill that no installed release ships until the post-merge regeneration is
  installed, so `Skill(engineering:skill-authoring)` fails in the meantime. Fix: link the canonical
  definition path as `SKILL_KINDS.md` does.
  Fixed: `AGENTS.md` links the canonical definition.

Dropped after verification: alias-name collisions (hypothetical, no current alias clashes), route anchoring
and the route test's root (moot once F1 removes the table), and the `engineering:docs-and-debt` reference
(valid on `main`; #173 keeps that name as a routing entry and its owner is told to retarget it).
