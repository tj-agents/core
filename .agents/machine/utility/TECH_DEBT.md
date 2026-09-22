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
