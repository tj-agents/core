---
name: session
description: Engineering session rules: whole-outcome delivery, lifecycle selection, routine-decision delegation, standards-defect repair and source ownership. Use for any engineering work.
kind: policy
domain: process
---

# Engineering session

Owns the software-specific session rules applied on top of `workflow:session`. They grant no implementation,
publication or installation authority beyond what the user and the owning repository grant.

## Deliver the whole requested outcome

The requested outcome is the unit of work. Phases, handoffs and briefs never narrow it, and a merged PR is not
completion while requested work remains. `engineering:branching` owns how many PRs carry it.

```text
Request: replace old-launch with launch across the CLI and its installers.
PR 1 merges the CLI rename; installers still call old-launch.
Result: not complete. Continue with the installers before reporting done.
```

## Select the lifecycle before the first edit

A bounded behavior change selects `engineering:feature`; a defect selects `engineering:bugfix`. Creating a PR
or editing its description enters `engineering:open-pr` first. Start each work item from a current base under
`engineering:branching`; planning-only work in the normal checkout fast-forwards a clean default branch first
and never syncs over uncommitted changes.

## Routine-decision delegation

Read `configuration.core.auto_approve` from the checkout's `.agents/settings.json`; an explicit `design`
overrides `all`. When the effective design value is true, make routine design and convention choices and state
the rationale. An explicit user reservation, task scope or stricter repository rule still controls. This grants
no merge, publication, installation or permission authority.

## Failures and standards defects

A failed CI observation requires recovery under `workflow:run`; a failed test selects
`engineering:failing-tests`. Never weaken a check to produce a pass.

When the user calls out a suspected defect in a reusable agent standard or tool, establish its source owner and
causal evidence, apply [the incidental-problems decision](https://github.com/tj-agents/core/blob/main/.agents/workflow/resources/problem-records.md#incidental-problems),
and follow that repository's repair process. A standard the agent overlooked needs a task correction, not a
source change. When an applicable standard is ambiguous or silent, propose concrete wording to the user and
continue under the existing standard meanwhile.

Give shared behavior one source owner. Before returning a terminal result, check the work against the standards
that governed it and reconcile every problem encountered: fixed, routed to an existing owner, or recorded
through the selected profile under [the shared recording contract](../../../workflow/resources/problem-records.md).
