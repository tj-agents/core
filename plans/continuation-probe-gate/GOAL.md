# Repair continuation probe failures without false gates
Status: prepared for Claude successor pickup on 2026-10-12 at Tommy's explicit request.
## Outcome
Diagnose and repair the core runtime/Stop path that produced a blocked continuation owner without its required genuine typed gate after Git returned128.
## Authorization
Tommy explicitly asks to record failing hooks and fix them; engineering:session-guidance provides standing standards-defect repair/delivery authority. Implement, focused tests, review, one final full CI and merge under core policy. No installed-profile changes, cache edits, hook disabling or global configuration changes.
## Ownership
Worktree: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-ContinuationProbeGate
Branch: Fix/ContinuationProbeGate
Base: c91b60c955ad4a3f0f7a9383fc20f1c4a6b58510
This independent successor owns only this hook/probe workstream. Parent's dotnet scaffold is complete/mergedPR47; do not reopen or change it. Other core writers are active; do not revert their work. Inert closeout cadence repair has its own successor and owns shared committing/problem-record/merge guidance.
## Evidence
In the parent sandbox a supported continuation_runtime.py heartbeat returned {"state":"blocked","reason":"git exited 128"}. Native Stop prompt said "The blocked continuation owner lacks a genuine typed gate; reconcile it before ending this turn." Supported yield/claim in authorized normal execution restored the same owner060208e34169e293041bf3de, PID16108, authority and goal to working. A later complete checkpoint passed; no external user gate was pending. Exact denied Git operation/root cause is not yet established. Existing core PR226 repairs a DIFFERENT proven normalization issue (binding head becomes remote_head_sha); PR209/218 also touch continuation ownership. Inspect their exact ownership and avoid overlapping writes; use a dependent or disjoint correction when needed. Do not call ordinary sandbox Git-access errors an auto-review rejection.
Separate auto-review later rejected a composite dotnet cleanup because it perceived possible note overwrite. That is a distinct approval decision, not evidence that the Stop hook failed. Parent preserved notes.
## User testing decision
Run interim checks targeted to what changed. Batch local commits. One full CI run on the finished implementation, not after every small commit or record update. No unrelated full suites or metadata-only pushes.
## Lane
L3 for bounded uncertain diagnosis; specified repair routes to L4. Delivery does not raise lane. Claude handoff selects L3 because the actual Git failure and classification cause remain unresolved. Tommy explicitly selected Claude for this work; retain that host choice for non-frontier work.
## Pickup checkpoint
The Codex predecessor read the goal, repository conventions, continuation Stop source and lifecycle guidance. No runtime source edits, tests, commits or delivery occurred. A bounded read-only evidence worker was interrupted before transfer; it has no write authority. Related PR queries failed because the sandbox could not read GitHub CLI configuration; their current state remains unverified. An escalated read batch was interrupted, so do not assume it produced results. The checkout remains on Fix/ContinuationProbeGate with only this goal directory untracked. No canonical continuation owner or delivery binding exists in this checkout.
Effective routine design approval is false, from the absent design setting in this checkout's .agents/settings.json (configuration.core.auto_approve default). Preserve the existing repair and delivery authorization and the user's focused-test/one-final-CI decision.
The predecessor stops owned-path writes before launching one Claude successor. Successful launcher submission proves launch only; the successor must acknowledge pickup here before deliverable writes.
## Pickup acknowledgement
2026-10-12: Claude successor (Opus 5.5) acknowledged pickup in this worktree at base c91b60c with only this goal directory untracked. Lane L3 retained for diagnosis. Diagnosis complete; see below.
## Diagnosis (2026-10-12, from dotnet owner events.jsonl)
Confirmed chain: after the 19:12:21 heartbeat, sandbox heartbeats failed at `main()`'s `git rev-parse --show-toplevel` (exit 128), so the lease was not renewed; the 19:19:29 scheduled wake found a live foreground older than `lease_seconds` (300) and raised `stale-live-foreground-reconciliation`, persisting a `blocked` owner with no typed gate; Stop then demanded reconciliation. Separately, the CLI failure output `{"state":"blocked",...}` impersonated owner state: at 21:29 the session "recovered" a blocked state the owner file never held. Exact sandbox Git stderr was never captured. Recorded as BUGS.md B008; the recurring receipt-recovery test timing flake is B009.
Related PRs: PR226 and PR218 change only continuation_stop.py binding/foreign-foreground paths; PR209 adds runtime operations (association, reconcile, renew) but does not touch the wake stale-lease branch, heartbeat Git probe or failure output. This repair is disjoint; PR209's B004/B005 numbers already collide with main and are its own rebase concern.
## Repair
- `heartbeat`/`yield` validate the owner's recorded worktree instead of running Git; they are token-authenticated.
- `wake` with a live stale foreground keeps `working`, records `foreground-lease-stale`, and never launches or blocks.
- CLI failures print `{"outcome":"failed","reason":...}`; Git failures carry their last stderr line.
## Host coverage
```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/workflows/continuation_runtime.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "A Git failure or stale live foreground lease never produces an ungated blocked continuation owner, and failed runtime commands are not reported as owner state.",
      "source": ".agents/workflows/continuation_runtime.py",
      "mapping": "Shared continuation runtime and Stop hook shipped through engineering harness sources for both hosts.",
      "verification": {"level": "planned", "result": "pending", "evidence": "test_fresh_and_stale_foreground, test_git_failure_keeps_foreground_owner_and_reports_command_failure and test_stale_live_foreground_wake_leaves_a_continuable_owner exercise the shared runtime and Stop hook."}
    },
    {
      "host": "codex",
      "behavior": "A Git failure or stale live foreground lease never produces an ungated blocked continuation owner, and failed runtime commands are not reported as owner state.",
      "source": ".agents/workflows/continuation_runtime.py",
      "mapping": "Shared continuation runtime and Stop hook shipped through engineering harness sources for both hosts.",
      "verification": {"level": "planned", "result": "pending", "evidence": "The same shared-source regressions run against a Codex-harness owner fixture; the GIT_DIR exit-128 case reproduces the observed sandbox heartbeat failure."}
    }
  ]
}
```
## Progress
- Focused runtime and Stop suites: 65 of 66 passed with the new regressions; the failure was B009 (`test_recover_final_launch_receipt_before_budget_gate`), which passed 3 isolated reruns. Catalog digest refreshed.
- Next: commit candidate, independent review, push, open PR, one final required CI, merge, observe causal generated output.
## Acceptance
Reproduce actual Git128/runtime classification through focused tests. Recoverable internal failures preserve the owner and independent authorized progress; genuinely blocked actions carry correct resolver/unblock/resume evidence. Real runtime/Stop regression proves no malformed blocked owner; both-host source coverage as applicable. Source fix reviewed, final required CI green, merged and causal generated output observed. Do not install it into the parent's profile.
## Next Steps
Acknowledge pickup here. Read core guidance and owning bugfix/lanes workflow. Diagnose the observed path and existing repair ownership before editing; record in core BUGS under deduplication rules. Reconcile related PRs and repair only the remaining defect. Use focused tests during implementation and final required CI once. Keep this goal actionable and report the result.

