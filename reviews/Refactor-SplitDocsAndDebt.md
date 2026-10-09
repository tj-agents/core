# Code review — Refactor/SplitDocsAndDebt

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `847ec60150095556f6b642ca998e85db2119020b`  `(2026-10-09)`
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

- [x] **DEBT1 — MEDIUM — correctness** — `.agents/plugins/TECH_DEBT.md`
  The removal steps omit the hand-maintained `docs-and-debt` row in `.agents/catalog/catalog.json` and the
  skill count in `tests/test_source_layout.py`, so following the entry fails the catalog roster check and
  its own grep condition. Fix: list both in the resolution steps.
- [x] **COMPAT1 — MEDIUM — followability** — `.agents/engineering/convention/docs-and-debt/SKILL.md:3`
  The compatibility entry's description repeats the three owners' trigger words, so description matching
  can pick the routing stub over the real owner. Fix: describe it only as a compatibility entry for
  existing callers that is never selected for new work; keep the routes in the body.
- [x] **XREF1 — LOW — followability** — `.agents/engineering/convention/guidance-ownership/SKILL.md`
  The direction-change rule says "record code that has not moved as tech debt" but no longer shares a
  body with the recording rule. Fix: point it at `debt-records`.
- [x] **DEBT2 — LOW — accuracy** — `.agents/plugins/TECH_DEBT.md`
  "Releases through `v2.1.15` publish the old name" understates it: every release until removal ships the
  compatibility entry. Fix: say published releases before the split ship it as the rules owner and every
  later release until removal ships the routing entry.
- [x] **PLAN1 — LOW — accuracy** — `plans/split-docs-and-debt/GOAL.md`
  The allowlist calls the `catalog.json` skill list generated; it is authored. Fix: call it the authored
  catalog skill roster.
- [x] **PLAN2 — LOW — plan-checkpoint** — `plans/split-docs-and-debt/GOAL.md`
  `## Next Steps` still says to start at step 1 after the move landed. Fix: checkpoint progress and the
  current slice.

## Review pass — 2026-10-09 — code (rebased candidate)

The branch was rebased four times onto the moving parent, so pass 1's watermark `39588f6` is no longer an
ancestor; this pass covers the whole rebased layer rather than an incremental delta.

**Candidate base:** `bf43af58331a565aa586123aef74f3211e3c1722`
**Candidate head:** `847ec60150095556f6b642ca998e85db2119020b`
**Candidate branch:** `Refactor/SplitDocsAndDebt`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:485fa121bf598d0ea37595a9737ddfd65a5ab0212fb33c085a46cbbde795ce38` `(26 paths)`
**Candidate bundle:** `/home/tommy/projects/tj-agents/core/.git/agent-workflow/runs/split-docs-and-debt-review-2/review/2aa9268c3cadaed145dfad281de072e04ed20acc451834ac8bc9e5b4cefa5496`
**Candidate bundle identity:** `sha256:f25bf8b9ba23fee52a50be114ca9a484fc371ef9538ae24c6dce825707b61bea`
**Work-order path:** `reviews/Refactor-SplitDocsAndDebt.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Native layer: Claude Code built-in `code-review` skill (medium). No further lens: the layer's content was
unchanged since pass 1's clean `workflow` lens apart from the parent's re-moved text, checked word-for-word
against the parent. Security layer not required.

Dropped at synthesis: `kind: convention` on the compatibility entry (`SKILL_KINDS.md` gives a compatibility
entry the role of what it enters); docs-review's loading of the guidance rules (unchanged in substance — it
loaded the same corpus under the old name); session-guidance's "as `engineering:debt-records` defines"
(the clause binds to the recording obligation, and the sentence is parent text); bare versus qualified skill
names (no loaded rule states one form); triplicated host descriptions (an existing repository-wide design,
not introduced here); a route requiring the old name being satisfied by the routing entry (folded into
DEBT3's resolution condition).

### Findings

- [x] **DEBT3 — MEDIUM — correctness** — `.agents/plugins/TECH_DEBT.md`
  The removal condition was a date alone, so deletion could strand a consumer route row or alias that still
  names the old skill. Fix: resolve only after the date and once no `tj-agents` consumer names it,
  migrating each reference first.
- [x] **DEBT4 — LOW — convention** — `.agents/plugins/TECH_DEBT.md`
  `debt-records` puts an entry in the area that owns the problem; the compatibility entry lives in
  `.agents/engineering/convention/docs-and-debt/`. Fix: move the entry to a `TECH_DEBT.md` there, linked
  from the entry, so deleting the directory deletes the record.
- [x] **PLAN3 — LOW — plan-checkpoint** — `plans/split-docs-and-debt/GOAL.md`
  Next Steps still said to commit the review fixes and cited pre-rebase validation. Fix: checkpoint the
  rebased validation and the PR step.
- [x] **TEST1 — LOW — test-impact** — `.agents/hooks/tests/test_process_standards.py`
  Nothing pinned `working-docs`' deletion rule or kept rule text out of the compatibility entry. Fix: add
  both assertions.
