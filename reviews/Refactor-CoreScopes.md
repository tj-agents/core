# Code review — Refactor/CoreScopes

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `30925db6e35961aba525c9fe5992b57955ac5c6c`  `(2026-09-20)`
**Security-reviewed up to commit:** `2d20db6eb950ce0b97ab116d7545b402d565b10d`  `(2026-09-20)`
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

- [x] **REV-005 — HIGH — security/workflow** — `.agents/workflows/workflow_ops.py:317`
  Review routing searches the frozen candidate tree before the installed workflow package for
  `skill_router.py` and executes the first match. A consumer candidate can therefore place executable
  Python at `.agents/hooks/skill_router.py` and run it during `review-prepare`, before review isolation has
  judged the patch. Prefer the workflow package's trusted sibling router; retain the repository copy only
  as a compatibility fallback when no packaged runtime exists, and add a regression test proving a
  candidate router cannot shadow the packaged copy.
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
## Review pass — 2026-09-20 — incremental:runtime-remediation

**Candidate base:** `a9200fe71c6167fea4dcb7469c001cc7400a2204`
**Candidate head:** `a086aaf0b8da99f4f98607c19abce17e3556fe2f`
**Candidate branch:** `Refactor/CoreScopes`
**Candidate scope:** `incremental`
**Candidate path-set:** `sha256:20964a9931a5f391f78a4f7cc6f0cb7b8aaf7b7061e7f1f4cca357e4e121e235` `(37 paths)`
**Candidate bundle:** `C:\Users\tommy\source\repos\base-agents\.git\agent-workflow\runs\p2-core-scopes-incremental-20260920\review\00732b841e84f020d3c09a25f6022038c160c98a06228ce48e0451b55622c68c`
**Candidate bundle identity:** `sha256:033bff459f872b6d036459d9475af1e870db543a273a9dd125aee78f1bce71e7`
**Work-order path:** `reviews/Refactor-CoreScopes.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

- Added `REV-005`. The restored runtime and prior four dispositions otherwise match their contracts,
  generated copies, host registrations, and validation evidence.

### Coverage

- [x] Runtime restoration, manifest relocation, generated output, tests, and remediation record — 37 paths — 2026-09-20

### Rules manifest

No `.agents/skill-routes.json` exists in this repository, so no repository-specific routed skill applies.
The incremental pass used the canonical local guidance and performed security review over both executable
hooks and the packaging boundary.

### Parent finalization

**Cross-area notes status:** `complete`
**Parent summary status:** `complete`

The frozen remediation delta was reviewed against `a9200fe`. One new HIGH security finding was opened;
all earlier finding text, severities, candidate identity, and pass judgment are preserved.

**REV-005 disposition:** `workflow_ops` now prefers the router beside its own trusted workflow package
and uses a candidate repository copy only when the package has no router. The regression fixture commits a
shadow router that returns a false skill and proves review preparation still resolves the packaged route.
All 26 workflow-operation tests and 15 package/source-layout tests pass, and generation remains stable.
## Review pass — 2026-09-20 — incremental:trusted-router-remediation

**Candidate base:** `a086aaf0b8da99f4f98607c19abce17e3556fe2f`
**Candidate head:** `c632a2984f3b1330d4e6205bd1aaf8eec0806e5f`
**Candidate branch:** `Refactor/CoreScopes`
**Candidate scope:** `incremental`
**Candidate path-set:** `sha256:8ab9adc5d6c9ff58b1c1c70acc12770435b9fc5897dd0ed48d39961887005856` `(4 paths)`
**Candidate bundle:** `C:\Users\tommy\source\repos\base-agents\.git\agent-workflow\runs\p2-core-scopes-incremental-security-20260920\review\7df1f53409ac2b16588b8500590f28d958076311e9f6ddd9b5b3146545f4f1da`
**Candidate bundle identity:** `sha256:3c576fb26b6ea878bf2af494fc03422627275df953fcbadd319fbba2b1840a19`
**Work-order path:** `reviews/Refactor-CoreScopes.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

### Findings

No new findings. The workflow runtime now selects its own packaged router before considering a repository
fallback. The regression candidate carries a shadow router and cannot influence the resolved rule set.
The generated workflow copy is byte-equivalent to canonical source, and the work-order-only changes retain
all earlier candidate identities, finding text, severities, and completed pass judgments.

### Coverage

- [x] Trusted router selection, shadowing regression, generated copy, and review disposition — 4 paths — 2026-09-20

### Rules manifest

No `.agents/skill-routes.json` exists in this repository, so no repository-specific routed skill applies.
The security and workflow lenses reviewed the exact four-path frozen delta.

### Parent finalization

**Cross-area notes status:** `complete`
**Parent summary status:** `complete`

The exact `a086aaf..c632a29` remediation delta is approved with zero new findings. All five findings in the
canonical work order are resolved, and the current review and security watermarks advance to `c632a29`.
## Review pass — 2026-09-20 — incremental:large-pr-binding

**Candidate base:** `c632a2984f3b1330d4e6205bd1aaf8eec0806e5f`
**Candidate head:** `b8e2df716aa0283d58393b82b98ac5eb993db167`
**Candidate branch:** `Refactor/CoreScopes`
**Candidate scope:** `incremental`
**Candidate path-set:** `sha256:8ab9adc5d6c9ff58b1c1c70acc12770435b9fc5897dd0ed48d39961887005856` `(4 paths)`
**Candidate bundle:** `C:\Users\tommy\source\repos\base-agents\.git\agent-workflow\runs\p2-core-scopes-incremental-large-pr-v2-20260920\review\cddd3805c5b7075d30e1c4b33b2a54428c1214cd95e54b8a03f8322700c9dbb0`
**Candidate bundle identity:** `sha256:3a5bdd26cfc15e77bd04232204cece0007f592e6d3e8815a03ac10f50ef5b2ba`
**Work-order path:** `reviews/Refactor-CoreScopes.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

### Findings

No new findings. Delivery binding now reads every PR path from GitHub's paginated pull-files endpoint,
requires all summary paths, and compares the unique result with the authoritative `changedFiles` count.
The command uses fixed argument boundaries and fails closed on API errors, missing paths, empty output, or
count disagreement. PR #12 returned 658 unique paths against an authoritative count of 658.

### Coverage

- [x] Large-PR path discovery, complete-set validation, generated workflow copy, and review record — 4 paths — 2026-09-20

### Rules manifest

No `.agents/skill-routes.json` exists in this repository, so no repository-specific routed skill applies.
The security and workflow lenses reviewed the exact four-path frozen delta.

### Parent finalization

**Cross-area notes status:** `complete`
**Parent summary status:** `complete`

The exact `c632a29..b8e2df7` delivery-binding delta is approved with zero findings. All 29 workflow-operation
tests pass, generation remains stable at 295 files from 58 definitions, and the current review and security
watermarks advance to `b8e2df7`.
## Review pass — 2026-09-20 — incremental:windows-path-identity

**Candidate base:** `b8e2df716aa0283d58393b82b98ac5eb993db167`
**Candidate head:** `2d20db6eb950ce0b97ab116d7545b402d565b10d`
**Candidate branch:** `Refactor/CoreScopes`
**Candidate scope:** `incremental`
**Candidate path-set:** `sha256:a1ead035a6bf66aae38142e0e618e1f87d013a2f090f63310d44de478024b545` `(4 paths)`
**Candidate bundle:** `C:\Users\tommy\source\repos\base-agents\.git\agent-workflow\runs\p2-core-scopes-incremental-windows-ci-20260920\review\03b7aa51d85819e82f6c3f1f02e43f35b6ad39bb22e2e837bc014423e580e65c`
**Candidate bundle identity:** `sha256:66670d029eb96aff766d5f8abbf1f7ce0c9cc5ede8668df34d514d2cdf08009f`
**Work-order path:** `reviews/Refactor-CoreScopes.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

### Findings

No new findings. The generator resolves its input root once before deriving canonical relative paths, and
both temporary package fixtures resolve their root before constructing expected paths. This makes Windows
8.3 and long path aliases compare as one identity without weakening containment checks.

### Coverage

- [x] Generator root identity, both Windows package fixtures, and review record — 4 paths — 2026-09-20

### Rules manifest

No `.agents/skill-routes.json` exists in this repository, so no repository-specific routed skill applies.
The workflow lens reviewed the exact four-path frozen delta.

### Parent finalization

**Cross-area notes status:** `complete`
**Parent summary status:** `complete`

The exact `b8e2df7..2d20db6` Windows path-identity delta is approved with zero findings. All 22 root/package
tests pass locally, generation remains stable at 295 files from 58 definitions, and the current review and
security watermarks advance to `2d20db6`.

## Review pass — 2026-09-20 — incremental:delivery-gate-fixture

**Candidate base:** `2d20db6eb950ce0b97ab116d7545b402d565b10d`
**Candidate head:** `45616059eb48943489d88cda2bda59a9c064cb57`
**Candidate branch:** `Refactor/CoreScopes`
**Candidate scope:** `incremental`
**Candidate path-set:** `sha256:78725d60be3d9a3f87d537d1d3fb7e7cfc50386008a53a3d78b173fd26a3834e` `(2 paths)`
**Candidate bundle:** `C:\Users\tommy\source\repos\base-agents\.git\agent-workflow\runs\p2-core-scopes-incremental-ci-fixture-20260920\review\ecf4661f2dda0acaf565f188862a96fb74a42dbaf5f203ce32648b151bb253ac`
**Candidate bundle identity:** `sha256:027ef9bd4a5c2bccc390e6dd3b691ceec776208df419be4faa262abfcc5c1e24`
**Work-order path:** `reviews/Refactor-CoreScopes.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

- [x] **REV-006 — MEDIUM — workflow/testing** — `.agents/hooks/tests/test_delivery_binding_gate.py:148`
  The subprocess fixture omits the `changedFiles` field that production requests and forwards into the
  complete-path validation. These tests therefore exercise `expected_count=None` and would still pass if
  delivery binding stopped enforcing GitHub's authoritative changed-file count. Include `changedFiles` in
  the mocked PR summary and add a subprocess regression proving a truncated paginated response creates no binding.

### Coverage

- [x] Delivery-binding subprocess fixture and review-only watermark commit — 2 paths — 2026-09-20

### Rules manifest

No `.agents/skill-routes.json` exists in this repository, so no repository-specific routed skill applies.
The native-general and workflow lenses inspect the exact two-path frozen delta.

### Parent finalization

**Cross-area notes status:** `complete`
**Parent summary status:** `complete`
The exact `2d20db6..4561605` delta has one new MEDIUM workflow/testing finding. Native-general found no
defect; the workflow lens identified the missing authoritative-count coverage. The completed pass advances
the review watermark to `4561605`; remediation must return through a fresh incremental review.

**REV-006 disposition:** The subprocess PR summary now includes `changedFiles`, and a dedicated
truncation case proves that one returned path against an authoritative count of two fails closed and
creates no persistent delivery binding. The focused delivery-binding suite passes all 20 tests.

## Review pass — 2026-09-20 — incremental:changed-file-count-remediation

**Candidate base:** `45616059eb48943489d88cda2bda59a9c064cb57`
**Candidate head:** `30925db6e35961aba525c9fe5992b57955ac5c6c`
**Candidate branch:** `Refactor/CoreScopes`
**Candidate scope:** `incremental`
**Candidate path-set:** `sha256:78725d60be3d9a3f87d537d1d3fb7e7cfc50386008a53a3d78b173fd26a3834e` `(2 paths)`
**Candidate bundle:** `C:\Users\tommy\source\repos\base-agents\.git\agent-workflow\runs\p2-core-scopes-incremental-count-remediation-20260920\review\26d63520b42efd27b78b0db3efd32172b8c3c32bd27cc8a3466aa450d7e12414`
**Candidate bundle identity:** `sha256:2de0c6d6ad3bd96402086732f26ac52477de9162be72ce88ec5886670030e55f`
**Work-order path:** `reviews/Refactor-CoreScopes.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

- [x] **REV-007 — MEDIUM — workflow/testing** — `.agents/hooks/tests/test_delivery_binding_gate.py:213`
  The new truncation regression triggers both a missing-summary-path mismatch and a changed-file-count mismatch.
  It can therefore remain green if the authoritative count stops controlling rejection, because the missing
  summary path still fails closed. Let the fixture override `changedFiles`, then keep the summary and API path
  sets equal while only the authoritative count disagrees so the test isolates the REV-006 safety property.

### Coverage

- [x] REV-006 remediation, regression coverage, and review disposition — 2 paths — 2026-09-20

### Rules manifest

No `.agents/skill-routes.json` exists in this repository, so no repository-specific routed skill applies.
The native-general and workflow lenses inspect the exact two-path frozen remediation delta.

### Parent finalization

**Cross-area notes status:** `complete`
**Parent summary status:** `complete`
The exact `4561605..30925db` remediation delta has one new MEDIUM workflow/testing finding. The
workflow lens found no defect; native-general identified that the regression does not isolate the count gate.
The completed pass advances the review watermark to `30925db`; remediation requires another incremental pass.

**REV-007 disposition:** `write_pr` now accepts an explicit authoritative count. The regression keeps
the PR summary and paginated API at the same single path while reporting `changedFiles: 2`, asserts the
count-mismatch error, asserts no missing-path error, and proves no binding is written.
