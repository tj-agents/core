# Plugin host integration debt

## Codex cannot guarantee a fail-closed write boundary through plugin hooks

Codex dispatches a tool call when its `PreToolUse` hook process fails or is skipped. PowerShell translated a child router's exit code 2 into hook exit code 1, so live writes continued even though the router printed a denial. The packaged Windows adapter now returns a JSON deny with exit code 0 and denies child failures. Fresh normal-profile Codex and Claude probes blocked a missing-marketplace write after the released hooks were active.

Codex plugin installation and updates do not trust new or changed hook definitions. A fresh v2.1.11 session wrote the disposable probe file while 13 definitions awaited review; `/hooks` trust review activated them and the repeat probe was blocked. The adapter itself can still fail to start, an untrusted or disabled hook can be skipped, and some specialized tools opt out of normal hooks. Marketplace code cannot make those host paths fail closed.

Resolve when Codex provides trusted, fail-closed host policy for every local write path, including hook launch failures, changed definitions and specialized tools. Bind the shared router to that policy and require a fresh-session missing-marketplace write probe as a release gate. Until then, verify live activation after every release that changes a hook definition.

Upstream behavior: https://learn.chatgpt.com/docs/hooks#review-and-trust-hooks and https://github.com/openai/codex/issues/41979.

## Routed skill recovery needs a host delivery proof

The router still blocks a routed write when its owning skill is absent or has no successful load
proof. Codex documents model-visible `PreToolUse` `additionalContext`, but does not specify whether
it is delivered together with a `deny` decision. An isolated CLI probe was stopped by local process
policy before its test hook ran, so it did not establish that combined behavior. The router must not
mark an injected skill as loaded on an unobserved denial or let the pending write run first.

Resolve when a trusted live Codex probe proves that a denied write delivers the complete skill body
and the next invocation can verify that delivery from the session transcript or an equivalent host
acknowledgment. Then add pinned-release install repair for genuinely absent skills and repeat the
missing-marketplace write probe without a restart.
