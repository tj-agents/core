# Code review — Refactor/SplitDocsAndDebt

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `39588f61047c2d78b15b9b125cd59b6e165b4afd`  `(2026-10-09)`
**Judgment:** `changes-requested`

## Review pass — 2026-10-09 — code

**Candidate base:** `3f9ab37d00f625004287b2e5728f80d154577cd5`
**Candidate head:** `39588f61047c2d78b15b9b125cd59b6e165b4afd`
**Candidate branch:** `Refactor/SplitDocsAndDebt`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:28a8edcc63c2a7304adcf45c90412bc20fe8b3b1c0ba81574db4fc162e849906` `(22 paths)`
**Candidate bundle:** `/home/tommy/projects/tj-agents/core/.git/agent-workflow/runs/split-docs-and-debt-review-1/review/d384d30ad0beb1156201458c2451dbd1e93669c427bda3aec8fd7144a782070d`
**Candidate bundle identity:** `sha256:57113bef6b4693481938d9632ed5b4c6be6c954987c588c7ade155da679c06fc`
**Work-order path:** `reviews/Refactor-SplitDocsAndDebt.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

Native layer: Claude Code built-in `code-review` skill (medium) over the frozen range. Lenses dispatched:
`workflow` (ownership, cross-references, followability) — no findings. Security layer not required
(`first_path` and `trunk_first_path` both null). Routed skills: none returned by review-prepare. Tier
gate: no stack tier conventions apply. `docs_reachability.py`: 0 errors.

Dropped at synthesis: making the `skills` alias table accept several targets (a design alternative to the
recorded compatibility decision, not a defect in this candidate; no route row in this repository names
`docs-and-debt`).

### Findings

- [ ] **DEBT1 — MEDIUM — correctness** — `.agents/plugins/TECH_DEBT.md`
  The removal steps omit the hand-maintained `docs-and-debt` row in `.agents/catalog/catalog.json` and the
  skill count in `tests/test_source_layout.py`, so following the entry fails the catalog roster check and
  its own grep condition. Fix: list both in the resolution steps.
- [ ] **COMPAT1 — MEDIUM — followability** — `.agents/engineering/convention/docs-and-debt/SKILL.md:3`
  The compatibility entry's description repeats the three owners' trigger words, so description matching
  can pick the routing stub over the real owner. Fix: describe it only as a compatibility entry for
  existing callers that is never selected for new work; keep the routes in the body.
- [ ] **XREF1 — LOW — followability** — `.agents/engineering/convention/guidance-ownership/SKILL.md`
  The direction-change rule says "record code that has not moved as tech debt" but no longer shares a
  body with the recording rule. Fix: point it at `debt-records`.
- [ ] **DEBT2 — LOW — accuracy** — `.agents/plugins/TECH_DEBT.md`
  "Releases through `v2.1.15` publish the old name" understates it: every release until removal ships the
  compatibility entry. Fix: say published releases before the split ship it as the rules owner and every
  later release until removal ships the routing entry.
- [ ] **PLAN1 — LOW — accuracy** — `plans/split-docs-and-debt/GOAL.md`
  The allowlist calls the `catalog.json` skill list generated; it is authored. Fix: call it the authored
  catalog skill roster.
- [ ] **PLAN2 — LOW — plan-checkpoint** — `plans/split-docs-and-debt/GOAL.md`
  `## Next Steps` still says to start at step 1 after the move landed. Fix: checkpoint progress and the
  current slice.
