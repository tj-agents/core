---
name: plan-artifacts
description: Create, correct, or resume a substantive execution plan as one maintained Markdown artifact, including standalone planning without an engineering lifecycle.
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
