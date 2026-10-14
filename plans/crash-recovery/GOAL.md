# Deterministic crash recovery

Worktree: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-CrashRecovery
Branch: Feature/CrashRecovery
PR: https://github.com/tj-agents/core/pull/253
Parent session: codex:01a13a7c-e3d3-7d83-93fd-51a323f9cfce

## Outcome and authority

Tommy requested on 2026-10-14 that crash recovery take priority over the remaining work-item migration. A thin `machine:recover-agents` skill must invoke one deterministic portable script command that reopens all eligible interrupted native agents without AI session selection. Existing migration PR251 and its checkout remain preserved and paused. This goal owns the recovery command, focused tests, review and delivery under existing Core authority; it does not authorize reopening completed historical sessions or changing unrelated plans.

## Design

Extend the shipped `work_item_sessions.py interrupted` path with machine-wide inventory and bulk resume. Use the central SQLite registry and existing guarded `agent_recovery.open_session`; add no backend or third-party dependency. Default inventory remains read-only. The bulk command skips completed work items, ended sessions, live agents, foreign machines, unknown identities and stale checkouts; it reports each exclusion/failure explicitly and continues other eligible launches serially. Preserve existing explicit-handle behavior.

Repeated and concurrent runs retain the native launch receipt safeguards. Report recovery success only after a fresh SessionStart registration of the exact native handle with a live PID/start identity. A launched but unregistered session remains pending/ambiguous and is never automatically retried. All native process/terminal launches use the existing portable launcher.

Database setup already creates missing parent/schema, uses WAL and a serialized schema-version migration, and upserts native handles. This creates an empty database on a new PC; transcripts and historical work do not appear automatically. This machine's observed database is healthy (schema2, 12 Codex rows, zero work items, zero Claude rows). Old JSON entries lack reliable finished/crashed classification, so never import all historical rows as unfinished. Prompt/Stop hooks will repair a missing current-session row through the canonical registrar, preserving provable native PID/start identity; existing rows are never reset by this fallback.

## Slice and lanes

One atomic runtime/CLI/skill-invocation slice based on fetched `origin/main` at `eded20b2014d46dd65b9bfc9bdb49d23f422fc1c`, branch `Feature/CrashRecovery`, isolated checkout `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-CrashRecovery`. Expected size below 600 substantive lines. The skill invocation and harness permissions must match the exposed command in the same reviewed slice; this is the interface of this utility, not a global convention change. Broader plan-format migration stays with PR251.

L3 investigation selected because population and resume safeguards were unresolved; one read-only bounded investigator supplies evidence. L4 implementation selected for specified CLI behavior with testable guards, assigned to one worker with exclusive runtime/test paths. Parent retains design, acceptance, review and delivery decisions. L2 review is required because duplicate writers and stored recovery state carry migration risk.

## Verification and current state

- Database `C:/Users/TommySeery/.agents-state/sessions.db`: read-only quick_check returned `ok`; user_version2;12 native Codex rows; no work items. Current owner is recorded.
- SQLite S1 delivered by PR228. S2 plan migration survives in `Feature-WorkItemPlanMigration`, native handle `codex:01a13788-88de-7170-9743-ffcc9ffb68e2`, draft PR251, with review/CI repair next.
- Baseline interrupted command restricted inventory to the calling Git repo, required explicit handles and stopped on one launch failure. The new machine-wide inventory ran successfully against the real registry: 10 eligible closed sessions, one stale checkout and the current live owner skipped. No native launches performed during investigation.
- Legacy Windows vault inspection proved no reliable current crash set: October snapshots contain a process predating their own boot timestamp; the unconsumed manual pin is from September1 and points to missing transcripts. Do not automatically seed SQLite from these records.
- Harness and Windows hook command checks passed. Local package generation/check passed; a broader source-layout test observed a digest changing during the worker edit, so package checks must be refreshed after the source freeze. The frozen implementation passes both runtime test files and the targeted missing-prompt, missing-stop and per-row verification-failure regressions. Existing receipt-guard tests also pass.
- Frozen package self-containment/determinism and both-host recovery contract checks pass after source freeze. Native review at `232e1dacd8318eb20ca92eb9755407cebb772659` passes and ran 99 runtime tests. Fresh L2 evidence confirmed two capture-ordering defects; canonical work order `reviews/Feature-CrashRecovery.md` is complete with changes requested and verified both-host coverage. One serial worker owns the coupled fixes. Linux CI is green; Windows remains pending at this first candidate.
- Native histories and working checkouts survived; no destructive cleanup is authorized here.

## Next Steps

The original foreground native owner remains active. A supported five-minute continuation wake is registered; a UI successor launch failed before opening a tab because unrelated CPP plugin activation returned Access denied. No successor pickup or agent restore has occurred.

1. Fix confirmed incremental finding R3: fallback SQLite capture must also restore its canonical JSON registry entry using the validated identity, preserving atomic missing-row and concurrent-state guards. The existing L4 worker owns only runtime and targeted tests. R1/R2 are fixed. Both-platform CI passes at `c6063f1`; native incremental review reported R3.
2. Commit the focused repair, review only its frozen delta, and validate exact-head host coverage. Refresh only required package closure checks. Keep generated plugins/catalog uncommitted. Update and monitor PR253 at its exact new head; use existing guarded merge authority after clean review and required CI. Observe the causal main regeneration commit.
3. Make recovery available in existing host profiles through supported native sync; verify installed bytes. Codex cache is old; Claude machine@tj-agents is pinned to v2.1.15 and lacks SQLite. Resolve the supported native selection without duplicate hooks or cache hand edits.
4. Exercise `work_item_sessions.py interrupted --all-repos --resume-all` against a fresh real inventory. Record successful fresh registrations and exact pending/failure handles. Repeat only to prove live sessions are skipped. Preserve ambiguous receipts and the user's active dialogue. Do not import unreliable old vault history.
5. Finish with direct command, database location/setup semantics and surviving migration location. Clean only owned disposable checkouts under the existing merge rules.

A managed continuation child, if dispatched after foreground release, reads this goal and owns the existing supervisor lease. It must not claim/register/wake recursively. Follow the supervisor prompt and write the nonce-bound checkpoint to CONTINUATION_RESULT_PATH before its 900-second timeout; include exact old/new identity rebind after any commit. Use fresh L2 review for consequential recovery-state acceptance. Foreground/native ownership claims apply only to an actual UI successor, which has not launched.

- Scope: deterministic recovery through verified delivery and a concrete recovery command.
- Current slice: machine-wide interrupted-agent recovery.
- Remaining scope: registry repair, final delta review, exact-head delivery, installed host adoption and observed local use.
- Done when: one script command reopens eligible interrupted sessions with no AI selection, repeated runs create no duplicate writers, fresh registrations prove successful recovery, and Windows/Linux/package checks pass.

```agent-host-coverage
{"schema_version":1,"shared_source":".agents/machine/scripts/work_item_sessions.py","hosts":[{"host":"claude","behavior":"Persist missing current sessions and deterministically resume eligible interrupted native agents with receipt and fresh-registration guards.","source":".agents/machine/scripts/work_item_sessions.py and .agents/machine/scripts/session_store.py","mapping":".claude/skills/recover-agents/SKILL.md routes to the shared machine utility and packaged machine scripts.","verification":{"level":"source","result":"passed","evidence":"Both runtime test files pass; targeted missing prompt/stop recovery and per-row verification failure tests pass; existing agent_recovery launch-guard suite passes. Native process launches are mocked in unit tests."}},{"host":"codex","behavior":"Persist missing current sessions and deterministically resume eligible interrupted native agents with receipt and fresh-registration guards.","source":".agents/machine/scripts/work_item_sessions.py and .agents/machine/scripts/session_store.py","mapping":".codex/skills/recover-agents/SKILL.md routes to the shared machine utility and packaged machine scripts.","verification":{"level":"source","result":"passed","evidence":"Both runtime test files pass; targeted missing prompt/stop recovery and per-row verification failure tests pass; existing agent_recovery launch-guard suite passes. Native process launches are mocked in unit tests."}}]}
```

## Adoption and execution checkpoint

R1/R2 fixes passed focused regressions and both-platform CI. Native incremental review found R3: fallback capture omitted the JSON registry required by canonical liveness checks; a serial repair owns that gap. Native bulk recovery invokes the native terminal launcher directly, and its Windows sync treats SyncError as best-effort. It can therefore exercise the verified source without the failed UI handoff's blocking unrelated plugin activation. Installed Codex helper bytes remain old; installed adoption is still required.

The original native foreground lease is retained with token-backed heartbeats. A supported five-minute managed wake is registered, but a stale-live reconciliation changed its state to blocked during context compaction; heartbeat alone preserves the lease but does not clear that state. Reconcile through the supported checkpoint/claim operations before releasing to managed continuation. No successor has acknowledged pickup and no interrupted agent has yet reopened.

## Core overhead notes requested by Tommy

On 2026-10-14 Tommy asked to keep notes for later because this urgent utility had taken over two hours. Recovery stays first; these observations do not authorize a parallel process overhaul.

Observed overhead: full native review took 527 seconds and independently repeated 99 tests; the subsequent native delta review took 468 seconds. Each stable candidate also required a fresh specialist lens, source bundle export, host coverage, work-order updates and delivery binding. Repeated skill reads and redundant checks by the parent added avoidable work; an incorrect unittest invocation and a generated digest race also required corrections. Continuation bookkeeping consumed time, and a fresh UI handoff failed on unrelated CPP plugin cache activation. Existing Claude release pinning prevents ordinary sync from adopting the utility. Hook permission synchronization repeatedly exceeded its seven-second timeout, and tool calls often incurred additional startup latency.

At the measured checkpoint: 151 model turns, 148 tool calls, 56 wait/poll events, 32 skill reads, approximately 13.47 million cached input tokens and 287,070 uncached input tokens. Workflow hard limits then forced fresh-context transfer preparation during an already urgent task. These are measured session costs, not proof that every requirement was necessary.

Candidate follow-ups after recovery: one proportionate review per stable utility candidate; focused test ownership so reviewers avoid repeating full suites; cached rule reads; cheaper deterministic bundle preparation; fewer operational checkpoints; continuation that avoids unrelated profile sync; and reliable host release adoption. Record precise enforcement sources before changing any requirements. Core should keep the agentic wrapper thin and make the deterministic path faster.

R3 repair is frozen and passes six focused recovery cases plus three registrar cases. The tested frozen c606 checkout started the authorized real bulk restoration under captured run crash-recovery-live; no final outcomes have been observed yet. Final source delta is ready for commit and incremental review.

The first real bulk run was paused for Tommy's question after 468.735 seconds. It was recovery, not UI handoff. SQLite shows four fresh registrations: codex:01a132e7-26a7-7fa3-9484-9a8897e77d18 (tj-agents), codex:01a135fb-ec26-76f3-abd8-398ba45127b4 (Azure learning), codex:01a1362c-5751-75f3-a54d-9bb37f25a41a (.NET snippets), codex:01a136de-d754-7f02-be3f-636803f5cc0a (docs review). The parent stopped only its own bulk process; reopened native agents remain. No final per-row output was emitted before termination, so receipts and fresh liveness must decide remaining work. Tommy then explicitly said to keep going.

A measured runtime slowdown is now included in the same recovery slice: bulk restore was repeating the best-effort full plugin upgrade for every session. The specified worker adds an optional canonical launch parameter and disables that upgrade only for bulk recovery, retaining native executable/resume/profile/liveness/receipt checks and all host hooks. Ordinary manual launch keeps its existing default. This is a bounded restore performance repair, not a global workflow overhaul. Final review will freeze the registry and performance delta together from c6063f1.

The performance repair is frozen: bulk disables only best-effort plugin refresh; default/manual open preserves it. Six focused launch and bulk tests pass, syntax/diff checks pass. Registry and performance fixes will receive one final combined incremental review from c6063f1. Foreground tool commands now avoid loading PowerShell profiles while preserving explicit native paths and host guards.
