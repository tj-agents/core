---
name: plan
description: Design substantive work and produce its implementation-ready canonical plan. Use when asked to plan, phase, design, revise a substantive plan, or choose what to plan next.
kind: workflow
domain: process
---

# Plan substantive work

Read `workflow:plan-artifacts` and use a selected technical discipline conditionally. Standalone work needs
no repository, roadmap, or ledger.

Before exploration or design, resolve the goal and existing owner. Same-goal follow-ups and plan revisions
stay with their existing planning owner and canonical plan. Apply `workflow:handoff`'s ownership boundary
when selecting a context: use a native subagent when the owner needs a fresh planning context and a result
back; use handoff only for an actual transfer of responsibility. A fresh recipient proceeds without another
transfer. Resuming or forking an earlier conversation does not establish a fresh planning context. Carry
planning inputs under that skill's decision-provenance rules for either form of delegation.

Before selecting a reusable tool, infrastructure capability, or general technical mechanism, explicitly
load `base:solution-assessment` and apply it against the actual requirements. Carry a completed assessment
forward only when it belongs to this same idea.

Own the outcome, constraints, evidence, scope, acceptance, unresolved decisions and resolvers, reviewable
dependency order, readiness, and one next action. Keep one canonical Markdown artifact and return its absolute
clickable path. Preserve publication and installation limits. Planning-only work returns its authorized
artifact, outcome evidence, remaining authority, and any typed gate; a ready verdict adds no authority.

For authorized execution after planning, choose one of two routes. Record a short reason, the lane selected
through `agent:lanes`, and the next authorized action in the existing canonical goal or readiness section. Judge
ownership, usable context, and remaining work; a lane or cost change alone does not select a handoff.

1. **Retain owner:** keep the same canonical goal and plan, and continue in the same session when suitable.
   When authorized implementation needs a different lane, use a bounded native lane subagent. The parent
   integrates, verifies, and accepts its result and remains the goal owner.
2. **Transfer owner:** hand the agreed implementation-ready plan and explicitly authorized implementation
   to one successor at the selected lane through `workflow:handoff`'s verified execution pickup procedure.
   That skill owns pickup, first-action evidence, and the conditions for release and invoking `agent:close`.
   A recipient begins the agreed next action rather than recursively handing off to change lane.

For an implementation transfer, the canonical goal or existing progress owner must contain
`## Execution readiness` with authority provenance, source and standards references, constraints, budgets,
stop and escalation conditions, execution lane, transfer reason, exact next action, and a ready verdict with
evidence or an unresolved decision with its resolver. Selected Engineering software details such as checkout,
branch, review, graph, and delivery belong to `engineering:plans`.

A ready transfer means the successor can begin the authorized next action without deciding unresolved
architecture. Send an explicitly requested unresolved-architecture handoff immediately to `workflow:handoff`
from a verified repository checkout or non-repository task directory, with its objective, constraints, and
open questions; do not require a ready verdict or receipt for that dispatch-first path.

When asked what to plan next, reconcile selected live owners and dependencies, report existing work, present
implementable choices with a recommendation, and obtain a genuinely missing product choice. Do not infer
priority from list order or turn planning into implementation. `engineering:update-roadmap` owns selected
Engineering roadmap fact reconciliation.

```text
Input: while implementing billing, get a fresh assessment of its cache design and use the result here.
Route: native subagent returns the assessment; this owner retains billing and its canonical plan.
Input: transfer a separately authorized cache migration to an independent owner through completion.
Route: workflow:handoff in bounded side-workstream mode; billing stays with its owner.
Input: revise the same cache plan, whose planning owner already exists.
Route: reuse that owner and canonical plan; no duplicate planning session.
Input: an authorized parser implementation needs an L4 slice; this parent will integrate and accept it.
Route: retain owner; use a bounded native L4 subagent and continue the same goal here.
Input: the user requested a plan only, and the plan is ready.
Route: return the plan; no implementation or implementation transfer is authorized.
```
