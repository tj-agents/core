# Code review — Fix/ContinuationEnforcement

**Review status:** `complete`
**Reviewed up to commit:** `202b330ca177ecbf36ac7fd0a12f21e9dbd00a3d`  `(2026-10-10)`
**Judgment:** `approved`
**Security-reviewed up to commit:** `202b330ca177ecbf36ac7fd0a12f21e9dbd00a3d`

## Review pass — 2026-10-10 — full

**Candidate base:** `33fb4155973b8ee1d26a8fd6f2a27d8428f6f166`
**Candidate head:** `d108247c0a48e93c4505273c4155695a057676c0`
**Candidate branch:** `Fix/ContinuationEnforcement`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:8e0ae10c8fa049a08bf50b7e89f04c4e4c345add89403d895c2cf9fb014dc15c` `(10 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\TNdZlHwRLMPim6WGjuDPpp\OSmhI56cksm9lrVW1DOiK4`
**Candidate bundle identity:** `sha256:5dc8ed44b075c76ebdad09406ac9af055f64db81feea574fe892b7d76e2aa914`
**Work-order path:** `reviews/Fix-ContinuationEnforcement.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

### Findings

- [x] **R1 — MEDIUM — workflow** — `.agents/hooks/continuation_stop.py:13`
  Direct cancellation prompts "Cancel it." and "Cancel this." do not match the anchored PAUSE grammar, so an active obligation blocks the user cancellation. Accept these direct referents while continuing to exclude quoted or fenced example text.

- [x] **R2 — HIGH — parent correctness** — `.agents/hooks/workflow_route.py:210`
  A direct pause or cancellation permits only its current Stop event; record_receipt retains the execution obligation without persisting the pause. The next status prompt replaces the pause text and forces the same paused goal to resume without user authorization. Persist session/worktree suspension until an explicit execution resume, with multi-turn regressions.

- [x] **R3 — HIGH — native / parent full-candidate confirmation** — `.agents/hooks/continuation_stop.py:224`
  An existing malformed or unreadable owner.json is treated as a missing owner, so an unrouted Stop with no binding returns without reconciliation. The original d108247 addition has this exact path. Distinguish absent state from invalid or unreadable existing state and block for reconciliation; cover malformed, non-object and unreadable artifacts without an execution receipt.

- [x] **R4 — HIGH — native / parent full-candidate confirmation** — `.agents/hooks/continuation_stop.py:163`
  An existing malformed or unreadable delivery binding is treated as inactive; when no owner or route obligation exists, Stop then passes. The original d108247 addition has this exact path. Reject invalid existing bindings and add a regression proving the ownerless, unrouted path blocks.

- [x] **R5 — HIGH — parent authorization probe** — `.agents/hooks/workflow_route.py:124`
  A question such as "How does plan-execution work?" selects execution and writes an execution obligation despite having no execution directive. The actual prompt-to-receipt-to-Stop probe then blocks a fresh question for missing initialization. Restrict authorization selection to execution directives or explicit skill invocations; exclude discussion, quoted examples and negative questions while preserving the accepted mixed planning directives.

- [x] **R6 — MEDIUM — parent ownership probe** — `.agents/hooks/continuation_stop.py:177`
  Foreground association accepts any descendant of the owning CLI. A simulated ancestry hook -> independent read-only CLI -> owning CLI is therefore adopted despite no routed obligation. Require the nearest matching CLI process boundary to be the recorded owner, retaining its creation identity check. This is source and simulated ancestry evidence; a live nested host event has not been observed.

### Review evidence

Native CLI review was invoked against the frozen base but every source read failed before launch because of the deferred sandbox defect. Its no-findings statement is unusable. A fresh supported L4 native-general fallback inspected the immutable bundle and returned no concrete defect. The workflow L4 lens inspected the same bundle and returned R1 with confidence 94; parent verified the anchored grammar and its Stop use. Parent independently confirmed R2 from receipt retention and the current-prompt-only pause exception. The configured review_lens model was unavailable on this account; supported L4 contexts supplied the same bounded independent source lenses.

Linux CI at this exact head found a separate packaging launch-budget regression: Claude Stop launches two interpreters. Its 897-test source-layout run failed only the nine tool subcases of test_each_plugin_launches_at_most_one_interpreter_per_prompt_or_tool_event. CI repair must put continuation_stop into the existing Stop dispatcher without weakening the budget.

Applicable root AGENTS.md/CODE_CONVENTIONS.md; tier gate resolves no stack conventions; routed rule identities and route violations are empty. Security classification is empty. Pre-review synchronization completed once with zero missing base commits. origin/main later moved on an overlapping catalog path, so base integration and fresh incremental review are required before delivery.

## Host coverage

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/hooks/continuation_stop.py and workflow_route.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Prevent ending an observed authorized execution without a verified terminal or registered continuation",
      "source": ".agents/hooks/continuation_stop.py",
      "mapping": ".agents/plugins/manifests/claude/engineering-hooks.json Stop",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Source and packaged Stop regressions passed, including both host mappings, routed obligations, scheduler evidence and completion identity; native Codex Stop block/continued callback was separately observed. Normal-profile gate activation and Claude live acceptance remain unobserved."
      }
    },
    {
      "host": "codex",
      "behavior": "Prevent ending an observed authorized execution without a verified terminal or registered continuation",
      "source": ".agents/hooks/continuation_stop.py",
      "mapping": ".agents/plugins/manifests/codex/engineering-hooks.json Stop",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Source and packaged Stop regressions passed, including both host mappings, routed obligations, scheduler evidence and completion identity; native Codex Stop block/continued callback was separately observed. Normal-profile gate activation and Claude live acceptance remain unobserved."
      }
    }
  ],
  "candidate_head": "202b330ca177ecbf36ac7fd0a12f21e9dbd00a3d"
}
```

Remediation: direct_control now recognizes anchored referents and is shared by routing and Stop. Suspension persists only in the same worktree until explicit resume, including active-owner sessions without a prior obligation. Focused prompt-to-Stop and packaged Claude dispatcher assertions passed; launch-budget 4/4, dispatcher 20/20, routing 14/14, Stop 21/21, generated Check passed. Final incremental review is required.

Result format follow-up: corrected lens records passed schema and identity checks but retained extra immutable-artifact classifications for source citations. Dispatches closed after the one correction; parent independently verified the cited parser and receipt defects and completed the bounded correctness check. Raw artifacts are retained under the review run.

## Review pass — 2026-10-10 — incremental

**Candidate base:** `d108247c0a48e93c4505273c4155695a057676c0`
**Candidate head:** `ee157c4093e561deb8823dbe819119c28836fd4a`
**Candidate branch:** `Fix/ContinuationEnforcement`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:3b43c9ab5fb362f79d3163221ff9db1769e00cdb90fc98470904e154242043cf`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\GN4vFMRXb-WdROMKmBbZlK\vF47xXKBTL5mQhYXIC8VWf`
**Candidate bundle identity:** `sha256:20ea3c314f9a198f5557605e69c8132d316ecdfb9906016ad86d72887640d5f6`
**Work-order path:** `reviews/Fix-ContinuationEnforcement.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

### Findings

No retained findings. Both fresh results passed WorkflowContract.validate_result against exact dispatch identities. The two candidate reports describe generated package drift at the frozen authored head. Parent rejected them as intentional: scripts/check_generated_paths.py forbids generated distribution and catalog digest commits in PRs; .github/workflows/ci.yml regenerates and checks before both test matrices, then commits generated packages only after main merges. At ee157c4 Linux generation/check and all 897 source-layout tests passed; 1022 shared-runtime tests ran with only the obsolete callout Stop prohibition failing. Local 21 Stop/integration tests include fresh packaged Claude dispatch. Causal post-merge regeneration remains an explicit delivery acceptance step.

The native CLI was invoked for this range but could not inspect source because of the deferred sandbox setup failure. Supported independent frozen native-general and workflow source lenses provide the usable evidence. Security classification and routed technical rules are empty; one pre-review synchronization found zero missing commits. Parent read the frozen changed source and test paths, checked the canonical runtime delegation and anchored same-worktree controls, and found no additional changed-line defect.

## Review pass — 2026-10-10 — incremental

**Candidate base:** `ee157c4093e561deb8823dbe819119c28836fd4a`
**Candidate head:** `ffeafa9eb82c5b491d2a5d242b7eb59f723a5cd5`
**Candidate branch:** `Fix/ContinuationEnforcement`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:c6d835acd38076e165bb4d4e438a3d53278122eef1b34a534183c89403f8b668`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\giz1r7Feb0FYYU7cPdm6bF\-YdGVeXHJvCfRi7NZA7F5G`
**Candidate bundle identity:** `sha256:280e248a17d483c7c86f5baf428d3bfbb11bbc916660e705c4609cc5d1845cad`
**Work-order path:** `reviews/Fix-ContinuationEnforcement.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

No retained changed-line findings. Both supported fresh lenses validated against exact envelopes and confirmed the two-line test correction preserves callout coverage. Native CLI accessed the published whole PR through GitHub and reported two malformed-state paths in the original shared Stop addition; those findings are separately confirmed against the original full candidate and require serial repair before merge.

Parent finalized the final test-only pass after valid host coverage and exact-envelope lens checks. Its changed lines are clean; cumulative original-candidate malformed-state findings and parent authorization/association probes require repair. Windows and Linux CI at ffeafa9 both finished green.

R3–R6 remediation: strict owner/binding reads distinguish FileNotFound from malformed, non-object, invalid-UTF8 and PermissionError state; actual unreadable-file regressions exercise the reader. Direct directive/whole-skill selection excludes questions and quoted/fenced examples while preserving all planning-intent cases and pause state. Foreground ancestry stops at the nearest matching executable boundary; Windows uses one process snapshot and exact current-process ownership is recognized after creation identity verification. Final Stop 26/26, routing 30/30, dispatcher 20/20, callout 13/13, launch budget 4/4; additional 80 in-process actual authorization/preserved planning cases passed. Regeneration and Check passed. Fresh incremental review required.

## Review pass — 2026-10-10 — incremental

**Candidate base:** `ffeafa9eb82c5b491d2a5d242b7eb59f723a5cd5`
**Candidate head:** `848598b31e1647a34c45529f56164d62f951fce7`
**Candidate branch:** `Fix/ContinuationEnforcement`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:b04a282d220ae2b22c181315688f2705ea905e945415a9eec793e61fea4b678d` `(5 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\lUzIIzBaD7FgDHrnEweXR3\b2nnlb6i_xeGdGHWD_fIiq`
**Candidate bundle identity:** `sha256:24b4ed922670809ee415e43f181f3c9cd72bce3e5e4fd153fb7a3f51ca386bca`
**Work-order path:** `reviews/Fix-ContinuationEnforcement.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

- [x] **R7 — HIGH — parent authorization verification** — `.agents/hooks/workflow_route.py:16`
  The new directive grammar treats conjunctions within an indirect question as execution commands. Actual route probes select plan-execution for "How do I plan and implement the migration?", "Can you explain how to plan and implement the migration?", and "Explain how to plan and implement the migration." These requests authorize explanation, not execution. Reject indirect question/explanation sentences before matching their internal directive-shaped clauses, while retaining direct action requests and explicit execution in a subsequent sentence. Add actual prompt-to-receipt-to-Stop cases alongside the existing question regressions.

Both fresh source lenses returned valid exact-envelope results with no candidate findings. Parent rejected the generalized authorization conclusion after independently reproducing the three compound questions above. Native CLI source reads failed due to the deferred sandbox defect, so its no-findings output is unusable. Frozen root contracts and tier resolution were checked: no stack tier applies; routed rule/security sets are empty. Four reviewer-created bytecode files were removed from the disposable bundle; subsequent full integrity and exact-head host coverage validation passed, proving the authored frozen files remained unchanged. Current judgment is changes-requested for R7.

R7 remediation accepted: sentence-scoped indirect question/explanation exclusion, including polite prefixes, preserves direct and later-sentence execution. Final routing 30/30 and Stop 26/26 passed with regenerated packages; actual compound-question receipt/Stop regressions passed. Fresh incremental review required.

## Review pass — 2026-10-10 — incremental

**Candidate base:** `848598b31e1647a34c45529f56164d62f951fce7`
**Candidate head:** `4918af6dd1c3430ab6c0cf66682a5fcd6c213bdc`
**Candidate branch:** `Fix/ContinuationEnforcement`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:b7fbb1c282bed61810c37eb4fb92bc892e44fad5f232b69dcc004ef99f697469` `(4 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\Y76euleP6ZVkH7-MsyzK_E\Omji0jazdVFNI2oU4a8_ID`
**Candidate bundle identity:** `sha256:75f5512ecf1347149ebbd06dd2a13a92e60ab26bb58c4fab2cbe963194965bf9`
**Work-order path:** `reviews/Fix-ContinuationEnforcement.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

- [x] **R8 — HIGH — native-general / parent confirmation** — `.agents/hooks/workflow_route.py:23`
  Recommendation/capability questions still match internal execution conjunctions. Parent reproduced plan-execution selection for "Should we plan and implement the migration?", "Can I plan and implement the migration?", and "Would we plan and implement the migration?". Extend the interrogative boundary and cover actual route-to-Stop behavior while preserving polite direct requests.

Both fresh results validated against their exact v2 envelopes. Workflow lens had no candidates; parent confirmed the native-general finding in the live exact-head source. Native CLI was invoked but all source reads failed due to the deferred sandbox defect; its no-findings output is unusable. Frozen root contracts, empty routed rules/security, complete bundle integrity and exact-head host coverage passed. Judgment changes-requested for R8.

R8 remediation accepted: two grammar lines extend the existing indirect-context predicate; full routing 30/30 and Stop 26/26 passed after generation/check. Explicit Could you/Would you action requests and all existing mixed planning cases remain passing. Fresh incremental review required.

## Review pass — 2026-10-10 — incremental

**Candidate base:** `4918af6dd1c3430ab6c0cf66682a5fcd6c213bdc`
**Candidate head:** `b8482a676c661a89b362ff9e7e80b446329c0e6a`
**Candidate branch:** `Fix/ContinuationEnforcement`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:b7fbb1c282bed61810c37eb4fb92bc892e44fad5f232b69dcc004ef99f697469` `(4 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\QDMAHaAlNUPdKBNdGOnYYz\HNdjDqxeCDwEcV_6s86w15`
**Candidate bundle identity:** `sha256:081c3a83ba19fdabff1817d5630765e3500ebae7c772b1801060e9d00c1cc211`
**Work-order path:** `reviews/Fix-ContinuationEnforcement.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

- [x] **R9 — HIGH — native CLI / parent changed-line confirmation** — `.agents/hooks/workflow_route.py:25`
  Bare auxiliary exclusion rejects direct requests. Parent compared exact 4918af6 and b8482a6 source: Need to plan and implement, Must plan and implement, Do the plan and implement, and Have a plan and implement changed from execution=true to false. Restrict the ambiguous auxiliary forms to interrogative subjects and preserve these direct requests. Native CLI's bare Must complete/Need to implement examples were already false before this delta and are dropped; its mechanism is confirmed by these actual changed cases.

- [x] **R10 — HIGH — native-general / parent confirmation** — `.agents/hooks/workflow_route.py:26`
  Contracted modal questions bypass the new uncontracted question branch. Actual Can't I and Couldn’t we compound-question probes select execution. Support modal negative contractions, preserving positive polite directives, and add routing plus actual receipt/Stop cases.

Both fresh v2 results validated against exact envelopes; workflow had no candidates. Native CLI accessed the published candidate through GitHub after local sandbox reads failed. Parent confirmed the changed direct-request regression and contracted question gap. A misplaced reviewer result was moved out of the disposable bundle; full integrity and exact-head coverage must pass before disposal. No source edits/imports/tests occurred in the bundle. Current judgment changes-requested.

R9/R10 remediation accepted: direct compound Need to/Must/Do/Have requests restored; contracted modal questions and explicit must-not prohibitions excluded. Final package generation/check and 26 Stop tests passed. The 30-test routing run had one existing recovery subprocess timeout; the full affected recovery method passed unchanged in focused verification. Assertions/timeouts preserved. Fresh incremental review required.

## Review pass — 2026-10-10 — incremental

**Candidate base:** `b8482a676c661a89b362ff9e7e80b446329c0e6a`
**Candidate head:** `13a22abe36841079c2e07866d8c4148c0ca6595f`
**Candidate branch:** `Fix/ContinuationEnforcement`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:b7fbb1c282bed61810c37eb4fb92bc892e44fad5f232b69dcc004ef99f697469` `(4 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\yBeIFaFc-RNsh37FrjzrZa\NikB_o3SP02ts79Qdpx1Yi`
**Candidate bundle identity:** `sha256:8a1cf6ebcc22fceeb80b8c1107a9872d1f5c95f1f56beeb1d3e14ea9bbe83a82`
**Work-order path:** `reviews/Fix-ContinuationEnforcement.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

- [x] **R11 — MEDIUM — native CLI / parent changed-line confirmation** — `.agents/hooks/workflow_route.py:27`
  With an active goal, "Do the agents plan and implement the migration?" changes from no route at b8482a6 to plan execution at 13a22ab. The narrowed ambiguous auxiliary branch recognizes only pronoun subjects; preserve question punctuation and exclude this interrogative before matching its internal conjunction, while retaining accepted direct Do/Have requests.

Both fresh static source lenses returned valid exact v2 envelopes. Their coordinated-negation candidate is dropped from this incremental pass: actual planning_intent strips the negated planning phrase before authorization in both frozen base and head, so both actual routes already execute. Raw predicate differences do not establish a new routing regression. Native CLI accessed the exact published source through GitHub and reported the distinct noun-subject question above; parent confirmed its actual changed routing behavior. Full bundle integrity and exact-head host coverage are required before disposal. Current judgment changes-requested for R11.

R11 remediation accepted: preserved sentence delimiters and excluded Do/Have interrogatives carrying a question mark. Actual routing negative/direct-positive methods and read-only receipt-to-Stop method passed; accepted direct auxiliary requests and later-sentence execution remain covered. Latest main integrated at e63a6e6. Fresh exact-head review and CI required.

## Review pass — 2026-10-10 — incremental

**Candidate base:** `13a22abe36841079c2e07866d8c4148c0ca6595f`
**Candidate head:** `202b330ca177ecbf36ac7fd0a12f21e9dbd00a3d`
**Candidate branch:** `Fix/ContinuationEnforcement`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:9a2a85c641fc64ff769b2ce87fb50ad970317d2620001f11b2a0f7cce1051c71` `(116 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\wEsEwNGo9TKXwr18bBDA7n\dYV6VB0N5t_BXqxPpCNhSt`
**Candidate bundle identity:** `sha256:7903c0add8bc7ed3b4a7373bb970ebbbded4314d313a895cfd3405b51ee622f4`
**Work-order path:** `reviews/Fix-ContinuationEnforcement.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

### Findings

No additional findings. Corrected native-general, workflow and security v2 results validated against their exact dispatch envelopes. Native-general cites the frozen R11 source, focused routing/Stop regressions and distinct host mappings. Workflow returned no candidates; its source citation detail is limited, so parent relies on the prior confirmed routing/receipt checks and the source-cited native/security evidence. Security authenticated the authored trunk range 2dc7641..202b330 and checked strict owner/binding state, nearest CLI identity, scheduler/completion evidence, receipts and both canonical host mappings with no candidate. Native CLI local source reads failed before launch; its final statement is unusable and is not a clean review claim. All R1-R11 findings are resolved. Exact-head source CI run 38079457158 passed guard, Windows and Linux; package generation and Check passed for 505 files. Full immutable integrity and exact-head coverage must pass before delivery. Normal-profile gate activation and live Claude acceptance remain unobserved.
