---
name: persistent-delivery
description: Shared safety and identity contract for a PR that must survive an agent turn and continue through exact-head validation, repair, review, and authorized delivery. The host-specific persistent-workflow skill supplies the actual wake mechanism.

kind: policy
domain: process
---

# Persistent delivery contract

Use this contract only through the current harness's `persistent-workflow` skill. It defines the delivery
owner; it does not create a watcher, scheduler, background process, or model turn.

A continuation goal may exist before a PR or delivery binding. Keep its repository, worktree, canonical
goal, completion condition and authorized actions in the existing goal record; add the exact PR/head/run
binding when a remote delivery stage exists. Missing merge authorization gates merge only. It does not
block authorized local work, exact-head repair, or review that can proceed before that gate.

## Bind one delivery owner

Before creating or updating persistent work, capture one immutable delivery binding in the host task and in
the current durable handoff or plan state when one exists:

- repository owner/name and PR URL/number;
- absolute worktree and branch that own the change;
- current remote head SHA;
- every pending check ID and run ID with its full head SHA;
- review work-order path, execution order, and completed reviewed-SHA watermark;
- explicit merge authorization: absent, `--auto` authorized, or a narrower recorded instruction; and
- the explicit completion condition.

When the current PR is one stage of a longer plan-managed delivery, also bind one workflow handoff:
workflow ID, repository-relative plan or ledger state artifact, and the exact next stage to resume after this
PR merges. The workflow handoff preserves the broader goal across successive delivery owners; it never
weakens the exact PR/head/run identity active at any moment.

There is exactly one persistent owner for a PR/head pair. Reuse and update that owner when the binding is the
same. A new head created by this owner replaces its binding. A head changed by somebody else, a changed PR,
or a different worktree ends ownership and surfaces a human decision; never silently follow it.

Resolve authority from the repository's recorded standing instruction, the owning goal's recorded user
authorization (`engineering:merging` owns that goal-wide scope), or an observed user approval for
this exact PR. The source command below, or packaged `workflows/workflow_ops.py`, is the single writer of
the binding artifact:

```text
python -B .agents/workflows/workflow_ops.py --root ROOT --workflow-run-id ID delivery-bind --pr NUMBER [--approval-record PATH]
```

The optional approval record has exactly these fields. Replace the illustrative values with the actual
owning checkout identity, permitted merge mode, user's wording and observed message provenance:

```json
{
  "repository": "example/test",
  "pr_number": 42,
  "worktree": "C:\\source\\test",
  "branch": "feature",
  "mode": "merge",
  "instruction": "Merge PR 42 when checks and review pass",
  "source": "User message in SESSION at TIMESTAMP"
}
```

`worktree` must match the binder's normalized absolute checkout root, and `branch` must match both the
checkout and remote PR. `mode` is `merge` or `auto`, according to the actual approval. A goal file's bare
existence never invents merge authority; the user's recorded authorization of the goal does, for the
goal's own PRs (`engineering:merging`) — write it as this record, with its wording and provenance, for
each PR the goal creates. Invalid explicit input fails before any standing-authority fallback. Without a
standing instruction, goal authorization, or matching scoped approval, authority remains `absent` and
merge requires a user decision.

The binder reads authoritative forge state and resolves `.agents/delivery-authorization.json`, when
present, against the current changed paths and labels. Six stop classes hold everywhere: the authorization
table itself, CI workflow, migration, auth, money and published contract. Repository stop paths and its
hold label also apply; without a table, `human-gate` is the hold label. A scoped approval cannot bypass
these stops. **Re-run the binder on every rebind:** a repaired head may add a stop path or hold.

The artifact retains matching approval wording and provenance as `scoped_approval` across wakes and
supported repairs to the same PR, worktree and branch. Each rebind refreshes the remote head, checks and
review evidence and reevaluates the stops. A stopped head retains the approval record but resolves
`absent`; it does not authorize unattended merge. A wake or same-PR repair never requires another approval
solely because the repository lacks a standing table. The record cannot carry into another repository,
PR, worktree or branch. If ordinary merge is approved and GitHub auto-merge is unavailable, wait for
terminal checks and current-head review, then perform the authorized ordinary merge. End the binding with
`delivery-release --reason <terminal>`.

That command writes the binding to `.agents/persistent-workflow-binding.json` at the owning worktree root — repo
owner/name, PR number and URL, branch, absolute worktree, full head SHA, the exact check and run IDs, and
the completion condition. It is per-worktree runtime state, gitignored, and is the discoverable form of the
binding a hook can read. Update it on every rebind to a new head, and delete it on any terminal (merge,
closure, supersession, external head replacement, a human gate). `.agents/hooks/persistent_workflow_merge_gate.py`
refuses `gh pr merge … --auto` on a PR whose checks or merge queue have not settled unless this file exists
and its PR, head, and worktree match the enqueue — so an unattended auto-merge cannot be armed without a
continuation that owns the wait.

## Route every wake through the shared decision contract

The parent remains the workflow owner. It owns the plan, durable delivery state, stage transitions, exact
binding, authorization, and final terminal decision. A host wake reads authoritative forge state once and
passes the binding and observation through `workflows/delivery_runtime.py`. Reject a PR, check, run, review,
or merge observation from another head.

An exact-head failure selects its test tier before repair:

| Evidence | Fresh-context procedure |
|---|---|
| Unit | `failing-tests` |
| In-process integration | `integration-debug` |
| Service E2E | `e2e-api-debug` |
| Browser E2E | `e2e-ui-debug` |
| Both E2E tiers | `e2e-debug` |

Dispatch one clear context through the host's agent API with the selected skill,
repository/PR/worktree/branch, full bound SHA, exact
check and run IDs with their head SHA, and the failure signature. The debug context reads the remote log
first, reproduces only the failing scope, applies the tier procedure, runs focused validation, and returns
structured repair evidence to the parent. It does not create another monitor, select follow-on scope, or
merge. This dispatch is not a keyboard macro, `/clear`, pasted prompt, or new top-level conversation. The
parent validates the result, accepts one stable repair, commits and pushes it, then updates the existing
continuation to the new SHA and exact pending runs. It never creates a second continuation during that rebind.

A green exact head enters independent `review` or `incremental-review`. A host with a declared model
fallback keeps the same semantic stage, frozen SHA, role boundary, and fresh-context requirement, and records
both the primary and selected model. Exhausting a protected-stage route is a human decision. Actionable current-head findings
enter `address-review` and return through a new current-head watermark. Only a green, independently reviewed
head may enter `merge`, and only under the recorded authorization.

## Transfer an intermediate merge

The runtime owner is bound to one worktree and branch, and permits head repair within that identity.
It cannot rebind itself to a successor PR or another checkout. When a slice PR merges, complete its
recorded delivery condition, release its binding, checkpoint its runtime owner and remove its scheduled
task. Preserve that owner's receipts and results. Before reusing the same checkout, archive its terminal
`.agents/continuation/` directory, including `owner.json`, receipts and results, outside the tracked tree;
the next initialization needs the canonical owner path available. Remove the old scheduler before
archiving its receipt. Completing the slice owner does not complete the broader canonical goal.

With a workflow handoff, the foreground parent resumes the recorded stage through `plan-execution` and
reconciles the next slice's existing branch, worktree and PR, including its actual base and head. Create
those only when absent. After retiring the old owner, initialize and claim the next worktree's canonical
owner against the same goal, then register its continuation when needed. Keep one active writer. The
repository, workflow ID and state artifact remain identical; automatic supervisor transfer across
worktrees is outside the runtime's supported transition.

The successor is a new delivery binding with its own checks, review watermark, and merge authorization.
A completed PR's binding never carries over; the successor re-resolves authority from the same recorded
sources, and the goal's authorization covers each PR the goal itself creates (`engineering:merging`). The
workflow owner may implement, validate, push, open, and review that successor without intervention when
those actions are already in scope, and stops at its merge gate only when no recorded goal, standing, or
scoped authority covers it.

An unchanged authoritative state produces no report, mutation, replacement continuation, or model-driven
work. Host mechanics decide how a later transition wakes the owner; shared policy never claims that a shell
process, hook, or ordinary model turn provides persistence.

## Authorization and terminals

Persistent delivery may implement, test, commit, push, diagnose exact-head CI, and obtain the required review.
It must not merge, enable auto-merge, approve, deploy, delete, or widen scope without the recorded authority.
A merge authorization never covers publishing: releasing to a package feed stays an explicit human call
whatever the standing instruction says about merging.
The merge hook and the ordinary review/merge skills remain authoritative. `.agents/hooks/forge_poll_gate.py`
also enforces the single-monitor / one-read-per-wake rule from this contract. Launch
`.agents/workflows/workflow_ops.py monitor` for the exact binding; it persists state across disconnects and
wakes the owner only for a material transition or terminal result. A repeated model-turn status read of
unchanged state is blocked.

Stop and remove the slice's host task when the bound PR merges, closes, is superseded, or reaches a genuine human,
authorization, external-head, model-availability, or product-capability decision. A closed continuation is
never replaced merely to report why it stopped. Record the final PR/head/result and next decision in the
normal handoff or plan artifact when one owns the work. The host task prompt itself carries the full binding
so the owning conversation can resume after application restart without the user restating the task.
