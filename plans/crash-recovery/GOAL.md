# Deterministic crash recovery

Worktree: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-CrashRecovery
Branch: Feature/CrashRecovery
PR: not opened
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
- Native histories and working checkouts survived; no destructive cleanup is authorized here.

## Next Steps

1. Review the frozen tested runtime and thin skill/harness candidate.
2. Refresh package closure checks and required remote checks, then deliver under repository gates.
3. Exercise authorized machine-wide recovery; retain specific failed or pending handles as actionable output.

- Scope: deterministic recovery through verified delivery and a concrete recovery command.
- Current slice: machine-wide interrupted-agent recovery.
- Remaining scope: package verification, immutable review, delivery and observed local use.
- Done when: one script command reopens eligible interrupted sessions with no AI selection, repeated runs create no duplicate writers, fresh registrations prove successful recovery, and Windows/Linux/package checks pass.

```agent-host-coverage
{"schema_version":1,"shared_source":".agents/machine/scripts/work_item_sessions.py","hosts":[{"host":"claude","behavior":"Persist missing current sessions and deterministically resume eligible interrupted native agents with receipt and fresh-registration guards.","source":".agents/machine/scripts/work_item_sessions.py and .agents/machine/scripts/session_store.py","mapping":".claude/skills/recover-agents/SKILL.md routes to the shared machine utility and packaged machine scripts.","verification":{"level":"source","result":"passed","evidence":"Both runtime test files pass; targeted missing prompt/stop recovery and per-row verification failure tests pass; existing agent_recovery launch-guard suite passes. Native process launches are mocked in unit tests."}},{"host":"codex","behavior":"Persist missing current sessions and deterministically resume eligible interrupted native agents with receipt and fresh-registration guards.","source":".agents/machine/scripts/work_item_sessions.py and .agents/machine/scripts/session_store.py","mapping":".codex/skills/recover-agents/SKILL.md routes to the shared machine utility and packaged machine scripts.","verification":{"level":"source","result":"passed","evidence":"Both runtime test files pass; targeted missing prompt/stop recovery and per-row verification failure tests pass; existing agent_recovery launch-guard suite passes. Native process launches are mocked in unit tests."}}]}
```
