# Code review â€” Feature/AgentRecovery

**Review status:** `complete`
**Judgment:** `approved`

## Review pass â€” 2026-10-08 â€” full

**Candidate base:** `78665c194839583ba5fc2eca016bc07a3ab7842f`
**Candidate head:** `19c5b452e65c5eb01331de3111a9fafdecb9ee7a`
**Candidate branch:** `Feature/AgentRecovery`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:7d4ec0ef5251dd3bba0491c2d69ce05de41c7580ecefdea745b3f9f241662c38` `(20 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\DbVw-AscOdm4u7tGgvDYao\DO4T_eJiszgSw6Zzf178_a`
**Candidate bundle identity:** `sha256:123a0ec5b8e4c2d3e125206e76fb2d10f0bc6a2878e1659c0aed3cbfc7237d35`
**Work-order path:** `reviews/Feature-AgentRecovery.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

Native review: configured native Codex reviewer over the frozen range. Fresh lens: workflow/recovery behavior on the same immutable bundle. No security-path inventory match. Parent owns synthesis.

### Findings

- [x] **R1 â€” P1 â€” error outcomes** â€” `.agents/machine/scripts/agent_recovery.py:391`
  Fresh module loads create incompatible LaunchTimeout classes; a synthetic timeout escapes main instead of returning3. Existing open-claude also misses recovery ValueError and ordinary LaunchError failures. Share loaded exception identities across both callers and return controlled1/3 results. Native Spark was unavailable; native fallback could not execute local reads; artifact-fed retry was rejected by automatic approval review for source transmission. Parent fallback validated the frozen bundle and repros; fresh internal behavior lens independently confirmed error gaps.

- [x] **R2 â€” P1 â€” concurrency** â€” `.agents/machine/scripts/agent_recovery.py:230`
  Two processes retiring a completed receipt can both claim: B unlinks A's newly created pending receipt. A deterministic two-process synthetic repro returned success for both. Serialize retirement/read/create with an OS file lock and cover the race.

- [x] **R3 â€” P2 â€” native history shape** â€” `.agents/machine/scripts/agent_recovery.py:116`
  Native Codex session_index uses thread_name, while this reader accepts only title. Normalized history.session records also lack preview. Read actual title shape and derive a bounded user preview; test an archive-only record instead of leaving a duplicate live copy.

- [x] **R4 â€” P2 â€” profile isolation** â€” `.agents/machine/scripts/agent_recovery.py:302`
  Native Codex launch selects CODEX_HOME but prelaunch standards sync still uses the current/default profile. Scope both sync and launch to the selected profile and restore the caller environment.

- [x] **R5 â€” P2 â€” recovery selection** â€” `.agents/machine/scripts/agent_recovery.py:367`
  Repeated or invalid later selections are discovered after earlier launches. Validate/deduplicate the complete selection before side effects and retain partial-launch reporting for actual later failures. Fresh behavior lens independently confirmed repeated-selection partial recovery.


**Reviewed up to commit:** `9a4162621e97da6a6e7610a2e92e143e799a3b6b` `(2026-10-08)`

Validation: 52 focused tests passed with1 platform skip; read-only native search found the current exact session in its original cwd with status live. Frozen synthetic repros confirmed native title/preview and timeout failures, and the separate-process claim race. No security-path inventory match. Parent assigned final severities; no lens assigned approval.

Addressing: one exclusive L4 writer repairs the coupled shared search/resume flow and its two host entry points. Parent retains work-order/goal/commit ownership; no source-review writer overlap.

## Review pass — 2026-10-08 — full refreshed candidate

**Candidate base:** `8fb3c340f65f1af4f55d42bbf41c46df37ff7bc1`
**Candidate head:** `1b6557c8f15b9141694c356e6dc4358f4a849a37`
**Candidate branch:** `Feature/AgentRecovery`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:7d4ec0ef5251dd3bba0491c2d69ce05de41c7580ecefdea745b3f9f241662c38 (20 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\Vi4uWyoZBgdZc1nrYuYd_9\1YfMCIvQAu2dB81mEZ3zL0`
**Candidate bundle identity:** `sha256:8ac547435d1521c519adda1adc14ddc596ebb5fe949a4bac68d46e0324741ff2`
**Work-order path:** `reviews/Feature-AgentRecovery.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Pre-review synchronization: origin/main 8fb3c340f65f1af4f55d42bbf41c46df37ff7bc1 merged; behind count zero. Fresh internal recovery lens plus parent native-general fallback; known unavailable native tools and rejected external source transmission are not retried. Previous review bundle failed integrity verification, so this full candidate was exported afresh and is authoritative for final synthesis. No security inventory path match.

Final synthesis: fresh recovery behavior lens found no high-confidence introduced defects in the immutable final source/patch. Parent native-general fallback inspected the same committed capability and regressions; R1 stable native exceptions and controlled1/3 exits, R2 separate-process receipt serialization, R3 native thread_name plus title aliases/archive-only fixture, R4 selected profile sync/launch and environment restoration, and R5 prevalidated selection/partial-timeout identity reporting are resolved. Final bundle integrity passed review-reconcile. Native reviewer remains unavailable/rejected as documented; no native interactive resume was claimed. Focused tests and packaging checks provide synthetic boundary evidence; exact-head CI remains the remote validation gate.

## Review pass — 2026-10-08 — incremental inventory correction

**Candidate base:** `1b6557c8f15b9141694c356e6dc4358f4a849a37`
**Candidate head:** `beac6a19843ec9770d252fbf4c90dafdf8ec2a17`
**Candidate branch:** `Feature/AgentRecovery`
**Candidate scope:** `tests/test_source_layout.py`
**Candidate path-set:** `sha256:2719d377ef5b780db2ee7515c1ade7a4699568ab4ef1d69259207d392af9b8e0 (1 path)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\-1X1lAoz9C0e-3tcyHS1u6\u2Whbgpbsk70momM33IUVm`
**Candidate bundle identity:** `sha256:aa42c0ccd23e68a19493651d265c857fe394f18a6c9faba5aabc67b54426f906`
**Work-order path:** `reviews/Feature-AgentRecovery.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Parent native-general fallback inspected the frozen one-line patch. Four new canonical definitions make the exact count73; all existing host-set and canonical-pointer assertions remain. All19 source-layout tests passed after the required catalog fixture refresh. No new findings. Native review remains unavailable as recorded; no external source transmission was retried.

## Review pass — 2026-10-08 — full integrated launcher

**Candidate base:** `ab32149213bf30895f11d85f1bf73c0a09b25317`
**Candidate head:** `9a4162621e97da6a6e7610a2e92e143e799a3b6b`
**Candidate branch:** `Feature/AgentRecovery`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:6f3ae038567264438ec9ad5e56299176f932ce6921c356ef4e1fff92ec1647b6 (21 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\y-xhE6rPLSJ5m5VDNbdVwX\TlF2cejbm9bIAf5D6ZEm3r`
**Candidate bundle identity:** `sha256:21e82c868ce81eaa14026f89bd23ec1133a97eb3bba55ca74b7ac7a6c9f1e8ce`
**Work-order path:** `reviews/Feature-AgentRecovery.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Synchronization: main ab32149213bf30895f11d85f1bf73c0a09b25317 was merged before this fresh freeze. Shared agent_cli resolution API remains compatible; integrated recovery14, agent_cli77, open-claude27 and source-layout19 tests passed, with12 platform skips after package refresh. Native-general parent fallback plus fresh internal workflow lens; known rejected external source transmission is not retried.

Final integrated synthesis: the fresh workflow lens found no high-confidence introduced defects; it checked current agent_cli signatures, profile/cwd propagation, registry identity, cross-process receipts, selection validation and packaged peer loading. Parent native-general fallback confirmed compatibility with the merged resolve_lane extraction and retained resolve_lane_model API. Manifest identity21e82c868ce81eaa14026f89bd23ec1133a97eb3bba55ca74b7ac7a6c9f1e8ce and patchfa9ac12941dedf11528678ea7ddfea712fd07c196fe9db63f25ac2205bc59eb2 are different artifacts and both match the descriptor. Review is approved; native interactive resumes were not exercised. Exact integrated-head CI remains required.
