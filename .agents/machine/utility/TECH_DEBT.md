# Machine utility tech debt

## Handoff model routing

When neither the user nor checked-in repository policy names a model, the handoff caller has no reliable
fallback for selecting one from the work's characteristics. An open-ended research and architecture task
therefore inherited the configured default until the user manually requested Astra, making model quality
and routing depend on user intervention. Define one caller-owned routing rule that preserves explicit user
and repository policy precedence, then selects proportionately for research and judgement, ordinary
implementation, or mechanical work. Resolve this debt when the owning orchestration classifies those task
types and selects an appropriate model without routine user prompting, while both handoff launchers remain
transport only.

## In-process lane routing

Bounded, independent, low-risk work can currently be escalated to a full new-CLI handoff too
readily, even when an appropriate in-process lane could complete it without changing
active-workspace ownership. The current lanes heuristic that delegated work is mainly for
multi-turn loops and "not a one-shot" is incomplete when the alternative is a true context
handoff. Compare main-agent execution, in-process lane delegation, and context transfer
explicitly: prefer same-CLI lane delegation for bounded subtasks, and reserve a handoff or new
CLI tab for genuine active-workspace ownership transfer or context continuation. Resolve this
debt when the routing guidance reconciles that policy conflict and a representative bounded
subtask stays in the current CLI lane without an unnecessary handoff.
