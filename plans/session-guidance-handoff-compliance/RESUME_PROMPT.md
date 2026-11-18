# Resume PR #199 self-repair enforcement

You are the sole successor for the existing Core source-repair checkout. Read the canonical goal at `plans/session-guidance-handoff-compliance/GOAL.md` completely, then execute its next steps.

Tommy has explicitly refined the intended architecture: the user-callout response must be a distinct, specifically selectable workflow. The canonical `engineering:self-repair` workflow already exists in this checkout and is the intended focused owner; preserve that split. `engineering:session-guidance` must only retain the lifecycle pointer needed to select it, not carry the full self-repair procedure.

The required behavior is non-negotiable: every covered user mistake callout resolves before normal continuation or terminal close with either (A) a verified existing/actually launched single Core repair owner, or (B) a canonical typed deferred disposition with category (`capability`, `dependency`, `conflict`, or `capacity`), exact blocker, resolver, and observable resume condition. The gate must reject explanations, intent, an unverified launch, or a forged/stale record.

Preserve all existing local and uncommitted work. Do not create a new worktree, duplicate a writer, discard generated output, or adopt the separate session-registration repair. Reconcile the stale continuation and PR #199 state first. Update the goal to acknowledge this pickup and the user’s refinement before substantive edits. The active-session query reported four live sessions but no declared numeric capacity ceiling: do not call that a capacity block unless you implement or find an explicit source of truth for the ceiling.

Deliver this existing repair through focused validation, independent review, PR #199 update, required CI, merge, and causal publication under its recorded standing authority. Do not close or delete the originating Feature-WorkItemSessions checkout; that remains outside this workstream.
