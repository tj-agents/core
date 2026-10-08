# Goal — activate durable delivery continuation on both hosts

## Defect

After PR #156 merged, its post-merge CI/regeneration run remained active but no durable continuation was registered. The foreground session stopped, leaving the CLI open until a user intervened. The continuation design requires a scheduler-backed owner to monitor that transition and run the closing path only after downstream delivery work completes.

## Authorization

User authorization on 2026-10-08: fix this for both Claude and Codex, with a Codex handoff.

## Scope

Repair the shared continuation activation path and each host adapter as needed so both Claude and Codex can establish and yield a durable owner for post-merge monitoring. Preserve the single-writer lease and host-specific safeguards. Add focused regression coverage and deliver the repair through its own PR.

## Evidence

- PR #156 merged at `d3bf264f0271236f0275b659e4b99a9607e6033e` while its post-merge CI run `37828691013` was still active.
- The prior session did not initialize, claim, yield, and register a continuation owner because it treated the absence of a trustworthy foreground process ID as a capability gate. The actual ancestry exposed a long-lived `codex.exe` parent; the shared runtime instead defaults `claim` to the transient tool-shell parent when no PID is supplied.
- `persistent-workflow` requires initialization, a foreground claim, scheduler registration, and an observed wake before unattended continuation can be claimed.

## Next Steps

Scope: whole goal through repair, review, dedicated PR and terminal delivery.
Current slice: host process claim, native launch path and required public-operation permissions for both hosts.
Remaining scope: incremental review, exact-head CI and downstream delivery monitoring.
Done when: the repair is merged and its post-merge regeneration has finished successfully.

1. Require an explicit host PID in the shared runtime claim interface so it cannot silently lease a transient tool shell.
2. Add a Windows adapter claim operation that walks process ancestry to the nearest exact `codex.exe` or `claude.exe`, passes that PID to the shared runtime, and rejects missing, cyclic, or wrong-host ancestry.
   Record that ancestor's native executable path for later headless launches, preserving an explicitly initialized host pin. The live PATH resolves both names to `.cmd` wrappers, which the runtime correctly rejects; PID discovery must also make the native launch path recoverable.
3. Document and test the init → adapter claim → register → yield → wake sequence for both hosts, including mocked ancestry cases.
4. Run focused continuation and host-adapter checks, review, commit, push, and open a dedicated PR. Monitor it through its own terminal delivery path.

Lane: L4 implementation complete; independent review and delivery next.

## Progress

- 2026-10-08: isolated worktree created from `origin/main`; the failure reduces to transient tool-shell leasing rather than missing host identity. Codex handoff prepared.
- 2026-10-08: Codex picked up this checkout at base `27596c9a260b0991cd90392bbeee5961a58b9142`; remote base is current. L3 investigation confirmed the fallback and missing adapter claim; L4 owns specified implementation. One atomic slice covers runtime, adapter, workflow usage, permissions and focused tests (expected below 1,000 substantive changed lines).
- Durable runtime owner initialized at `.agents/continuation/owner.json`, explicitly claimed with the observed long-lived Codex PID, registered with Windows Task Scheduler, and an adapter wake observed `foreground-owned`. Runtime receipts stay untracked. Keep heartbeating while foreground work continues and yield before unattended monitoring.
- Sandbox process setup currently fails before command launch; escalation succeeds. A separate investigator owns that infrastructure issue. Workflow lifecycle-name resolution also assumes the old source layout; the existing `docs/workflows/TECH_DEBT.md` entry owns that defect. Use the explicit canonical lifecycle path for this task.
- Live executable resolution exposed a second activation dependency: `shutil.which('codex')` and `shutil.which('claude')` both select `.CMD` wrappers. Extend this same atomic slice to pin the discovered native ancestor executable during claim; a foreground-owned wake alone is not proof that a headless launch will succeed.

- Focused Python runtime tests (38), PowerShell 7 and Windows PowerShell 5.1 adapter suites, harness manifest tests, and generated-source/catalog checks passed. The implementation is ready for a committed, frozen independent review.

- Independent native review found that operation permission prefixes failed the shipped consumer validator. R1 adds exact public `operation:*` prefixes and a narrow validator correction, with direct consumer coverage. Focused harness and bootstrap checks validate this remediation; incremental review follows.

## Delivery identity

Worktree: `C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-ContinuationMonitorActivation`
Branch: `Fix/ContinuationMonitorActivation`
PR: not opened
Review: `reviews/Fix-ContinuationMonitorActivation.md`

## Completion evidence

```completion
{
  "outcome": "Both hosts establish a durable foreground owner through explicit host ancestry and deliver the repair through terminal post-merge regeneration.",
  "acceptance": [
    {
      "id": "host-claim",
      "criterion": "Explicit PID validation and both-host ancestry, lease, scheduler and wake regressions pass.",
      "evidence": [
        {"source": "workflow_ops run continuation-runtime", "result": "38 focused Python tests passed."},
        {"source": "workflow_ops run delivery-continuation", "result": "PowerShell 7 adapter regressions passed."},
        {"source": "workflow_ops run delivery-continuation-inbox", "result": "Windows PowerShell 5.1 adapter regressions passed."}
      ],
      "owner": "current Codex execution",
      "next_action": "Preserve this validated implementation through review and delivery."
    },
    {
      "id": "review",
      "criterion": "The committed repair receives independent current-head review with no open findings.",
      "evidence": [],
      "owner": "current Codex execution",
      "next_action": "Freeze the green candidate and run isolated review."
    },
    {
      "id": "delivery",
      "criterion": "Dedicated PR CI passes, the repair merges, and its causally linked post-merge regeneration succeeds.",
      "evidence": [],
      "owner": "current Codex execution",
      "next_action": "Open and monitor the dedicated PR through downstream completion."
    }
  ],
  "deliveries": [],
  "open_tasks": []
}
```
