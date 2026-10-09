# Code review — Docs/DirectionChangeConventions

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `724e5b5ef1d8e4cd54245267b2f8c0d0b49734f3`  `(2026-10-09)`
**Judgment:** `changes-requested`

## Review pass — 2026-10-09 — docs

**Candidate base:** `21b482cb43b7e210ba211f262cccd7902715335c`
**Candidate head:** `3f9ab37d00f625004287b2e5728f80d154577cd5`
**Candidate branch:** `Docs/DirectionChangeConventions`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:c3d1c11a24f6825a1901c0216b2f9bcf23e438fada6eac21023f79a7dc6f498a` `(9 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/ladXomU7O8RirNW7jZsCvJ/klPLPQk_wXX4psUSbah0WH`
**Candidate bundle identity:** `sha256:b3b73449123dfa962e6ce6d4631dca0499912a1e6e2de83a01855bc428ee3bc2`
**Work-order path:** `reviews/Docs-DirectionChangeConventions.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

### Findings

Native layer: Claude `code-review` skill at medium over the frozen range. Documentation lenses ran in the
parent (Codex unavailable on this host). Security layer not required (no security path). Dropped after
verification: the Windows-only `finish.ps1`/`close.ps1` closeout in `session-guidance` (unchanged lines,
owned by the Linux port plan's peer-cli step on the default branch) and `review` naming `docs-and-debt`
outside the route table (same precedent as `plans`; a semantic check has no path route).

- [x] **CON1 — MEDIUM — contradiction** — `.agents/engineering/convention/review-lifecycle/SKILL.md:121`
  Postponed findings may go to "the owning tech-debt file or issue" (also `address-review/SKILL.md:38`),
  but the new `docs-and-debt` rule makes a record only a merged `TECH_DEBT.md` entry or a handoff. Point
  both lines at `docs-and-debt`.
- [x] **INST1 — MEDIUM — followability** — `.agents/engineering/convention/docs-and-debt/SKILL.md:146`
  "Its own docs-only PR straight away" has no delivery authority in a consuming repository. Grant the
  same standing authorization planning artifacts have through `merge-docs`, keeping user limits and holds.
- [x] **ACC1 — MEDIUM — accuracy** — `.agents/engineering/convention/docs-and-debt/SKILL.md:117`
  Allowing "a convention doc it directs every affected change to read" contradicts the parent section:
  a silently costly rule must be always loaded. Require the `AGENTS.md` statement, linking detail.
- [x] **INST2 — MEDIUM — followability** — `.agents/engineering/workflow/plan-execution/SKILL.md:139`
  The trigger covers only "a direction the plan decided", missing the cross-plan case that caused the
  incident. Trigger on any unstated direction the slice depends on.
- [x] **HOME1 — LOW — one-rule-one-home** — `.agents/engineering/convention/docs-and-debt/SKILL.md:142`
  The new paragraph overlaps "Everything you decide not to fix earns an entry" without saying how a
  handoff relates to an entry. State that the receiving goal is the record and others get the entry.
- [x] **HOME2 — LOW — one-rule-one-home** — `.agents/engineering/policy/session-guidance/SKILL.md:88`
  The first sentence restates the default-branch requirement and the direction pointer restates the rule;
  make both plain pointers to `docs-and-debt`.
- [x] **ACC2 — LOW — accuracy** — `plans/direction-change-conventions/GOAL.md:42`
  Steps are unchecked though progress records them done, and no step retires the goal after merge. Tick
  completed steps and add the closeout.

## Review pass — 2026-10-09 — incremental

**Candidate base:** `3f9ab37d00f625004287b2e5728f80d154577cd5`
**Candidate head:** `724e5b5ef1d8e4cd54245267b2f8c0d0b49734f3`
**Candidate branch:** `Docs/DirectionChangeConventions`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:af52152b0bc9d21c9dc03404a417a87ef8b6e90aa5e78f27e7706e15d7ddf03d` `(7 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/BYXEghlf7eJq14F57CmzeA/rO2MVPhefuld80pFucGUSc`
**Candidate bundle identity:** `sha256:b977a01d8f8b0fa06f6cdb56131577e0f2b3d3dbf08bef89bfea3ed10c190167`
**Work-order path:** `reviews/Docs-DirectionChangeConventions.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

- [x] **CON2 — MEDIUM — contradiction** — `.agents/engineering/convention/docs-and-debt/SKILL.md:118`
  "The always-loaded `AGENTS.md`" read as the root, against "a doc lives at the lowest node". State it at
  the lowest node containing every affected path.
- [x] **CON3 — MEDIUM — contradiction** — `.agents/engineering/convention/docs-and-debt/SKILL.md:147`
  Under a merge hold the entry stayed unmerged with only a report mention, which the same paragraph says is
  not a record. Keep the problem open in the goal and report until the entry lands.
- [x] **CON4 — MEDIUM — contradiction** — `.agents/engineering/convention/docs-and-debt/SKILL.md:136`
  "Everything you decide not to fix earns an entry" still demanded an entry for handed-off work. Exempt
  handoffs in that sentence.
- [x] **INST3 — LOW — followability** — `.agents/engineering/convention/docs-and-debt/SKILL.md:146`
  The debt-PR authorization did not include the docs review `merge-docs` requires. Name it.
- [x] **CON5 — LOW — contradiction** — `.agents/engineering/convention/review-lifecycle/SKILL.md:119`
  `[wontfix]` still required "any required debt entry" only. Accept a handoff or debt entry.
- [x] **INST4 — LOW — followability** — `.agents/engineering/workflow/address-review/SKILL.md:39`
  Bare `docs-and-debt` in review-lifecycle and address-review; use the `engineering:` identity.
- [x] **CON6 — LOW — contradiction** — `.agents/engineering/policy/session-guidance/SKILL.md:103`
  The terminal check accepted a debt entry anywhere. Require it on the default branch or in this change,
  keeping the pinned wording.
