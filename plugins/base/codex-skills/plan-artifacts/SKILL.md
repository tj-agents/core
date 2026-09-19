---
name: plan-artifacts
description: Maintain one Markdown plan for a long-term goal or substantive planning request, automatically route authorized execution to its available workflow, and keep corrections and resumable progress in the same artifact.
kind: contract
domain: behavior
---

# Maintained plan artifacts

For a substantive plan intended for execution, write an actual Markdown file before presenting the plan
as ready. Follow applicable project plan conventions and an existing canonical owner; otherwise choose a
descriptive filename in the working directory. A standalone directory needs no repository, roadmap,
companion ledger, workflow provider, pull request, or publication. Quick answers and one-step tasks do
not need ceremonial plans.

Whenever you create, revise, or resume a plan, include its exact absolute path as a clickable Markdown
link in the response, including a fresh-session progress summary. A bare filename or relative link is
not enough to locate the artifact outside the session. For a path containing spaces, wrap the link
target in angle brackets. Keep the chat summary aligned with the saved file.

Apply corrections to that same canonical file: reconcile scope, decisions, sequence, and acceptance
criteria directly. Never ask the user to splice replacement paragraphs or maintain competing copies.
If the user names an existing plan, read it before changing it; resolve ambiguous ownership before
creating another. The optional [template](templates/PLAN.md) is a starting point, not a required format.

Keep current progress, useful verification evidence, unresolved decisions, and remaining work in the
canonical plan, or in its existing project-owned progress artifact where that convention applies. Before
resuming, read those artifacts and reconcile them with available evidence. Record material changes and
enough next-step context for another session to continue; do not claim unobserved work or tests passed.

Planning alone grants no implementation authority. Record the authorized scope separately from proposed
steps. A request to plan, correct a plan, or resume planning does not authorize executing it; an existing
request to implement remains valid within its scope. Neither a ready plan nor this contract authorizes
publication, installation, or other actions outside that request.

The richer `plans`, `plan-authoring`, and `plan-checkpoint` engineering conventions apply only when the
project or user selects that lifecycle. They are not prerequisites for this common behavior. Preserve
user plans when disabling or rolling back the plugin.

## Default ownership of long-term work

When a request authorizes a long-term or multi-phase goal, select the available `plan-execution`
workflow without waiting for the user to name it. Before the first deliverable edit, invoke that skill
through the host's skill tool when available (for example `base:plan-execution`), or read its advertised
SKILL.md path when skills are loaded as files. Merely announcing the workflow or following this summary
does not load its instructions.
Explicit phases or an existing goal/plan file trigger this routing even for a documentation-only task.
Read the existing goal before acting, reconcile it with the current request, and keep its progress current;
finishing deliverable files while leaving that goal stale is incomplete. Keep the same goal, authorization,
and next action through implementation, review, validation, and authorized
delivery. Follow the project's selected workflow when present. If its runtime is unavailable, keep
ownership in the current session and use the available native tools; do not invent missing providers.
Planning-only requests still end with planning, as described above.

A phase, local commit, open PR, or fresh context is an execution checkpoint, not a new permission
boundary. Record a slice as the next unit of work without silently narrowing the user's goal to that
slice. Continue while authorized work remains. Report full completion only at the user's actual outcome;
a genuine external, destructive, authorization, or unresolved ownership gate must identify the blocked
action while independent authorized work continues.

A context clear or handoff preserves the goal; it does not return orchestration to the user. Checkpoint
before transfer and invoke the available automated continuation or handoff capability, confirming the
successor was started before releasing ownership. Never launch duplicate owners. If no such capability
is available, preserve a recoverable checkpoint and state that limitation rather than claiming a transfer
occurred. A user request for only a handoff prompt does not authorize launching a session.

## Context delivery

The packaged SessionStart hook reads this file relative to its own script, including on startup, resume,
and compaction. It emits context only. It requires Python 3.9 or newer available as `python` on PATH;
the host reports a missing executable, and the helper reports an unreadable contract on stderr with a
nonzero exit. Plugin installation does not prove hook trust or execution, particularly in Codex.

When hooks are unavailable, explicitly generate the same contract as a native instruction fragment:

```text
python -B "<skill-directory>/scripts/session-context.py" --instruction-fragment
```

The command prints a source-digest-marked fragment; it writes nothing. Deliberately place or replace only
that marked block in the applicable AGENTS.md or CLAUDE.md, preserving unrelated instructions. Report
that fallback separately from hook activation. Do not install it silently in a normal profile.
