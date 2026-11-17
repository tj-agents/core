---
name: continue
description: Establish a supported later wake for an existing authorized goal. Use only when the user asks for unattended or delayed progress; workflow:run keeps the goal.
kind: workflow
domain: process
---

# Continue an authorized goal

Owns establishing the next supported wake for the existing `workflow:run` goal when the user asks for
progress without them. It keeps that goal, its acceptance, authority and single owner. Rebuild missing
context through `workflow:resume` first.

- A deferred command or result in this conversation goes to `agent:listen`; reuse its watcher rather than
  another polling loop. Short inline work needs no scheduler.
- Use the host's native goal mechanism or its supported scheduling interface, within the user's limits on
  sessions, schedulers and child processes. A timer or notification is evidence to evaluate, never
  authority.
- Before switching mechanism, reconcile the existing owner and registration; refuse an ambiguous transfer.
- Claim unattended progress only after the interface is established and a real wake is observed; a
  session-local loop ends with its session. Without the capability, continue in the foreground and record
  the resolver and resume condition.
- For unattended delivery of a software PR, read [unattended software delivery](references/delivery.md).
  It is the only route to the Codex CLI continuation runtime.

```text
Goal: finish a research report once a source export exists; the user asks to be left to it.
Wait: give the export watcher to agent:listen for this conversation.
Later: establish the host's supported scheduled wake with the same goal and authority.
On wake: read the changed evidence and return to workflow:run until acceptance is observed.
```
