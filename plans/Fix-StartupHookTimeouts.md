# Repair Codex startup hook timeouts

Status: review finding repaired; CI blocked by GitHub billing

PR: https://github.com/tj-agents/core/pull/119

## Goal and authority

Fix the reproduced startup hook timeouts in the authoritative core repository, verify the generated
packages in Codex's native Windows runner, commit, review and deliver the source repair through the
repository's checks. The user explicitly directed implementation after the diagnosis on 2026-10-06.
The selected engineering session-guidance standing standards-defect authorization covers PR and merge
after checks pass. Installation into another scope is not inferred from that standing rule.

Owner: this session in `Fix/InjectHarnessPermissions`, current worktree. The original prompt-file task
is stopped; this goal owns only the startup timeout repair.

## Evidence and repair

Native Codex 0.160.0 reported SessionStart timeouts after Python work had completed: plan-artifacts
finished in 0.066 seconds but received a timeout at 12.760 seconds; tier_gate finished in 1.578 seconds
but received a timeout at 11.349 seconds. Direct commands and concurrent subprocess batches passed.
The native runner launched ten startup shell processes progressively and collected early completions
after the later launches. This repair reduces core's nine startup commands to one dispatcher per package,
preserving all original scripts, arguments, context and blocks without increasing host timeouts.

Raw evidence: `C:/Users/TOMMYS~1/AppData/Local/Temp/codex-hook-timing-4p2clpcw/` and
`C:/Users/TOMMYS~1/AppData/Local/Temp/codex-hook-native-diagnostic.json`.

The bounded slice owns startup dispatch, package wiring, snapshot traversal and their regressions.
The earlier pre-tool repair was merged separately; this work does not resume the cancelled prompt task.
The source change preserves snapshot integrity verification while using cached directory entry metadata.
Dispatcher, package-context and snapshot regressions pass. Native instrumentation traced the remaining
cold failure to serial file reads: individual PowerShell files took 1-4 seconds to read in native hook
processes. Bounded concurrent reads retain every integrity check and deterministic hash framing.
Cold plus two warm native starts now pass, with three completed SessionStart handlers each, all expected
context and no timeout or dispatcher-overrun notice. Evidence is in
`C:/Users/TommySeery/AppData/Local/Temp/codex-startup-verified-t_7d7vla/attempt-{0,1,2}.json` and
workflow run `fix-startup-hook-timeouts`, label `native-parallel-startup-acceptance`.
Full validation belongs to PR CI.

The candidate incorporates main at `fb365abb8478a87eb8f0129312c839b05debbc0a`. Combined dispatcher
tests passed, all three startup handlers passed three native runs, and a fresh retry verified startup
plus the first prompt after one transient first-prompt timeout. The native review found an old test
assuming four Codex registrations; it is corrected and all four goal-continuation tests pass.
The independent workflow lens found no other defect. The work order is
`reviews/Fix-InjectHarnessPermissions.md`; incremental review covers the test correction.

CI run `37521879275` on `39d77a80f2067f795c6b59b3fa62567cbb08c602` executed no steps. Both guard
and verify jobs were rejected by GitHub for failed account payments or an insufficient spending limit.
Resolver: the account billing administrator. Unblock: restore Actions billing/spending availability,
then rerun CI on PR 119's current exact head. No merge or active-profile installation has occurred.

## Completion

- Focused regressions prove hook arguments, context aggregation, block/failure reporting and launch count.
- Isolated native Codex startup runs the generated candidate with trusted, enabled hooks and no timeout.
- Review is complete on the delivered candidate; required Windows CI and post-merge generation pass.
- Report source delivery and active-profile adoption separately; never claim permanent immunity to host failures.

## Next action

Complete incremental review and preserve the clean watermark. After billing is restored, rerun exact-head
CI, merge under the recorded standing authorization only when gates pass, and verify post-merge package
generation. Do not repeat native startup tests unless executable startup code changes or a new failure
requires them. Installation into the user's active profile remains outside the standing source-only grant.
