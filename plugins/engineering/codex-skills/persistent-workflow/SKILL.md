---
name: persistent-workflow
description: Keep one Codex Desktop PR delivery alive across delayed CI, review, queue, and merge transitions with one same-chat Scheduled Task bound to the owning local project and worktree. Use after remote work has a real future decision; not for ordinary foreground implementation or terminal-only Codex.

kind: workflow
domain: process
---

# Codex persistent workflow

Read and follow the [canonical shared definition](../../.agents/engineering/workflow/persistent-workflow/SKILL.md) first.

Read `engineering:persistent-delivery` before creating or changing persistent work. It supplies the shared binding,
decision router, debug dispatch, review, repair, authorization, and terminal rules.

## Capability gate

Use a Scheduled Task attached to this owning Codex/ChatGPT Desktop conversation with its local project and
absolute worktree selected. The task must return to this same chat and its existing context. A terminal
process, shell watcher, hook, background command, ordinary model turn, new chat, or web task is not this
continuation.

If the current product surface cannot list, create, update, and remove same-chat Scheduled Tasks, stop with
`product-capability-unavailable`. Name the missing Scheduled Tasks capability, the bound PR/head/worktree,
and the observable product change that permits resumption.

## Keep one task and rebind it

Compute a standalone delivery owner from repository owner/name, PR number, absolute worktree, and branch. A
plan-managed chain instead uses repository, workflow ID, and state artifact so the same task survives an
expected successor transfer. List existing
tasks before creating one. More than one match is a duplicate-continuation decision; zero means create one and
one means update it. The current full remote head is the binding revision, not a reason to create another task.
`.agents/hooks/forge_poll_gate.py` backs the polling rule: one authoritative `gh` status read per wake and
one `.agents/workflows/workflow_ops.py monitor` process per exact PR/run identity. The monitor persists its
binding and observations across reconnects; repeated model-turn reads of unchanged state are blocked.

Write the binding with `python .agents/workflows/workflow_ops.py --workflow-run-id <id> delivery-bind` as
`persistent-delivery` describes, refresh it whenever this owner rebinds to a new head, and
`delivery-release` it at any terminal. `.agents/hooks/persistent_workflow_merge_gate.py` refuses
`gh pr merge … --auto` on a PR whose checks or queue have not settled unless that file exists and matches —
so bind the task before arming any unattended auto-merge.

**Codex binds in-procedure, not on a hook.** Claude registers `delivery_binding_gate.py` on its tool-result
event so a `gh pr create` binds by itself; Codex exposes no result event, the same limitation that keeps
`red_run_gate.py` unwired there. So run `delivery-bind` as the last step of `open-pr`, every time, and treat
a PR with no binding as an unowned delivery rather than a normal state.

Where the Scheduled Tasks surface is unavailable, `pwsh "../../.agents/engineering/workflow/persistent-workflow/scripts/delivery-continuation.ps1" register -Harness
codex` registers the equivalent operating-system task, which drives the same binding through `codex exec` in
the owning worktree.

After this owner pushes one stable repair, update that same task with the new full SHA and exact check/run IDs.
An external head replacement ends ownership and removes the task. An intermediate plan merge closes its PR
binding, resumes the recorded plan stage, and rebinds this same task to the successor PR; it does not create a
second task. Remove the task, and delete `.agents/persistent-workflow-binding.json`, on a terminal merge,
closure, supersession, missing merge authorization, exhausted model route, or any genuine human gate.

Fresh debug and review contexts are native agent dispatches. Never simulate them by macro-typing `/clear`,
opening another top-level chat, or pasting a prompt through keyboard control. When the Spark review model is
unavailable, dispatch Terra as the declared fresh-context review fallback over the same frozen SHA and record
both models. A Spark quota or capacity failure closes that dispatch before a fresh Terra dispatch begins. If
Terra is unavailable too, stop at `model-unavailable`. Sol is reserved for strategic or critical evidence,
not ordinary review availability.

## Scheduled continuation prompt

Replace every bracketed value before scheduling:

```text
Continue exactly this delivery owner until its terminal condition.

Repository: [owner/name]
PR: [URL and number]
Worktree: [absolute path]
Branch: [branch]
Bound remote head: [full SHA]
Pending evidence: [each exact check ID, run ID, and full head SHA]
Review work order: [path and ordered review stages]
Reviewed-SHA watermark: [full SHA or pending]
Merge authorization: [absent | auto | merge, with the exact recorded instruction delivery-bind resolved]
Completion condition: [explicit condition]
Workflow handoff: [none | workflow ID, state artifact, and next stage]

On every wake, read authoritative forge state once and route it through the shared persistent-delivery
decision contract. Reject another PR or head. Unchanged state produces no report or mutation. Keep
`.agents/persistent-workflow-binding.json` at the worktree root in step with this binding.

For an exact-head failure, classify its tier and open one fresh implementation context with the selected
debug skill, the complete binding, exact failed check/run IDs, remote failure signature, and focused repair
condition. Validate the returned evidence, commit and push one stable repair, then update this Scheduled Task
and the binding file to the new head and runs.

For a green exact head, obtain independent current-head review. Address findings and renew the watermark.
Enter merge only when the recorded authorization permits it. Never approve, merge, enable auto-merge,
deploy, delete, widen scope, or create another continuation without authority.

On an intermediate merge with a workflow handoff, close the completed PR binding, checkpoint it, resume the
recorded next stage through plan-execution, create the successor delivery, and update this same Scheduled Task
to its exact PR/head/worktree/check binding. The successor has independent review and authorization gates.

On terminal merge, closure, supersession, external head replacement, missing authorization, exhausted
product/model/role capability, or another genuine human gate, remove this task, delete
`.agents/persistent-workflow-binding.json`, record the final binding and decision, and stop.
```
