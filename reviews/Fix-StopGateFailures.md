# Code review - Fix/StopGateFailures

**Review status:** `complete`
**Reviewed up to commit:** `7d6f49a0c50fa9b9aefc11055a48f8a4b616daf1`  `(2026-10-13)`
**Judgment:** `approved`

## Review pass - 2026-10-13 - full

**Candidate base:** `cdd71edd394e5a8afdb4fe0c94fffa75e57eb79d`
**Candidate head:** `c4c268a62dde3044ac461a3f2f9a73a444c106d6`
**Candidate branch:** `Fix/StopGateFailures`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:8d9950887fc0714395d080c74187a05c0bf2b251720bc8d957236775efd1500e` `(10 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\AjpppJi8bPIczRmeX4TlFQ\-vNjcuqmefvWKeQ2ndOCqB`
**Candidate bundle identity:** `sha256:56c99b870e468d07c9494b0b49b25cf7213f35c79de0e5f00434f27003eb3c0d`
**Work-order path:** `reviews/Fix-StopGateFailures.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

Phase selection: L4 ordinary correctness/workflow review over the child delta. Parent PR #236 is fixed at `cdd71edd394e5a8afdb4fe0c94fffa75e57eb79d`; cumulative local source tests and packaging passed. Fresh native-general fallback and workflow lens inspect the same frozen artifacts. The native CLI is forbidden by the user and specialist model is unavailable. One synchronization completed, actual-parent behind zero. No security classification or routed technical rule.
Scope assessment: delivery slice 3, stacked because the parent has a recorded published-contract delivery gate while this repair remains authorized and unblocked. Create a child PR against `Docs/StopGateOwnership`, land bottom-up and reconcile after parent merge.

## Agent-host coverage

```agent-host-coverage
{
  "schema_version": 1,
  "candidate_head": "7d6f49a0c50fa9b9aefc11055a48f8a4b616daf1",
  "shared_source": ".agents/hooks/hook_dispatch.py and .agents/hooks/continuation_stop.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Fail closed on Stop gate failure or missing deadline verdict; require published whole-goal boundary without trailing actionable tasks.",
      "source": ".agents/hooks/hook_dispatch.py; .agents/hooks/continuation_stop.py; their tests and three harness manifests",
      "mapping": "Canonical claude engineering Stop hook invokes shared dispatcher and continuation gate; base/machine dispatcher resources retain other event behavior.",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "23 dispatcher and 31 continuation tests passed, including real missing workflow_route, both host event spellings, missing gate/crash/KeyboardInterrupt, deadlines and published boundaries; generation, harness and skill packaging checks passed. Fresh installed-host adoption unobserved under the session limit."
      }
    },
    {
      "host": "codex",
      "behavior": "Fail closed on Stop gate failure or missing deadline verdict; require published whole-goal boundary without trailing actionable tasks.",
      "source": ".agents/hooks/hook_dispatch.py; .agents/hooks/continuation_stop.py; their tests and three harness manifests",
      "mapping": "Canonical codex engineering Stop hook invokes shared dispatcher and continuation gate; base/machine dispatcher resources retain other event behavior.",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "23 dispatcher and 31 continuation tests passed, including real missing workflow_route, both host event spellings, missing gate/crash/KeyboardInterrupt, deadlines and published boundaries; generation, harness and skill packaging checks passed. Fresh installed-host adoption unobserved under the session limit."
      }
    }
  ]
}
```

### Findings

- [x] **R1 - HIGH - workflow/native-general** - `.agents/hooks/continuation_stop.py:101`
  The metadata predicate accepts partial, duplicate or absent metadata after Paused and partial extensions to the legacy four-field blocker. The parent plans contract requires the four non-empty metadata fields after either boundary, except an unextended legacy blocker. Require complete unique metadata with no trailing tasks, preserve that legacy exception, and add regressions for partial/duplicate/full forms.

Parent validation: both v2 results matched the immutable run/stage/dispatch identities, supplied source citations, completed status and 98% confidence. Workflow evidence confirms the contract mismatch. Native evidence overlaps R1 for Paused with only Current slice. Its broader request to classify arbitrary metadata prose as actionable is dropped: the published contract defines allowed metadata labels and requires scope descriptions, without a reliable content grammar. Exact shape enforcement addresses the cited partial-form reproduction. No other findings. Agent-host coverage check passed for this exact head. Serial remediation is authorized by the original implementation request; one exclusive runtime writer is active.

Disposition R1: complete ordered non-empty metadata enforced for extended blockers and Paused; legacy blocker preserved. Focused continuation suite passed (31 tests). Source/test fix accepted by parent; fresh incremental watermark required.

## Review pass - 2026-10-13 - incremental

**Candidate base:** `c4c268a62dde3044ac461a3f2f9a73a444c106d6`
**Candidate head:** `7d6f49a0c50fa9b9aefc11055a48f8a4b616daf1`
**Candidate branch:** `Fix/StopGateFailures`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:205cb0c043a91b6df9443379c80cf1212a6008516d9a90b74d9e24479127e161` `(3 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\AjpppJi8bPIczRmeX4TlFQ\Nct-vYD3hzddhPh-yvFL0g`
**Candidate bundle identity:** `sha256:3a042cda4194d376ca6b608e6d866f023c411c19405a441ea117968100f6d2b8`
**Work-order path:** `reviews/Fix-StopGateFailures.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

L4 incremental native-general and workflow review, fresh read-only contexts, no writers or subdispatch. Exact patch SHA b2672d87df427b6efce8ec49b62c54c7d95bb255fe74d4722e00277fc8fe433c. Review only R1 repair and canonical goal checkpoint; previous pass remains immutable. No security route. Focused continuation tests (31) passed after the fix; earlier dispatcher (23) and packaging checks still cover unchanged paths.

### Findings

No incremental findings. Parent validated both completed v2 identities, numeric confidence 97-99, exact immutable citations and passed acceptance conditions. Each reviewer received one schema-only correction; the corrected results are valid. R1 is resolved; prior frozen candidate and changes-requested pass judgment remain unchanged. Exact-head agent-host coverage check passed. Current watermark covers the fixing head.

Delivery reconciliation: parent merged at 19b91b8 and child retargeted to main. The original full-path descriptor reports only candidate-head-changed; that change is covered by the approved incremental watermark. The incremental descriptor reports exact head 7d6f49a, disjoint base movement and no required review. Exact-head Windows/Linux CI 38398088850 passed.
