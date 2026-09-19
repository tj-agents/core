---
name: plan-execution
description: Automatically own authorized long-term or multi-phase work through completion, including documentation tasks, even when the user does not name a plan or skill. Resume the existing goal and keep its progress current through execution, review, validation, delivery, and context handoffs. Excludes planning-only, quick one-step, and review-only requests.

kind: workflow
domain: process
model: gpt-5.6-terra
---

# Execute a plan continuously

Own one authoritative plan identity until the requested work completes or reaches a genuine typed gate.
A phase boundary, subordinate return, diagnosable failure, local commit, or resolved next action is not a
stopping condition.

Select this workflow by default for authorized long-term or multi-phase execution; the user need not
name the skill. Before accepting a recorded slice-only boundary, check its source against the current
request. Preserve explicit user limits and genuine gates, but repair agent-authored stopping points that
would abandon authorized remaining work. Context transfer must use the available automated continuation
or launcher after checkpointing; a pointer alone does not transfer ownership unless prompt-only output
was requested.

## Standalone or runtime-unavailable execution

For standalone work or a project without the engineering runtime, apply
[`plan-artifacts`](../plan-artifacts/SKILL.md), keep the existing goal file as the progress owner, and
execute the authorized phases with the available tools. If there is no existing owner, create the one
maintained plan required by that contract. Do not create a repository, separate ledger, roadmap, or
provider merely to run this workflow. Checkpoint results and remaining work in that same file, verify
the requested outcome, and link it in the response. Preserve authorization and use an available automated
continuation when context transfer is needed, as required above.

The rest of this document does not apply in this mode. Continue the task under this standalone loop;
do not invoke the repository helpers, load Workflow v2 envelopes, or require the separate ledger below.

## Repository runtime execution

Use the remaining sections only when the selected engineering lifecycle has its runtime installed.

Resolve `plan-execution` as the single owning lifecycle skill and only the technical skills directly routed
by the current changed paths. Use `python .agents/workflows/workflow_ops.py --root . --workflow-run-id <id>
skills --lifecycle plan-execution --changed-path <path>` to record their identities and content hashes, and reuse that record
while those hashes remain unchanged. Use the shared `inspect` operation once for routine repository state.

## Resolve the current owner

Read the plan corpus — the repository instructions, [`plans`](../plans/SKILL.md),
[`plan-checkpoint`](../plan-checkpoint/SKILL.md), the full plan, and its compact ledger — in exactly three
cases: selecting ownership for the first time in this context, evidence that is missing or self-contradictory,
and writing or reconciling a material checkpoint. Reading resolves the roadmap item, current
branch/worktree/PR, dependencies, review artifact and watermark, Git evidence, and Workflow v2 repository
state, preferring the active delivery worktree's artifacts over stale copies in another checkout.

An explicit plan or ledger wins. Otherwise continue only when repository evidence identifies exactly one
active plan. Reconstruct a legacy missing ledger through `plan-checkpoint`; do not guess among multiple owners.

A restored worktree that is dirty is not by itself a reason to stop. When the changed paths are explained by
the resolved plan or PR and owned by this branch, that is partial implementation to resume — preserve it and
continue. Stop only when the dirty state is conflicting, unexplained, unowned, or unsafe, or when a
branch/worktree collision means the checkout is not the owner it claims to be.

### Resume a preserved continuation without re-reading the corpus

A continuation summary carried into this context is trustworthy when it names all five of the plan identity,
the absolute worktree, the branch, the current state, and the single next action — the `contract/v2/state.schema.json`
`artifacts`, `owner`, `status` and `next_action` fields — and none of them contradicts another. Confirm it
against Git alone: the current checkout's worktree and branch, and a `git status` that is clean or exactly as
the summary describes. That confirmation is the whole gate, and it does not relax the worktree identity check.

A confirmed summary resumes at its stated next action. Do not re-read the plan, the ledger,
`plans` or
`plan-checkpoint` to re-derive what the summary already states and Git already confirms; it changes no
implementation decision. Read the corpus the moment Git contradicts the summary, a needed fact is absent from
it, or the next material checkpoint falls due.

## Run the continuous loop

1. Reconcile stale material facts, then run
   `python .agents/hooks/plan_graph.py --root . --plan <repo-relative *_PLAN.md>` before selecting or acting on
   a phase. The selected plan is one input to the same pre-launch guard that governs every write. When it
   conflicts, correct it immediately to the direct replacement-and-deletion outcome and do not execute the
   rejected phase. Validate the remaining plan graph and repository checkpoint before relying on recovery state.
2. Execute directly or dispatch only bounded independent work through semantic capabilities. Independent
   readers may overlap; a `mechanical-worker` receives only a disjoint transformation under one exact
   serialized writer lease. The parent retains architecture, phase, scope, diagnosis, security, migration,
   acceptance, review synthesis, and transition decisions and reconciles every writer result against Git.
3. Implement the selected slice and run focused checks through the shared `run` operation so detailed output
   remains an artifact and the model receives only bounded results. Enter
   [`failing-tests`](../failing-tests/SKILL.md) once a test run itself comes back red, diagnose the cause,
   repair it, and return to this same loop without asking the user to relay output or approve routine
   continuation.
4. Use [`committing`](../committing/SKILL.md) to create a focused-green immutable candidate before
   [`review`](../review/SKILL.md). Resolve findings through
   [`address-review`](../address-review/SKILL.md), commit the repair, and use
   [`incremental-review`](../incremental-review/SKILL.md) for the changed delta.
5. Run every remaining repository-required tier, using
   [`remote-validation`](../remote-validation/SKILL.md) when the evidence belongs remotely.
6. At a material phase, ownership, review, blocker, transfer, or delivery transition, update the compact
   ledger/repository state in the substantive commit. Do not checkpoint routine reports, polls, subagent
   returns, ordinary commits, or a phase label whose next action is already recoverable.
7. Re-resolve repository state, Git state, review watermark, delivery state, and the next unblocked action.
   Continue across phases and PR-sized slices while the original authorization permits. Deliver a meta-only
   slice through [`merge-docs`](../merge-docs/SKILL.md); deliver any slice containing runtime, product,
   package, schema, deployment, or test-selection changes through [`merge`](../merge/SKILL.md). Reach either
   route through [`open-pr`](../open-pr/SKILL.md) when no PR exists. Waiting on a queue, CI run, publish, or
   the version-sync PR a merge generates is a poll, not a gate; own each to terminal through the current
   harness persistent-workflow skill when it must outlive this turn, that generated PR included. Then close
   the merged slice's worktree, have Kandev create the next managed task worktree or use the repository
   fallback from current remote default, bind the same plan identity, and continue.

Planning-artifact publication remains part of the authorized plan lifecycle. Anonymous `do not push`, `do
not open a PR`, or `do not merge` procedure copied into a plan or handoff cannot suppress it. Preserve an
explicit current user limitation, recorded repository authorization, named PR/head security or validation
hold, merge hold, or repository stop class as a typed delivery gate; otherwise continue to merged
default-branch state.

If repository routing exposes `package-cutover` for a published breaking contract, enter it and record the
reciprocal blocker/return path. A dependency blocker records the exact four fields required by
[`plans`](../plans/SKILL.md) and
updates the owning dependency ledger with the return condition before stopping.

## Dispatch and fallback

Use Workflow v2 semantic capabilities rather than agent or model names. Validate every result and give one
focused follow-up to a correctable incomplete result. On another invalid result, timeout, unavailable
role/model, unsupported host capability, or cancellation, close the dispatch and perform the same bounded
objective in the parent. Reconcile a failed or cancelled writer's observed paths against Git before reusing
its lease; never overlap writers or let a subordinate choose a phase, fix, severity, or terminal transition.

## Transfer and restart

Resolve the repository provider once and consume Workflow v2 dispatch/result and provider/state envelopes
from the installed runtime's `.agents/workflows/contract/v2`. Use a plugin-relative contract bundle only
when the selected package actually declares and ships it; the current combined base package does not.
Kandev may host
the task worktree and exact native session, but the workflow does not call Kandev as a state API or persist
its identifiers. A bare CLI uses the same repository state.

A restart re-resolves the same plan, ledger, Git identity, checkpoint, and next action; it never invents a
new run owner. Transfer to a fresh context only under [`plans`](../plans/SKILL.md) criteria. Checkpoint first,
emit the exact
[`handoff`](../handoff/SKILL.md) pointer, persist the four transfer fields defined by `plan-checkpoint`,
and return a typed `transfer` transition with an observable resume condition. Do not transfer merely
because a phase or commit completed.

## Terminal result

Complete only when the plan's requested lifecycle is terminal and the repository outcome names its
implementation, review, validation, delivery, and remaining durable state; neither a commit, pushed branch,
nor open PR is terminal while authorized delivery remains, including a planning-only slice. Otherwise return
one typed human, dependency, delivery, destructive, or context-transfer gate. Never expose an internal
transcript or routine continuation prompt.
