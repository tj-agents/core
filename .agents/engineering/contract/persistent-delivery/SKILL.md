---
name: persistent-delivery
description: Shared safety and identity contract for a PR that must survive an agent turn and continue through exact-head validation, repair, review, and authorized delivery. The host-specific persistent-workflow skill supplies the actual wake mechanism.

kind: contract
domain: process
---

# Persistent delivery contract

Use this contract only through the current harness's `persistent-workflow` skill. It defines the delivery
owner; it does not create a watcher, scheduler, background process, or model turn.

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
PR merges. The workflow handoff owns the single continuation across successive PR bindings; it never weakens
the exact PR/head/run identity active at any moment.

There is exactly one persistent owner for a PR/head pair. Reuse and update that owner when the binding is the
same. A new head created by this owner replaces its binding. A head changed by somebody else, a changed PR,
or a different worktree ends ownership and surfaces a human decision; never silently follow it.

**Resolve the authorization from the repository's recorded standing instruction; never ask for it once per
PR.** `python .agents/workflows/workflow_ops.py --workflow-run-id <id> delivery-bind [--pr <n>]` is the
single writer of the binding artifact. It reads authoritative forge state once and resolves
`.agents/delivery-authorization.json` — the standing mode, its exact recorded wording, and the repository's
own always-stop paths — against this head's changed path set and labels. Six stop classes hold everywhere
(the table itself, CI workflow, migration, auth, money, published contract); a repository adds its own.
Editing the table always stops, because a diff that changes who may merge unattended must not merge
unattended. A repository carrying
no such table resolves `absent`, which is the ordinary stop-and-ask. **Re-run it on every rebind:** a repair
push can add a stop-class path, so the authorization belongs to the head, not the PR. End it with
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

When a bound PR merges with no workflow handoff, remove the continuation normally. When it merges with a
workflow handoff, close the completed PR binding without removing the continuation, checkpoint the merge,
and enter the recorded next stage through `plan-execution`. The parent resolves the plan's next owned work
and reconciles its existing recorded branch, worktree and PR, including the actual base and current head.
Create those only when the successor does not yet exist. Refresh its exact delivery binding and rebind
the same continuation to it. Only the parent may perform this transfer, and the repository, workflow ID,
and state artifact must remain identical.

The successor is a new delivery binding with its own checks, review watermark, and merge authorization.
Authorization for the completed PR never silently authorizes the successor. The continuation may implement,
validate, push, open, and review that successor without intervention when those actions are already in scope,
but it stops at its merge gate unless the recorded instruction explicitly covers that exact successor or
bounded delivery chain.

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

Stop and remove the host task when the bound PR merges without a workflow handoff, closes, is superseded, or reaches a genuine human,
authorization, external-head, model-availability, or product-capability decision. A closed continuation is
never replaced merely to report why it stopped. Record the final PR/head/result and next decision in the
normal handoff or plan artifact when one owns the work. The host task prompt itself carries the full binding
so the owning conversation can resume after application restart without the user restating the task.
