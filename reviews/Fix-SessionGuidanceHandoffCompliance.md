# Code review — Fix/SessionGuidanceHandoffCompliance

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `259e02268c9e9c94ccf65e29b3a3f6faf525e9c3`  `(2026-10-11)`
**Judgment:** `changes-requested`

## Review pass — 2026-10-11 — full

**Candidate base:** `8a860ce6ae1cbef41ef576b3e632c177c6bda518`
**Candidate head:** `cb6825236d97784f28e8286f56e99981911e4f89`
**Candidate branch:** `Fix/SessionGuidanceHandoffCompliance`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:c219f3d82df80c88bdbe51940b6ca19feb750758524cca49fde8b3d7df2a7e19` `(11 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\3J5-crc9TLXYviIo6wXozs\9TSnGi0N7rR7LqUDIdzE_G`
**Candidate bundle identity:** `sha256:fc07fa9a50607af86fa1e54bd79b41f503ce47bcc91bc24e3c8946a779455dec`
**Work-order path:** `reviews/Fix-SessionGuidanceHandoffCompliance.md`
**Work-order mode:** `new`
**Pass judgment:** `approved`

The native Codex reviewer could not initialize its tool environment because setup refresh failed. The parent reviewed the frozen bundle and exact diff as the required fallback. No findings were retained.

### Findings

No findings.

```agent-host-coverage
{
  "schema_version": 1,
  "candidate_head": "cb6825236d97784f28e8286f56e99981911e4f89",
  "shared_source": ".agents/hooks/callout_repair_gate.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "A pending Core-callout repair remains blocked at Stop until a verified standards-defect handoff launch exists.",
      "source": ".agents/plugins/manifests/claude/engineering-hooks.json",
      "mapping": "Claude dispatches the shared callout gate at Stop.",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "CalloutRepairGateTests.test_callout_blocks_automatic_feedback_and_terminal_stop and test_manifests_ship_only_supported_callout_events passed."
      }
    },
    {
      "host": "codex",
      "behavior": "A pending Core-callout repair cannot end the Codex turn until a verified standards-defect handoff launch exists.",
      "source": ".agents/plugins/manifests/codex/engineering-hooks.json",
      "mapping": "Codex Stop dispatch invokes the shared callout gate with its existing terminal gates.",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "CalloutRepairGateTests.test_callout_blocks_automatic_feedback_and_terminal_stop and test_manifests_ship_only_supported_callout_events passed."
      }
    }
  ]
}
```

## Review pass — 2026-10-11 — full

**Candidate base:** `73f1fbcc24efdda8ed1c0b0ccf07dc4064e7782c`
**Candidate head:** `259e02268c9e9c94ccf65e29b3a3f6faf525e9c3`
**Candidate branch:** `Fix/SessionGuidanceHandoffCompliance`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:869a217eee94f2bc5ddb11aa0a664fb8c577874a4138ec57dda3e9a701647f02` `(18 paths)`
**Candidate bundle:** `C:/Users/TommySeery/AppData/Local/Temp/review/mS7RZPUPbus2bffhy8mjBa/iL3fcjd4RWW9fJeF6mfwFz/aXEQA2r1WL8BH4YBecO2NQ`
**Candidate bundle identity:** `sha256:3d7e7384b8e7c92ac4e19181e0ae990d23ad627e527d7c0a5582fd2c2438959f`
**Work-order path:** `reviews/Fix-SessionGuidanceHandoffCompliance.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Patch SHA-256: `714a83bded18400d8480645d713179ea803b96c08bdac2f489e5c86c6bf7f702`.
One synchronization: origin/main at the frozen base, zero commits behind; head unchanged.
Lenses: native-general and workflow, one wave. No security-classified paths or routed rules.
Tier conventions: none apply. The existing flat-layout rule-loader defect remains out of scope.

### Findings

Native reviewer invoked on the frozen base; no result within 15 minutes. The read-only L4 fallback was
interrupted before full coverage and returned failed. The parent then completed the native-general fallback
against the same frozen descriptor and bundle, retaining no additional findings. The workflow lens completed
and the parent validated these two new-evaluator defects:

- [x] **PRIORITY-1 — HIGH — workflow** — `.agents/engineering/workflow/handoff/scripts/admission.py:303`
  Capacity can count unrelated live registry owners against a local goal budget, and the evidenced primary
  owner need not occur in the occupied list. Require each counted owner to have exact goal/problem-record
  linkage and native acknowledgement, and require the primary owner in the list. Add a regression where
  an unrelated live registry owner cannot satisfy budget one.
  Disposition: fixed by requiring every counted owner to carry the record backlink and exact native acknowledgement, and by requiring the primary owner among the counted identities. Verified by `test_registered_existing_owner_and_capacity_use_current_process_identity`.

- [x] **PRIORITY-2 — HIGH — workflow** — `.agents/engineering/workflow/handoff/scripts/admission.py:197`
  Any unreadable target can justify a capability deferral even when it is not a declared repair prerequisite.
  Source-owner and authority validation also accept free-form or anywhere-text matches. Bind read,
  executable and dependency evidence to explicit requirements in the linked goal, match its source owner,
  and require repair authority within the Authorization section. Reject unrelated targets and historical
  authority text; preserve positive declared-prerequisite cases.
  Disposition: fixed by binding source owner, repair authority, and read, executable, and dependency evidence to declared goal entries. Verified by `test_evidence_requires_declared_prerequisite_source_owner_and_authorization`, `test_declared_executable_and_dependency_prerequisites_admit_current_evidence`, and the callout-gate disposition tests.
