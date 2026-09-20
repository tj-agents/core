---
name: persistent-workflow
description: Keep one Claude PR delivery alive across agent turns, delayed CI, session resume, and cross-restart scheduling by using each native Claude mechanism only for its supported lifetime. Use after remote work has a real future decision; not for ordinary foreground implementation.

kind: workflow
domain: process
---

# Claude persistent workflow

Read and follow the [canonical shared definition](../../../.agents/engineering/workflow/persistent-workflow/SKILL.md) first.

Read `engineering:persistent-delivery` before creating or changing persistent work. It supplies the shared binding,
decision router, debug dispatch, review, repair, authorization, and terminal rules.

## Keep the mechanisms separate

- `/goal` starts another agent turn when the previous turn ends until its completion condition holds. One goal
  may be active per session. It does not wait for delayed CI independently of a running session.
- `/loop` schedules prompts while the session stays open. Monitor or Channels react to delayed output or
  pushed events in a running session. Background Bash and Monitor state are not restored on resume.
- `--resume`, `--continue`, or `/resume` restores the supported conversation state. An active goal and an
  unexpired session task may return; restoration is not an independent wake mechanism.
- Claude Code's own scheduler is session-scoped whatever a durability flag claims: its jobs are held in
  memory and are gone when the session exits. It is not a cross-restart surface.
- Desktop scheduled tasks run independently of an open session and may use the owning local worktree while
  the machine is on. Cloud Routines run independently on Anthropic infrastructure against remote state or a
  fresh clone, not uncommitted local worktree state.
- An operating-system scheduled task is the cross-restart surface for Claude Code itself, which has no
  desktop scheduler of its own. `pwsh "../../../.agents/engineering/workflow/persistent-workflow/scripts/delivery-continuation.ps1" register` builds one from the
  binding artifact and drives the delivery through `claude -p` in the owning worktree; `remove` is what a
  terminal owes. Its identity is the delivery owner, so a rebind updates that task rather than adding a
  second.
- Dynamic Workflows orchestrate large in-session stages and subagents. They do not wake a stopped session
  across restarts and are not a declarative `workflows` payload in Claude's plugin format.

Use the operating-system scheduled task, or one Desktop scheduled task, when continuation must mutate the
exact local worktree after the terminal or app closes. Use a cloud Routine only when every required input and
write target is remote and a fresh clone is safe. If no supported surface is available for the binding, stop
with `product-capability-unavailable`.

## Goal evaluator prerequisite

Claude evaluates `/goal` with its configured small/background model, which defaults to Haiku independently
of normal subagent routing, so `/goal` needs `ANTHROPIC_DEFAULT_HAIKU_MODEL` to resolve to a Sonnet model.
**Prove it rather than assume it:**

```bash
python .agents/workflows/workflow_ops.py --workflow-run-id <id> goal-preflight
```

It reports the value this session actually resolved and every persisted scope a fresh session would read,
and exits non-zero with `goal-evaluator-model-unavailable` when either is missing — a value that is live but
unpersisted passes no differently from one that is absent, because the next session would lose it. Stop on
that code; do not claim the workflow is Haiku-free without it. The repository project setting supplies the
mapping here; `scripts/provision-agents.ps1` writes it at user scope so an installed-plugin
consumer gets it from the install rather than a per-machine hand edit.

## Own one continuation

Bind repository owner/name, PR URL/number, absolute worktree, branch, full remote head, every exact check and
run ID with its head SHA, review work order and reviewed-SHA watermark, recorded merge authorization, and the
explicit completion condition. Reuse one goal, loop/listener, Desktop task, or Routine for that owner. Never
create a duplicate monitor or recursively start another workflow. `.agents/hooks/forge_poll_gate.py` backs
this: it permits one authoritative `gh` status read per wake and one
`.agents/workflows/workflow_ops.py monitor` process per exact PR/run identity. The monitor persists its
binding and observations across reconnects; repeated model-turn reads of unchanged state are blocked.

Write that binding with `workflow_ops.py delivery-bind` as `persistent-delivery` describes, refresh it
whenever this owner rebinds to a new head, and `delivery-release` it at any terminal.
`.agents/hooks/persistent_workflow_merge_gate.py` refuses `gh pr merge … --auto` on a PR whose
checks or queue have not settled unless that file exists and matches — so bind the continuation before
arming any unattended auto-merge.

**A PR opened here is bound without being asked.** `.agents/hooks/delivery_binding_gate.py` runs
`delivery-bind` on a successful `gh pr create` in a repository that records a standing instruction, then
tells this session to give the binding a continuation. Entering this skill is that continuation, not a
second owner — never bind again on top of it.

For a plan-managed chain, bind repository, workflow ID, state artifact, and next stage as the stable
continuation owner. An intermediate merge closes only the current PR binding, resumes that stage through
`plan-execution`, and rebinds the same continuation to the successor PR. Each successor gets new exact-head
checks, review, and merge authorization; an earlier PR's authorization does not silently carry forward.

A local `/goal` may drive immediate implementation turns. A `/loop`, Monitor, or Channel may wake the open
session on delayed state. Cross-restart delivery uses the single operating-system task, Desktop task, or
Routine. After this owner pushes one stable repair, re-run `delivery-bind` and `../../../.agents/engineering/workflow/persistent-workflow/scripts/delivery-continuation.ps1
register` so the continuation follows the new SHA, exact runs, and freshly resolved authorization. An
external head replacement stops ownership.

On an exact-head failure, classify the tier through `persistent-delivery` and dispatch one fresh Sonnet
implementation context with the selected debug skill, complete binding, exact failed run evidence, and error
signature. The parent validates its structured repair evidence, owns the commit and push, and updates the
continuation. Dynamic Workflows may orchestrate these stages when the product capability is available, but
the parent remains the workflow owner and the scheduled/listener mechanism remains the wake owner.

Fresh contexts use Claude's Agent or Dynamic Workflow dispatch, not keyboard control, `/clear`, or pasted
prompts.

Stop the listener, clear the goal, remove the scheduled task or Routine (`../../../.agents/engineering/workflow/persistent-workflow/scripts/delivery-continuation.ps1
remove`), and run `delivery-release --reason <terminal>` on a terminal merge, closure, supersession,
external head replacement, missing merge authorization, a model/role/product capability decision, or any
genuine human gate. Unchanged forge state produces no report, mutation, or replacement continuation.
