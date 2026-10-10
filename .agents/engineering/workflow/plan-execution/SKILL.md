---
name: plan-execution
description: Automatically own authorized long-term or multi-phase work through completion, including documentation tasks, even when the user does not name a plan or skill. Resume the existing goal and keep its progress current through execution, review, validation, delivery, and context handoffs. Excludes planning-only, quick one-step, and review-only requests.

kind: workflow
domain: process
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

When execution follows substantial critical-plan design, load `engineering:plan-authoring`'s execution
readiness section before choosing inline execution or a fresh owner. A successor named by a transfer
receipt follows `engineering:handoff`'s verified pickup procedure before deliverable writes. Read the
canonical goal, validate the checkpoint and authority, acknowledge the exact attempt, then perform its
next action immediately. Acknowledgement is not completion; keep the same goal through its remaining
authorized slices and record the first action or genuine gate as progress evidence.

After design approval or completion of a prerequisite, resolve the next authorized substantive action and
execute or dispatch it at the selected lane. Use existing valid ownership, scope, review and validation
evidence; refresh only evidence whose inputs changed, whose result is missing or contradictory, or whose
governing gate requires a fresh check. If substantive work cannot start, identify the exact unmet
dependency and continue authorized work that does not depend on it. Repeating satisfied preparation is
not progress toward the next action.

A CI query, transport or monitor error leaves the delivery result unknown. Diagnose and restore
observation through the supported monitor, retaining its repository, PR, head and run binding and
reconciling the failed monitor before replacing it. Preserve TLS verification, authorization and every
required review and CI gate. Continue independent authorized work while observation recovers; when fresh
evidence establishes that delivery is ready, perform the next authorized delivery action. If recovery
requires an external change, record the failed action, resolver, unblock action and observable resume
condition.

## Select the execution lane

Before choosing either execution mode below or making a deliverable edit, load `engineering:lanes`
through the host's skill invocation or read its advertised SKILL.md in full. Select and record the lane
for the next bounded phase using that contract and resolve it from the current host's canonical table.
Repeat selection when the phase changes, including after design approval, review entry, or fallback.
Approval supplies execution authority; it does not carry the design lane into implementation.

Apply the selected lane through a supported host control or a bounded lane worker before implementing.
Direct execution is appropriate when the current owner already runs at the selected lane. Preserve the
canonical contract's tiny inline follow-up allowance and its distinction between in-session workers and
a fresh execution owner after substantial critical-plan design. If the host cannot apply the lane,
follow that contract's capability-limit procedure; do not treat inherited session settings as selection.
This step applies to standalone work and runtime-unavailable work as well as repository execution.

## Standalone or runtime-unavailable execution

For standalone work or a project without the engineering runtime, apply
`base:plan-artifacts`, keep the existing goal file as the progress owner, and
execute the authorized phases with the available tools. For repository code changes, apply
`engineering:git-branching` before the first implementation and whenever the candidate grows beyond its
recorded slice. Preserve reviewable PR boundaries even without the runtime. If there is no existing owner, create the one
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

Read the plan corpus — the repository instructions, `engineering:plans`,
`engineering:plan-checkpoint`, the full plan, and its compact ledger — in exactly three
cases: selecting ownership for the first time in this context, evidence that is missing or self-contradictory,
and writing or reconciling a material checkpoint. Reading resolves the roadmap item, current
branch/worktree/PR, dependencies, review artifact and watermark, Git evidence, and Workflow v2 repository
state, preferring the active delivery worktree's artifacts over stale copies in another checkout.

An explicit plan or ledger wins. Otherwise continue only when repository evidence identifies exactly one
active plan. Reconstruct a legacy missing ledger through `plan-checkpoint`; do not guess among multiple owners.

Resolve the slice's owning review under `engineering:git-branching` alongside its plan identity. Carry
the ledger's `PR:` field across execution branches and handoffs; the provider exposes it as
`artifacts.pull_request` for delivery preflight.

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

1. Reconcile stale material facts. For a project selecting the Concertable pre-launch profile, run
   Concertable's own adapter CLI before selecting or acting on
   a phase; the selected plan is one input to the same pre-launch guard that governs every write. When it
   conflicts, correct it immediately to the direct replacement-and-deletion outcome and do not execute the
   rejected phase. Run `python -B .agents/hooks/plan_graph.py --root .` to validate the remaining plan graph
   and repository checkpoint before relying on recovery state.
   Other repositories validate dependencies and checkpoints under their own selected policies, preserving published compatibility windows; they do not implicitly select the Concertable profile.
2. Apply `engineering:git-branching` before implementation and at each scope expansion. Check the current
   PR's measured size against its recorded delivery slice. Split large dependent work into a stack,
   carrying the same goal and owner; record any atomic exception before growing the candidate. An open
   PR or phase is not a container for all remaining work. Route a distinct, independently actionable
   side workstream with its own authorization through `engineering:handoff` in bounded side-workstream
   mode; retain this session's active goal instead of transferring it.
   Execute directly at the selected phase lane or dispatch only bounded independent work through semantic
   capabilities that honor that lane. Independent readers may overlap; a `mechanical-worker` receives
   only a disjoint transformation under one exact
   serialized writer lease. The parent retains architecture, phase, scope, diagnosis, security, migration,
   acceptance, review synthesis, and transition decisions and reconciles every writer result against Git.
3. Implement the selected slice and run focused checks through the shared `run` operation so detailed output
   remains an artifact and the model receives only bounded results. When the slice depends on a change of
   direction that the repository's standing conventions do not state yet, whoever decided it, land that
   convention in this slice under `engineering:docs`. Enter
   `engineering:failing-tests` once a test run itself comes back red, diagnose the cause,
   repair it, and return to this same loop without asking the user to relay output or approve routine
   continuation.
4. Use `engineering:committing` to create a focused-green immutable candidate before
   `engineering:review`. Resolve findings through
   `engineering:address-review`, commit the repair, and use
   `engineering:incremental-review` for the changed delta.
5. Run every remaining repository-required tier, using
   `engineering:remote-validation` when the evidence belongs remotely.
6. At a material phase, ownership, review, blocker, transfer, or delivery transition, update the compact
   ledger/repository state in the substantive commit. Do not checkpoint routine reports, polls, subagent
   returns, ordinary commits, or a phase label whose next action is already recoverable.
7. Re-resolve repository state, Git state, review watermark, delivery state, and the next unblocked action.
   Continue across phases and PR-sized slices while the original authorization permits. Deliver a meta-only
   slice through `engineering:merge-docs`; deliver any slice containing runtime, product,
   package, schema, deployment, or test-selection changes through `engineering:merge`. Reach either
   route through `engineering:open-pr` with the resolved slice and owning review. Waiting on a queue, CI run, publish, or
   the version-sync PR a merge generates is a poll, not a gate; own each to terminal through the current
   harness persistent-workflow skill when it must outlive this turn, that generated PR included. Then close
   the merged slice's worktree. For an existing stack, reconcile and continue its next layer; do not
   duplicate it from main. Otherwise start the next branch from the current remote default and select
   its checkout under `engineering:git-branching`. A managed host may allocate required isolation;
   native execution can reuse an available checkout. Bind the same plan identity and continue.

Planning-artifact publication remains part of the authorized plan lifecycle. Anonymous `do not push`, `do
not open a PR`, or `do not merge` procedure copied into a plan or handoff cannot suppress it. Preserve an
explicit current user limitation, recorded repository authorization, named PR/head security or validation
hold, merge hold, or repository stop class as a typed delivery gate; otherwise continue to merged
default-branch state (`engineering:merging` owns the goal-wide merge-authorization scope).

If repository routing exposes `package-cutover` for a published breaking contract, enter it and record the
reciprocal blocker/return path. A dependency blocker records the exact four fields required by
`engineering:plans` and
updates the owning dependency ledger with the return condition before stopping.

## Dispatch and fallback

Use Workflow v2 semantic capabilities rather than agent or model names. Validate every result and give one
focused follow-up to a correctable incomplete result. On another invalid result, timeout, unavailable
role/model, unsupported host capability, or cancellation, close the dispatch and reselect the phase lane
under `engineering:lanes` before performing the same bounded objective in the parent. Parent fallback must
satisfy the same lane and capability-limit rules as direct execution; a missing worker does not promote
implementation to the design lane. Reconcile a failed or cancelled writer's observed paths against Git
before reusing its lease; never overlap writers or let a subordinate choose a phase, fix, severity, or
terminal transition.

## Transfer and restart

Resolve the repository provider once and consume Workflow v2 dispatch/result and provider/state envelopes
from the installed runtime's `.agents/workflows/contract/v2`. Use a plugin-relative contract bundle only
when the selected package actually declares and ships it; engineering supplies this bundle under `../../workflows/contract/v2` from its installed skill directory.
Kandev may host
the task worktree and exact native session, but the workflow does not call Kandev as a state API or persist
its identifiers. A bare CLI uses the same repository state.

A restart re-resolves the same plan, ledger, Git identity, checkpoint, and next action; it never invents a
new run owner. Transfer to a fresh context only under `engineering:plans` criteria. Checkpoint first,
execute `engineering:handoff`, and persist the four transfer fields defined by `plan-checkpoint`. That workflow
uses `engineering:handoff-format` for the pointer and invokes one selected launcher before this context releases
ownership. Return a typed `transfer` transition with an observable resume condition. Do not transfer merely
because a phase or commit completed. A massive plan whose substantial design phase produced a durable
phased execution plan normally has a separate transfer reason under `engineering:plans`.

## Terminal result

When the canonical goal has a fenced `completion` record, invoke the `persistent-workflow` completion
contract before reporting the user outcome complete or deleting the goal. A failing completion check keeps
the goal and its returned next actions owned by the current execution.

Complete only when the plan's requested lifecycle is terminal and the repository outcome names its
implementation, review, validation, delivery, and remaining durable state; neither a commit, pushed branch,
nor open PR is terminal while authorized delivery remains, including a planning-only slice. Otherwise return
one typed human, dependency, delivery, destructive, or context-transfer gate. Never expose an internal
transcript or routine continuation prompt.
