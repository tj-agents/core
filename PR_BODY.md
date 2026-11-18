## Why

Workflow handoff guidance still preserved raw model, effort and frontier requests, bypassing the lane-only selection contract. Generated Codex agent pins also needed to follow Agent's updated L4 table.

Companion to https://github.com/tj-agents/agent/pull/176.

## What

- Preserve explicit harness and lane choices during handoff; otherwise select the lane for the reasoning the transferred work needs.
- Remove frontier-specific assertions and duplicated hardcoded model rankings from lane tests. Retain generated table-pair checks, effort ordering and the Claude L1 routing invariant.
- Align the Codex implementation, review fallback and test-impact role pins with the updated L4 model.

## Validation

- Focused lane suite: 25 passed, 480 subtests passed after generation using the supported local Agent source override.
- Locked dependency sync, Ruff format/lint, mypy and generation/check passed.
- Full-suite collection remains blocked by five existing `fixtures.lane_expectations` import errors, reproduced on unchanged base.
- Full Linux CI source suite: 546 passed, 6 skipped, 489 subtests passed; one existing failure in `test_renovate_config_parses_and_has_no_extends`. The test and `.github/renovate.json` have identical Git blobs on the base commit and this head.
- Full Windows CI source suite: 544 passed, 8 skipped, 489 subtests passed; the same existing Renovate test failed. Python standards passed on both platforms.

## Draft gates

- Agent #176 merged at `cc6403e4f68fa7b94c65684a4e31bc22613454ca`; post-merge run 43232518173 passed and published generated commit `d64a152f30b91cd42f9fb67e0eaf8054854b482f`. The Renovate-owned Agent runtime pin update with `ci:full` is still required. This PR leaves the protected pin unchanged.
- Independent review remains incomplete: native review recursed and was stopped; the configured reviewer model was unavailable. Parent review found no source findings in this three-file change.
- Generated distribution files and digests remain owned by the existing publication jobs.
