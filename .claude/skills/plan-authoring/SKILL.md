---
name: plan-authoring
description: Design or phase multi-step work and create or update its implementation-ready plan and compact ledger, or an implementation-ready design document such as a research decision or RFC. Use for planning-only requests, roadmap-item planning, implementation-ready design documents, or durable promotion when no active plan already owns the work; do not use to execute an existing plan, prioritize a roadmap without a selected item, or directly complete a short unplanned task.
domain: process
route: infer
---

# Author a durable plan

Turn an explicitly requested planning outcome into one authoritative implementation design. A phased plan
has a recovery ledger; a standing reference that owns no phases keeps its bare filename and needs no ledger.
Both follow the `plans` skill's implementation-examples and standards contract. Planning-only authority ends
with the planned artifacts; when the same request also authorizes implementation, enter
[`plan-execution`](../plan-execution/SKILL.md) in the same parent after the plan identity is valid.

## Resolve ownership before writing

Read the repository instructions and [`plans`](../plans/SKILL.md); resolve the implementation-path standards
under its implementation-examples contract before drafting code. For plan/ledger work, also read
[`plan-checkpoint`](../plan-checkpoint/SKILL.md). Inspect plans, references, ledgers, roadmap keys, branches,
worktrees, and pull requests for an existing owner. Update the unambiguous existing artifact directly; never
create a competing plan, reference or ledger.

For a request to choose the next roadmap item, let the
[`continue-roadmap`](../continue-roadmap/SKILL.md) compatibility entry resolve the candidate first.
[`update-roadmap`](../update-roadmap/SKILL.md) remains the owner of roadmap reconciliation, not plan design.

## Author the outcome

1. Establish the requested outcome, constraints, evidence, dependencies, authorization boundary, and
   objective completion conditions. A bounded read-only `evidence-explorer` or `test-impact-analyst` may
   gather independent evidence; the parent owns design and scope.
2. Apply the `plans` implementation-examples and standards contract. When phasing delivery, design
   independently shippable phases that each end green, with an exact consumption contract and verification
   gate for every phase that exposes a capability.
3. Write the owned artifact in the repository's current format. For a plan, create/update its compact ledger
   with its roadmap path and stable item key; the plan does not cite the roadmap. A standing reference keeps
   the bare-stem shape defined by `plans` and creates no competing phase owner.
4. For plan-managed work, resolve the Workflow v2 repository provider once and validate the plan, ledger,
   worktree, branch, and next action through it. When Kandev hosts the task, leave its task and session
   identifiers in Kandev.
5. Run the plan graph for plan/ledger changes and the relevant documentation checks. Enter `docs-review`,
   including the `plans` implementation-design review gate, and resolve its findings before declaring the
   artifact implementation-ready.
6. Checkpoint only the material authored state. Planning-only work follows the repository's docs delivery
   workflow when durable publication is required. Planning plus implementation transfers ownership directly
   to `plan-execution` without a routine continuation prompt.

Use the Workflow v2 dispatch/result and provider/state envelopes in `.agents/workflows/contract/v2` when
present, or the packaged `../../workflows/contract/v2` bundle. A subordinate may return evidence, never phase
design, architecture, prioritization, or the final plan.

## Terminal result

Return a completed planning outcome naming the design artifact, any owning ledger, validation, review, and
whether implementation authority was present. Otherwise return one typed human or dependency gate with its
owner, required action, evidence, and observable resume condition. Do not implement under planning-only
authority or expose internal agent transcripts.
