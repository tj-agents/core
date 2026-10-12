# Code review — Feature/WorkItemSessions

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `in-progress`
**Reviewed up to commit:** `afa69fa55a938cde389e56d171db21fac8877660`  `(2026-10-12)`
**Judgment:** `changes-requested`

## Review pass — 2026-10-12 — full

**Candidate base:** `c91b60c955ad4a3f0f7a9383fc20f1c4a6b58510`
**Candidate head:** `afa69fa55a938cde389e56d171db21fac8877660`
**Candidate branch:** `Feature/WorkItemSessions`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:5ce45e3415d8bf786db4b56fd8d0dfd107e22173051442035cf4dd0201f51df8` `(8 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\LVFP5jDNUJ7t4db8Ve9L_W\ok9rHq73XwWAmDRQ0gETxL`
**Candidate bundle identity:** `sha256:801a0add80f2d8c1de8ba3ca3ec72c8c75f7384ddfd7ccf4751c6514b3e19e50`
**Work-order path:** `reviews/Feature-WorkItemSessions.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

Native layer: Claude Code `code-review` skill (medium). Lens: `workflow` (`review-lens`). No security-sensitive paths.

```agent-host-coverage
{"schema_version":1,"shared_source":".agents/machine/scripts/work_item_sessions.py","candidate_head":"afa69fa55a938cde389e56d171db21fac8877660","hosts":[{"host":"claude","behavior":"Record, report and resume the exact Claude session recorded for a work item through the guarded open_session path.","source":".agents/machine/scripts/work_item_sessions.py","mapping":"Machine package resources/machine/scripts with Claude allow rules in .agents/plugins/harness/machine.json; routed by machine:recover-agents.","verification":{"level":"source","result":"passed","evidence":"tests/test_work_item_sessions.py records a Claude owner from CLAUDE_CODE_SESSION_ID, validates it, and resumes it through a mocked open_session with the Claude projects root; focused suite 115 passed on Windows."}},{"host":"codex","behavior":"Record, report and resume the exact Codex session recorded for a work item through the guarded open_session path.","source":".agents/machine/scripts/work_item_sessions.py","mapping":"Machine package resources/machine/scripts with a Codex prefix rule scoped to status/resume in .agents/plugins/harness/machine.json; routed by machine:recover-agents.","verification":{"level":"source","result":"passed","evidence":"tests/test_work_item_sessions.py records a bounded Codex row from CODEX_THREAD_ID beside the Claude owner and validates both; test_harness_manifests checks the Codex prefix rule match and not_match cases."}}]}
```

### Findings

- [x] **R1 — HIGH — native** — `.agents/machine/scripts/work_item_sessions.py:264`
  `Head` is compared for equality with HEAD, but the lifecycle commits the row, so every recorded row becomes
  `head-mismatch` and `resume` refuses it. Treat the row as current while HEAD contains `Head`
  (`git merge-base --is-ancestor`); report stale only when diverged.
  Fixed: _head_contains uses merge-base --is-ancestor; stale reason is head-diverged; tests test_later_commits_on_the_branch_keep_the_row_current, test_status_reports_diverged_head_as_stale.
- [x] **R2 — MEDIUM — native** — `.agents/machine/scripts/work_item_sessions.py:326`
  `resume --confirm-closed` is reachable under the auto-approved Codex `resume` prefix rule, so an agent can
  relaunch an `unknown` session without the user's reconciliation, contradicting "unknown authorizes
  nothing". Remove the flag from this helper; reconciliation stays with `open-claude`/`open-codex`.
  Fixed: --confirm-closed removed from resume; doc points unknown reconciliation at open-claude/open-codex.
- [x] **R3 — LOW — native** — `.agents/machine/scripts/work_item_sessions.py:375`
  `record` read-modify-writes the registry without a lock, so concurrent sessions in one checkout can lose a
  row or both claim ownership. Serialize `record`/`remove` with `agent_recovery._claim_lock` on a lock file
  outside the repository.
  Fixed: record/remove run under _registry_lock (agent_recovery._claim_lock in the temp directory); test_concurrent_records_keep_every_row.
- [x] **R4 — LOW — native** — `.agents/machine/scripts/work_item_sessions.py:370`
  On a detached HEAD `record` writes an empty `Branch`; a whitespace trim then makes the line malformed and
  breaks the whole file. Refuse detached HEAD and reject empty field values in `validate`.
  Fixed: record refuses a detached HEAD and validate rejects empty fields; tests test_record_refuses_detached_head, test_empty_field_is_rejected.
- [x] **R5 — LOW — workflow** — `.agents/machine/utility/recover-agents/SKILL.md:37`
  "several rows require an explicit `--handle`" contradicts `resume`, which selects the single `owner` row
  regardless of bounded rows. State the owner-count rule.
  Fixed: recover-agents states that resume without --handle selects the single owner row.
- [x] **R6 — LOW — workflow** — `.agents/machine/resources/work-item-sessions.md:34`
  The doc says `Profile` is compared against the reading machine; only `Machine` is compared and `Profile`
  locates history on resume. Split the bullet.
  Fixed: Machine and Profile bullets split; Profile only locates history on resume.

## Review pass — 2026-10-12 — incremental

**Candidate base:** `afa69fa55a938cde389e56d171db21fac8877660`
**Candidate head:** `5c13ab4e7ddca02f36ef5722302011dd6ff2cdd4`
**Candidate branch:** `Feature/WorkItemSessions`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:ab292007ea8fb141ead4411236cb6f4d587d6fd8cffc86ba4640b5f746e0fa46` `(5 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\1jNF5kys_vwuYr4h3iMEwz\S4rwcCQdvEobnlDrjcf1RI`
**Candidate bundle identity:** `sha256:e7656c7f4ed62ba5b28c30ff58943b65e911306bf02fa109a905ae10ffa72abc`
**Work-order path:** `reviews/Feature-WorkItemSessions.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Native layer: Claude Code `code-review` skill (medium). Lens: `workflow` (`review-lens`). R1–R6 dispositions verified against the delta.

### Findings

- [x] **R7 — LOW — native** — `tests/test_work_item_sessions.py:247`
  `test_concurrent_records_keep_every_row` wraps `_record_locked` in the lock itself instead of driving
  `record()`, so removing the lock from `record()` would still pass. Drive the threads through `WIS.record`.
  Fixed: threads call `WIS.record` with per-thread session ids and a slowed `load`; verified the test fails
  with the lock removed from `record()` and passes with it.
- [x] **R8 — LOW — workflow** — `.agents/machine/utility/recover-agents/SKILL.md:37`
  "with no owner or no rows, pass `--handle`" offers `--handle` for the no-rows case, where `resume` raises
  before reading it. Split the two conditions.
  Fixed: rows without a single owner need `--handle`; no rows start a new owner.
