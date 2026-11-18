# Code review — Fix/DependentPrBranchCleanup

**Review status:** `complete`
**Judgment:** `changes-requested`

**Reviewed up to commit:** `adc50e3d42a7723887107e9992612662148c006f`  `(2026-10-11)`

**Security-reviewed up to commit:** `da794afde95e02a10aa137f52786a7db7cd1941f`  `(2026-10-11)`

## Review pass — 2026-10-11 — full

**Candidate base:** `b4e6f1020b4c1edcfea8e21d6dae2ba5ebdb8a5e`
**Candidate head:** `6fd7c127919cf0055e9f9b67f41b0cb21aaf5591`
**Candidate branch:** `Fix/DependentPrBranchCleanup`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:32652d06428e4c65cc7db133d2346282fc99184510c7f9da231cd27899fa9c5d` `(13 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\ojuvuNxLNd9-TW3zgWmxVv\336iIeqKg4ksCFos92_rXA`
**Candidate bundle identity:** `sha256:a4836ae35b634407a5334af85d05960063c3fa28c6fe1791454f37c3d1ac2165`
**Work-order path:** `reviews/Fix-DependentPrBranchCleanup.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

Descriptor: C:/Users/TommySeery/source/repos/tj-agents/core/.git/agent-workflow/runs/dependent-cleanup/review/df7ea221ea8a83892c085a2cf76feb5c0a0a8c142aab35455ef1f5ee0040a10d/descriptor.json
Patch identity: sha256:26d315feebe437de79ccced16f5ef078334bfa7a2d87a867a294b46c0aad534a. Routed rules: none. Tier gate: no stack tier conventions. Root AGENTS and CODE_CONVENTIONS still apply. Lenses: native-general and workflow in one wave. Security classification: no qualifying path. Synchronization: origin/main at b4e6f1020b4c1edcfea8e21d6dae2ba5ebdb8a5e, zero missing base commits.

### Findings

- [x] R1 — MEDIUM — workflow: `cleanup_proof.py:444-447,503-504` permits a leading hyphen in a branch interpolated into deletion commands. Reject option-prefixed branches and verify rejection produces no commands.
- [x] R2 — MEDIUM — native-general: `merge/SKILL.md:323` instructs a raw remote deletion command emitted at `cleanup_proof.py:504`, but its host permission inventory contains only the proof helper. Route remote deletion through the declared proof helper, requiring fresh merged-head, containment and HEAD/BASE evidence plus exact remote-ref verification before deletion.

Both independent v2 results matched this frozen descriptor and included changed-line evidence and concrete corrections. Parent accepted both, deduplicated them, and assigned MEDIUM severity under the canonical severity vocabulary. Serial remediation completed this tightly coupled group. R1: explicit option-prefixed branch regression passed. R2: eight temporary-repository cases passed (156.060s), including fresh removal, new BASE dependency, failed/malformed evidence, changed remote head, lease race, nonfinite receipt, wrong repository and exact action parsing. Primary-origin binding pins forge queries to github.com/owner/repo. Local cleanup and both-host action inventory also passed. Required generated/resource checks are being captured; a fresh incremental watermark is still required after the correcting commit.

Native specialist invocation failed because the account rejected gpt-5.3-codex-spark (artifact aed3bcdd1612a38f-native-cleanup-review.log). The prescribed native gpt-5.6-terra fallback exited 0, but every local read failed before launch (artifact efc5f944fd6ffa91-native-cleanup-review-fallback.log). Its no-findings sentence is rejected because the frozen candidate was not inspected. Two fresh independent read-only L4 evidence workers completed native-general and workflow review on the same validated bundle using supported scoped reads. Their candidate identities and evidence were validated before parent synthesis. No failed invocation is clean-review evidence.

## Host coverage

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/engineering/workflow/merge and .agents/hooks/cleanup_dependency.py with machine peer-cli cleanup",
  "candidate_head": "adc50e3d42a7723887107e9992612662148c006f",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Preserve merged branches with open HEAD or BASE users before primary, linked and detached cleanup",
      "source": ".agents/engineering/workflow/merge/scripts/cleanup_proof.py; .agents/hooks/cleanup_dependency.py; .agents/machine/utility/peer-cli/scripts/session_close.py; .agents/engineering/workflow/merge/scripts/cleanup_proof.py --delete-remote",
      "mapping": ".agents/plugins/sources.json packages shared helper in engineering and machine hooks; canonical skill entry points generate into skills",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Real manifest validation/inventory and all28 permission-sync cases passed. Offline remote action, foreign/multiple push destination, explicit origin despite forge environment overrides, skipped/mismatched completion and post-observation claimant arrival cases passed. ReceiptSafetyTests3 and both real process cleanup routes passed. Required final/integrated catalog, generated resources, harness/payload and packaging checks passed. Both platform interpreter forms are declared. Incoming-main host guidance remains context. Source/generated-resource evidence only; no installed runtime adoption claim; independent review and exact-head CI are pending."
      }
    },
    {
      "host": "codex",
      "behavior": "Preserve merged branches with open HEAD or BASE users before primary, linked and detached cleanup",
      "source": ".agents/engineering/workflow/merge/scripts/cleanup_proof.py; .agents/hooks/cleanup_dependency.py; .agents/machine/utility/peer-cli/scripts/session_close.py; .agents/engineering/workflow/merge/scripts/cleanup_proof.py --delete-remote",
      "mapping": ".agents/plugins/sources.json packages shared helper in engineering and machine hooks; canonical skill entry points generate into codex-skills",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Real manifest validation/inventory and all28 permission-sync cases passed. Offline remote action, foreign/multiple push destination, explicit origin despite forge environment overrides, skipped/mismatched completion and post-observation claimant arrival cases passed. ReceiptSafetyTests3 and both real process cleanup routes passed. Required final/integrated catalog, generated resources, harness/payload and packaging checks passed. Both platform interpreter forms are declared. Incoming-main host guidance remains context. Source/generated-resource evidence only; no installed runtime adoption claim; independent review and exact-head CI are pending."
      }
    }
  ]
}
```

## Review pass — 2026-10-11 — incremental

**Candidate base:** `6fd7c127919cf0055e9f9b67f41b0cb21aaf5591`
**Candidate head:** `da794afde95e02a10aa137f52786a7db7cd1941f`
**Candidate branch:** `Fix/DependentPrBranchCleanup`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:3ee98e9978ea88cd9300c11c2ebc93469596819be1baa3d87f78619d867f0c6d` `(51 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\ojuvuNxLNd9-TW3zgWmxVv\NyHU_Fvi0QZuym3hbgRvCw`
**Candidate bundle identity:** `sha256:a8d7576f86a786de3eb79a3f0b8d1bef000e2764ad075d84dab03a0e7885c26e`
**Work-order path:** `reviews/Fix-DependentPrBranchCleanup.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Descriptor: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-DependentPrBranchCleanup/../../.git/agent-workflow/runs/dependent-cleanup/review/3721d4fc5be2d1066eca6de16e046f0b0a2e4d4c4dad7ea678ba7ded18fac9b5/descriptor.json
Patch identity: sha256:4c377c8cf78bf56fa1191a76fb00f41c9cb86084e2dad2ef0fcf085f7dbad9e8. Lenses: native-general, workflow and conditional security, one isolated wave. Security scope is current synchronized main 1bb1c130b2d1762bce07b599bb0fbb7e311c6749..da794afde95e02a10aa137f52786a7db7cd1941f. The full incremental range includes incoming main context; the owned PR is 13 paths and 977 changed lines. Incoming main changes and generated distributions are context, not additional owned implementation. Relevant overlapping harness source was integrated cleanly; the complete harness inventory and generated checks passed. Native specialist capability remains unavailable as established in the prior pass; use fresh supported isolated evidence readers rather than accepting an unread candidate.

### Findings

- [x] R4 — HIGH — security: `cleanup_proof.py:682-687` deletes through origin without binding its effective push URL to the repository whose PR and dependency evidence was checked. Resolve every effective push URL, preserve on multiple or mismatched repository identities, and send the leased deletion only to the verified destination.
- [x] R5 — HIGH — security: `cleanup_dependency.py:39-41`, `harness_grant.py:146` and `session_close.py:421` let ambient GH_REPO redirect local cleanup dependency observation. Derive the checkout origin identity and explicitly bind HEAD/BASE and merged-PR queries to it, preserving on unknown or mismatched identities.
- [x] R6 — MEDIUM — security: `finish_reaper.py:108` adds a blocking observation after the final live-claimant check. Revalidate target identity and live claimants after the observation immediately before removal; add a claimant-arrival regression.

Parent independently confirmed these changed boundaries in the frozen source and the effective Git push-url semantics. No real deletion was used to establish a finding. Workflow permission-loader finding is under final isolated review before synthesis.

- [x] R3 — HIGH — workflow: `engineering.json:146-157` introduces action declarations rejected by the shipped permission loader, causing the entire manifest to be ignored. Use the validator-supported cleanup helper wildcard form and validate/load the actual shipped declaration in a regression. Both exact-head CI platforms and a focused local reproduction confirm this failure.
- [x] R7 — MEDIUM — workflow: `cleanup_proof.py:569-583,654-691` does not record remote-action completion, so local grant and finish routes can remove the helper and checkout before the mandatory action runs. Record verified remote deletion or absence in the bound receipt, require it before local cleanup, and test omission preserves the checkout.
- [x] R8 — MEDIUM — workflow: `engineering.json:146-157` omits python3 allowances for the required initial proof on Linux/macOS. Declare the supported proof invocations for both platforms and assert their host inventory.

Parent synthesis complete: all three fresh isolated v2 results match frozen identities; one focused schema correction was required for workflow/security coverage conditions, without altering claims or evidence. Six confirmed findings retained: three HIGH and three MEDIUM. No source-writing reviewer contributed. Parent inspected actual changed boundaries and independently reproduced the manifest loader failure. Host coverage validation passed at this exact head. Serial repair is now required; no merge gate is satisfied by this changes-requested pass.

R3-R8 remediation checkpoint: 490a81009aac5de055e641a625ba8c6386fef732, integrated with main a7d91c0e4b37c456b4119512ffae2b773ae148a1 in adc50e3d42a7723887107e9992612662148c006f. Actual manifest validation/inventory and all28 permission-sync cases passed. Focused foreign/multiple push destination, explicit origin despite GH_REPO/GH_HOST, post-observation claimant arrival, absent remote completion and mismatched marker repository cases passed. Genuine offline remote action records matching completion. ReceiptSafetyTests3 and both real process routes passed (16.000s/19.070s). Final generated/catalog/package checks, harness/payload checks, and integrated full manifest inventory passed. Original finding text, severity and completed pass judgments are preserved; the next immutable incremental review must approve the correcting head before merge.

## Review pass — 2026-10-11 — incremental

**Candidate base:** `da794afde95e02a10aa137f52786a7db7cd1941f`
**Candidate head:** `adc50e3d42a7723887107e9992612662148c006f`
**Candidate branch:** `Fix/DependentPrBranchCleanup`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:127d5e13309f0511d581bb5df1f03f71e6fc3504634d79cee2a4bc42c82b0488` `(80 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\ojuvuNxLNd9-TW3zgWmxVv\208WorrbihtpHN3UZ6Yndx`
**Candidate bundle identity:** `sha256:f496908d2ba5f4715b8c31af5af1e74c49cc7455af22b5443063cc2a38074d7a`
**Work-order path:** `reviews/Fix-DependentPrBranchCleanup.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Descriptor: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-DependentPrBranchCleanup/../../.git/agent-workflow/runs/dependent-cleanup/review/db4f16a2badb8a1b691cddd467a62777196971760d97d08919924a8eae948c14/descriptor.json
Patch identity: sha256:240e2dc41ce91f1919b756025e0333c8a7cb7ec6060020c028adb1e9617b5c58. One observed pre-review synchronization integrated main a7d91c0e4b37c456b4119512ffae2b773ae148a1 into adc50e3; no missing base commits. Native capability unavailability remains established; fresh supported isolated readers inspect native-general, workflow and the repaired security boundary. Tier gate reports no stack tier; no routed rules or deny violations. The incremental80-path range includes incoming-main guidance/generated context; actual owned PR scope is13 authored paths,1172 changed lines. Incoming changes are not additional source owned by this repair. Security inventory classifies neither range, but a fresh risk-specific security lens covers the origin/remote-action/local-removal authority cutover.

### Findings

Parent synthesis complete: all three fresh isolated results match the immutable identities and their v2 coverage conditions are complete. Native-general and workflow required one focused decision-boundary correction each, retaining their evidence; neither found actionable defects. Risk-specific security identified three concrete authority gaps plus the stale offline success fixture. Parent confirmed receipt/target control flow and independently reproduced command-local double Git URL rewriting (read-only output b1b013). Retain the existing R4 destination finding as incompletely repaired, and add R9-R11 below. Source/generator/host evidence is valid, but this pass requests changes. The generic security inventory has no qualifying path; the historical conditional security watermark remains unchanged.

R4 reopened at this pass: `cleanup_proof.py:494-496,666,709-714` feeds an already rewritten URL back into Git, where another rewrite can select a different repository. The read-only probe resolved tj-agents/core to review-stage-one/core, then that captured URL to review-stage-two/core. Require the captured destination to remain bound to the verified repository through both fetch and push transport resolution. Original R4 text/severity and earlier pass judgments remain unchanged.

- [x] R9 — HIGH — security: `harness_grant.py:140-146,179-180` accepts a matching receipt/remote marker from another repository when branch/head coincide. Bind the receipt repository and recorded primary to the checkout receiving the action; enforce current origin identity in grant and finish receipt consumption.
- [x] R10 — MEDIUM — security: `harness_grant.py:203-206,215` grants cleanup using branch/worktree identity observed before blocking forge calls. Revalidate the exact receipt, branch head and target registration after observation immediately before granting; add deterministic branch-advance/worktree-switch refusals.
- [x] R11 — MEDIUM — security/test impact: `test_merge_cleanup_proof.py:175` creates its removable action fixture with repo=None although strict completion annotation now requires github.com/tj-agents/offline. Correct the offline initial receipt identity and verify the complete affected remote action group against the final source. The earlier action-success log predates the stricter repository comparison and is not green evidence for this head.

Completed risk coverage also confirmed the detached reaper repeats target and claimant checks after observation, unknown evidence preserves, forge queries use host-qualified origin identities, unsafe/abbreviated arguments are rejected, and deletion carries the saved-head lease. Findings concern the remaining new consumers/transport expansion rather than these verified controls.

R11 CI confirmation: exactadc50 run38135803091 failed on both platforms in the genuine remote-action completion and wrong-supplied-repository cases; all source/package and generated gates passed. The latter action fixture mocks primary_github_repository itself and bypasses its new supplied-origin validation, allowing deletion of the temporary ref before strict completion refusal. Correct the fixture evidence layer so the real identity validator executes; no production weakening or bypass is authorized. Full affected action group must be rerun at the final source state.

R4/R9-R11 final corrective evidence: actual chained command-scoped Git resolution now refuses further URL expansion (1 test,1.453s); all8 remote action cases passed (293.865s), including real identity validation and completion; all13 receipt grant cases passed (84.112s), including foreign repository/primary and post-observation branch/worktree changes. ReceiptSafetyTests3 and direct real cleanup observer1 passed. Required final generated/catalog/harness/payload/packaging gates passed. A separate scheduled finish process fixture has an unresolved local Windows startup delay on unchanged process-enumeration/scheduler code; no passing result is claimed. Original findings and completed pass judgments remain unchanged. Fresh exact-head review and CI remain mandatory.
