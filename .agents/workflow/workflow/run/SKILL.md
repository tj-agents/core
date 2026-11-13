---
name: run
description: Own authorized sustained or multiphase work through its whole requested outcome. Use when work continues across phases, commits, PRs, reviews or context changes.
kind: workflow
domain: process
---

# Run an authorized goal

Owns an authorized goal from its first action to its observed acceptance. Direct short requests stay with
their selected operation and need no plan.

## Authority and acceptance

- Deliver the whole requested outcome. The user's authorization covers every step and PR it needs; an
  agent-chosen phase, PR, handoff, brief or procedural limit never narrows it.
- The selected profile, or the user, decides how many PRs the outcome uses. Never split a cutover into
  broken intermediate states or keep the replaced capability by reclassifying it.
- Preserve explicit user holds, approvals requested for separately proposed work and repository guards.
  Engineering owns review, CI and merge checks. A required human approval is a wait on this same goal:
  resume when it is observed, without asking the user to announce it.
- A goal file records authority; it does not create it.

## Run it

Read the existing canonical goal through `workflow:plan-artifacts` and keep one next action. For software,
use `engineering:feature`, `engineering:bugfix` or the selected technical operation for each bounded
change; it returns evidence here. Apply `base:solution-assessment` before introducing a reusable mechanism
the user did not prescribe. Delegate bounded implementation or evidence through `agent:lanes` under
disjoint leases; this owner keeps design, acceptance, diagnosis and severity. For a side problem or user
callout, apply [incidental problems](../../resources/problem-records.md#incidental-problems) and keep this
goal's next action.

A local OS or missing runtime is not a blocker by itself: within existing authority, provision repeatable
validation before declaring a capability missing. Hand a deferred command to `agent:listen` before parking.
Use `workflow:continue` only when the user asks for unattended progress. After exhausting independent work,
record the blocker, resolver, unblock action and observable resume condition.

## Finish

Report the observed outcome, its validation evidence and remaining durable state. A commit, pushed branch,
open or merged PR, phase or context boundary is not completion while requested work remains, including an
authorized publication, update or installation.

```text
User: "Implement and ship the parser migration."
Profile decides one PR: the goal owns the change, its review and CI, the merge and the package update.
PR merged, update not yet observed: not complete; continue to the update.
Update observed in a fresh session: report the outcome and its evidence.
```
