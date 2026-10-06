# Repair Codex startup hook timeouts

Status: implementing

PR: not opened

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
Dispatcher, package-context and snapshot regressions pass. Native cold acceptance still reproduced
engineering and machine timeouts, so source implementation alone does not satisfy completion.
The next diagnostic instruments Python entry, snapshot verification, dispatch and exit in an isolated
native profile to locate the remaining delay. Full validation belongs to PR CI.

## Completion

- Focused regressions prove hook arguments, context aggregation, block/failure reporting and launch count.
- Isolated native Codex startup runs the generated candidate with trusted, enabled hooks and no timeout.
- Review is complete on the delivered candidate; required Windows CI and post-merge generation pass.
- Report source delivery and active-profile adoption separately; never claim permanent immunity to host failures.

## Next action

Resolve the remaining native startup failure, then freeze and review the passing candidate.
