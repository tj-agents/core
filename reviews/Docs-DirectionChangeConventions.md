# Code review — Docs/DirectionChangeConventions

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `6e494c955d432479a8f123fbc6c05380d6f916ab`  `(2026-10-09)`
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
  Fixed in `724e5b5`.
- [x] **INST1 — MEDIUM — followability** — `.agents/engineering/convention/docs-and-debt/SKILL.md:146`
  "Its own docs-only PR straight away" has no delivery authority in a consuming repository. Grant the
  same standing authorization planning artifacts have through `merge-docs`, keeping user limits and holds.
  Fixed in `724e5b5`.
- [x] **ACC1 — MEDIUM — accuracy** — `.agents/engineering/convention/docs-and-debt/SKILL.md:117`
  Allowing "a convention doc it directs every affected change to read" contradicts the parent section:
  a silently costly rule must be always loaded. Require the `AGENTS.md` statement, linking detail.
  Fixed in `724e5b5`.
- [x] **INST2 — MEDIUM — followability** — `.agents/engineering/workflow/plan-execution/SKILL.md:139`
  The trigger covers only "a direction the plan decided", missing the cross-plan case that caused the
  incident. Trigger on any unstated direction the slice depends on.
  Fixed in `724e5b5`.
- [x] **HOME1 — LOW — one-rule-one-home** — `.agents/engineering/convention/docs-and-debt/SKILL.md:142`
  The new paragraph overlaps "Everything you decide not to fix earns an entry" without saying how a
  handoff relates to an entry. State that the receiving goal is the record and others get the entry.
  Fixed in `724e5b5`.
- [x] **HOME2 — LOW — one-rule-one-home** — `.agents/engineering/policy/session-guidance/SKILL.md:88`
  The first sentence restates the default-branch requirement and the direction pointer restates the rule;
  make both plain pointers to `docs-and-debt`.
  Fixed in `724e5b5`.
- [x] **ACC2 — LOW — accuracy** — `plans/direction-change-conventions/GOAL.md:42`
  Steps are unchecked though progress records them done, and no step retires the goal after merge. Tick
  completed steps and add the closeout.
  Fixed in `724e5b5`.

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
  Fixed in `d110e09`; that wording was itself wrong and is superseded by CON7.
- [x] **CON3 — MEDIUM — contradiction** — `.agents/engineering/convention/docs-and-debt/SKILL.md:147`
  Under a merge hold the entry stayed unmerged with only a report mention, which the same paragraph says is
  not a record. Keep the problem open in the goal and report until the entry lands.
  Fixed in `d110e09`.
- [x] **CON4 — MEDIUM — contradiction** — `.agents/engineering/convention/docs-and-debt/SKILL.md:136`
  "Everything you decide not to fix earns an entry" still demanded an entry for handed-off work. Exempt
  handoffs in that sentence.
  Fixed in `d110e09`.
- [x] **INST3 — LOW — followability** — `.agents/engineering/convention/docs-and-debt/SKILL.md:146`
  The debt-PR authorization did not include the docs review `merge-docs` requires. Name it.
  Fixed in `d110e09`.
- [x] **CON5 — LOW — contradiction** — `.agents/engineering/convention/review-lifecycle/SKILL.md:119`
  `[wontfix]` still required "any required debt entry" only. Accept a handoff or debt entry.
  Fixed in `d110e09`.
- [x] **INST4 — LOW — followability** — `.agents/engineering/workflow/address-review/SKILL.md:39`
  Bare `docs-and-debt` in review-lifecycle and address-review; use the `engineering:` identity.
  Fixed in `d110e09`.
- [x] **CON6 — LOW — contradiction** — `.agents/engineering/policy/session-guidance/SKILL.md:103`
  The terminal check accepted a debt entry anywhere. Require it on the default branch or in this change,
  keeping the pinned wording.
  Fixed in `d110e09`.

## Review pass — 2026-10-09 — incremental

**Candidate base:** `724e5b5ef1d8e4cd54245267b2f8c0d0b49734f3`
**Candidate head:** `d110e09cd4e00b063a4850583808313de5ac7f69`
**Candidate branch:** `Docs/DirectionChangeConventions`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:bfb0c093466f893d9588b8d500d9a70f4eb1a6c683c0b93574ec431ac03d7dfe` `(5 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/gKtNYzWm6PMnRKNMazpxuM/TO5kViN9MoQvBaynI8HSBK`
**Candidate bundle identity:** `sha256:7d3256402d53592bde1c0ad955265b657766700e6782ba32d51717fedb258531`
**Work-order path:** `reviews/Docs-DirectionChangeConventions.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

Dropped after verification: bare sibling skill names such as `docs-and-debt` are the corpus convention
(`review` names `review-lifecycle`, `plans` and others the same way), so the remaining bare references are
not defects; and the bold lead's conflict with the hold exception is resolved by stating the exception.

- [x] **CON7 — MEDIUM — contradiction** — `.agents/engineering/convention/docs-and-debt/SKILL.md:117`
  CON2's "lowest node" `AGENTS.md` is not always loaded, which defeats the rule. Require the root
  `AGENTS.md` and say the cost of missing it outranks the lowest-node default.
  Fixed in `6e494c9`.
- [x] **CON8 — MEDIUM — contradiction** — `.agents/engineering/convention/review-lifecycle/SKILL.md:119`
  `[wontfix]` now demanded a handoff or entry even for a rejected finding. Require it only for postponed
  work.
  Fixed in `6e494c9`.
- [x] **CON9 — LOW — contradiction** — `.agents/engineering/policy/session-guidance/SKILL.md:105`
  "In this change" accepted an entry on a branch that may never merge. Say "landed or landing with this
  change".
  Fixed in `6e494c9`; superseded by CON11, which restores the plain pointer.
- [x] **INST5 — LOW — followability** — `.agents/engineering/convention/docs-and-debt/SKILL.md:149`
  The merge-hold clause relied on a goal a standalone task may lack and on the report. Open the entry's PR,
  name it, and let it land when the hold lifts.
  Fixed in `6e494c9`; superseded by CON10, which reuses the planning-artifact delivery gates.
- [x] **TEST1 — LOW — test-coverage** — `.agents/hooks/tests/test_process_standards.py:106`
  The pinned terminal-check phrase did not cover the new qualifier. Extend the assertion.
  Fixed in `6e494c9`.
- [x] **ACC3 — LOW — accuracy** — `reviews/Docs-DirectionChangeConventions.md:69`
  Ticked findings carried no fix evidence. Record the fixing commit on each.
  Fixed in `6e494c9`.

## Review pass — 2026-10-09 — incremental

**Candidate base:** `d110e09cd4e00b063a4850583808313de5ac7f69`
**Candidate head:** `6e494c955d432479a8f123fbc6c05380d6f916ab`
**Candidate branch:** `Docs/DirectionChangeConventions`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:9f97040830445a13f1fb91117a6d2848eb3f2924e48e7bf277523a9d5c8f6af6` `(5 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/afnBN4akVzlVwWsr7gS10D/klHwSE0f9WdBjh3lqz22D3`
**Candidate bundle identity:** `sha256:93c19ba3716d701e64ae41249b02946c9affead7c97b1df3482fc455ef0f0961`
**Work-order path:** `reviews/Docs-DirectionChangeConventions.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

Dropped after verification: the lowest-node rule in "One rule, one home" needs no exception, because the
"Sort a rule by the cost of missing it" section already places rules by cost and the direction rule, which
lives there, states its precedence.

- [x] **CON10 — MEDIUM — contradiction** — `.agents/engineering/convention/docs-and-debt/SKILL.md:149`
  The bespoke hold clause accepted an unmerged entry, dropped tracking and told the agent to open a PR
  against a "no PRs" limit. Replace it with the planning-artifact standing authorization and delivery gates.
- [x] **CON11 — MEDIUM — contradiction** — `.agents/engineering/policy/session-guidance/SKILL.md:105`
  "Landed or landing with this change" rejected the separate docs-PR path. Restore the plain pointer;
  `docs-and-debt` alone defines what counts as an entry.
- [x] **ACC4 — MEDIUM — accuracy** — `.agents/engineering/convention/docs-and-debt/SKILL.md:118`
  A one-line pointer in `AGENTS.md` leaves the costly parts (scope, unmoved code) on demand. State the rule
  itself in the root `AGENTS.md`, linking only further detail.
- [x] **ACC5 — LOW — accuracy** — `reviews/Docs-DirectionChangeConventions.md:121`
  Pass-3 findings lacked fix evidence. Record it.
- [x] **TEST2 — LOW — test-coverage** — `.agents/hooks/tests/test_process_standards.py:110`
  Neither new `docs-and-debt` rule was pinned. Pin the direction placement and the recording rule.
