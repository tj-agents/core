---
name: continue
description: Establish Claude continuation for an existing authorized goal whose next decision requires a later wake.
metadata:
  tj-agents-kind: workflow
  tj-agents-domain: process
---

Read the [shared continuation workflow](../../../../.agents/workflow/skills/continue/SKILL.md).
It owns goal identity, authority, existing-owner reconciliation and observed-wake requirements.

Use native `/goal` for turn-by-turn continuation. Use native `/loop` or exposed scheduling tools for
delayed checks within the supported session. For work that must survive its original application or
terminal, use a supported Desktop scheduled task or cloud routine with access to the goal and evidence.
Resume the native session when that is the intended lifecycle.

```text
/goal Finish the authorized report recorded in its canonical goal; verify its acceptance evidence.
/loop 5m Check whether the report's source export is available; continue the same goal on a change.
```

Verify permissions, checkout or artifact access and an actual wake before claiming unattended progress.
A local loop does not prove execution after session exit. Continue independent foreground work when the
required native surface is unavailable. Do not initialize an external supervisor or system scheduler for
Claude. Reconcile exact existing external registrations before claiming their native migration complete.

Software delivery additionally loads `engineering:persistent-delivery` for its existing PR and authority
contract. Other goals retain their own acceptance criteria.
