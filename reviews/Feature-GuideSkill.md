# Code review — Feature/GuideSkill

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `c1b3d8540a6a60161eb4d60099ec1feae4083bd0`  `(2026-10-04)`
**Judgment:** `approved`

## Review pass — 2026-10-04 — docs

**Candidate base:** `06480cfbdf376fac825e4b0581f3b4b6a8e0f5a2`
**Candidate head:** `2ba8f59e0f9f9f8cf72c97d5dcca485cea055ddf`
**Candidate branch:** `Feature/GuideSkill`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:05301d4b6d74846b11669b1daf13f3ba874c62b29471203c31ac1f6bf8cc4cea` `(14 paths)`
**Candidate bundle:** `removed after completion`
**Candidate bundle identity:** `sha256:89e7ddc498dd3d4f7abced8a041617d1e885da082eb75d49f34ffd04598fe727`
**Work-order path:** `reviews/Feature-GuideSkill.md`
**Work-order mode:** `new`
**Pass judgment:** `approved`

### Findings

No findings retained. Native layer: Claude Code `code-review` (medium) over the frozen range — zero
findings; verified generation is byte-faithful (`sync-generated.ps1 -Check` clean), entry-point links
resolve, and `tests/test_source_layout.py` passes. Lenses: accuracy, contradiction, and
one-rule-one-home returned no findings. The concision lens returned six wording-level candidates; the
parent dropped all six — the condensed-rules description matches the corpus-wide `kind: contract`
description convention (siblings in this repo and the stack repos), and the remainder were
preference-only rewrites below the medium-effort confidence bar. `docs_reachability.py` over the frozen
tree: 0 errors. No tier conventions apply; no route table; no security-sensitive paths (`first_path`
and `trunk_first_path` null), so no security layer was required.

## Review pass — 2026-10-04 — incremental

**Candidate base:** `2ba8f59e0f9f9f8cf72c97d5dcca485cea055ddf`
**Candidate head:** `c1b3d8540a6a60161eb4d60099ec1feae4083bd0`
**Candidate branch:** `Feature/GuideSkill`
**Candidate scope:** `all`
**Candidate path-set:** merge of `origin/main` (`f63058e`) plus conflict resolution by regeneration
**Candidate bundle:** `not materialized — merge-delta pass validated by the parent directly`
**Work-order path:** `reviews/Feature-GuideSkill.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

### Findings

No findings. The delta is the merge of `origin/main` — whose PRs #83 and #85 carried their own
completed, recorded reviews — plus conflict resolution done by regeneration, never by hand: main's
versions taken for the five digest files, the one-line `guide` catalog entry re-applied, then
`sync_harness_manifests.py`, `update_catalog_digests.py` and `sync-generated.ps1` rerun. Evidence:
the authored guide files are byte-unchanged since the reviewed head (`git diff 2ba8f59..c1b3d85` over
the three authored paths is empty); `sync-generated.ps1 -Check`, tier payload, catalog digest and
harness checks all green on the merged tree; packaging suite PASS; four unit-test failures during the
merged-tree full run (bootstrap transition, codex windows hook commands, continuation orphan gate,
handoff receipt path) each re-ran green in isolation — host-load blips under concurrent background
jobs, in areas owned by main's already-reviewed PRs. Exact-head CI on `c1b3d85` is the remaining
check before merge.
