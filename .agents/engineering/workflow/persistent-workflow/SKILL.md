---
name: persistent-workflow
description: Keep an authorized remote delivery owned across delayed checks using the selected host's supported continuation capability and one exact delivery identity.
kind: workflow
domain: process
---

# Persistent delivery continuation

## Completion record

Before reporting completion, maintain the canonical goal's fenced `completion` JSON with observed
acceptance evidence, every delivered PR identity, and every unresolved PR task with its owner and next
action. The shared completion check refreshes every recorded PR and rejects completion unless the bound delivery is
recorded, merged at its full head, has no unchecked tasks, and the outcome evidence is present. A rejection
keeps the current owner and leaves the returned actions open.

Before retiring recovery artifacts, reconcile and update any linked selected item through
[the shared recording contract](../../../workflow/resources/problem-records.md). Resolve it only after its own
acceptance is verified; the PR completion check alone does not close it. Preserve unresolved item
ownership and next action.

Run the same read-only check before a foreground terminal report:

Run the Python helpers with `python` on Windows or `python3` on Linux/macOS:

```bash
python -B <completion-check> --goal <absolute-goal> --root <absolute-worktree>
```

Resolve `<completion-check>` to `.agents/workflows/completion.py` in source or
`workflows/completion.py` in an installed engineering package.

The record has this exact shape. Every string is nonempty, every head is a forty-character SHA, acceptance
and delivery records are unique, and empty evidence keeps its acceptance item open with an owner and next
action.

```completion
{
  "outcome": "The requested user-visible outcome.",
  "acceptance": [
    {
      "id": "criterion-id",
      "criterion": "The observable acceptance criterion.",
      "evidence": [
        {"source": "artifact or observation", "result": "concrete observed result"}
      ],
      "owner": "current execution owner",
      "next_action": "Resolve this criterion when evidence is absent."
    }
  ],
  "deliveries": [
    {"repository": "owner/repository", "pr": 123, "head": "0123456789abcdef0123456789abcdef01234567"}
  ],
  "open_tasks": [
    {
      "repository": "owner/repository",
      "pr": 123,
      "head": "0123456789abcdef0123456789abcdef01234567",
      "text": "Unchecked visible PR task.",
      "owner": "current execution owner",
      "next_action": "Complete the task and refresh the PR."
    }
  ]
}
```

Load `engineering:persistent-delivery` for binding, review, repair, authorization and terminal behavior.
Use this workflow when a substantive authorized task has a future decision that may outlive the current
session. Its owner can begin before a PR exists. Ordinary quick answers and short inline work stay in the
foreground without a scheduler. The existing canonical goal remains the source of completion criteria and
authority; this workflow does not create a competing plan or permission.

Honor the user's limits on additional sessions, schedulers and child processes before choosing a
continuation capability. When a required wake cannot be established within those limits, continue all
authorized unblocked work in the foreground. Use the supported foreground remote monitor for an owned
delivery wait; it does not establish durable unattended continuation. Apply `workflow:run`
before ending at a genuine boundary for the remaining whole goal. A completed slice or unavailable
scheduler does not establish goal completion or a whole-goal blocker.

## Listen for the next result

Use `agent:listen` for this conversation's deferred result and completion notification.
It owns generic background execution, the host callback and existing desktop alerts. The scheduled
continuation below owns durable work separately. Keep the exact delivery identity from this workflow.

The bound run monitor returns immediately for an already-completed run. The PR monitor emits one initial
readiness observation when its nonempty exact-head check rollup is green, then suppresses unchanged
reconnects. That signal grants no review or merge approval. On a wake, route the bound result through
`persistent-delivery` and report the next gate through `engineering:open-pr`.

```text
Pending CI: give its exact-head monitor command to agent:listen.
Completion: route the returned bound result, report the PR's next gate and continue the same goal.
```

## Select native continuation

Use the host entry point's native goal mechanism for turn-by-turn continuation and its supported
scheduling interface for delayed work. Keep the same canonical goal, exact delivery binding and existing
authority on each wake. A scheduler notification is evidence to evaluate, not permission to merge.

A supported host continuation must be established and an actual wake observed before claiming unattended
progress. Honor user limits on sessions and scheduling. When a required native interface is unavailable,
continue authorized foreground work and retain the resolver and observable resume condition. The Codex
entry owns the additional durable CLI transport for work that must survive its original process.

Before switching an existing continuation, reconcile its recorded owner and registration. Preserve pending
evidence and reject an ambiguous transfer. Source packaging does not migrate a running registration or
establish installed host acceptance.

```text
CI becomes green -> wake the bound goal -> check exact-head review and merge authority.
A completed CI run alone -> retain the goal until its acceptance evidence passes completion.py.
```
