# Prevent premature terminal responses

## Authorization

Standing standards-defect authorization from `engineering:session-guidance` after a Codex session ended twice while an owned PR CI repair loop was active.

## Outcome

Identify and repair the core/hook/listener path that allowed a final response to end active owned execution without a registered continuation wake. Test it, open and merge its source PR.

## Required investigation

Do not assume the base package alone is sufficient. Determine whether the unmerged work-plugin changes the per-repository injection/routing that should make persistent delivery mandatory and available in personal repositories. Trace actual Codex session injection, capability discovery, and terminal-response enforcement across both hosts. The failure evidence is: `engineering:session-guidance` was injected, but `persistent-workflow` was not invoked or registered while a personal-repo PR had pending CI; the session emitted a final response and stopped.

## Next Steps

R3–R6 repairs and focused acceptance passed. Commit the four authored hook/test files and this checkpoint, push once, refresh the exact delivery binding and owner identity, then run fresh incremental review and exact-head Windows/Linux CI. Merge only after current-head review and checks pass; verify the causal main regeneration before terminal completion and owned cleanup. Review phase lane L4: ordinary isolated native and workflow lenses over the exact frozen guard repair; parent owns final synthesis and delivery.

## Deferred tech debt

Codex sandbox setup failed before PowerShell launch (orchestrator_helper_exit_nonzero / helper_unknown_error: setup refresh had errors); the same skill files read successfully through unsandboxed execution. User explicitly deferred this host defect on 2026-10-10. Resolve separately when sandboxed file reads and repository commands start successfully without escalation. Do not investigate it in this repair.

## Investigation progress

2026-10-10: resumed the updated handoff. Investigation lane L3: shared cross-repository continuation failure has unresolved causes. Read the installed plan-execution, lanes, handoff and persistent-workflow contracts. Continue tracing core hooks/listeners, personal-repository capability discovery and the unmerged work-plugin routing.


## Source ownership and delivery slice

Source repository: tj-agents/core. Worktree: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-ContinuationEnforcement. Branch: Fix/ContinuationEnforcement. Base: origin/main at 33fb4155973b8ee1d26a8fd6f2a27d8428f6f166. PR: https://github.com/tj-agents/core/pull/184.

This slice adds shared continuation Stop enforcement, its execution-obligation receipt, both host hook declarations, shipping requirements and regression tests. Expected under 1,000 substantive lines. It has no dependency on the work-plugin communications changes or the existing monitor-activation PR #161; neither active checkout is an implementation target.

## Confirmed cause

Installed engineering instructions tell agents to invoke persistent-workflow, but neither routing nor arbitrary final prose creates a durable continuation owner. Codex's engineering manifest has no Stop hook. Claude's Stop chain checks red test runs, selected plan handoff formatting and cleanup, not general active-goal continuation. The source integration debt incorrectly says neither host exposes a terminal hook; current Codex documentation explicitly supports Stop decision=block (https://learn.chatgpt.com/docs/hooks#stop). The CLI shutdown listener saves transcripts/windows and never advances an execution goal. The unmerged work plugin declares no hooks and only communication skills, so it cannot provide the missing enforcement. This is shared core behavior across consuming repositories.

## Specified prevention

Retain a session/worktree-bound execution obligation when workflow routing selects plan-execution. A shared Stop gate must also recognize canonical continuation owners and delivery bindings even when the agent omitted workflow initialization. Quick questions and planning-only prompts must not establish execution authority. Explicit pause/cancellation must remain honored. Do not infer authorization merely from arbitrary plans elsewhere in the checkout.

A missing owner or an active foreground state must prevent abandonment and instruct the agent to continue the existing goal or enter persistent-workflow. Waiting may yield only with matching, enabled, actually registered scheduling evidence and released foreground ownership. Verified complete and genuine typed blocked outcomes may end; invalid, stale or foreign owner/goal/binding/scheduler evidence must not silently pass. Repeat Stop invocations cannot drop an unchanged execution obligation just because stop_hook_active is true. Headless supervisor receipt ownership must be preserved.

Wire the same gate into shipped Codex and Claude Stop events, ship its resource and update engineering's harness requirements. Validate standalone and packaged hooks, two independent personal repositories, missing initialization, pending delivery, missing/foreign/disabled scheduler, foreground lease, genuine completion/blocker, pause/cancellation, quick questions and repeated stopping. Existing completion and continuation contracts remain authoritative; do not create a parallel owner or launcher. Do not install changes into the normal machine profile without separate authority.

Implementation phase: L4, specified enforcement with local choices caught by regression tests. Use one bounded lane worker; parent owns investigation, acceptance, goal updates, review and delivery.

## Continuation ownership evidence

Initialized the existing goal in this worktree's .agents/continuation/owner.json, owner bcf74f6f159fa6cb95243ae2; foreground claim identifies long-lived Codex PID 34536. The installed Windows adapter registered task AgentStandards-Continuation-91e79af042a475b6acc77f6c057978d70e425be080a7b4a0647e73d9da12e580 every five minutes. An explicit wake returned working/foreground-owned without launching a competing writer. Keep the lease renewed during foreground work; checkpoint and yield before any deferred wait. Remove the task only at a terminal owner result. This runtime registration changes no normal-profile plugin installation.

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
  ]
}
```

## Verification progress

2026-10-10: regeneration and sync-generated -Check passed (502 package files); tier payload and harness declaration checks passed; PowerShell skill-packaging tests passed. Broad local suites were stopped without a reported failure; remote-validation assigns the complete matrices to draft-PR Windows/Linux CI. Final focused verification: Stop suite 18/18, route suite 14/14, source and freshly generated package JSON Stop callback passed, typed blocked terminal delivery compatibility passed. Compact logs are in C:/Users/TommySeery/source/repos/tj-agents/core/.git/agent-workflow/runs/continuation-enforcement-checkpoint/artifacts/. The worker verified the real registered scheduler against this goal owner.

A disposable native Codex 0.162.0 profile proved terminal interception: the first Stop callback returned decision=block with stop_hook_active=false and final text FIRST; the same session continued to CONTINUED, then Stop called again with stop_hook_active=true. Normal user configuration and plugin installation were unchanged. Artifacts: C:/Users/TommySeery/source/repos/tj-agents/rust/.worktrees/Fix-ContinuationEnforcement/_stop_host_probe/received.jsonl, native_exec.jsonl and last_message.txt. This proves native Stop continuation, not installed acceptance of the new gate. Claude live acceptance remains unobserved.

Scope boundary: a fresh session without a routed execution obligation does not adopt another session's active foreground owner. The same owning CLI remains subject to the gate when process ancestry and recorded creation identity establish foreground ownership; routed obligations remain enforced independently of ancestry. The gate cannot recover authorization from arbitrary assistant prose or an absent/untrusted routing hook. Linux can enforce missing/active owners and verified terminals; current scheduler registration remains a Windows runtime capability, so Linux waiting cannot claim an enabled wake without a supported scheduler.

2026-10-10 delivery checkpoint: opened draft core PR #184 at d108247. Frozen native CLI review could not read source because of the deferred sandbox defect; supported fresh L4 native-general and workflow lenses inspected the exact immutable bundle. Parent finalized changes-requested at that head and validated both host coverage declarations. Review findings are in reviews/Fix-ContinuationEnforcement.md; normal-profile gate activation remains unobserved. Source CI run 38065040829 Linux source-layout suite ran 897 tests and found only nine launch-budget subcase failures: the new dedicated Claude Stop command doubled the existing interpreter launch. Do not weaken that check. Shared pause suspension and direct referents are being repaired before a stable follow-up push.

2026-10-10 repair acceptance: Stop integration 21/21 (actual prompt hook and registered packaged Claude dispatcher included), routing 14/14, dispatcher 20/20, launch budget 4/4, generated Check passed. Restored Claude deadline25/timeout30; no test or timeout weakened. Source integrates origin/main at 9f3d4dd. Review findings R1/R2 are resolved with a fresh incremental watermark still required.

2026-10-10 additional review acceptance: native GitHub source access confirmed malformed owner and delivery-binding artifacts fail open. Actual isolated routing of "How does plan-execution work?" creates an unauthorized execution receipt. Simulated nested CLI ancestry over-associates a separate read-only CLI with its parent owner; no live nested host event is claimed. These are guard defects in this delivery slice. The deferred skill-read/sandbox issue remains out of scope.

2026-10-10 guard repair acceptance: strict owner/binding loading, authorization directives and nearest CLI association implemented. Final 26 Stop, 30 routing/recovery, 20 dispatcher, 13 callout and 4 launch-budget tests passed. Eighty in-process cases additionally proved preserved planning choices and actual question-to-receipt-to-Stop behavior. Generation and Check passed. An initial Stop run exposed a short-path mock mismatch and repeated Windows ancestry lookups; both were corrected without weakening timeouts or assertions, and the complete final Stop suite passed. No normal-profile installation or live nested/Claude host acceptance is claimed.
