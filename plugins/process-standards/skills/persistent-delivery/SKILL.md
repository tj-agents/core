---
name: persistent-delivery
description: Shared safety and identity contract for a PR that must survive an agent turn and continue through exact-head validation, repair, review, and authorized delivery. The host-specific persistent-workflow skill supplies the actual wake mechanism.
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

## Route every wake through the shared decision contract

The parent remains the workflow owner. It owns the plan, durable delivery state, stage transitions, exact
binding, authorization, and final terminal decision. A host wake reads authoritative forge state once and
passes the binding and observation through `workflows/delivery_runtime.py`. Reject a PR, check, run, review,
or merge observation from another head.

An exact-head failure selects its test tier before repair:

| Evidence | Fresh-context procedure |
|---|---|
| Unit | `failing-tests` |
| In-process integration | `dotnet:integration-debug` |
| Service E2E | `dotnet:e2e-api-debug` |
| Browser E2E | `dotnet:e2e-ui-debug` |
| Both E2E tiers | `dotnet:e2e-debug` |

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
and enter the recorded next stage through `plan-execution`. The parent resolves the plan's next owned work,
creates its branch, worktree, PR, and exact initial head binding, then rebinds the same continuation to that
successor. Only the parent may perform this transfer, and the repository, workflow ID, and state artifact must
remain identical.

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
The merge hook and the ordinary review/merge skills remain authoritative.

Stop and remove the host task when the bound PR merges without a workflow handoff, closes, is superseded, or reaches a genuine human,
authorization, external-head, model-availability, or product-capability decision. A closed continuation is
never replaced merely to report why it stopped. Record the final PR/head/result and next decision in the
normal handoff or plan artifact when one owns the work. The host task prompt itself carries the full binding
so the owning conversation can resume after application restart without the user restating the task.
