# Code review — Fix/WorkflowBytecodeIntegrity

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `1de04c6a4a6dfdf0219b5b57bf0cb15443bb30e0`  `(2026-10-07)`
**Judgment:** `approved`

## Review pass — 2026-10-07 — full

**Candidate base:** `830c7891075b322e359e0bed8286add50ecd8b64`
**Candidate head:** `1de04c6a4a6dfdf0219b5b57bf0cb15443bb30e0`
**Candidate branch:** `Fix/WorkflowBytecodeIntegrity`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:460efd7a93fce95cc59b228bac580e01955d887aaa9a93857e3c1008a80b46c0` `(5 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\Vi58kLxap8J2kQwH_m1gbK\0FbqYlq5nJBMekkmTC_PR4`
**Candidate bundle identity:** `sha256:6981fcdfc27189d2e26bddcf57c1d6aa169837fbe6e893958b0378995014ae0f`
**Work-order path:** `reviews/Fix-WorkflowBytecodeIntegrity.md`
**Work-order mode:** `new`
**Pass judgment:** `approved`

Native code-review (medium), the `api-contract` lens, and the `workflow` lens each ran over the frozen
range. No qualifying security path (`security.first_path`/`trunk_first_path` both null), so Stage 6 did
not apply.

### Findings

No retained findings. The native layer raised one point that did not survive independent verification:
it asserted the new `test_entry_points_suppress_bytecode_without_relying_on_the_parent_interpreter` test
(test_workflow_contracts.py) would fail CI because `plugins/engineering/workflows/{workflow_ops,
continuation_runtime}.py` still lack the fix (generated output is deliberately left uncommitted on this
branch). Reproduced locally: true against an un-regenerated tree. But `.github/workflows/ci.yml`'s
`verify` job (runs on `pull_request`, unconditional) regenerates `plugins/*` via
`.agents/sync-generated.ps1` *before* its `shared runtime tests` step, so CI exercises a freshly
regenerated tree and the test passes there. The dependency on a prior local regeneration to pass outside
CI is pre-existing behavior already present in this same file (`test_each_verifier_executes_its_adjacent_bundle`,
`test_contract_provider_and_runtime_resources_are_generated_verbatim`) and documented in the root
README's "Run `pwsh .agents/sync-generated.ps1` locally only to refresh the tree for tests" guidance, not
a defect introduced by this diff. Both lenses (`api-contract`, `workflow`) returned `complete` with no
claims.
