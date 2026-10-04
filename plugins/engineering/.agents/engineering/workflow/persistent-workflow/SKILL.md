---
name: persistent-workflow
description: Keep an authorized remote delivery owned across delayed checks using the selected host's supported continuation capability and one exact delivery identity.
kind: workflow
domain: process
---

# Persistent delivery continuation

Load `engineering:persistent-delivery` for binding, review, repair, authorization and terminal behavior.
Use this workflow when a substantive authorized task has a future decision that may outlive the current
session. Its owner can begin before a PR exists. Ordinary quick answers and short inline work stay in the
foreground without a scheduler. The existing canonical goal remains the source of completion criteria and
authority; this workflow does not create a competing plan or permission.

## Initialize one owner

Use the packaged `<engineering-package-root>/workflows/continuation_runtime.py` module from an installed
package, resolving the package root from the installed host skill entry, or its source counterpart
`.agents/workflows/continuation_runtime.py` in a checkout. Initialize the durable owner with the canonical
goal path, completion condition, exact authorized actions, authority record and current harness:

```text
python -B "<engineering-package-root>/workflows/continuation_runtime.py" init --root ROOT --goal GOALPATH --completion TEXT --actions ACTION [ACTION ...] --authority TEXT --harness codex|claude
```

The default owner record is `.agents/continuation/owner.json` below the worktree. `init` records one
stable owner before any PR binding exists. Existing delivery identity and exact-head binding remain in
`persistent-delivery`; add or refresh that binding when the task reaches a PR. A continuation goal may
therefore own local work and later remote repair/review without pretending a PR already exists.

`GOALPATH` may name an existing worktree-relative file or an explicitly supplied absolute path to an
existing external canonical goal. The runtime normalizes and retains that identity; relative escapes,
missing files and directories are rejected. Keep the goal in place. The owner remains at the canonical
per-worktree path above. On `canonical-owner-path-required`, retry `init --root ROOT` with `--owner`
omitted. This recoverable invocation error does not establish that the runtime is unavailable.

The runtime supports `status --owner OWNER` and `wake --owner OWNER`. After initialization, the current
foreground session claims the owner with `claim --owner OWNER --pid PID`; PID must identify that
long-lived session, not a short-lived tool shell. The returned `foreground.token` is required by
`heartbeat`, `yield`, and `checkpoint`. Renew the lease with `heartbeat` while actively working. Yield with
a reason and next action before waiting so the scheduled writer can take the lease. Checkpoint only a real
`waiting`, `blocked`, or `complete` state with its reason and next action where applicable. Completion
preserves the goal, result and logs.

The child process returns a receipt through the paths and identifiers in `CONTINUATION_RESULT_PATH`,
`CONTINUATION_NONCE`, and `CONTINUATION_OWNER_ID`. It reports state, reason, next action, and an optional
exact identity rebind. After a repair, a terminal `complete` or `blocked` receipt that releases the
delivery binding must include its refreshed full artifact snapshot as `released_binding`, captured before
deletion, plus exact `rebind.old` and `rebind.new` identities. The snapshot must match the owner PR and
current repository, worktree, branch and HEAD. It cannot override an existing binding or authorize a
nonterminal release. The supervisor owns checkpointing while it holds the writer lock; the child must
not call owner checkpoint itself. Continue to honor the canonical goal and authorization on every wake.
The runtime lease coordinates its own writers; it does not gate arbitrary host writes or replace the
harness's permission controls.

The Windows adapter is shipped beside each host's `persistent-workflow` entry at
`<skill-directory>/scripts/delivery-continuation.ps1`. Initialize and claim the foreground
owner before `register`; the adapter supports `register`, `remove`, `list`, and `wake`. The Python runtime
supports `status` and `wake` against `--owner OWNER`. Remove only at a terminal result. Yield the foreground
lease before waiting. Do not register another task for an
existing owner or claim unattended progress before the host and scheduler report success. Other platforms
must use an implemented runtime adapter; if none is available, state the limitation and continue
independent authorized work in the current session.

Establish durable continuation through successful initialization, foreground claim, scheduler registration
and an observed wake. Child execution resolves L4 model and effort from the packaged canonical lane table.
The runtime owner remains bound to one worktree and branch; its receipt permits a head rebind within that
identity. To move a longer goal to the next slice, follow the foreground owner transition in
`persistent-delivery`, preserve the old receipts and maintain one active writer. Completing this runtime
owner's slice does not mark the full goal complete. Automatic supervisor transfer across worktrees is
outside this runtime.

Runtime budgets default to six child launches, three consecutive transport failures, a 24-hour deadline,
and a 900-second child timeout. Tighter limits already recorded by the user take precedence. Do not
increase them silently or add bypass-permission flags.

For remote delivery, preserve one exact PR/head/worktree/run identity and one continuation. Route every
remote decision through `persistent-delivery`; reject observations from another identity. An exact-head
failure receives one appropriate repair context, a green head receives independent current-head review,
and merge remains behind its existing authorization gate. Missing merge authorization blocks merge only;
it does not stop authorized local work, failure repair, or review that can proceed before that gate.
Preserve an observed approval for this PR through the delivery binder's `--approval-record` input.
A wake or supported same-PR repair does not require another approval merely because the repository has
no standing table; the binder reevaluates fresh stop paths and hold labels before authorizing the new head.

An unsupported host or unavailable runtime must expose the concrete missing capability and leave a
recoverable checkpoint. Installation of this package adds context and tools only: it does not create or
register a continuation, grant scheduler permission, prove hook trust, or establish authenticated host
acceptance.
