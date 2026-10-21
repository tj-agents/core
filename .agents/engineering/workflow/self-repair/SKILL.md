---
name: self-repair
description: Repair, in the current session, the consumed Core standard that caused or failed to prevent an agent mistake the user called out. Use when a user identifies an agent mistake and the governing standard, skill, hook, workflow, or host enforcement may have caused or failed to prevent it.

kind: workflow
domain: process
---

# Repair a Core-caused agent mistake

Own the standards-repair response when a user identifies an agent mistake and a consumed Core standard,
skill, hook, workflow, or host enforcement may have caused or failed to prevent it. This workflow does
not replace the active user task: answer the user's direct question first, keep that task's owner and
writer lease, then repair the standard in this session.

## Shared agent-lifecycle failures

A shared agent-lifecycle failure that makes ownership, completion, handoff, or cleanup untrustworthy is
P1 by default. Before repairing, use `machine:recover-agents` to check for a verified live owner of the
same repair; reconcile with that owner rather than duplicating it. Until the causal correction is
verified or the user explicitly defers it, the originating session pauses unrelated work and new
launches; repair and preservation actions may continue.

## Establish the repair boundary

1. Identify the governing Core behavior and the observed mistake. Read the directly governing source and
   distinguish a missing rule, an ambiguous rule, absent host enforcement, or an ignored but enforceable
   rule. A user callout is evidence to investigate, not permission to blame the user or close the issue
   with an apology.
2. Respect explicit user limits. Do not create a repair for an explicitly rejected change, and do not
   silently widen the repair into product work, profile installation, destructive cleanup, or unrelated
   standards redesign.
3. Select `work-items:write-bug`, `work-items:write-mistake`, or `work-items:write-debt` for the
   observed problem and update its canonical record. If the same source repair has a live canonical owner,
   reconcile that owner and contribute the new evidence without creating a duplicate writer.

## Repair it here

Fix the standard in the current session. When the current checkout belongs to unrelated work, make the
repair in its own worktree of the source repository from its current default branch; otherwise continue in
the current checkout. Hand the repair off only when the user asks. A blocker that stops the repair is
recorded with its resolver and resume condition. Then resume the original task.

This standing authorization covers the bounded Core repair through implementation, tests, review, pull
request, merge, and publication once the source repository's gates pass. It does not authorize installing
into a consuming repository, publishing outside the source repository, destructive operations, or work
excluded by an explicit user limit.

## Preserve existing delivery ownership

When the user asks to wait for or monitor an existing pull request or delivery, treat that request as
monitoring-only. Resolve and observe the existing delivery identity without changing its worktree, branch,
binding, head, review, queue state, or merge state. Do not take it over, rebase it, push to it, arm or
cancel auto-merge, or merge it merely because its work overlaps the source repair.

Monitoring does not grant delivery authority. A change of delivery owner or merge state requires explicit
delivery authority for that exact delivery plus its existing ownership transfer procedure. Standing
auto-merge authorization applies only after the resolved delivery owner has reached its own review and
check gates; it never authorizes taking over an unrelated pending delivery.

## Completion

The callout response is complete when the standard is repaired, tested and committed, or its blocker is
recorded, and the original task has resumed. A source change does not alter instructions already loaded in
the originating session.

## Example

```text
The user reports that an agent created a second bug record after a repair already had an owner. Inspect the
governing recording guidance, reconcile the existing Work Items record, and repair the source rule that
failed to require that reconciliation. Test the guidance change in Core, record the evidence on the selected
mistake item, and resume the user's original task without taking over an unrelated pending PR.
```
