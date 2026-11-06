---
name: plan
description: Design substantive work and produce its implementation-ready canonical plan. Use when asked to plan, phase, design, revise a substantive plan, or choose what to plan next.
kind: workflow
domain: process
---

# Plan substantive work

Read `workflow:plan-artifacts` and use a selected technical discipline conditionally. Standalone work needs
no repository, roadmap, or ledger.

Before exploration or design, resolve the goal and existing owner through `workflow:handoff`'s admission
checks. Same-goal follow-ups and plan revisions stay with their existing planning owner; reuse that owner
rather than create another plan or session. A distinct new substantive planning goal begins in a fresh
managed session through `workflow:handoff`. Use its bounded side-workstream mode when the origin retains
another active goal. A recipient already launched fresh for this planning goal proceeds without another
transfer. Resuming or forking an earlier conversation does not establish a fresh planning context.

Before selecting a reusable tool, infrastructure capability, or general technical mechanism, explicitly
load `base:solution-assessment` and apply it against the actual requirements. Carry a completed assessment
forward only when it belongs to this same idea.

Own the outcome, constraints, evidence, scope, acceptance, unresolved decisions and resolvers, reviewable
dependency order, readiness, and one next action. Keep one canonical Markdown artifact and return its absolute
clickable path. Preserve publication and installation limits. Planning-only work returns its authorized
artifact, outcome evidence, remaining authority, and any typed gate; a ready verdict adds no authority.

After planning, small and medium work normally continues inline when the same owner can safely execute the
next authorized action. For critical implementation transfer, the canonical goal or existing progress owner
must contain `## Execution readiness` with authority provenance, source and standards references, constraints, budgets,
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
Input: while implementing billing, plan an independent cache migration.
Route: workflow:handoff in bounded side-workstream mode; billing stays with its owner.
Input: a fresh recipient receives that cache-planning goal.
Route: plan here; load base:solution-assessment before selecting the cache mechanism.
Input: revise the same cache plan, whose planning owner already exists.
Route: reuse that owner and canonical plan; no duplicate planning session.
```
