# Keep the originating goal active across a side handoff

## Authority

Standing `engineering:session-guidance` standards-defect authority. This independent core repair
may change the shared routing and Stop enforcement, its focused tests, and this goal; it may be
reviewed, published and merged once normal gates pass. It does not alter the separate heartbeat,
close-cleanup, or handoff-contract repairs.

Checkout: `C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-ContinueAuthorizedGoal`

## Defect

A prompt that requests a bounded side-workstream handoff selects `engineering:handoff`, but the
route receipt only records an execution obligation for `plan-execution`. The Stop hook therefore
permits the originating session to finish after a successful side-handoff launch, even though the
handoff contract requires it to retain and continue the original goal. This lets one merged side
fix be treated as the end of the broader authorized work.

## Completion

The route records a retained-parent execution obligation for an explicitly bounded side handoff;
the existing Stop hook then requires a current continuation owner until that parent reaches a
verified terminal state. Full-goal transfers and ordinary handoff requests retain their existing
behavior. Source and generated host coverage prove the distinction.

## Next Steps

1. Add a narrow route classification for handoffs that explicitly retain the current goal.
2. Persist that classification as an execution obligation in direct and recovered prompt routes.
3. Add source and generated Stop regressions proving a retained parent cannot end without an owner,
   while a full transfer remains ungated.
4. Run focused route/Stop tests, generated consistency checks and review; commit, publish, monitor
   exact-head CI, merge, then verify generated publication.

## Progress

- 2026-10-11: diagnosed the missing parent obligation: side-handoff routing did not set the receipt
  flag consumed by the existing Stop gate. Added direct and recovered route coverage, source and
  generated route coverage, and a Stop regression. Targeted tests passed; package synchronization and
  its check passed. Full shared suites are still being observed separately because they include
  long-running continuation fixtures.

```completion
{
  "outcome": "A bounded side handoff cannot let its originating authorized goal end after a merged sub-fix while that goal still has work.",
  "acceptance": [
    {
      "id": "enforcement",
      "criterion": "Direct and recovered routing preserve the originating execution obligation only for explicit bounded side handoffs.",
      "evidence": [],
      "owner": "current execution owner",
      "next_action": "Implement and run focused route and Stop regressions."
    },
    {
      "id": "delivery",
      "criterion": "The reviewed candidate passes exact-head CI, merges, and its generated package publication is observed.",
      "evidence": [],
      "owner": "current execution owner",
      "next_action": "Review, publish, merge, and verify post-merge generation."
    }
  ],
  "deliveries": [],
  "open_tasks": []
}
```
