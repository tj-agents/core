# Repository workflow-state provider

The repository provider is the Phase 1 portable implementation. It correlates the current Git worktree with
one plan ledger and returns a validated `state.schema.json` record inline. It creates no workflow sidecar.

Repository artifacts own plan intent, the next action, decisions, review findings, and blockers. Git owns
the branch, worktree, commit, and history. The forge and package systems continue to own their remote facts.
The provider rejects a ledger whose recorded worktree or branch does not match the checkout being resolved.

The ledger's existing `PR:` header owns the slice's review identity independently of execution location.
The provider carries its URL as `artifacts.pull_request`; `not opened` becomes null for an assessed slice
awaiting its first review. An absent header stays absent for legacy state and leaves ownership unresolved.
Handoffs update the worktree and branch while retaining that review. Delivery preflight verifies its
current forge state and routes corrections back to its branch before publication.

`discover`, `resolve-task`, `read-state`, `checkpoint-state`, and `bind-worktree` are available. A
checkpoint is still applied through the existing `plan-checkpoint` contract as an edit to the owning plan,
ledger, or review artifact; the runtime validates and re-reads that state instead of creating another store.
Session launch, transfer, cancellation, and worktree mutation remain with their existing repository tools.
