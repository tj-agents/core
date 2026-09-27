# Bounded side-workstream handoff

## Authorized scope

Implement the core workflow change requested in the handoff: while an agent is executing an active task, a distinct, independently actionable, separately authorized side workstream is handed to one successor in an isolated checkout. The original session retains and continues its original task. This includes canonical engineering guidance, the UserPromptSubmit routing trigger, focused tests, generated package output, release metadata, validation, commit, and a GitHub PR. It excludes the Sandbox HWID/WinWrap task, cpp-agents, and the pre-existing workflow-identity recorder defect.

## Design

`engineering:handoff` owns the distinction between a full transfer and a bounded side-workstream handoff. `plan-execution` routes execution to that owner without redefining the policy. The UserPromptSubmit hook selects the handoff contract when the prompt explicitly requests an active side-workstream handoff; it otherwise preserves plan-execution selection.

| Implementation area | Standards read |
| --- | --- |
| `.agents/engineering/workflow/handoff/SKILL.md` | `engineering:handoff`, `engineering:docs-and-debt` |
| `.agents/engineering/workflow/plan-execution/SKILL.md` | `engineering:plan-execution`, `engineering:docs-and-debt` |
| `.agents/hooks/workflow_route.py` and its tests | `engineering:plan-execution`, `engineering:docs-and-debt` |
| Generated packages and release metadata | `PACKAGING.md`, repository `README.md` |

The route keeps the two selections exclusive:

```python
if selects_side_workstream_handoff(prompt, cwd):
    context = load_context(Path(__file__), "engineering/workflow/handoff/SKILL.md", "engineering:handoff")
elif selects_plan_execution(prompt, cwd):
    context = load_context(Path(__file__), "engineering/workflow/plan-execution/SKILL.md", "engineering:plan-execution")
else:
    return 0
```

The side-workstream predicate requires an explicit handoff action plus wording that identifies both a distinct side workstream and an active/current/original task (or an active `GOAL.md`). This prevents explanatory and planning-only prompts from launching the routing path.

## Phases

1. [x] Update the handoff owner, plan-execution route, UserPromptSubmit hook, and focused tests.
2. [x] Regenerate package output, update the 2.1.14 release metadata and catalog digests, run focused and repository checks, review, commit, push, and open a personal GitHub PR without merging.

## Acceptance criteria

- An explicit active side-workstream handoff loads the canonical `engineering:handoff` contract rather than `plan-execution`.
- Planning-only and explanatory prompts do not select the side-workstream route.
- The canonical handoff contract preserves the parent task, prohibits duplicate writers and inseparable offloads, captures authorization/context/checkout/completion expectations, and preserves prompt-only and launcher-failure behavior.
- Generated package output, package versions, catalog digests, and host hook contracts agree with source.
