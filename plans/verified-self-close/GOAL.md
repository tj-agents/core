# Verified self-close fallback after terminal discovery refusal

Status: focused verification passed; immutable candidate preparation active.
Date: 2026-10-12
Branch: Fix/VerifiedSelfCloseFallback
Worktree: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-VerifiedSelfCloseFallback
Base: origin/main at bdb63914c03e6d5d62dcac7edb556d5a79c90b85
PR: not opened
Predecessor: native Codex 01a12d05-0e36-7cd2-afac-1936aa63404b, PID9104/start1791756662.4871101, cwd Fix-FollowupRecoveryOwnership.
Lane: L3 for bounded diagnosis and safe terminal/process boundary; route specified implementation/review L4 and mechanical delivery L7.

## Outcome and authority

Tommy explicitly asked on 2026-10-12 why the completed CLI remained open and instructed investigation of Core. engineering:session-guidance supplies standing standards-source repair authority to diagnose, implement, test, independently review, open the personal GitHub PR and normally merge once gates pass. This is a distinct bounded side workstream; the predecessor retains conversation accountability and its completed PR207 evidence. Do not reopen the follow-up repair, edit settings/controller worktrees, change normal profile configuration, install into consumers, start daemons, bypass PID/start-time or peer-tab safeguards, or perform unrelated cleanup. Preserve this predecessor's worktree under its recorded limit unless later explicit authorization applies. CLI exit is independent of worktree deletion.

## Observed evidence

PR207 merged and generated publication verified; original source task completed. The predecessor delegated delayed self-close after its final report and did not reconcile actual outcome. Worker ran exact close.py, which failed Windows Terminal target is absent or ambiguous. The observer recorded accepted and armed, then cancelled: verified host (or Windows wrapper) did not exit. Actual evidence files are C:/Users/TommySeery/.agents-state/merge-cleanup/results/1f29421b77f448e39c489f380948dbc2.json and .accepted/.armed. Exact host PID/start/session/worktree match above; no closure success is claimed.

Fresh host-side read-only inspection on 2026-10-12 verified own_host_and_entry matches PID9104/start1791756662.4871101 and exact cwd. close_tab.merged_inventory returned actual_tab_count=0, with own registered title Core: recover follow-up ownership present only as actual=false. Thus this incident is not missing registration or invisible native process ancestry. The Windows Terminal UI discovery limitation's infrastructure cause remains unknown.

close.py and finish.py duplicate close_host: verified_live is checked; normal terminal-close path catches only TerminalUnavailable. Windows close_entry raises broader TerminalRefusal for absent or ambiguous actual target, so verified self-host exit is not attempted and observer cancels. Existing tests/test_finish.py verifies unavailable-terminal fallback and PID recheck but lacks this observed refusal path. Peer/tab close correctly refuses ambiguous targets; preserve that policy. An explicit existing AGENT_FINISH_CLOSE_MODE=process branch exists; evaluate it as a supported incident close path without configuration changes or alternate kills, not as the permanent repair.

Existing .agents/machine/TECH_DEBT.md first entry already owns wider registered sandboxed CLI close/finish acceptance. Link this incident and keep unrelated Linux namespace/registration questions separate. plans/sandbox-setup-read-failure/GOAL.md records the same Windows tab-discovery refusal and registry-only inventory. Do not claim that this narrower correction resolves all historical acceptance debt.

## Next Steps

1. Acknowledge native session/checkout/branch/pickup in this goal before source edits. Read repository AGENTS.md, README.md, CODE_CONVENTIONS.md, governing peer-cli/session-guidance, and linked problem records. Independently reproduce the refusal with mocked platform inspection and no real peer kills; determine safe self-host fallback and whether closure contract/reporting needs a directly causal clarification.
2. Implement the smallest correction for the verified own-host path in canonical .agents/machine/utility/peer-cli/scripts and focused tests/test_finish.py/test_close_tab.py; preserve all identity refresh, observer handshake, wrapper verification and peer-tab ambiguity protections. Unknown or changed host must never be killed; process exit must not claim tab closure. Avoid a broad exception swallow or arbitrary signal command. No new code comments. Extend existing owners; no new skill.
3. Run meaningful focused tests through workflow_ops compact captures; preserve Windows/Linux compatibility. Add coverage for absent/ambiguous terminal, PID reuse/change after inspection, wrapper safety, successful observer exit evidence, retained checkout and unchanged peer ambiguity refusal. Do not run complete matrices locally; draft PR CI owns them. Record exact commands/results and observed limitations.
4. Commit verified coherent source/test/record slice, run independent frozen review, fix actionable findings, push/open one plain GitHub draft PR, bind one continuation and exact-head CI monitor, drive Windows/Linux green, mark ready and merge normally under standing tj-agents authority. Never commit plugins generated output. Verify only causal generated publication.
5. Keep terminal closure owned until actual receipt/process evidence resolves it. Do not silently replace closing with a delayed worker promise. For this predecessor, reconcile the existing close receipt and any later process-mode attempt as exact evidence; do not force-close an active/new task. Use the supported own close/finish procedure for this successor after its actual completion report; maintain one owner if the command fails.

## Successor pickup

Native Codex session 01a12d92-aec1-75c0-b285-b0ba8cd4a4f3 acknowledges this handoff on 2026-10-12 from the exact recorded checkout and branch Fix/VerifiedSelfCloseFallback, at base bdb63914c03e6d5d62dcac7edb556d5a79c90b85. This session is the sole writer for the isolated repair; predecessor scope and checkout retention remain preserved. Ordinary command execution reports runtime 0.163.0-alpha.1. Existing dirty problem records belong to this repair.

Diagnosis selects L3: the fallback boundary requires checking process identity and terminal refusal semantics. The canonical Codex table resolves L3 to gpt-6.1-sol/high; this matches the handoff's selected lane. No model switch is claimed. Workflow inspection succeeded through supported host-side execution after normal sandbox access to shared Git metadata was denied.

## Current repair state

Reproduction with mocked Windows inventory confirmed TerminalRefusal escaped close_host before its mocked process signal. The repair catches that typed terminal refusal only in the two own-host entrypoints and preserves the immediate host and wrapper identity checks. Peer terminal closure retains its exact-target refusal. No closure-guidance change is needed: the existing peer-cli contract already distinguishes own-host exit from tab closure and preserves checkout files.

Implementation phase selects L4 for this specified, testable correction and its regression coverage; a bounded lane_l4 worker owns only the two entrypoints and tests. One delivery slice starts from the recorded origin/main base, includes these four code/test paths and existing causal problem records, has no stack dependency, and is expected below 200 substantive changed lines. Verification is focused local tests, independent frozen review, and Windows/Linux PR CI. Main advanced with settings-contract changes that do not touch this repair's code/test paths; synchronize before final review.

The native successor attachment is PID36084/start1791765947.727129, session 01a12d92-aec1-75c0-b285-b0ba8cd4a4f3. Continuation owner 5fc608727d8469fe42336d0a was initialized and claimed by that PID; receipt-owned Windows task AgentStandards-Continuation-2a5d8bb8edf42d6ad780f11eefcbb98b197c00ef16997132621cdf7a93f070e0 registered with the fixed native runtime. A supported wake returned working while the foreground lease retained one writer; no unattended child execution is claimed.

The predecessor receipt was reread: status cancelled, error verified host (or Windows wrapper) did not exit. No new close attempt or peer kill was performed. Actual predecessor liveness/task ownership requires reconciliation before any later supported attempt.

## Verification

- `workflow_ops.py --root . --workflow-run-id verified-self-close run --label close-tab-focused -- python -B -m unittest discover -s tests -p test_close_tab.py -v`: exit 0, 32 tests passed; artifact 0758d1e38b17e95a-close-tab-focused.log in the shared Git workflow run.
- `workflow_ops.py --root . --workflow-run-id verified-self-close run --label finish-close-focused -- python -B -m unittest discover -s tests -p test_finish.py -v`: exit 0, 27 tests passed, including actual disposable host exit/observer evidence and retained checkout for close, removed disposable worktree for finish; artifact 0a43720bbe71176e-finish-close-focused.log.
- `python -B scripts/sync_harness_manifests.py --check`: three manifests valid. `git diff --check`: passed. Plan graph: zero errors; one pre-existing unrelated progress-size warning.

The correction is two source lines; the changed tests add coverage without changing the peer close implementation. Process evidence establishes session exit and does not establish an actual terminal tab closed. Complete platform matrices remain with draft PR CI. Next action: commit the coherent repair and records, integrate current origin/main, then freeze independent review.

## Acceptance

Safe self-host exit remains available when actual terminal identity is unavailable/ambiguous, with no peer-tab ambiguity bypass; changed/unknown PID/start-time still refuses. Both close and finish regression cases pass, process/observer evidence distinguishes CLI exit from actual tab closure, checkout limits remain respected, both platform CI jobs execute and pass, independent review approves, source PR merges and its causal generated distribution is verified. Report exact result, not launch/promise as success.

## Problem records

Bug: BUGS.md#B004
Mistake: MISTAKES.md#M012
Existing owning machine debt: .agents/machine/TECH_DEBT.md#codex-close-and-finish-still-need-acceptance-from-a-registered-sandboxed-cli
