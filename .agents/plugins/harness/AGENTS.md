# Harness manifests

Every command a shipped skill tells an agent to run that needs host approval is declared in its package's
manifest here, in the same change, for both hosts (`permissions.claude_allow`, `permissions.codex_prefix_rules`),
matching the exact invocation. A command agents must never run is declared the same way in `claude_deny` and
`codex_forbidden_prefix_rules`. Agent commits the declarations of every selected package into each selecting
repository's own settings during adoption and `tj install`; nothing reaches user settings. Rules are committed
literally, so a declaration naming `${PLUGIN_ROOT}` or a machine-specific absolute path is rejected: declare a
command found on PATH. `tests/test_harness_manifests.py` pins the declared inventory. Never rely on a classifier retry.

```json
"claude_allow": ["Bash(tj item:*)"], "claude_deny": ["Bash(gh auth login *)"]
```
