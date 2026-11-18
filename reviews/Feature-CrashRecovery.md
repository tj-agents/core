# Code review ? Feature/CrashRecovery

**Review status:** `in-progress`
**Reviewed up to commit:** `c6063f1f46af1905aacf08a4fe1810e1be35d011` `(2026-10-14)`
**Judgment:** `pending`

## Review pass ? 2026-10-14 ? full

**Candidate base:** `eded20b2014d46dd65b9bfc9bdb49d23f422fc1c`
**Candidate head:** `232e1dacd8318eb20ca92eb9755407cebb772659`
**Candidate branch:** `Feature/CrashRecovery`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:4ae1a86fc8a481dcdbe96b0dc198b9e28b2171299b36ea7adcf488e9c23c9460` `(10 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\MBPgz__Itpd2L_B13NFEjq\BWSWaxYYMvpU7fQuwWyVQW`
**Candidate bundle identity:** `sha256:a400414a45e57ce67617a2ed6db39ff1cfab344abd9b1a055dabeb672a678d2b`
**Work-order path:** `reviews/Feature-CrashRecovery.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

Native layer: installed Codex CLI review against the frozen base from the frozen head.
Specialist lens: fresh L2 workflow and recovery state correctness review.
Security classification: no qualifying changed path.
Tier gate: no applicable stack tier. Routed rules and violations: none.

### Findings

- [x] **R1 ? MEDIUM ? workflow** ? `.agents/machine/scripts/session_store.py:563`
  The fallback calls the registrar, which persists a row before validating its native process start identity. A failed identity capture leaves a row with no process start time, so later Prompt/Stop hooks never retry. Capture and validate identity before persistence; rejected captures must leave the row absent.

- [x] **R2 ? HIGH ? workflow** ? `.agents/machine/scripts/session_store.py:619`
  The missing-row check and unconditional SessionStart upsert are separate. A concurrent valid registration or handoff can be overwritten, clearing ended state and owner role. Persist fallback identity atomically only if the handle remains absent and preserve concurrently created rows.

Parent verified the registrar write-before-return ordering and SessionStart conflict reset against the frozen source. Fresh L2 in-memory reproductions confirm both triggers. Native Codex review completed with no findings and ran 99 focused tests successfully.

```agent-host-coverage
{"schema_version":1,"shared_source":".agents/machine/scripts/work_item_sessions.py","hosts":[{"host":"claude","behavior":"Persist missing current sessions and deterministically resume eligible interrupted native agents with receipt and fresh-registration guards.","source":".agents/machine/scripts/work_item_sessions.py and .agents/machine/scripts/session_store.py","mapping":".claude/skills/recover-agents/SKILL.md routes to the shared machine utility and packaged machine scripts.","verification":{"level":"source","result":"passed","evidence":"Both runtime test files pass; targeted missing prompt/stop recovery and per-row verification failure tests pass; existing agent_recovery launch-guard suite passes. Native process launches are mocked in unit tests."}},{"host":"codex","behavior":"Persist missing current sessions and deterministically resume eligible interrupted native agents with receipt and fresh-registration guards.","source":".agents/machine/scripts/work_item_sessions.py and .agents/machine/scripts/session_store.py","mapping":".codex/skills/recover-agents/SKILL.md routes to the shared machine utility and packaged machine scripts.","verification":{"level":"source","result":"passed","evidence":"Both runtime test files pass; targeted missing prompt/stop recovery and per-row verification failure tests pass; existing agent_recovery launch-guard suite passes. Native process launches are mocked in unit tests."}}],"candidate_head":"c6063f1f46af1905aacf08a4fe1810e1be35d011"}
```

Remediation: native resolver identity is validated before persistence. Atomic only-if-missing conflict guard returns before work-item attachment when another row exists. Four focused capture/atomicity regressions pass (8.611s), including retry after failed discovery and full handed-off owner state preservation. Incremental review is required at the fixing head.

## Review pass ? 2026-10-14 ? incremental

**Candidate base:** `232e1dacd8318eb20ca92eb9755407cebb772659`
**Candidate head:** `c6063f1f46af1905aacf08a4fe1810e1be35d011`
**Candidate branch:** `Feature/CrashRecovery`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:8c8d893de4a404c0f745f90d904d808b143295b97feee5efdd32affda158dd8a` `(3 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\ZKOYySop2_KhGSlc0DozVO\YtrE5GP-UY9A0s-6Q43x-n`
**Candidate bundle identity:** `sha256:3cd32c715b584bee031c496dbc87d3c4f78d71d13ed8357f6b2543b989a8a2fe`
**Work-order path:** `reviews/Feature-CrashRecovery.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

- [x] **R3 - MEDIUM - workflow** - `.agents/machine/scripts/session_store.py:567`
  Missing-row fallback inserts SQLite without restoring `cli-sessions/<session>.json`. The canonical launcher liveness check reads that registry and returns unknown when absent, refusing later recovery. Persist the registry using validated native identity without reintroducing an unconditional SQLite upsert.

Parent verified `agent_recovery.liveness` returns unknown without the registry. Native incremental review completed in 468.419 seconds and reported R3; the fresh L2 lens found no additional defects. Source and focused capture tests cover both host routes at this exact head; installed adoption remains pending.

R3 remediation: canonical registry-only persistence reuses the validated identity after a successful atomic insert. A matching existing row can retry an absent sidecar after file-write failure. Six focused recovery cases and three registrar cases pass; syntax and diff checks pass. Final frozen delta review follows.

## Review pass - 2026-10-14 - incremental

**Candidate base:** `c6063f1f46af1905aacf08a4fe1810e1be35d011`
**Candidate head:** `42a5fb939f636678a1ebc5a195b914b453f19212`
**Candidate branch:** `Feature/CrashRecovery`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:40023bbcf86a548c59e8c3c89a6edca18ca8bea9ea605def7e746c13a0f31345` `(8 paths)`
**Candidate bundle:** `C:/Users/TommySeery/AppData/Local/Temp/review/mS7RZPUPbus2bffhy8mjBa/T9xhd1LZVeiW4_-NoVb1AH/NFrXYF6Jf1uL11lbg7I3Lh`
**Candidate bundle identity:** `sha256:fe8d96015adec8de776182db8b7725f77dcfa49c0443a1ba5899c06abfcb0b30`
**Work-order path:** `reviews/Feature-CrashRecovery.md`
**Work-order mode:** `append`
**Pass judgment:** `pending`

Native Codex CLI review and one fresh bounded workflow lens cover the frozen delta. No security-classified or routed paths; unchanged rule bodies remain cached. Six registry recovery and three registrar cases plus six performance launch/bulk cases pass. Native process restoration is no longer authorized during review, following Tommy's latest explicit limit.

### Findings

Final combined incremental review in progress.
