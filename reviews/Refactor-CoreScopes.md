# Code review — Refactor/CoreScopes

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `a9200fe71c6167fea4dcb7469c001cc7400a2204`  `(2026-09-20)`
**Security-reviewed up to commit:** `a9200fe71c6167fea4dcb7469c001cc7400a2204`  `(2026-09-20)`
**Judgment:** `changes-requested`

## Review pass — 2026-09-20 — staged:all

**Candidate base:** `c90b6021aecf7f809d240fd6ae7b469b36b9387e`
**Candidate head:** `a9200fe71c6167fea4dcb7469c001cc7400a2204`
**Candidate branch:** `Refactor/CoreScopes`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:6a9d5ddadf1ab8dc3eb4b94a88ffdb008a622c2f1812af158fc809c1f966a1bd` `(647 paths)`
**Candidate bundle:** `C:\Users\tommy\source\repos\base-agents\.git\agent-workflow\runs\p2-core-scopes-20260920\review\0d4bb1dcaa5bcd763358407e3c36c4df6b6cdd629d8a190116cec9ffc45c106f`
**Candidate bundle identity:** `sha256:436294b778bd706eb28d6f8d829d1128298d35c1607c566f5b028b23d20ad446`
**Work-order path:** `reviews/Refactor-CoreScopes.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

### Findings

- [x] **REV-001 — HIGH — workflow** — `.agents/workflows/workflow_ops.py:313`
  The review runtime requires `.agents/hooks/skill_router.py`, but that file is absent from the frozen
  candidate and every generated package. `review-prepare` therefore recorded an empty rule set and the
  contract's required frozen-tree routing command fails before review dispatch. Restore the canonical
  router, package it with its owning scope, and add coverage proving source and packaged review preparation
  resolve non-empty applicable rules instead of silently degrading.

- [x] **REV-002 — HIGH — workflow** — `.agents/engineering/workflow/failing-tests/SKILL.md:19`
  The migrated failing-tests contract says `.agents/hooks/red_run_gate.py` enforces the red-run write gate,
  but the executable, host registration, and its semantic tests are absent from source and packages. A failed
  test run therefore does not activate the promised protection. Restore the shared gate, wire Claude's supported result/stop events while preserving Codex's documented
  result-event limitation, package it, and recover its behavioral tests.

- [x] **REV-003 — MEDIUM — workflow** — `.agents/engineering/workflow/docs-review/SKILL.md:66`
  The docs-review workflow requires `.agents/hooks/docs_reachability.py`, but the executable and tests were
  not migrated. Every docs review reaches a command that cannot open its target file. Restore and package the
  shared reachability check with its tests.

- [x] **REV-004 — LOW — documentation** — `AGENTS.md:25`
  The repository instruction still says the runtime migration and base/engineering/machine split are future
  separate work, even though this candidate performs both. Remove the stale statement and describe the
  current ownership boundary so later agents do not treat the landed architecture as unfinished.

## Coverage

- [x] Canonical shared contracts and runtime — 103 files — 2026-09-20 — `.agents/{base,engineering,machine,workflows}/**`
- [x] Canonical hooks, maps, generator, tests and docs — 75 files — 2026-09-20 — `.agents/{hooks,plugins,skills}/**`, `.agents/sync-generated.ps1`, `.github/**`, `scripts/**`, `tests/**`, root files
- [x] Claude and Codex host adapters — 131 files — 2026-09-20 — `.claude/**`, `.claude-plugin/**`, `.codex/**`
- [x] Generated base and machine distributions — 95 files — 2026-09-20 — `plugins/base/**`, `plugins/machine/**`
- [x] Generated engineering canonical runtime — 112 files — 2026-09-20 — `plugins/engineering/{.agents,hooks,workflows}/**`
- [x] Generated engineering host surfaces — 131 files — 2026-09-20 — remaining `plugins/engineering/**`

## Rules manifest

Route source: `.agents/hooks/skill_router.py` at `a9200fe71c6167fea4dcb7469c001cc7400a2204` — missing; tracked as REV-001.

- Canonical shared contracts and runtime — skills: unavailable pending REV-001; local guidance: `AGENTS.md`; security: yes
- Canonical hooks, maps, generator, tests and docs — skills: unavailable pending REV-001; local guidance: `AGENTS.md`; security: yes
- Claude and Codex host adapters — skills: unavailable pending REV-001; local guidance: `AGENTS.md`; security: yes
- Generated base and machine distributions — skills: unavailable pending REV-001; local guidance: `AGENTS.md`; security: yes
- Generated engineering canonical runtime — skills: unavailable pending REV-001; local guidance: `AGENTS.md`; security: yes
- Generated engineering host surfaces — skills: unavailable pending REV-001; local guidance: `AGENTS.md`; security: yes

## Cross-area notes

- [x] Missing-runtime evidence was split into REV-001 through REV-003; remediation and post-fix route resolution are owned by the next address/incremental passes.

## Parent finalization

**Cross-area notes status:** `complete`
**Parent summary status:** `complete`

All six areas and 647 frozen paths were reviewed. Existing generated output matches canonical source byte-for-byte.
The unavailable review-lens role used the contract's parent fallback. Parent synthesis retained two HIGH, one
MEDIUM, and one LOW finding; all are authorized for immediate remediation.
## Remediation evidence — 2026-09-20

- **REV-001:** Restored the host-neutral router at `.agents/hooks/skill_router.py`, packaged it in
  `engineering`, and made `workflow_ops.routed_skills` use the frozen repository copy or the installed
  package copy. An opted-in repository now fails visibly when neither exists. Source and relocated-package
  review tests both resolve `feature` from a non-empty consumer route table; frozen trees route correctly
  without a `.git` directory.
- **REV-002:** Restored `.agents/hooks/red_run_gate.py` under the `engineering` owner. Claude registers it
  for `PostToolUse`, `PostToolUseFailure`, and `Stop`; Codex remains deliberately unwired because its
  supported result event is still unavailable. Five behavioral tests cover local failures, build/pass
  exclusions, successful CI reads that report failure, Stop enforcement, and repository opt-in.
- **REV-003:** Restored and packaged `.agents/hooks/docs_reachability.py`. Nineteen semantic tests pass and
  the checker reports zero errors and zero warnings against this repository, including generated Claude
  agent-directory discovery.
- **REV-004:** Removed the stale future-migration statement. `AGENTS.md` now records the current shared
  runtime boundary, `CLAUDE.md` inherits it exactly, and authored host manifests are centralized under
  `.agents/plugins/manifests/` with source-layout coverage.

Validation: the complete hook suite passed 540 tests with 8 skips before the final focused remediation;
post-remediation focused suites passed 5 router, 5 red-run, 19 docs, 2 review-routing, 22 root/package,
and 7 relocated engineering-package tests. Workflow verification, both PowerShell regression suites, and
`pwsh .agents/sync-generated.ps1 -Check` also pass; generation is stable at 295 files from 58 definitions.
