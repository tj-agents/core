# Code review — Refactor/SplitDocsAndDebt

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `f316ccd4728e8eedf7ebd20059c09d34ea39418b`  `(2026-10-09)`
**Judgment:** `approved`

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

## Review pass — 2026-10-09 — incremental

**Candidate base:** `847ec60150095556f6b642ca998e85db2119020b`
**Candidate head:** `5ad4c42e1ec83d999e34baef65a0056352ed005d`
**Candidate branch:** `Refactor/SplitDocsAndDebt`
**Candidate scope:** `all`
**Work-order path:** `reviews/Refactor-SplitDocsAndDebt.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Native layer: Claude Code built-in `code-review` skill (medium) over the pass-2 fix commit. All findings kept.

### Findings

- [x] **DEBT5 — MEDIUM — packaging** — `.agents/engineering/convention/docs-and-debt/TECH_DEBT.md`
  A skill-local debt file is copied into three generated package paths, so the `techdebt` survey sees four
  copies and consumers receive a maintainer record. Fix: move the entry to `.agents/engineering/TECH_DEBT.md`,
  which generation does not package, and drop the link from the routing entry.
- [x] **DEBT6 — MEDIUM — correctness** — same entry
  "No pinned release still names it" can never become true, and the steps omit the compatibility test.
  Fix: condition on default-branch route tables and instructions only, note pinned consumers keep their
  release, and list the test among the deletions.
- [x] **DEBT7 — LOW — accuracy** — same entry
  The final grep did not say how to exclude only generated `plugins/`. Fix: give the exact `git grep`.
- [x] **TEST2 — LOW — test-impact** — `.agents/hooks/tests/test_process_standards.py`
  The routing-only guard rejected only `## ` headings. Fix: reject bold rule leads and any heading below
  the title.
- [x] **PLAN4 — LOW — accuracy** — `plans/split-docs-and-debt/GOAL.md`
  The allowlist omitted the new test reference. Fix: list it.
- [x] **PLAN5 — LOW — plan-checkpoint** — same file
  Next Steps skipped the incremental review the fix commit needs. Fix: add it.
- [x] **REV1 — LOW — accuracy** — `reviews/Refactor-SplitDocsAndDebt.md`
  Rebase count disagreed with the goal. Fix: six in both.
- [x] **GEN1 — LOW — accuracy** — (folded into DEBT5) the routing body shipped a link to a maintainer file.

## Review pass — 2026-10-09 — incremental

**Candidate base:** `5ad4c42e1ec83d999e34baef65a0056352ed005d`
**Candidate head:** `0b4624fcef7f403af362285ba21ac6523a7b2cac`
**Candidate branch:** `Refactor/SplitDocsAndDebt`
**Candidate scope:** `all`
**Work-order path:** `reviews/Refactor-SplitDocsAndDebt.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Native layer: Claude Code built-in `code-review` skill (medium) over the pass-3 fix commit. Pass 2's
narrative said "four times"; the branch had been rebased six times by then. It is left as written.

Dropped at synthesis: a `**Resolution condition.**` lead (this repository's debt files open the condition
paragraph with "Resolve …", which the entry does).

### Findings

- [x] **PKG1 — MEDIUM — packaging** — `.agents/engineering/TECH_DEBT.md`
  Generation packages any skill-local `TECH_DEBT.md` (`bootstrap-capabilities` ships three copies today);
  moving one entry treats a symptom. Fix: out of this slice's scope; recorded in
  `.agents/plugins/TECH_DEBT.md` with an objective resolution condition.
- [wontfix] **DEBT8 — LOW — convention** — `.agents/engineering/TECH_DEBT.md`
  `debt-records` prefers the owning area, `convention/docs-and-debt/`. Reason: a skill-local file ships in
  every generated package until PKG1 is resolved, and the problem spans the engineering package's skill,
  host entries and catalog row, so the engineering package's file is the lowest home that does not leak.
  PKG1's entry names this placement.
- [x] **REV2 — LOW — review-lifecycle** — `reviews/Refactor-SplitDocsAndDebt.md`
  The fix edited completed pass 2's text. Fix: restore it and note the count here.
- [x] **DEBT9 — LOW — correctness** — `.agents/engineering/TECH_DEBT.md`
  The final grep would match the entry itself. Fix: delete the entry before the grep.
- [x] **PLAN6 — LOW — accuracy** — `plans/split-docs-and-debt/GOAL.md`
  The allowlist used `grep -rniE` while the entry uses `git grep`. Fix: one command.
- [x] **TEST3 — LOW — test-impact** — `.agents/hooks/tests/test_process_standards.py`
  The guard let a plain bullet rule through, counted `#` inside code fences and could raise `IndexError`.
  Fix: require exactly three `engineering:` routing bullets, one heading, no bold lead or code fence, and
  assert the front matter exists.

## Review pass — 2026-10-09 — incremental

**Candidate base:** `0b4624fcef7f403af362285ba21ac6523a7b2cac`
**Candidate head:** `ae55ca1f74d09c123d5fc24523311f961f1f5fd0`
**Candidate branch:** `Refactor/SplitDocsAndDebt`
**Candidate scope:** `all`
**Work-order path:** `reviews/Refactor-SplitDocsAndDebt.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Native layer: Claude Code built-in `code-review` skill (low) over the pass-4 fix commit. No findings.

### Findings

None.

## Review pass — 2026-10-09 — incremental (merge into `engineering:docs`)

**Candidate base:** `01736046ec0fb01af8e5b0171c92812f10dac0f3`
**Candidate head:** `22c2685b9d672d0f06a4913729ce8fdff2d0fa65`
**Candidate branch:** `Refactor/SplitDocsAndDebt`
**Candidate scope:** `all`
**Work-order path:** `reviews/Refactor-SplitDocsAndDebt.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Native layer: Claude Code built-in `code-review` skill (medium). Tommy decided to merge `guidance-ownership`
and `working-docs` into one `engineering:docs` skill; this pass covers that merge.

Dropped at synthesis: a test comparing the catalog roster with the skill folders (`update_catalog_digests.py`
already fails on roster drift, which is how CI would have caught CAT1); the `docs` name overlapping
`anthropic-skills:docs` (Tommy chose the name; plugin-qualified listings and `engineering:docs` references keep
them apart, and the skill-authoring side workstream owns naming rules); reading the `docs` skill in two tests
(this file reads per test throughout).

### Findings

- [x] **CAT1 — HIGH — correctness** — `.agents/catalog/catalog.json`
  The authored engineering roster still listed `guidance-ownership` and `working-docs` and lacked `docs`:
  restoring the file after local validation discarded the roster edit along with the generated digest.
  Fix: re-apply the roster change; validation now restores a saved copy instead of `HEAD`.
- [x] **DEBT10 — LOW — correctness** — `.agents/engineering/TECH_DEBT.md`
  Its removal steps assumed a correct roster. Fix: covered by CAT1.
- [x] **PLAN7 — LOW — plan-checkpoint** — `plans/split-docs-and-debt/GOAL.md`
  Progress claimed the review was approved before the merge was reviewed. Fix: say the merge is reviewed as
  a further pass.

## Review pass — 2026-10-09 — incremental

**Candidate base:** `22c2685b9d672d0f06a4913729ce8fdff2d0fa65`
**Candidate head:** `f316ccd4728e8eedf7ebd20059c09d34ea39418b`
**Candidate branch:** `Refactor/SplitDocsAndDebt`
**Candidate scope:** `all`
**Work-order path:** `reviews/Refactor-SplitDocsAndDebt.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Native layer: Claude Code built-in `code-review` skill (low) over the roster fix. Its only remarks were this
work order's stale header, corrected by this pass.

### Findings

None.
