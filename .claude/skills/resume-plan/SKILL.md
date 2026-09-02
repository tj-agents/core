---
name: resume-plan
description: Compatibility entry for an explicit resume-plan invocation or legacy handoff. Resolve the named plan, ledger, or worktree and enter plan-execution; ordinary natural-language requests to implement or resume an active plan select plan-execution directly.
domain: process
---

# Resume a plan through plan execution

This public name remains for existing callers. It resolves the durable owner, then immediately enters
[`plan-execution`](../plan-execution/SKILL.md); it does not own a second execution lifecycle.

## Resolve the compatibility input

1. A named ledger resolves its `Worktree`, branch, and PR. A named plan resolves every ledger whose `Plan:`
   header points to it; a named worktree resolves the ledger it owns.
2. When exactly one owner exists, reconcile it against Git, GitHub, review state, and repository state. Restore
   its exact open branch worktree, or create the next delivery worktree from current remote default after a
   merged slice.
3. When several independent ledgers remain and no worktree was named, list their owners and next-action
   gists and obtain the missing choice. Do not guess. A legacy plan without a ledger gets the labelled
   reconstructed baseline defined by [`plan-checkpoint`](../plan-checkpoint/SKILL.md).
4. Read the full plan and ledger, validate the plan graph, then invoke `plan-execution` with the resolved
   plan identity and current Workflow v2 repository state.

All continuation, failure recovery, checkpoint, review, delivery, blocker, transfer, and terminal behavior
belongs to `plan-execution`. Do not return a routine prompt merely because resolution, a phase, a commit, or
a subordinate result completed.
