# Code review — Fix/LetModelsPickLaneOne

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `c1f8f3f4aba9a48c6fe5ee0489704563937e5b1c`  `(2026-09-27)`
**Judgment:** `changes-requested`

## Review pass — 2026-09-27 — all

**Candidate base:** `d3fd962a348923f2d2e6c5a49c27f083e9bb349a`
**Candidate head:** `c1f8f3f4aba9a48c6fe5ee0489704563937e5b1c`
**Candidate branch:** `Fix/LetModelsPickLaneOne`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:3952b7b05448173357fc4b13946271f192b154ada9977069c88ef0fcef169a2d` `(35 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\lane-l1-followup-review-1\review\a28b1c2130eb23efd411e6777784147add3d2b98913c44f0cc6a905f0f1fd735`
**Candidate bundle identity:** `sha256:4f612e63172b424a2a20b3611450df2c2bd8c29139799daa163dcef28eaf3993`
**Work-order path:** `reviews/Fix-LetModelsPickLaneOne.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

### Findings

- [x] **REV-001 — MEDIUM — workflow** — `.agents/machine/handoff-claude/SKILL.md:54`
  Both handoff skills' lane tables still carry the old L1-L3 meanings ("Critical design decisions", "One-way
  design decisions", "Open-ended judgement at the top of the ladder") directly under the updated "design,
  stakes, ambiguity and verifiability" sentence, so a caller reading the table routes design work to L2/L3.
  Replace the L1-L3 rows in both skills with the tables' new summaries and regenerate.

- [x] **REV-002 — LOW — correctness** — `.agents/machine/handoff-codex/scripts/launch-codex.ps1:158`
  `$tier` is set for every lane resolution, so `-Lane L4 -Model x` prints `lane L4 -> x at high` although the
  model was the caller's. Label the model with the lane only when the lane supplied it, as the Claude launcher
  does, and assert the message for the explicit-model case.

Lenses: native-general, security, api-contract, workflow. Security layer: no path matches the generic or
repository `security_paths` inventory; the security lens found no regression.
