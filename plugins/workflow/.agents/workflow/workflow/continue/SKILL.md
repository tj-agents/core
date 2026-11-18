---
name: continue
description: Establish a supported continuation for an existing authorized goal when its next decision needs a later wake. Use for delayed or unattended progress; workflow:run retains goal ownership and workflow:resume reconstructs interrupted context.
kind: workflow
domain: process
---

# Continue an authorized goal

Owns selecting and establishing the next supported wake for the existing `workflow:run` owner. Preserve
its canonical goal, completion criteria, authorized actions and one execution owner. Reconstruct missing
context through `workflow:resume` before scheduling more work.

```text
Goal: finish an authorized research report after a source export becomes available.
Wait: give the export watcher to agent:listen for this conversation's result.
Later execution: establish the host's supported scheduled wake with the same goal and authority.
On wake: read the changed evidence and return to workflow:run until acceptance is observed.
```

Use `agent:listen` for a deferred command or result notification in this conversation. Reuse its existing
watcher and callback rather than creating another model-driven polling loop. Short inline work needs no
scheduler.

Use the host entry point's native goal mechanism for turn-by-turn continuation and its supported
scheduling interface for delayed work. Honor the user's limits on sessions, schedulers and child processes.
A timer or notification supplies evidence to evaluate; it grants no additional authority.

Before switching continuation mechanisms, reconcile the exact existing owner and registration. Preserve
pending evidence and refuse an ambiguous transfer. Source packaging alone neither migrates a running
registration nor proves installed host acceptance.

Claim unattended progress only after the chosen interface is established and an actual wake is observed.
A session-local loop does not establish execution after that session exits. If a required capability is
unavailable, continue independent authorized work in the foreground and retain its concrete resolver and
observable resume condition under `workflow:run`.

Use the selected discipline's existing completion and delivery contract when one applies. Software remote
delivery reads `references/delivery.md` beside the selected `engineering:merge` entry for PR identity,
completion evidence, repair, review and merge authority. That package also supplies the Codex CLI transport. Other goals use their own acceptance evidence;
they do not acquire a PR requirement by selecting this skill.
