---
name: persistent-workflow
description: Keep one Claude PR delivery alive across agent turns, delayed CI, session resume, and cross-restart scheduling by using each native Claude mechanism only for its supported lifetime. Use after remote work has a real future decision; not for ordinary foreground implementation.
route: infer
---

# Claude persistent workflow

Read `persistent-delivery` before creating or changing persistent work. It supplies the shared binding,
decision router, debug dispatch, review, repair, authorization, and terminal rules.

## Keep the mechanisms separate

- `/goal` starts another agent turn when the previous turn ends until its completion condition holds. One goal
  may be active per session. It does not wait for delayed CI independently of a running session.
- `/loop` schedules prompts while the session stays open. Monitor or Channels react to delayed output or
  pushed events in a running session. Background Bash and Monitor state are not restored on resume.
- `--resume`, `--continue`, or `/resume` restores the supported conversation state. An active goal and an
  unexpired session task may return; restoration is not an independent wake mechanism.
- Desktop scheduled tasks run independently of an open session and may use the owning local worktree while
  the machine is on. Cloud Routines run independently on Anthropic infrastructure against remote state or a
  fresh clone, not uncommitted local worktree state.
- Dynamic Workflows orchestrate large in-session stages and subagents. They do not wake a stopped session
  across restarts and are not a declarative `workflows` payload in Claude's plugin format.

Use one Desktop scheduled task when continuation must mutate the exact local worktree after the terminal or
app closes. Use a cloud Routine only when every required input and write target is remote and a fresh clone is
safe. If neither supported surface is available for the binding, stop with
`product-capability-unavailable`.

## Goal evaluator prerequisite

Claude evaluates `/goal` with its configured small/background model, which defaults to Haiku independently
of normal subagent routing. Before using `/goal`, require `ANTHROPIC_DEFAULT_HAIKU_MODEL` to resolve to a
Sonnet model. If it does not, stop with `goal-evaluator-model-unavailable`; do not claim the workflow is
Haiku-free. The repository project setting supplies this mapping, while an installed plugin consumer must
supply an equivalent user, project, managed, or provider configuration.

## Own one continuation

Bind repository owner/name, PR URL/number, absolute worktree, branch, full remote head, every exact check and
run ID with its head SHA, review work order and reviewed-SHA watermark, recorded merge authorization, and the
explicit completion condition. Reuse one goal, loop/listener, Desktop task, or Routine for that owner. Never
create a duplicate monitor or recursively start another workflow.

For a plan-managed chain, bind repository, workflow ID, state artifact, and next stage as the stable
continuation owner. An intermediate merge closes only the current PR binding, resumes that stage through
`plan-execution`, and rebinds the same continuation to the successor PR. Each successor gets new exact-head
checks, review, and merge authorization; an earlier PR's authorization does not silently carry forward.

A local `/goal` may drive immediate implementation turns. A `/loop`, Monitor, or Channel may wake the open
session on delayed state. Cross-restart delivery uses the single Desktop task or Routine. After this owner
pushes one stable repair, rebind the existing continuation to the new SHA and exact runs. An external head
replacement stops ownership.

On an exact-head failure, classify the tier through `persistent-delivery` and dispatch one fresh Sonnet
implementation context with the selected debug skill, complete binding, exact failed run evidence, and error
signature. The parent validates its structured repair evidence, owns the commit and push, and updates the
continuation. Dynamic Workflows may orchestrate these stages when the product capability is available, but
the parent remains the workflow owner and the scheduled/listener mechanism remains the wake owner.

Fresh contexts use Claude's Agent or Dynamic Workflow dispatch, not keyboard control, `/clear`, or pasted
prompts.

Stop the listener, clear the goal, and remove the Desktop task or Routine on a terminal merge, closure, supersession,
external head replacement, missing merge authorization, a model/role/product capability decision, or any
genuine human gate. Unchanged forge state produces no report, mutation, or replacement continuation.
