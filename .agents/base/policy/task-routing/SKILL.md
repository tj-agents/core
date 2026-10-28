---
name: task-routing
description: Choose the selected task operation while preserving authority and the existing goal. Use when receiving a substantive planning, execution, status, recovery or transfer request.
kind: policy
domain: behavior
---

# Route a task

Choose the qualified advertised owner for the request and preserve its existing goal and authority.

1. Route planning or design-only work to `workflow:plan`; it grants no implementation authority.
2. Route authorized sustained or multiphase work to `workflow:run`, with or without a named plan. Keep the same goal through commits, phases and context changes.
3. Route explicit reconstruction or resumption after interruption to `workflow:resume`; ordinary ongoing work stays with `workflow:run`.
4. Route open-work and progress queries to `workflow:status`; route an explicit handoff to `workflow:handoff`. A prompt-only request does not launch a process.
5. Use the appropriate selected operation directly for quick answers and one-step tasks. Selected Engineering owns software implementation, diagnosis, review and delivery; Workflow has no generic review operation.
6. Resolve and load the qualified advertised skill. If Workflow is unavailable, report the concrete missing selection or capability, preserve the goal and continue independent authorized work. Do not fall back to retired lifecycle names, invent availability, install a package, or treat selection as activation.

This establishes no scheduler, enforcement, authority, or continuation.

```text
Request: plan the migration
Route: workflow:plan. Produce the authorized planning artifact; do not implement migration files.

Request: implement the migration through completion
Route: workflow:run. Retain the current goal and continue authorized work through its acceptance condition.
```
