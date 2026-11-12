# Harness manifests

Every command a shipped skill tells an agent to run that needs host approval is declared in its package's
manifest here, in the same change, for both hosts (`permissions.claude_allow`, `permissions.codex_prefix_rules`),
matching the exact invocation. Agent repository preparation applies the verified selected plugins' grants
to repository-local host files. An installed cache entry does not grant permissions in another repository.
`tests/test_harness_manifests.py` pins the declared inventory. Never rely on a classifier retry.

```json
"claude_allow": ["Bash(python -B ${PLUGIN_ROOT}/workflows/completion.py)"]
```
