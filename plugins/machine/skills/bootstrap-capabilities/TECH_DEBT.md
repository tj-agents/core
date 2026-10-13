# Tech debt — bootstrap-capabilities

## The harness permission sync redoes its whole check on every session start

`harness_permissions_sync.py --apply` runs at every session start on both hosts. It is idempotent and
writes only on drift, but nothing short-circuits it: each start re-reads the plugin registry, every
installed `harness.json`, the settings file and the sidecar, renders every grant and compares. Measured
2026-10-08: 530–575 ms standalone, about 300 ms of it interpreter startup that `hook_dispatch` shares, so
roughly 250 ms of its own work per start.

**Resolution condition.** The sync stores a fingerprint of its inputs (registry content, each
`harness.json`, the settings file and sidecar) and returns before rendering when it matches.
