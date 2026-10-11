# Enforce callout-repair handoff completion in Codex

## Defect and authority

`engineering:session-guidance` currently owns the callout-repair body inline, while a separate `callout_repair_gate.py` detects that state. The current Codex UserPromptSubmit and PreToolUse wiring detects a pending repair, but its Stop hook does not run the gate. A Codex agent can therefore receive the instruction and answer without a tool invocation, then terminate the turn without a verified native handoff.

This is a standing `engineering:session-guidance` standards-defect repair. It is authorized through diagnosis, implementation, tests, review, pull request, merge, and generated publication once repository gates pass. The repair remains limited to the runtime enforcement seam; it does not alter the cancelled receipt/wording work, Core delivery policy, or unrelated handoff semantics.

## Ownership and slice

Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-SessionGuidanceHandoffCompliance
Branch: Fix/SessionGuidanceHandoffCompliance
Base: 0411b56134367ccfd42d9765e11ece5ea9f5aedf

Own the new canonical `engineering:self-repair` workflow and its plain host adapters, `session-guidance` routing, `.agents/plugins/manifests/codex/engineering-hooks.json`, the directly focused callout-gate tests, required generated catalog metadata, and this goal. Preserve all other live worktrees and do not modify the cancelled native-handoff receipt repair.

## Next Steps

Scope: deliver the narrow shared enforcement repair to merged default-branch state.
Lane: L7 for the local checkpoint; return to L4 for review and any repair.

1. Commit the validated authored source, adapters, manifest, tests, catalog metadata, and this goal; exclude generated `plugins/` output.
2. Review the frozen candidate at L4 and resolve any finding.
3. Preserve existing delivery ownership: a wait/monitor request stays observational and cannot silently take over, rebase, push, arm/cancel auto-merge, or merge a pending delivery. Require explicit authority and the existing ownership transfer procedure before those delivery-state changes.
4. Open and monitor the source PR under standing authority once review is green.
5. Merge once review and required CI are green.
6. After merge, observe the causal generated publication and run the normal terminal worktree cleanup. Record either that terminal evidence or a typed external gate here.

## Completion

Done when: `engineering:self-repair` is the direct, shippable lifecycle route for Core-caused user callouts; both host manifests invoke the same callout repair enforcement at their available terminal boundary; a pending Codex callout blocks termination without a verified native source-owner handoff; focused tests, review, required CI, merged source PR, and causal generated publication pass.

## Host coverage

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/hooks/callout_repair_gate.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "A pending Core-callout repair remains blocked at Stop until a verified standards-defect handoff launch exists.",
      "source": ".agents/plugins/manifests/claude/engineering-hooks.json",
      "mapping": "Claude already dispatches the shared callout gate at Stop.",
      "verification": {"level": "source", "result": "passed", "evidence": "CalloutRepairGateTests.test_callout_blocks_automatic_feedback_and_terminal_stop exercises the shared Stop gate; test_manifests_ship_only_supported_callout_events verifies the existing Claude Stop dispatch."}
    },
    {
      "host": "codex",
      "behavior": "A pending Core-callout repair cannot end the Codex turn until a verified standards-defect handoff launch exists.",
      "source": ".agents/plugins/manifests/codex/engineering-hooks.json",
      "mapping": "Codex Stop dispatch will invoke the shared callout gate alongside its existing terminal gates.",
      "verification": {"level": "source", "result": "passed", "evidence": "CalloutRepairGateTests.test_callout_blocks_automatic_feedback_and_terminal_stop exercises the shared Stop gate; test_manifests_ship_only_supported_callout_events requires the Codex Stop dispatch to ship it."}
    }
  ]
}
```

## Verification

- `test_process_standards.py` passed all 23 tests, including the routed self-repair callout contract.
- Focused terminal-gate and host-adapter tests passed: `CalloutRepairGateTests.test_callout_blocks_automatic_feedback_and_terminal_stop`, `CalloutRepairGateTests.test_manifests_ship_only_supported_callout_events`, and `TaskWorkflowAcceptanceTests.test_task_skills_keep_one_canonical_body_and_thin_host_entries`.
- Host coverage validation passed. Package synchronization reported 512 files from 76 shared definitions with no remaining changes.
- The candidate was rebased onto `origin/main` at `0411b56134367ccfd42d9765e11ece5ea9f5aedf`; the focused validation set and generation checks passed again on the rebased head.
- The stale source-layout skill count and session-context mutation expectation reported by the draft PR's CI were repaired; `tests.test_source_layout` and `tests.test_engineering_hooks` passed.
