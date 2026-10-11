---
name: self-repair
description: Route a user callout about an agent mistake caused or not prevented by a consumed Core standard into a verified bounded Core repair handoff. Use when a user identifies an agent mistake and the governing standard, skill, hook, workflow, or host enforcement may have caused or failed to prevent it.

kind: workflow
domain: process
---

# Repair a Core-caused agent mistake

Own the standards-repair response when a user identifies an agent mistake and a consumed Core standard,
skill, hook, workflow, or host enforcement may have caused or failed to prevent it. This workflow does
not replace the active user task: answer the user's direct question first, keep that task's owner and
writer lease, then create one bounded, independently actionable Core side workstream.

## Establish the repair boundary

1. Identify the governing Core behavior and the observed mistake. Read the directly governing source and
   distinguish a missing rule, an ambiguous rule, absent host enforcement, or an ignored but enforceable
   rule. A user callout is evidence to investigate, not permission to blame the user or close the issue
   with an apology.
2. Respect explicit user limits. Do not create a repair for an explicitly rejected change, and do not
   silently widen the repair into product work, profile installation, destructive cleanup, or unrelated
   standards redesign.
3. If the same source repair already has a live canonical owner, reconcile that owner and contribute the
   new evidence without creating a duplicate writer. Otherwise record the bounded Core defect, its
   authority, source context, expected completion, exact isolated checkout, and one next action in a
   canonical goal or plan.

## Hand off the source repair

Use `engineering:handoff` in bounded side-workstream mode. The repair gets an isolated Core checkout and
one selected successor; the originating session retains its original goal and continues only independent
work. The handoff is complete only when the native launcher reports successful submission. A skill load,
prompt text, collaboration worker, claimed intent, or failed launcher is not a handoff.

If the launcher fails, preserve the canonical repair goal and report the actual capability failure. Do not
claim that the repair was handed off, do not create a second successor, and do not allow that failure to
silently discharge the active repair obligation. Resume the original task only where its next action is
independent of the unlaunched repair.

## Completion

The callout response is complete only after the bounded source repair has a verified native launch or a
typed launch-capability gate, and the original task has a precise independent next action. The successor
then owns diagnosis, implementation, tests, review, delivery, and merged publication under the recorded
standards-defect authority. A source change does not alter instructions already loaded in the originating
session.
