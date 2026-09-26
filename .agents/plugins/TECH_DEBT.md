# Plugin host integration debt

## Codex cannot guarantee a fail-closed write boundary through plugin hooks

Codex dispatches a tool call when its `PreToolUse` hook process fails or is skipped. The Windows PowerShell shell translated a child router's exit code 2 into hook exit code 1, so live writes continued even though the router printed a deny reason. The packaged Codex adapter now returns a JSON deny response with exit code 0 and also denies when its child hook fails. A fresh candidate-package probe blocked a missing-marketplace write before file creation.

The adapter itself can still fail to start, an untrusted or disabled hook can be skipped, and some specialized tools opt out of normal hooks. Marketplace code cannot make those host paths fail closed.

Resolve when Codex provides trusted, fail-closed host policy for every local write path, including hook launch failures and specialized tools; bind the shared router to that policy and enforce a fresh-session missing-marketplace write probe as a release gate. Until then, treat the route hook as a guardrail and verify its live activation.

Upstream behavior: https://learn.chatgpt.com/docs/hooks#tool-coverage and https://github.com/openai/codex/issues/41979.