---
name: plan-authoring
description: Design or phase multi-step work and create or update its implementation-ready plan and compact ledger, or an implementation-ready design document such as a research decision or RFC. Use for planning-only requests, roadmap-item planning, implementation-ready design documents, or durable promotion when no active plan already owns the work; do not use to execute an existing plan, prioritize a roadmap without a selected item, or directly complete a short unplanned task.

kind: workflow
domain: process
---

# Author a durable plan

## Applicability

Read `base:plan-artifacts` for the common maintained-plan contract.
The engineering lifecycle below applies only when selected by the project or user. For standalone
planning, correction, or resume, follow that common contract and stop here; do not require a roadmap,
ledger, provider, review pipeline, or publication. Installing base or invoking planning alone does not
select this richer lifecycle or grant implementation or publication authority.


Turn an explicitly requested planning outcome into one authoritative implementation design. A phased plan
has a recovery ledger; a standing reference that owns no phases keeps its bare filename and needs no ledger.
Both follow the `plans` skill's implementation-examples and standards contract. Planning-only authority ends
with the planned artifacts; when the same request also authorizes implementation, apply the execution
readiness decision below and enter `engineering:plan-execution` under the selected owner.

## Execution readiness

Planning includes responsibility for making the next owner able to act. For a large critical plan,
evaluate whether substantial design, costly mistakes, independent delivery slices and the remaining
execution context justify a distinct readiness responsibility and a fresh executor. Use judgment;
plan length, a phase label or a model change alone does not select another agent. The current planner
can perform readiness. A bounded independent reader can check evidence without becoming a permanent
middleman. Small and medium work normally continues in the same parent with bounded lane delegation.

Before selecting a substantial-design transfer, maintain a compact `## Execution readiness` section
in the canonical goal or its existing progress ledger, referencing existing sections instead of copying them:

- intended outcome and observable acceptance criteria;
- scope, exclusions and the source of implementation, publication and installation authority;
- actual checkout, branch, owning review, source evidence and applicable standards;
- resolved mechanism decisions/examples, ordered reviewable slices and their dependencies;
- verification gates, user budgets, stop/escalation rules and objective resume conditions;
- exact next action, execution lane and reason for transferring;
- ready verdict with evidence, or the specific unresolved decision and its resolver.

Apply the `plans` implementation-design review gate. Ready means the selected executor can start the
next authorized action without deciding unresolved architecture. A delivery hold can coexist with
ready local implementation; an implementation blocker routes to its resolver while independent work
continues. Planning-only work stops at its authorized planning outcome, however ready the design is.

For ready, authorized work meeting `plans`' context-transfer criteria, enter `engineering:handoff`
and perform its verified execution pickup procedure without a further go-ahead. Otherwise continue
with `engineering:plan-execution` in this context. The canonical goal owns all execution requirements;
the launcher prompt remains a pointer.

## Resolve ownership before writing

Read the repository instructions and `engineering:plans`; resolve the implementation-path standards
under its implementation-examples contract before drafting code. For plan/ledger work, also read
`engineering:plan-checkpoint`. Inspect plans, references, ledgers, roadmap keys, branches,
worktrees, and pull requests for an existing owner. Update the unambiguous existing artifact directly; never
create a competing plan, reference, or ledger.

For a request to choose the next roadmap item, let the
`engineering:continue-roadmap` compatibility entry resolve the candidate first.
`engineering:update-roadmap` remains the owner of roadmap reconciliation, not plan design.

## Author the outcome

1. Establish the requested outcome, constraints, evidence, dependencies, authorization boundary, and
   objective completion conditions. A bounded read-only `evidence-explorer` or `test-impact-analyst` may
   gather independent evidence; the parent owns design and scope.
2. Apply the `plans` implementation-examples and standards contract. When phasing delivery, design
   independently shippable phases that each end green, with an exact consumption contract and verification
   gate for every phase that exposes a capability. Apply `engineering:git-branching` to map large phases
   into reviewable PR slices before implementation: purpose, actual base/parent, dependencies, expected
   size and verification. Plan sequential delivery by default. When dependent work must begin before
   its parent lands, record why and use the required stack relationship from `git-branching`. Allocate
   checkouts for active work rather than pre-creating every planned branch. Do not equate one phase with
   one PR or defer decomposition until the accumulated implementation is ready to merge.
3. Write the owned artifact in the repository's current format. For a plan, create or update its compact
   ledger with its roadmap path and stable item key; the plan does not cite the roadmap. A standing reference
   keeps the bare-stem shape defined by `plans` and creates no competing phase owner. When the design
   changes the repository's direction, land its standing convention in the same change, as
   `engineering:docs-and-debt` requires.
4. For plan-managed work, resolve the Workflow v2 repository provider once and validate the plan, ledger,
   worktree, branch, and next action through it. When Kandev hosts the task, leave its task and session
   identifiers in Kandev.
5. Run `python -B .agents/hooks/plan_graph.py --root .` for plan and ledger
   changes and the relevant documentation checks. Enter `docs-review`, including the `plans`
   implementation-design review gate, and resolve its findings before declaring the artifact
   implementation-ready. Correct structural, ownership, and pre-launch policy errors immediately.
6. Checkpoint only the material authored state. Planning-only work carries standing authorization to run its
   documentation review and land through `merge-docs`. A live delivery restriction overrides that standing
   authorization: preserve an explicit current user limitation, repository authorization, security or
   validation hold, merge hold, or stop class as a typed delivery gate. With no live restriction, never report
   completion at a local commit, pushed branch, or open PR. Planning plus implementation transfers ownership
   to the executor selected by the readiness decision without a routine continuation prompt.

Use the Workflow v2 dispatch/result and provider/state envelopes in `.agents/workflows/contract/v2` when
present, or the packaged `../../workflows/contract/v2` bundle. A subordinate may return evidence, never phase
design, architecture, prioritization, or the final plan.

## Terminal result

Return a completed planning outcome only after the design artifact and any owning ledger are merged to the
default branch, naming their validation, review, PR, and merge commit, plus whether implementation authority
was present. Otherwise return one typed human, dependency, or delivery gate with its owner, required action,
evidence, and observable resume condition. Do not implement under planning-only authority or expose internal
agent transcripts.
