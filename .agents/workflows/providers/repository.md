# Repository workflow-state provider

The repository provider is the Phase 1 portable implementation. It correlates the current Git worktree with
one plan ledger and returns a validated `state.schema.json` record inline. It creates no workflow sidecar.

Repository artifacts own plan intent, the next action, decisions, review findings, and blockers. Git owns
the branch, worktree, commit, and history. The forge and package systems continue to own their remote facts.
The provider rejects a ledger whose recorded worktree or branch does not match the checkout being resolved.

`discover`, `resolve-task`, `read-state`, `checkpoint-state`, and `bind-worktree` are available. A
checkpoint is still applied through the existing `plan-checkpoint` contract as an edit to the owning plan,
ledger, or review artifact; the runtime validates and re-reads that state instead of creating another store.
Session launch, transfer, cancellation, and worktree mutation remain with their existing repository tools.
