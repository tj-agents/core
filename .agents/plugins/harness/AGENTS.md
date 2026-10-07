# Harness manifests

Every command a shipped skill tells an agent to run that needs host approval is declared in its package's
manifest here, in the same change, for both hosts (`permissions.claude_allow`, `permissions.codex_prefix_rules`),
matching the exact invocation. `harness_permissions_sync.py` applies them to every installed harness at session
start, and `tests/test_harness_manifests.py` pins the declared inventory. Never rely on a classifier retry.
