# Tech debt — plugin-lock

## The harness permission sync redoes its whole check on every session start

`harness_permissions_sync.py --apply` runs at every session start on both hosts. It is idempotent and
writes only on drift, but nothing short-circuits it: each start re-reads the plugin registry, every
installed `harness.json`, the settings file and the sidecar, renders every grant and compares. Measured
2026-10-08: 530–575 ms standalone, about 300 ms of it interpreter startup that `hook_dispatch` shares, so
roughly 250 ms of its own work per start.

**Resolution condition.** The sync stores a fingerprint of its inputs (registry content, each
`harness.json`, the settings file and sidecar) and returns before rendering when it matches.

## `adopt_plugins.py` and `bump_plugin_lock.py` only handle project scope

`repo_config.py --scope local` writes uncommitted per-clone settings, but `adopt_plugins.py` and
`bump_plugin_lock.py` always plan with `scope="project"`. A clone adopted locally (the work-repository case,
where `settings.local.json` and Git excludes keep the selection out of the repository) is bumped as if it were
committed: tracked `.claude/settings.json` is rewritten and `settings.local.json` stays on the old revision.
Found by the 2026-10-15 review of the plugin-lock change; deferred because no work repository exists on this
machine and Tommy said to discuss that case later.

**Resolution condition.** Both commands take `--scope project|local` and pass it to `repo_config.plan`, a
test adopts and bumps a local-scope clone and checks that only the local files and ownership state change, and
a project-scope command refuses a clone that carries local ownership state.
