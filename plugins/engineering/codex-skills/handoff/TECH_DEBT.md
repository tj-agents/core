# Handoff debt

## D001 - Transfer separate follow-up work before closing the finished origin

- **Kind:** debt. **Observed/reported:** 2026-10-15; Tommy challenged why the completed work-item migration session retained its CLI and worktree instead of handing separate terminal-cleanup repair to its owner and closing the finished origin.
- **Cause:** confirmed reasoning error: this session carried the cleanup goal's earlier no-additional-CLIs restriction into the new task without reconciling its scope, and rejected the handoff route too broadly. This does not establish that the handoff runtime itself is broken.
- **Impact and priority:** P2; completed sessions and checkouts retain disk space and create cognitive load, and separate work becomes attached to the wrong task.
- **Source owner:** Core engineering handoff and session completion. **State:** deferred.
- **Repair link:** `.agents/engineering/workflow/handoff/TECH_DEBT.md#D001`; related terminal-closeout prevention remains M020 and `plans/verified-terminal-cleanup/GOAL.md` in `Fix/VerifiedTerminalCleanup` (PR252). This entry does not duplicate that runtime repair.
- **Deferral:** Tommy explicitly requested recording this for future tech debt and said the handoff correction does not matter for this round. **blocked_by:** dependency. **Resolver:** Core handoff workflow owner. **Resume when:** Tommy or an authorized owner takes up this deferred handoff assessment.
- **Next action:** assess how task-local launch limits are reconciled when independent follow-up work already has an owner; transfer that work through verified handoff where authorized, then close the finished originating session and preserve/remove its completed checkout.
- **Resolution condition:** a separate-follow-up scenario reconciles the applicable launch limit, verifies successor pickup and predecessor release, closes the finished origin and removes its preserved finished worktree without stopping the follow-up or closing an active dialogue. Delete this entry after that condition is observed.
- **Verification evidence:** direct user correction and the originating session's acknowledged scope error; no new handoff runtime correction or acceptance is claimed.
