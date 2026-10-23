---
name: plan
description: Design substantive work and produce its implementation-ready canonical plan. Use when asked to plan, phase, design, revise a substantive plan, or choose what to plan next.
kind: workflow
domain: process
---

# Plan substantive work

Read `workflow:plan-artifacts`, resolve exactly one existing owner before writing, and use a selected
technical discipline conditionally. Standalone work needs no repository, roadmap, or ledger.

Own the outcome, constraints, evidence, scope, acceptance, unresolved decisions and resolvers, reviewable
dependency order, readiness, and one next action. Keep one canonical Markdown artifact and return its absolute
clickable path. Preserve publication and installation limits. Planning-only work returns its authorized
artifact, outcome evidence, remaining authority, and any typed gate; a ready verdict adds no authority.

Small and medium work normally continues inline when the same owner can safely execute the next authorized
action. For critical implementation transfer, the canonical goal or existing progress owner must contain
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
Outcome: plan the cache migration only.
Artifact: /work/repo/plans/cache/MIGRATION_PLAN.md
Next action: obtain the product choice between write-through and cache-aside.
```
