---
name: remote-validation
description: Split verification between workstation and CI: focused checks locally, full matrices in CI, one monitor for waits, reproduce only a failing scope. Use before pushing, waiting on CI, or on a red check.

kind: policy
domain: process
---

# Remote-first validation

Owns which checks run locally and which run in CI, the compact command boundary and the remote wait. Several
agents share one workstation: it is the inner loop, and CI is the full validation plane.

| Gate | Owner |
|---|---|
| Formatting, generators, grep/invariant checks | Local checkout |
| Smallest build covering every consumer of the change | Local checkout |
| Focused unit tests for the changed behavior | Local checkout |
| Full build, complete unit, integration and E2E matrices | CI on the exact PR head |
| Supported-platform and native-host acceptance | CI jobs that invoke the real executable |

Coverage follows what consumes the change: a changed signature is covered by building its call sites, not by
building the files you opened. Local integration and E2E runs are diagnostics after a CI failure, never routine
gates; no plan step may add one "to be safe". The exception is a path no cheaper gate executes, such as a
seeder only E2E runs: run that path once locally when a suitable environment exists, otherwise route it to CI.
Never launch local integration or E2E suites concurrently from different checkouts.

## Run commands through the compact boundary

Run every test, build, generator and remote-log command through the shared executable (`python` on Windows,
`python3` on Linux/macOS). It stores full output in repository-private Git artifacts and returns identity,
duration, exit state and, on failure, bounded failing items. `inspect` reports the checkout's branch, head,
upstream distance and dirty paths.

```bash
python .agents/workflows/workflow_ops.py --workflow-run-id 7f3a run --label unit -- uv run pytest -q tests/test_map.py
python .agents/workflows/workflow_ops.py --workflow-run-id 7f3a monitor --kind pr --id 42 --head "$(git rev-parse HEAD)"
```

## Push, wait and repair

Commit checkpoints locally and push a stable candidate once. CI on the exact remote head is authoritative only
for the tiers that event runs; read the workflow to know which. Wait through one `monitor` per PR, head or run
(`--kind run --id <run-id>` for a run), invoked through `agent:listen` for the completion notification. Re-run
the same command after process loss to reconnect. Never poll in model turns, sleep in ad hoc loops or call
`gh run watch`; read forge status once per wake. `workflow:continue` owns the wait only when the user asks for
unattended progress, and `workflow:run` owns whether the goal continues to merge.

On failure, read the remote log first, reproduce only the failing scope, fix it, run its focused regression
and push once. Batch related fixes per push.
