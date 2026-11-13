---
name: plan
description: Design substantive work and produce its implementation-ready canonical plan. Use when asked to plan, phase, design, revise a substantive plan or choose what to plan next.
kind: workflow
domain: process
---

# Plan substantive work

Owns designing work and its one canonical plan, kept through `workflow:plan-artifacts`. Planning grants no
implementation authority; a ready verdict adds none.

- Before exploring, resolve the goal and its existing owner. Follow-ups and revisions stay with that owner
  and its plan.
- A fresh context that returns a result here is a native subagent; a transfer of responsibility is
  `workflow:handoff`, which owns decision provenance for both. Resuming or forking an earlier conversation
  is not a fresh context.
- Apply `base:solution-assessment` before selecting a reusable mechanism the user did not prescribe.
- The plan holds the outcome, constraints, evidence, scope, acceptance, unresolved decisions with their
  resolvers, dependency order and one next action. Return its absolute clickable path.
- When execution is authorized, the owner normally stays and continues through `workflow:run`; record no
  route. Work needing another lane goes to a bounded native subagent the owner integrates. Transfer the
  owner only for a real handoff, recording why and the selected lane.
- An explicitly requested handoff of unresolved architecture goes straight to `workflow:handoff` with its
  objective, constraints and open questions; it needs no ready plan.
- Asked what to plan next: reconcile live owners and dependencies, report existing work, present
  implementable choices with a recommendation and ask only for a genuinely missing product choice. List
  order is not priority.

```text
Input: while implementing billing, get a fresh assessment of its cache design and use the result here.
Route: native subagent; this owner keeps billing and its plan.
Input: revise the cache plan, whose planning owner already exists.
Route: that owner and plan; no second planning session.
Input: the user requested a plan only, and it is ready.
Route: return the plan's absolute path; nothing is implemented or transferred.
```
