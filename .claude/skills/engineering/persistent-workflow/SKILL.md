---
name: persistent-workflow
description: Select Claude continuation for authorized work whose next decision may outlive this session.
kind: workflow
domain: process
---

Read the [shared continuation workflow](../../../../.agents/engineering/workflow/persistent-workflow/SKILL.md)
and `engineering:persistent-delivery` first. They own the canonical goal, exact delivery binding,
acceptance evidence, repair, review and authority.

Use native `/goal` for turn-by-turn continuation toward the canonical completion condition. Use native
`/loop` or the exposed scheduling tools for delayed checks within the supported session. For work that
must survive its original application or terminal, use Claude's supported Desktop scheduled task or cloud
routine with access to the required checkout and evidence. Resume or continue the native session when that
is the intended lifecycle. Preserve the exact goal and delivery identity in every scheduled instruction.

```text
/goal Finish the authorized delivery recorded in the canonical goal; require its completion evidence.
/loop 5m Check the bound PR once; route changed evidence through engineering:persistent-delivery.
```

Verify the selected native interface, permissions and actual wake before claiming unattended execution.
A local-session loop does not establish execution after that session exits. If the required native surface
cannot reach the owning checkout, preserve the concrete capability gate and continue independent authorized
work in the foreground. Do not initialize an external supervisor or system scheduler for Claude.

Existing external registrations require reconciliation of their exact owner before native adoption. This
package neither migrates nor removes a running registration; unresolved owner state prevents claiming the
migration complete. Shared completion and merge evidence still apply on every native wake.
