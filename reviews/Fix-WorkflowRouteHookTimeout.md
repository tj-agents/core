# Code review — Fix/WorkflowRouteHookTimeout

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `3c81e52`  `(2026-10-01)`
**Security-reviewed up to commit:** `e868fc3ba938fa9dc35cd32d866e762aefe1fd8d`  `(2026-10-01)`
**Judgment:** `approved`

## Review pass — 2026-10-01 — all

**Candidate base:** `bcfa25a4f8377d03442febac838cd8af4ef3ff68`
**Candidate head:** `e868fc3ba938fa9dc35cd32d866e762aefe1fd8d`
**Candidate branch:** `Fix/WorkflowRouteHookTimeout`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:8ab599ae2a95a579e432574699fd194ebc5050751d6cc4626d0cee6c46da939f` `(33 paths)`
**Candidate bundle:** `.git/agent-workflow/runs/route-timeout-review-1/review/b43270785cc14f9980c380ec2c93a0af851d3ad89177847e6a9f87eebe2b80b1`
**Candidate bundle identity:** `sha256:8062a77aeef92aee54cc7a0e0164fc776c09eea951c7152ae669dd3a55131424`
**Work-order path:** `reviews/Fix-WorkflowRouteHookTimeout.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

### Findings

- [x] **REV-001 — HIGH — correctness/security** — `.agents/hooks/hook_dispatch.py:192`
  Gates run in sequence in one process and emit only at the end. A gate that hangs past the shared host
  timeout therefore discards every verdict already computed, including a deny. `harness_grant.git()` and
  `hook_runtime.origin_owner()` ran git with no timeout. Fix: add a `--deadline` under the host timeout, which
  emits the finished gates' merged verdicts plus a notice naming the stalled gate. Bound both git calls. Run
  network-bound gates last.

- [x] **REV-002 — MEDIUM — correctness** — `.agents/hooks/workflow_route.py:163`
  A failure while pruning another session's stale receipt skipped writing this session's receipt, so a
  route that was delivered got recovered again. Fix: write the receipt first and guard each pruned file on
  its own.

- [x] **REV-003 — MEDIUM — correctness** — `.agents/hooks/workflow_route.py:244`
  Whether a route was delivered depended only on the transcript timestamp being earlier than the receipt.
  Fix: live payloads carry `prompt_id`, so the receipt stores it and a matching `prompt_id` decides delivery
  before any timestamp comparison.

- [x] **REV-004 — MEDIUM — correctness** — `.agents/hooks/workflow_route.py:257`
  Parallel tool calls could each recover the same lost route. Fix: take an `O_EXCL` claim per prompt
  before recovering.

- [x] **REV-005 — LOW — efficiency** — `.agents/hooks/workflow_route.py:253`
  Every tool call read up to 1 MiB of the transcript. Fix: return early when the receipt's `prompt_id`
  matches.

- [x] **REV-006 — LOW — correctness** — `.agents/hooks/hook_dispatch.py:169`
  A gate with an `@matcher` ran when the payload had no tool name. Fix: skip it, as the host does.

- [x] **REV-007 — LOW — error-handling** — `.agents/hooks/hook_dispatch.py:109`
  When two gates set the same custom output key with different values, the later value was dropped
  silently. Fix: report the conflict as a diagnostic.

- [x] **REV-008 — LOW — validation** — `scripts/sync_plugin_packages.py:95`
  An exec-form `args` element could hold a whole command line. Fix: reject whitespace in `args` elements.

Dropped after validation. A subagent tool call receiving the parent's route was refuted by a live
2.1.282 probe, where subagent PreToolUse payloads carry `agent_id` and `agent_type`. Reusing the
claim-pruning helper doesn't fit, because receipts are per session, not per invocation. Re-execution of
sibling modules is inert, since no shipped module state crosses gates.

## Review pass — 2026-10-01 — incremental `e868fc3..3c81e52`

**Pass judgment:** `approved` after REV-009

- [x] **REV-009 — MEDIUM — correctness** — `.agents/hooks/hook_dispatch.py:242`
  The dispatcher read `worker.is_alive()` twice: once before merging and once before `os._exit`. If a
  gate finished between the two reads, the output reported that gate as unfinished and left out its
  verdict. Fix: decide whether the deadline was overrun once, from the locked results snapshot.
