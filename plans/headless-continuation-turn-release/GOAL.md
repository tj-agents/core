# Release a foreground turn after verified durable headless continuation

Status: Claude picked up 2026-10-12 at c91b60c955ad4a3f0f7a9383fc20f1c4a6b58510 (branch Fix/HeadlessContinuationTurnRelease, this checkout). Diagnosis and source fix complete; focused tests green; review and delivery in progress.

Authorization: engineering:session-guidance standing standards-defect authority covers diagnosis, implementation, testing, opening a PR and normal merge when Core gates pass. Installation in other scopes, publication outside this repository and destructive actions remain gated. Original Kit goal is retained by its existing continuation; this side goal does not adopt or close it.

Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-HeadlessContinuationTurnRelease
Branch: Fix/HeadlessContinuationTurnRelease
Base: fetched origin/main c91b60c (verify full SHA on pickup).
PR: not opened.
Lane: L3 for bounded investigation of an uncertain Stop ownership/turn-release contract; reroute implementation and reviews per engineering:lanes.

## Observed defect

The Kit to Template rename was merged in tj-agents/kit PR9 on 2026-10-12 at 20:16:01 UTC and v1.4.0 released at 20:22:11 UTC. The foreground reported that completed milestone. Approved durable continuation then owned a separate follow-up PR10 in the same larger goal. Foreground had yielded its lease; the approved scheduler and a supported wake had been observed. One native headless writer was active. Stop still injected: "The canonical continuation has a headless writer; wait for its receipt before ending this turn." This kept the foreground turn open waiting for separately owned follow-up work and confused the user about an already merged release.

Source owner: .agents/hooks/continuation_stop.py plus existing continuation runtime and workflow contract as necessary. Source map .agents/plugins/sources.json ships that hook to both hosts. Inspect actual requirements before selecting a fix: persistent workflow permits supported continuation to outlive a foreground turn, whereas Stop currently blocks on a writing child. Treat this as a contract mismatch to diagnose, not permission to disable Stop.

Original evidence paths (READ ONLY; original live writer owns them): C:/Users/TommySeery/source/repos/tj-agents/kit/.worktrees/Refactor-TemplateStructureContract/.agents/continuation/owner.json, scheduler.json, launch-2e8b9c2d8fb24b1cb43467ff7eccaa17.log and result-2e8b9c2d8fb24b1cb43467ff7eccaa17.json. No result existed when the complaint was investigated. Do not read secrets or mutate those files, Kit source, Kit Goal, PR10 or installed caches.

## Boundary and existing owners

This is an independent side repair from current remote main. PR209/Fix-ControllerGoalAssociation concerns reciprocal native session association; PR218/Fix-ForeignForegroundStopOrder concerns foreign foreground identity checks. Neither goal owns the observed authenticated active-headless case; reconcile source overlap through normal Git/review without adopting those writers. Other Core writers are active. You are not alone: preserve their edits and ownership.

User explicitly said do not run Windows/Linux checks after every change and said that future policy is handled elsewhere. Do not create or expand that standards repair here. Use focused validation for actual changed behavior and required CI on stable delivery candidates; do not weaken required checks. Do not treat this side repair as a Kit merge gate.

## Outcome and acceptance

Diagnose whether a foreground turn with a proven released lease and verified supported durable continuation can finish a status/completed-milestone response while the genuine headless writer keeps ownership of the unfinished canonical goal. Implement the smallest warranted contract/runtime repair, preserving one active writer, exact process/session identity, nonce/receipt integrity, finite budgets, actual scheduler/wake proof and full-goal completion gates. No fake completion, forged receipts, owner edits by hand, hook disabling, blanket headless exemptions or new scheduler/backend/config scheme. Unproven, stale, foreign, conflicting or unsupported continuation still gates appropriately. Genuine current foreground execution and supervised-child completion keep their obligations.

Use meaningful disposable regression tests that expose the current obstruction, paired positive/negative ownership and durable-continuation cases, and equivalent Claude/Codex shipped payload coverage. Source tests do not establish installed host acceptance. Follow Core AGENTS.md, CODE_CONVENTIONS.md and generated-source discipline; update its existing harness manifest in the same change if required. Default zero code comments. Record limitations honestly.

## Diagnosis (confirmed by source inspection and a failing regression)

`continuation_runtime.launch` runs inside a scheduler `wake`: it sets `state=working`, `foreground=None`, records the supervisor as `child={pid, identity}`, and blocks up to `timeout_seconds` (900 s default) for the receipt. Persistent-workflow's contract is init, claim, register, observed wake, and then yield so the scheduled writer can take over. `continuation_stop.outcome` let a released-lease `waiting` owner stop once `scheduler_ready` and `observed_wake` held. But it blocked unconditionally on any `owner.child` (old line 239), so a foreground whose lease was released could not end a turn while the scheduler-launched writer ran. The supervised child itself was already exempt through `supervised()`.

Fix: a `child` record releases Stop only when the owner is `working`, the child's live process identity exactly matches the record (`unknown`, missing, reused or exited identities are rejected), and the same scheduler receipt and observed-wake proof required for `waiting` hold. A live writer without that durable proof still waits for its receipt. An unverified writer gets a reconcile block. Foreground-lease, stale-obligation, completion and blocker gates run before this branch and are unchanged.

Owner reconciliation: PR218 (foreign foreground order) and PR226 (binding head key) touch other lines of the hook and do not overlap. PR209 adds an association path that treats an associated `working` owner without a foreground lease as `association-foreground-lease-missing` before this branch. If PR209 lands, an associated session with a proven headless writer would still be blocked there. That is PR209's reconciliation to make; it is recorded under B011. Defect record: BUGS.md B011 (B008–B010 are taken by origin/Fix/HookDeliveryIdentity).

Known limitation: the runtime writes the `wake` event only after the wake operation returns. During the very first scheduler wake's launch there is therefore no observed wake yet, and Stop still waits for that first receipt. The contract names an observed wake as durable proof, so this was not widened.

## Progress

- Pickup acknowledged by Claude (see Status).
- `.agents/hooks/continuation_stop.py`: `headless_writer_live` plus the gated child branch.
- `.agents/hooks/tests/test_continuation_stop.py`: four tests. One covers the positive case across claude/codex harness, both Stop payload spellings, and with and without an obligation. One covers missing scheduler or wake proof. One covers reused, unknown, missing-pid, malformed, waiting-state and exited writers. One covers a foreground lease and a stale obligation with a live writer.
- Evidence: against the original hook, `-k headless` failed 14 subtests, including all 8 positive host and payload cases. With the fix, the full file passed 32 tests locally on Windows (`python -B -m unittest discover -s .agents/hooks/tests -p test_continuation_stop.py`).
- No harness manifest change: no new hook, file or permission. Catalog digests are left to the post-merge job (`check_generated_paths.py` passes); harness and tier checks pass locally.
- Independent read-only review of 1d0b42d (engineering:review-lens): no high or medium findings. Low 1: owner.json is per worktree, so another session in the same worktree shares the gate; this predates the change and the `waiting` gate behaves the same way. Low 2: a wake process that crashes mid-launch leaves a dead child, which gets a reconcile block until the next wake self-heals it, as acceptance intends. Neither needs a change.

## Next Steps

1. Open the owning PR, monitor its required CI to terminal, merge normally under standing authority; leave generated `plugins/*` uncommitted.
2. Record delivery evidence here and in B011, then finish only this side session.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/hooks/continuation_stop.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Stop releases a foreground turn whose lease is released while an identity-verified scheduled headless writer owns the goal",
      "source": ".agents/hooks/continuation_stop.py",
      "mapping": ".agents/plugins/manifests/claude/engineering-hooks.json Stop via .agents/plugins/sources.json",
      "verification": {"level": "source", "result": "pending", "evidence": "test_released_lease_with_live_scheduled_headless_writer_allows_stop_on_both_hosts claude subtests"}
    },
    {
      "host": "codex",
      "behavior": "Stop releases a foreground turn whose lease is released while an identity-verified scheduled headless writer owns the goal",
      "source": ".agents/hooks/continuation_stop.py",
      "mapping": ".agents/plugins/manifests/codex/engineering-hooks.json Stop via hook_dispatch.py and .agents/plugins/sources.json",
      "verification": {"level": "source", "result": "pending", "evidence": "test_released_lease_with_live_scheduled_headless_writer_allows_stop_on_both_hosts codex subtests"}
    }
  ]
}
```

Submission is not pickup. Original Kit continuation remains active and separate.

## Transfer checkpoint

Codex verified this checkout on branch Fix/HeadlessContinuationTurnRelease at full head c91b60c955ad4a3f0f7a9383fc20f1c4a6b58510. Working-tree status showed only this untracked goal directory. No runtime code was edited, no tests were run, and no diagnosis or delivery result has been established. Read README.md, CODE_CONVENTIONS.md, the lane contract, plan-execution, and handoff procedures before transfer; resume the pending source investigation.

The latest explicit user instruction is to perform a Claude handoff. This full transfer supersedes the preceding instruction to stay in Codex. Launch lane L3: the Stop ownership and durable continuation contract still requires bounded investigation with unresolved alternatives. Codex stops owned-path writes before invoking one Claude launcher. Successful submission proves launch only; Claude records its own pickup above before implementation.

Routine design delegation is false: .agents/settings.json has configuration.core.auto_merge=true and no configuration.core.auto_approve object or legacy auto_approve_design alias. Existing repair authority and acceptance remain those recorded above. This transfer adds no installation authority or change to the original Kit goal.
