---
name: write-story
description: Record a user-centred product outcome with its user benefit and observable acceptance criteria in the repository's selected tracker. Use when logging a story for later work; recording does not start implementation.

kind: convention
domain: process
---

# Record a story

Read [the shared record contract](../../resources/problem-records.md). Follow its repository selection
and reconciliation procedure. Record the user, requested outcome, user benefit, scope, exclusions,
acceptance criteria, owner, priority, dependencies and supporting source links. Keep unknown details
explicit. Use the provider's Story template and validation rather than hand-writing its body.

Reconcile an existing story, goal, session or PR before creation; append clarified user benefit or
acceptance criteria to that canonical story. A substantial design plan stays in source and links to the
selected item. Keep the item's state and delivery links current as work proceeds, and close only after
its acceptance criteria have observed verification. Recording grants no implementation or publication
authority beyond the request. Use `engineering:feature` or `engineering:plan-execution` only when
execution is separately authorized.

Without a selected provider, use the repository's declared story or product-backlog convention and
preserve its identities. If none exists, retain the request in the current task context and ask for its
intended owner; do not record it as a task, adopt a tracker, or create a new backlog convention merely
to record it. Employer-specific work item creation remains with that repository's authorized tooling.
