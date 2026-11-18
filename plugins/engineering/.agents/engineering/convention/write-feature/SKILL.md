---
name: write-feature
description: Record a requested new or changed product behavior with requirements, scope and observable acceptance criteria in the repository's selected tracker. Use when logging a feature for later work; implementation belongs to feature or an existing plan owner.

kind: convention
domain: process
---

# Record a feature

Read [the shared record contract](../../resources/problem-records.md). Follow its repository selection
and reconciliation procedure. Record the intended outcome, current behavior, requirements, scope and
exclusions, acceptance criteria, owner, priority, dependencies and supporting source links. Keep unknown
details explicit. Use the provider's feature template and validation rather than hand-writing its body.

Reconcile an existing feature, goal, session or PR before creation; append clarified requirements to
that canonical feature. A substantial design plan stays in source and links to the selected item.
Keep the item's state and repair/delivery links current as work proceeds, and close only after its own
acceptance criteria have observed verification. Recording grants no implementation or publication
authority beyond the request. Use `engineering:feature` or `engineering:plan-execution` only when
execution is separately authorized.

Without a selected provider, use the repository's declared feature/backlog convention and preserve its
identities. If none exists, retain the request in the current task context and ask for its intended owner;
do not adopt a tracker or create a new backlog convention merely to record it. Employer-specific work
item creation remains with that repository's authorized tooling.
