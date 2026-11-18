# WorkItemSessions S2 migration handoff

Work in this exact checkout only:

`C:\\Users\\TommySeery\\source\\repos\\tj-agents\\core\\.worktrees\\Feature-WorkItemPlanMigration`

Read `plans/work-item-sessions/GOAL.md` completely and execute its `S2 handoff boundary — 2026-10-14`.

The uncommitted goal amendment currently contains duplicate copies of the 2026-10-14 decision and
boundary because its predecessor's patch matcher applied the insertion more than once. Before any
substantive implementation, retain one copy of each and remove only the duplicates.

Tommy has now made the missing product decision: work-item README is the single durable plan/current
execution document, including `## Next Steps` and compact material delivery state; the SQLite store owns
work-item status and session ownership. Stop adding append-only progress dumps or parallel progress
ledgers. Git, PRs, CI and review artifacts retain history.

This is a multi-slice plan. Own the whole goal, but implement and land S2 first: runtime dual-read for
the new work-item README while legacy plan/ledger inputs still work. Do not bulk-convert Core or consumer
plans until the S2 capability is reviewed and merged. Preserve the current branch's clean base, create no
duplicate writer, and do not touch the merged S1 checkout or the separate self-repair/session-registration
repairs.

Before substantive edits, reconcile the old goal's historical S1 narrative into a compact current-state
form in the material S2 commit; do not perform a documentation-only “progress dump” commit. Select and
record the lane for each phase. Complete focused tests, independent review, required CI, PR, merge and
causal publication under the recorded authority. Update the goal at material boundaries only.
