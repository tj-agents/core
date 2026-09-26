# Plugin host integration debt

## Codex cannot guarantee a fail-closed write boundary through plugin hooks

Codex reports a failed `PreToolUse` command and continues the tool call. An untrusted or disabled plugin hook may be skipped, and some specialized tools opt out of normal hooks. A live Windows probe created a file while the base router could not launch. The router correctly blocked the same write when invoked directly, and Claude blocked its live probe.

The marketplace now checks generated hook commands under the native Windows shell and provides `skill_router.py --verify-install` for both hosts. These checks prove packaging and healthy-hook behavior. They cannot make Codex reject a write when the host fails to execute its hook.

Resolve when Codex provides a trusted, fail-closed host policy for every local write path, including hook launch errors; wire the marketplace router to that policy and make a fresh-session missing-marketplace write probe a release gate. Until then, describe the router as a guardrail and require activation checks before relying on it.

Upstream behavior: https://learn.chatgpt.com/docs/hooks#tool-coverage and https://learn.chatgpt.com/docs/hooks#plugin-bundled-hooks.
