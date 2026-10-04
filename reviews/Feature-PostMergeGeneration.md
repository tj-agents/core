# Code review — Feature/PostMergeGeneration

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `57e000e3033f910dedc910367be2eeffb71381dd`  `(2026-10-04)`
**Judgment:** `approved`

## Review pass — 2026-10-04 — full

**Candidate base:** `eb7d65d4ab39c6defdb15f03026f5c5f7009abd1`
**Candidate head:** `42d0a11f346778365c44b9275375191fb16825cc`
**Candidate branch:** `Feature/PostMergeGeneration`
**Candidate scope:** `all`
**Candidate path-set:** `(15 paths)` — descriptor `2ece406218da3c99528dda1da187e29ae2ae7149d528387884f3c0a1afedea14`
**Candidate bundle:** `removed after completion`
**Candidate bundle identity:** `sha256:b2c827c24817c947dcb1cc554461cf312d5eef17f716ac476e1fe2672a283a6e`
**Work-order path:** `reviews/Feature-PostMergeGeneration.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

### Findings

- [x] **NAT1 — LOW — native-general** — `plans/repo-declared-config/REPO_DECLARED_CONFIG_PLAN.md:122`
  The plan still specified the removed `source_excludes`/`source_digest` manifest fields, which
  `sync_harness_manifests.py` now hard-rejects; anyone authoring a manifest from the doc would fail
  validation. Fixed on this branch: manifest example reduced to the four-field shape and the digest
  paragraph replaced with the validator's recompute-on-every-run description.

Native layer: Claude Code `code-review` (medium) over the frozen range — verified the removal is
complete and consumerless (full-repo grep), generated mirrors and embedded Codex hook digests
correctly regenerated (`sync-generated.ps1 -Check` clean), harness tests pass. No additional lens was
dispatched: the candidate is a deletion-heavy tooling change whose surface the mechanical checks
(tier payload, catalog digests, harness validation, 55 affected-module tests) already validate, and no
security path was classified (`first_path`/`trunk_first_path` null).

## Review pass — 2026-10-04 — incremental

**Candidate base:** `42d0a11f346778365c44b9275375191fb16825cc`
**Candidate head:** `57e000e3033f910dedc910367be2eeffb71381dd`
**Candidate branch:** `Feature/PostMergeGeneration`
**Candidate scope:** `plans/repo-declared-config/REPO_DECLARED_CONFIG_PLAN.md`
**Work-order path:** `reviews/Feature-PostMergeGeneration.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

### Findings

No findings: the delta is the NAT1 doc fix verified above, plus this work order.
