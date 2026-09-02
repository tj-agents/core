---
name: continue-roadmap
description: Compatibility entry for asking what to plan next on an epic roadmap. Resolve one implementable unowned roadmap item, then enter plan-authoring; do not resume an existing plan, execute implementation, or reconcile roadmap facts already owned by update-roadmap.
domain: process
---

# Select a roadmap item for plan authoring

This public name owns only the special selection stage before
[`plan-authoring`](../plan-authoring/SKILL.md). It creates no competing authoring or execution lifecycle.

## Resolve one item

1. Read the repository instructions, [`plans`](../plans/SKILL.md), the roadmap, and any named preference.
2. Classify every outstanding item against real ledgers, branches, worktrees, pull requests, dependencies,
   and exact producer artifacts:
   - in flight: report its existing owner; enter
     [`plan-execution`](../plan-execution/SKILL.md) only when the original request explicitly authorizes
     implementation or resumption;
   - implementation-blocked: name the blocker and owner;
   - implementable but delivery-gated: local planning and implementation may proceed with the delivery gate;
   - ready and unowned: eligible for selection.
3. A natural-language preference selects its matching item only when that item is implementable. With no
   preference, present all implementable candidates with one recommendation and obtain the user's product
   choice. Never infer priority from checklist order alone.
4. Resolve or assign the stable roadmap item key. Enter `plan-authoring` with the selected item, roadmap
   evidence, dependency state, and the original authorization boundary. A status or planning-only request
   never gains implementation authority merely because the selected item is already in flight.

Planning-only selection creates no delivery worktree. When the original request also authorizes execution,
`plan-authoring` transfers the valid plan identity to `plan-execution` in the same parent. Roadmap fact
reconciliation remains with [`update-roadmap`](../update-roadmap/SKILL.md).

Return the completed planning outcome or one typed selection/dependency gate. Do not implement directly,
duplicate an in-flight plan, or stop between selection and authorized plan authoring.
