# Recover Codex preflight failures without repeated user intervention

## Authority and ownership

Bounded standards-source repair under engineering:session-guidance's standing authorization, reinforced by Tommy's 2026-10-11 request to fix the repeated intervention loop. This checkout and branch own only this side workstream. The existing fixed-runtime successor remains sole writer of Fix-SandboxSetupReadFailure, and its parent remains sole writer of Fix-DependentPrBranchCleanup. Do not edit or adopt either sibling goal.

Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-CodexPreflightRecovery
Branch: Fix/CodexPreflightRecovery
Base: origin/main at 3cf59c0
PR: not opened
Lane: L3 for causal diagnosis and bounded recovery design; resolve model/effort from the installed canonical table. Route implementation and review to their appropriate lanes.

## Outcome and limits

Repair the core-owned launcher/preflight recovery mechanism that turned an approved fixed-runtime reopening into another user intervention. A safe recoverable refresh failure should receive bounded owned recovery while freshness, package authenticity, hook trust and sandbox controls remain enforced. Establish the cause before choosing a repair. Validate Windows and Linux behavior, commit, independently review, open a focused plain GitHub PR and merge once repository gates pass under the standing source-repair authority.

Do not solve this by bypassing failed hook trust, disabling hooks/sandboxing, changing ACL policy, killing shared peer processes, editing installed cache files manually, blindly retrying ambiguous terminal submission, or installing a new machine profile. Machine installation outside this source repository remains separately gated. Generated plugins output stays uncommitted. Existing release compatibility remains preserved.

## Evidence

The user approved isolated official Codex 0.163.0-alpha.1 installation. Actual fresh-host sandboxed Get-Content passed with exit 0, and matching setup refresh errors=[] while peers remained active. Reopening through the installed machine 2.1.16 packaged handoff launcher then definitively failed before tab submission:

Codex plugin sync failed: plugin marketplace upgrade --json: Failed to upgrade marketplace base-agents: failed to refresh plugin cache for engineering@base-agents: failed to back up plugin cache entry: Access is denied. (os error 5)

An attempted direct-native fallback was rejected by automatic approval review because it skipped the failed packaged plugin-refresh/hook-trust preflight and was not specifically authorized. It was not executed. Do not reproduce that bypass through another path.

Read-only CreateFileW probes requested DELETE, READ_CONTROL and WRITE_DAC against the engineering cache directory and version directory with FILE_SHARE_READ|WRITE|DELETE; all handles opened successfully and were closed without modification. This alone does not prove the failed rename's cause.

The complete official marketplace upgrade through the already installed stable 0.162.0 native CLI subsequently exited 0 with errors=[] and upgraded the base-agents marketplace root. After that observed prerequisite recovery, the normal fixed-runtime packaged launcher succeeded with all refresh checks, reported Trusted 10 tj-agents hook definitions, and submitted one 0.163.0-alpha.1 tab. This observation could be transient/cache-state-dependent or runtime-specific; do not assert alpha causality without a discriminator.

The handoff launcher treats SyncError as fatal. The current typed terminal launcher catches SyncError and continues with installed plugins. Existing PR #81 Fix/CLIRefreshTimeouts owns bounded timeouts and warning behavior, but supplied evidence does not establish Access-denied recovery there. Reconcile owning review before publication if the causal fix belongs to that existing slice; avoid duplicating its work.

Relevant canonical source: .agents/machine/scripts/codex_marketplace_sync.py, codex_hook_trust.py, codex_terminal_launcher.py, agent_cli.py, and .agents/machine/utility/handoff-codex/scripts/launch_codex.py. Source freshness/security checks must remain real, not mocked acceptance claims.

Installed native execution runtime: C:/Users/TommySeery/.local/share/codex/runtimes/0.163.0-alpha.1/bin/codex.exe
Installed stable management runtime: C:/nvm4w/nodejs/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe
Invocation-local Responses compatibility catalog: C:/Users/TommySeery/.local/share/codex/runtimes/0.163.0-alpha.1/responses-compatible-models.json
Original evidence owner for reading only: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-SandboxSetupReadFailure/plans/sandbox-setup-read-failure/GOAL.md

## Next Steps

Pickup acknowledged 2026-10-11 by Codex session 01a12aef-9dbc-7cb2-b5a6-b5ac56b71cf0, running codex-cli 0.163.0-alpha.1. Checkout and branch match the handoff; no deliverable changes existed at pickup. L3 causal diagnosis is delegated to the canonical lane worker, with this session retaining goal ownership.

Scope: whole goal through repair, review, validation and terminal delivery.
Current slice: bounded preflight recovery with security regression coverage.
Remaining scope: causal diagnosis, implementation, independent review, Windows/Linux checks, PR and merge.
Done when: the focused repair is reviewed and merged with required checks passing.

Acknowledge pickup here with your identity and runtime version before deliverable writes. Load plan-execution and lanes, read repository conventions, and continue this bounded standards-source repair immediately. Diagnose the failed cache transition and assess the inconsistent launcher recovery paths. Use existing source-owner evidence and tests; do not repeat completed archive/runtime verification. Reproduce a focused causal regression with disposable caches or controlled mocks as appropriate, implement the smallest safe recovery, test failures still enforce authenticity/hook-trust/security, validate cross-platform code and deliver through repository gates. Keep this same goal current with actual evidence and next action. No routine continuation approval is required.

## Progress

2026-10-11: Reconciled the active branch and PR #81. This branch had no implementation; PR #81 remains open with a failed verify check and only owns the older PowerShell timeout work, so it is not a dependency for this Python recovery.

Implemented the bounded recovery in `.agents/machine/scripts/codex_marketplace_sync.py`: retry once only when Codex reports the observed `plugin marketplace upgrade` cache-backup access-denied error. The retry repeats the marketplace upgrade before inventory, installation and hook trust continue. All other refresh errors, including hook-trust failures, remain fail-closed. Added regression coverage for the one retry and retained the fatal-error coverage.

Focused validation passed on Windows: `python -B -m unittest tests.test_codex_marketplace_sync tests.test_launch_codex -v` (75 tests passed; 1 symlink test skipped by the filesystem).

Next action: refresh generated package output for validation, run the remaining required checks, commit the focused candidate, then enter independent review and delivery.
