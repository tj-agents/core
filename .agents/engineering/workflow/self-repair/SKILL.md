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

## Shared agent-lifecycle failures

A shared agent-lifecycle failure that makes ownership, completion, handoff, or cleanup untrustworthy is
P1 by default. Before dispatching, use `machine:recover-agents` to check for a verified live causal
repair owner; reconcile that owner rather than dispatching a duplicate. Until the causal correction is
verified or the user explicitly defers it, the originating session pauses unrelated work and new
launches; repair and preservation actions may continue. Other mistakes use the independent-work route
below.

## Establish the repair boundary

1. Identify the governing Core behavior and the observed mistake. Read the directly governing source and
   distinguish a missing rule, an ambiguous rule, absent host enforcement, or an ignored but enforceable
   rule. A user callout is evidence to investigate, not permission to blame the user or close the issue
   with an apology.
2. Respect explicit user limits. Do not create a repair for an explicitly rejected change, and do not
   silently widen the repair into product work, profile installation, destructive cleanup, or unrelated
   standards redesign.
3. Select `engineering:write-bug`, `engineering:write-mistake`, or `engineering:write-debt` for the
   observed problem and update its canonical record. If the same source repair has a live canonical owner,
   reconcile that owner and contribute the new evidence without creating a duplicate writer. A verified
   closed context resumes only through its supported open skill. Otherwise record the bounded Core defect,
   its authority, source context, expected completion, exact isolated checkout, and one next action in a
   canonical goal or plan. Before launch, that goal records `Repair workflow: engineering:self-repair`,
   the affected `Source owner`, and the callout's session, nonce, and prompt SHA-256 so the host gate can
   bind a successful launcher receipt to this exact repair.

## Hand off the source repair

Use `engineering:handoff` in bounded side-workstream mode after it admits the repair. The repair gets an
isolated Core checkout and one selected successor; the originating session retains its original goal and
continues only independent work. Shared agent-lifecycle failures follow the exception above. A
capability, dependency, conflict, or capacity obstacle is recorded as a linked deferred disposition with
its resolver and observable resume condition. The handoff is complete
only when the native launcher reports successful submission. A skill load, prompt text, collaboration
worker, claimed intent, or failed launcher is not a handoff.

If the launcher fails, preserve the canonical repair goal and report the actual capability failure. Do not
claim that the repair was handed off, do not create a second successor, and do not allow that failure to
silently discharge the active repair obligation. Resume the original task only where its next action is
independent of the unlaunched repair and not subject to the shared agent-lifecycle exception.

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

The callout response is complete only after the bounded source repair has a verified native launch, a
verified existing owner, or a current typed deferred disposition, and the original task has a precise
independent next action. The shared agent-lifecycle exception still governs resumption after dispatch or
a deferred disposition. The successor then owns diagnosis, implementation, tests, review, delivery, and
merged publication under the recorded standards-defect authority. A source change does not alter
instructions already loaded in the originating session.
