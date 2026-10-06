# Code review — Fix/WorkflowRouteHookTimeout

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `6aa6fd570e8fc146e6e73c3f58f6d4d8e0f23fe1`  `(2026-10-06)`
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

## Review pass — 2026-10-05 — incremental `3c81e52..27bc3d6`

**Candidate base:** `3c81e52`
**Candidate head:** `27bc3d6e036d5afd21f6224c6c047a10f67f1461`
**Candidate branch:** `Fix/WorkflowRouteHookTimeout`
**Candidate scope:** the 23 paths this branch changes against origin/main `df1bc41` (`git diff --name-only origin/main...27bc3d6`, excluding this work order); the remaining range paths are main's own commits arriving through merge 9d45911
**Candidate path-set:** `sha256:e2ac16e9c3f240e0d25b4211e786e06af187026ea934ab413a985920ed603b4f` `(360 paths, unscoped range)`
**Candidate bundle:** `.git/agent-workflow/runs/backlog-pr75-incremental/review/3de2739e630044822844a15817f63f54cbb68a30cadb9c05d79ff4f6f21e1237`
**Candidate bundle identity:** `sha256:75657397a6d25b7f05e0cf9728ed2e2611c52f48b87d340b805a2be8e2ba1ffb`
**Work-order path:** `reviews/Fix-WorkflowRouteHookTimeout.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Scoped paths: `.agents/catalog/catalog.json` `.agents/hooks/harness_grant.py` `.agents/hooks/hook_dispatch.py` `.agents/hooks/hook_runtime.py` `.agents/hooks/tests/test_hook_dispatch.py` `.agents/hooks/tests/test_merge_review_gate.py` `.agents/hooks/tests/test_workflow_route.py` `.agents/hooks/workflow_route.py` `.agents/plugins/TECH_DEBT.md` `.agents/plugins/harness/base.json` `.agents/plugins/harness/engineering.json` `.agents/plugins/manifests/claude/base-hooks.json` `.agents/plugins/manifests/claude/engineering-hooks.json` `.agents/plugins/manifests/claude/machine-hooks.json` `.agents/plugins/sources.json` `scripts/sync_harness_manifests.py` `scripts/sync_plugin_packages.py` `tests/test_agent_files.py` `tests/test_engineering_hooks.py` `tests/test_goal_continuation.py` `tests/test_hook_contract.py` `tests/test_hook_launch_budget.py` `tests/test_plan_artifacts.py`

Native layer: Claude Code `code-review` (medium) over `3c81e52..27bc3d6` scoped to the paths above. Lenses: workflow + api-contract (fresh review-lens; no findings — manifests all exec form with existing script paths, timeouts 5s above dispatcher deadlines, harness/sources shape matches main's PR #86 removal, merged bash discovery type-consistent). Security layer not run: the range's only security path (`.github/workflows/ci.yml`) is main's content outside scope, and `trunk_base..head` has none.

### Findings

- [x] **REV-010 — LOW — correctness** — `.agents/hooks/hook_dispatch.py:241`
  37cd2a5 decides overrun as `len(finished) < len(names)`. `run_gate` caught only `SystemExit` and `Exception`, so a gate raising another `BaseException` ended the worker early: with `--deadline` the crash was reported as "did not finish within Ns" and skipped `return 0`; without one, `overrun_notice` formatted `None` and the dispatcher died with `TypeError`. Fix: catch `BaseException` in `run_gate` so a gate failure is always a recorded crash and the worker only stops early at the deadline; regression test with a gate raising `KeyboardInterrupt` under both modes.

Not retained here (pre-existing on main 0b989f3 and preserved exactly by the `route()` fold; `PLANNING_REQUEST` is a subset of `PLANNING_ONLY`): planning-route false positives on "plan only"/"only plan" and its narrower phrasing coverage. Routed to the standards-defect side workstream `C:\Users\TommySeery\.claude\plans\tj-agents-core\SIDE_PEERCLI_SCOPE_AND_REVIEW_BUNDLE.md` (Defect 4), sequenced after this PR lands.

## Review pass — 2026-10-05 — incremental `27bc3d6..6033957`

**Candidate base:** `27bc3d6e036d5afd21f6224c6c047a10f67f1461`
**Candidate head:** `6033957dc3d7d92fcc40b30a3f8f08d7cc025237`
**Candidate branch:** `Fix/WorkflowRouteHookTimeout`
**Candidate scope:** this branch's paths against origin/main `b2b1d87`; in range: `.agents/catalog/catalog.json`, `.agents/hooks/hook_dispatch.py`, `.agents/hooks/tests/test_hook_dispatch.py` (the rest is main's PR #102/#105 content arriving through merge 6033957)
**Candidate path-set:** `sha256:c96fa413994cb6cec9f1d6fca490322b1cc378adc9c230185648313c8c559711` `(25 paths, unscoped range)`
**Candidate bundle:** `.git/agent-workflow/runs/backlog-pr75-incremental2/review/222204f842318aaa125d1cc37ee7b39e630be8f36f21f8b347afe7b9e851cebc`
**Candidate bundle identity:** `sha256:92cfa317b3f4e245cdcd431fa08bb8649dc122e5e2d77b17a3cb6340ab535c47`
**Work-order path:** `reviews/Fix-WorkflowRouteHookTimeout.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Native layer: Claude Code `code-review` (low) over `27bc3d6..6033957` scoped to the three in-range paths. No security path (`first_path` and `trunk_first_path` null).

### Findings

No new findings. REV-010 fixed in 0ddee37 (`run_gate` catches `BaseException`; regression test `test_a_gate_raising_a_base_exception_is_a_crash_not_an_overrun` failed before the fix with the `TypeError` and passes after). Merge 6033957 conflicted only in `.agents/catalog/catalog.json`, resolved from main and regenerated; `update_catalog_digests.py --check` reports 0 changed, generated-path guard, harness, sync-generated `-Check` and tier-payload checks pass.

## Review pass - 2026-10-06 - incremental `6033957..6aa6fd5`

**Candidate base:** `6033957dc3d7d92fcc40b30a3f8f08d7cc025237`
**Candidate head:** `6aa6fd570e8fc146e6e73c3f58f6d4d8e0f23fe1`
**Candidate branch:** `Fix/WorkflowRouteHookTimeout`
**Candidate scope:** this branch's paths against origin/main 1ad8655; in range: `.agents/catalog/catalog.json`, `scripts/sync_plugin_packages.py` (the rest is main's PR #104/#106/#98/#107 content arriving through merge 6aa6fd5)
**Candidate path-set:** `sha256:040014480c82f7b6804f6a9cca87aa8eafca2a638a66f606e8cbe9448848009f` `(85 paths, unscoped range)`
**Candidate bundle:** `.git/agent-workflow/runs/backlog-pr75-incremental3/review/7a8a2f7eefe54090a521069c7a1bb981a613bb49e481af76a5049ed007c700b5`
**Candidate bundle identity:** `sha256:a035770cc6dd272839816b17eeec3d832b6a15d41b1e4fec31b0ac917a9da15c`
**Work-order path:** `reviews/Fix-WorkflowRouteHookTimeout.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Native layer: Claude Code `code-review` (low) over `6033957..6aa6fd5` scoped to the two in-range paths. No security path.

### Findings

No findings. Merge 6aa6fd5 conflicted only in `.agents/catalog/catalog.json`: taken from main, regenerated for structure, then every `digest` restored to origin/main's value as PR #107's guard requires, leaving this branch's net catalog change as the twelve `hooks/hook_dispatch.py` resource lines. `scripts/check_generated_paths.py --base origin/main` reports no generated paths changed; `tests/test_check_generated_paths.py`, harness, sync-generated `-Check` and tier-payload checks pass. `scripts/sync_plugin_packages.py` combines main's reworded error message with this branch's exec-form validation without conflict.
