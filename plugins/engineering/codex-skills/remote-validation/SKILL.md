---
name: remote-validation
description: Splitting verification between the workstation and CI when several agents share one machine — locally run only the required generators and invariant checks, the smallest affected build, and focused unit tests; let draft-PR CI own the full build, service carves, and complete unit and integration matrices; let the merge queue own selected E2E; wait for remote state outside model inference through a notification or one silent background process; diagnose a red remote check by reproducing only its failing scope; never run an expensive suite "to be safe" or duplicate the queue's E2E ahead of a merge; and treat a Docker daemon that answers `docker ps` but does not move real bytes (the `pre-login handshake` signature) as an environment failure rather than an application bug. Use when deciding what to run before pushing, waiting for CI, a queue, publication or generated sync, when a remote check goes red, before any local integration or E2E run, or when a plan step says to run a full suite.

kind: contract
domain: process
---

# Remote-first validation

Read and follow the [canonical shared definition](../../.agents/engineering/contract/remote-validation/SKILL.md) in full.
This entry point supplies only Codex discovery metadata; the shared procedure is authored once under `.agents/`.
