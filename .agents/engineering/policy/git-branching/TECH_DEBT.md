# Branch and worktree naming debt

## D-ENGINEERING-WORKTREE-NAMES: Worktree and branch names must describe the active change

- **Kind:** debt.
- **Observed/reported:** 2026-10-11, the coordinator resumed
  `Fix/SessionGuidanceHandoffCompliance` in `.worktrees/Fix-SessionGuidanceHandoffCompliance` for
  handoff eligibility, priority and deferral. Tommy could not tell what the work was doing from that
  internal policy name. Cause confirmed for this incident: the coordinator changed the assignment but
  retained a name describing the older enforcement slice. The branching convention specifies prefix
  and casing, without requiring a clear action/outcome or handling a changed assignment's display name.
- **Impact and priority:** P2; stale or internal names obscure task ownership and progress, requiring
  manual explanation and increasing the chance of selecting the wrong context.
- **Source owner:** core engineering git-branching, open-worktree and handoff/continuation naming contracts.
- **State:** open.
- **Repair link:** this entry; no separate repair session assigned. Terminal naming is tracked in
  [D-MACHINE-TASK-TITLES](../../../machine/TECH_DEBT.md#d-machine-task-titles-terminal-names-must-explain-the-current-task).
- **Next action:** require branch/worktree names to state the concrete change, and define an owner-safe
  naming transition when a resumed assignment changes scope. For this task, an example is
  `Fix/LaunchReuseOrDeferHandoffs` with `.worktrees/Fix-LaunchReuseOrDeferHandoffs`.
- **Resolution condition:** new worktrees describe the task; scope changes receive a descriptive name at
  a verified safe lifecycle boundary. Preserve the native session, existing commits, PR identity,
  continuation/writer ownership and updated recovery references. Do not move or rename a live agent's
  checkout as a cosmetic operation, or create a duplicate context merely to obtain a better name.
  Validate representative new-work and resumed-work cases on supported hosts/platforms.
- **Verification evidence:** the exact existing branch/worktree, its updated priority/deferral goal,
  Tommy's report and the inspected prefix/casing convention. No active checkout has been renamed.

Recorded at Tommy's request. The current implementation remains with the existing PR #199 owner;
this debt records the naming correction without interrupting or taking over that work.
