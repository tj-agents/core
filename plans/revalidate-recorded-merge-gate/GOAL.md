# Goal — re-resolve recorded merge gates against current delivery authority

## Defect

On 2026-10-12 a Claude session resuming PR #161 asked Tommy twice for a merge decision. It also recorded "Blocked by: Tommy" in that goal and checkpointed its continuation owner `blocked`. The repository's standing authority already covered the merge. The gate came from a 2026-10-08 delivery binding (`authorization_resolution.standing: absent`, `stopped_by.class: auth`). On 2026-10-09 `.agents/delivery-authorization.json` became `standing_authorization: auto` with `authorized_stop_classes: ["auth"]`, and `.agents/settings.json` set `auto_merge: true`. Tommy called the question out as a mistake (recorded as M015 in `MISTAKES.md` on branch `Fix/ContinuationMonitorActivation`, PR #161).

The guidance already says to resolve authority from the standing table and re-run `delivery-bind` on every rebind (`engineering:persistent-delivery`). It also says to check whether existing authorization resolves a blocker before surfacing it (`base:goal-continuation`). Nothing enforces either for a gate that is recorded and then resumed. `continuation_stop.py`'s `documented_blocker()` accepts any `Blocked:`/`Blocked by:`/`Unblock action:`/`Resume when:` lines without checking whether the blocked action is a merge the current authority already permits.

## Authorization

Standing standards-defect authorization from `engineering:session-guidance` ("Maintain the right source owner"): diagnose, implement, test, open the PR and merge once this repository's gates pass. The repository's standing table (`standing_authorization: auto`, `auth` exempt) covers merge after green CI and independent review. Installing into other scopes and publishing outside this repository stay gated.

## Scope

- Guidance: in the owning skill(s), not new sections, require that a recorded merge-authorization blocker is re-resolved against the current delivery authorization (fresh `delivery-bind` or the same resolution logic) before it is surfaced to the user, recorded as a typed blocker, or carried across a resume/handoff. Fewest words; fix existing wording in place.
- Enforcement: make the continuation Stop hook (or the binder/runtime path it relies on) refuse to accept a merge-authorization typed blocker when the current table and settings authorize that merge for the bound PR's changed paths. Choose the smallest reliable mechanism. Fail closed on malformed settings, consistent with the existing settings contract.
- Regression tests for both Claude and Codex Stop payload paths, on Windows and Linux per `CODE_CONVENTIONS.md`.
- Out of scope: PR #161's files (`continuation_runtime.py`, `delivery_continuation.py`, persistent-workflow SKILL, harness manifests) and `MISTAKES.md` until PR #161 merges. Open PRs #209, #218, #226, #229 and #230 also edit `.agents/hooks/continuation_stop.py`; check their state first and rebase over whichever merge before you.

## Next Steps

1. Read `AGENTS.md`, `CODE_CONVENTIONS.md`, `.agents/hooks/continuation_stop.py`, `engineering:persistent-delivery`, `base:goal-continuation` and the delivery binder (`workflow_ops.py delivery-bind`, `delivery_policy.py`). Choose the enforcement point and record the decision and its rationale here.
2. Implement guidance and enforcement with focused tests; run the hook and binder suites.
3. Commit, push, open a PR with What/Why, obtain independent review, pass CI, and merge under the standing table. Confirm the causal post-merge regeneration succeeds.
4. After PR #161 merges, set M015's repair link in `MISTAKES.md` to this PR.

Lane: L3 — the enforcement point is a bounded design choice with real alternatives (hook-side check vs binder-side resolution).

## Progress

- 2026-10-12: Side workstream created by Claude session `3865e8e2` from PR #161's resume. Checkout `C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-RevalidateRecordedMergeGate`, branch `Fix/RevalidateRecordedMergeGate` from `origin/main` `1327120`. The originating session keeps PR #161 and its owner.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/hooks/continuation_stop.py and the persistent-delivery / goal-continuation guidance",
  "hosts": [
    {
      "host": "claude",
      "behavior": "A Claude session cannot end a turn on, or surface, a merge-authorization blocker that the current delivery table already authorizes.",
      "source": ".agents/hooks/continuation_stop.py",
      "mapping": "Claude Stop hook wiring in .agents/plugins/manifests/claude/engineering-hooks.json dispatches continuation_stop.py.",
      "verification": {"level": "planned", "result": "pending", "evidence": "Focused Stop-payload regression for a stale auth-class gate with an authorizing table."}
    },
    {
      "host": "codex",
      "behavior": "A Codex session cannot end a turn on, or surface, a merge-authorization blocker that the current delivery table already authorizes.",
      "source": ".agents/hooks/continuation_stop.py",
      "mapping": "Codex Stop hook wiring in .agents/plugins/manifests/codex/engineering-hooks.json dispatches continuation_stop.py.",
      "verification": {"level": "planned", "result": "pending", "evidence": "Focused Codex Stop-payload regression for the same case."}
    }
  ]
}
```
