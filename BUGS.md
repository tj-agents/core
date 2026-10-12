# Recorded bugs

## B001 — Task recovery omits concrete authority evidence

**Kind:** bug. **Observed:** 2026-10-12. **State:** in-progress.

**Observation:** Exact-owner recovery was rejected before launch for insufficient task-specific authority. The original call named a goal and asserted authorization but omitted the authority wording/provenance and an execution justification. The existing machine recovery template asks only for the blocker and ownership reconciliation. These are confirmed evidence-carrying gaps; whether different evidence would have changed the original automatic-review decision is unknown.

**Impact and priority:** P2; recovery of an already owned task incurred another human interruption and could stall authorized work.

**Source owner:** tj-agents/core machine task-recovery guidance and no-send follow-up advice.

**Repair link:** branch `Fix/RecoveryAuthorizationContext`; private diagnostic evidence is retained locally and excluded from Git. Related incident: [M002](MISTAKES.md); prior M005/PR207 is a separate fallback repair.

**Next action:** Implement the shared evidence-carrying recovery contract, preserve live-owner/uncertain-send/automatic-review gates, and verify both-host packaging and exact-head delivery.

**Resolution condition:** Both native hosts receive unchanged recovery instructions containing existing authority evidence; supported caller guidance carries exact task/scope/provenance into approval review without adding authority or overriding rejection; focused regressions, independent review and Windows/Linux CI pass, and the source correction plus causal generated packages reach main.

**Verification evidence:** Baseline recovery/follow-up/Claude-launcher suites passed on Windows. Delivery and new-regression evidence remains pending.
