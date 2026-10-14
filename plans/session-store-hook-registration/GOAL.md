# Codex SessionStart store registration

Status: Core delivery complete; probe exited; checkout deliberately retained for continued user work
Date: 2026-10-14
Branch: Fix/SessionStoreHookRegistration
PR: https://github.com/tj-agents/core/pull/247
Worktree: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-SessionStoreHookRegistration
Base: origin/main at 4f760f460ef5fd5ee9362a38e2023093e93ea2fe
Lane: L4 — specified regression coverage for the already working registration path; L3 investigation is complete.

## Outcome and authority

Tommy explicitly called out that a completed Core delivery left its Codex CLI and merged worktree open, and asked for the prevention path to be fixed rather than merely explained. `engineering:session-guidance` supplies standing standards-source authority for this bounded Core repair: diagnose the missing automatic Codex session registration, implement and test the smallest canonical fix, review, open a PR and merge after repository gates pass.

This workstream owns only automatic SessionStart registration and its fresh-host acceptance evidence. It must not alter the separately owned `Fix/CodexMergeCleanupStop` repair, which owns Codex Stop enforcement after a merged PR. It must not close, delete, or otherwise mutate the originating `Feature-WorkItemSessions` checkout.

## Observed evidence

Pickup acknowledged on 2026-10-13 by the successor in this exact checkout and branch. This session is the sole writer for this goal. The first action is read-only comparison of the enabled machine plugin, trusted hook definition, snapshot and canonical registration path. Investigation selects L3 because the first divergent state remains unknown; the canonical Codex lane table resolves it to the investigation worker.

On 2026-10-13, the source worktree `Feature-WorkItemSessions` merged PR #228, but its Codex session was absent from `C:\Users\TommySeery\.agents-state\sessions.db`. A read-only query returned two active rows, both for other worktrees:

- `career.worktrees/Docs-AzureLearning`
- `core.worktrees/Fix-DocsReviewProportionality`

The source manifests declare `register_session.py` for Codex SessionStart and `session_store.py` for prompt/stop, but source declarations and a cached `session_store.py` do not prove that the active installed Codex hook definition is enabled, trusted, or executing. The precise failure point is unknown.

## Reconciled diagnosis and execution

Read-only investigation disproved a failure of the currently shipped registration path. Originating session `01a135ff-de5e-7a50-b7d7-7fae53deef9f` started on October 13 at 17:02:04 BST; PR228 introduced the SQLite hook registration on main at 17:51:33 BST (merge `39f0e49`). The earlier origin `01a1354f-3d06-7c80-83a0-4ab0e6c5d679` started at 13:49:08 BST. Both have native registry entries and no store row. Retained premerge machine snapshots `69d0aff…` and `9cf945a…` contain neither the store nor `_record_session_start`; their exact use by each origin cannot be proven from retained rollout metadata. An already running host does not replay SessionStart when the marketplace refreshes. The package loader correction is already in PR228 (`3df86558f1dfb2193989cd6db054d8596ffb64a3`). No additional runtime repair is supported by this evidence.

The enabled machine 2.1.16 package and active snapshot `182569cd…` both verify against digest `sha256:22049d2585729f4691d32d36cdd1ff7aa5653288a5a9cb6cd11419dda4a66765`; their registration source matches canonical source after newline normalization and imports the real packaged store. Current session `codex:01a13725-d930-7340-8425-8eca8d8e37f0` started at 22:23:10 BST and registered at 22:23:26 BST. Its row has this exact worktree, branch `Fix/SessionStoreHookRegistration`, HEAD `4f760f460ef5fd5ee9362a38e2023093e93ea2fe`, PID30012 and start time `1791926587.123207`. Read-only native process inspection independently matches `codex.exe` with that PID/start time. SQLite was inspected immutably only after checking that no WAL files existed.

One focused delivery slice will strengthen `tests/test_register_session.py` using the real store in source and all supported package layouts, including Windows/Linux CI. Existing loader tests use marker-only stubs and cannot prove persistence. Expected size is below 200 substantive lines, with no runtime, hook, generated distribution or dependency changes. Base remains fresh `origin/main` at `4f760f460ef5fd5ee9362a38e2023093e93ea2fe`. Owning review is PR247 at `352312dafd3e6a43f9bc39911a7674868596e3e5`. L4 implementation is assigned to one bounded worker; this parent retains goal, review and delivery ownership.

Primary incident reconciliation has a preserved conflict: `C:/Users/TommySeery/source/repos/tj-agents/core/MISTAKES.md` is still user-owned and untracked in that checkout. Its M012 history includes separately owned terminal-close obligations and an older limit on additional native sessions. This workstream will not overwrite that record or resolve its separate closure condition. Resolver: primary-register owner/Tommy. Resume condition: release or explicit permission to append this dated registration evidence to M012. The authorized diagnosis and regression delivery proceed independently. This goal retains the exact recurrence evidence and its link to `MISTAKES.md#M012` as requested by the handoff's conflict alternative.

The `workflow_ops skills` legacy flat-layout defect is already owned by `docs/workflows/TECH_DEBT.md`; the supported `name=canonical/path` argument successfully recorded the lifecycle. `plan_graph.py` reports zero errors and one pre-existing oversized-ledger warning outside this goal.

## Scope

- Establish why a newly started Codex session can be absent from `sessions.db`.
- Repair the canonical source or generated-hook installation path that caused it.
- Add regression coverage that proves the SessionStart path records a matching `host:session_id` row.
- Obtain fresh-host acceptance: a newly launched Codex session through the supported wrapper must produce its own row before any completion claim.
- Reconcile the dated evidence into `MISTAKES.md#M012` without overwriting the primary checkout's currently untracked user-owned record.

## Verification

Causal main CI run38475529578 completed successfully (monitor58a62f286a7c6a9e53bc0bd4f97f70f880bfbaffbc80ef993d1f37c43e902766, workflowci, attempt1). Both PR and post-merge Windows/Linux verification are green; regeneration was a verified no-op. The only local blocker is the finished probe's actual tab/process closure. No career/Teams research or Claude launch has started.

Causal regeneration job115565150913 passed and its captured log explicitly reports `Generated output already current.` The generated-path diff between the pre-PR main and fetched merge is empty; no package publication or generated downstream change resulted.

Cleanup preflight independently resolved the parent attachment and returned the exact acceptance probe as another live claimant. One empty mixed-format PowerShell display was briefly misread as exit; the claim was corrected immediately after native/CIM inspection confirmed PID42764 still running with its original start time. No closure or cleanup was performed on that inconclusive evidence.

PR247 merged on October 13, 2026 at 22:06:55 UTC as `6a41416e6783ddbc10663bcf4848916cc1762f47`, after independent review and exact-head Windows/Linux CI run38473175808 passed. Causally bound push run38475529578 is observed through one corrected monitor (forge workflow name `ci`, attempt1); its regeneration job115565150913 already completed successfully. No publishable source changed. The initial run-monitor attempt using filename `ci.yml` refused a workflow-name mismatch before any wait; it was corrected to the actual forge name for the same run/head.

Primary checkout remains on its pre-existing old main with user-owned modified and untracked files. Remote main was fetched only. `MISTAKES.md`, `BUGS.md`, machine debt and engineering resources overlap upstream changes, so fast-forwarding the primary would overwrite or collide with protected user material. Resolver remains the primary-checkout owner/Tommy; this task neither stashes nor overwrites those files. Linked-checkout cleanup can still be proven against fetched `origin/main` without changing primary files.

Continuation owner: `.agents/continuation/owner.json`, owner `04547d86b9a44797e4a82de6`. Foreground claimed and one Windows receipt-owned scheduler registered; observed wake reported `working` while the foreground writer retained its lease. No unattended completion is claimed.

Focused registration/store/snapshot checks passed: 78 tests, four platform-specific skips, on Windows. Full output is Git-private artifact `5e41be3673b5993b-registration-focused.log`; the package-integrity rejection printed by a negative test is expected. The focused source/store test uses disposable paths containing spaces and non-ASCII characters. Final register-session module: 20 passed after portability/cleanup follow-ups. Temporary mutation probes failed as expected: suppressed registration failed all five cases, and removal of the canonical packaged lookup failed its packaged case. Native Codex review completed with exit 0 and no actionable findings; `reviews/Fix-SessionStoreHookRegistration.md` is approved at `352312dafd3e6a43f9bc39911a7674868596e3e5`. The noninteractive reviewer emitted no SessionStart row and was not counted as native acceptance.

One fresh native TUI launched through supported `launch_codex.py` registered `codex:01a1373d-fe0f-7b03-8410-cf0a1412911d` automatically with this checkout/branch and exact candidate HEAD `352312dafd3e6a43f9bc39911a7674868596e3e5`. SQLite and native registry match live Codex PID42764/start `1791928169.4989567`. Independent parent observation retained `registration-fresh-host-observed.json` in the system temporary directory. The probe is read-only and must be closed after its result is reconciled, without touching this checkout. PR247 CI run `38473175808` remains owned through one monitor bound to the exact candidate head.

## Next Steps

Scope: the authorized Core registration work is complete; the separately requested private career documentation now follows.
Current slice: Reviewed PR247 is merged with exact-head and causal main CI green; native acceptance passed and its probe has verified process status exited.
Remaining scope: None for this Core source delivery. This checkout and current conversation are deliberately retained under the loaded merge/peer-cli policy for Tommy's October14 continue instruction; primary user files and the M012 conflict remain preserved.
Done when: Completed — source persistence coverage, native acceptance, review, green delivery, exact probe exit and supported deliberate-retention disposition are observed.

## Cleanup resume context

On October14 the full recorded native entry for acceptance probe01a1373d-fe0f-7b03-8410-cf0a1412911d was independently checked: identity status exited, liveness false, and no other claimant for this worktree. The parent has resumed in native PID40524. The previously recorded human gate is resolved.

The currently loaded installed merge and peer-cli skills require honoring explicit continue instructions and active dialogue, and provide the `merge_cleanup_gate --clear` deliberate-retention escape when no supported post-report execution path remains. The escape was run for this exact linked checkout; it reported no recorded obligation for this target. The goal records deliberate retention, rather than falsely claiming physical checkout removal or host exit. Primary checkout files and the separately owned WorkItemSessions/merge-cleanup-stop workstreams remain untouched. The former scheduler is removed; the Core owner is completed and its merged PR binding released after the fresh completion check. The separately held career work may now begin in its private owner.

## Acceptance

Every new Codex session launched through the supported wrapper records its own SessionStart row in `~/.agents-state/sessions.db`; the record carries the exact `host:session_id`, PID/start time, worktree, branch and HEAD. A focused regression test and fresh-host acceptance both pass. The recurrence is linked to M012, and this repair does not overlap the existing Codex merge-cleanup-stop owner.

## Host coverage

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/machine/utility/peer-cli/scripts/register_session.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "SessionStart writes the native registry and real SQLite session row.",
      "source": ".agents/machine/utility/peer-cli/scripts/register_session.py",
      "mapping": ".agents/plugins/manifests/claude/machine-hooks.json SessionStart",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Actual-store SessionStart integration regression passed for Claude process identity, source layout, native registry and exact SQLite/Git metadata on Windows; Windows and Linux CI both passed for the exact candidate head."
      }
    },
    {
      "host": "codex",
      "behavior": "SessionStart writes the native registry and real SQLite session row.",
      "source": ".agents/machine/utility/peer-cli/scripts/register_session.py",
      "mapping": ".agents/plugins/manifests/codex/machine-hooks.json SessionStart through hook_dispatch.py and codex_hook_snapshot.py",
      "verification": {
        "level": "installed",
        "result": "passed",
        "evidence": "Supported fresh terminal launcher produced codex:01a1373d-fe0f-7b03-8410-cf0a1412911d at candidate352312dafd3e6a43f9bc39911a7674868596e3e5; parent independently matched its SQLite/native registry to live PID42764/start1791928169.4989567. Actual-store tests cover source and all supported packaged layouts."
      }
    }
  ]
}
```

## Reviews

Full native review approved at `352312dafd3e6a43f9bc39911a7674868596e3e5`; canonical work order `reviews/Fix-SessionStoreHookRegistration.md`, no open findings, no security-sensitive changed path. Base reconciliation found no movement.

## Completion boundary

```completion
{
  "outcome": "PR247 delivered reviewed real-store SessionStart regression coverage; native acceptance and all CI passed; the finished probe exited and the checkout is deliberately retained for the ongoing user-requested work.",
  "acceptance": [
    {
      "id": "persistence",
      "criterion": "Actual SessionStart records exact native identity and metadata.",
      "evidence": [
        {
          "source": "Fresh native session codex:01a1373d-fe0f-7b03-8410-cf0a1412911d and registration-fresh-host-observed.json",
          "result": "Exact SQLite/native/process/cwd/branch/head matched without manual bootstrap."
        }
      ],
      "owner": "",
      "next_action": ""
    },
    {
      "id": "delivery",
      "criterion": "Regression reviewed, tested and merged.",
      "evidence": [
        {
          "source": "PR247 head352312dafd3e6a43f9bc39911a7674868596e3e5 and merge6a41416e6783ddbc10663bcf4848916cc1762f47",
          "result": "Independent native review clean; focused tests and exact-head Windows/Linux CI passed; causal main run38475529578 succeeded with no generated changes."
        }
      ],
      "owner": "",
      "next_action": ""
    },
    {
      "id": "incident",
      "criterion": "M012 evidence reconciled without overwriting the primary user-owned register.",
      "evidence": [
        {
          "source": "Reconciled diagnosis and execution in this goal",
          "result": "Dated source evidence retained here; primary-register conflict preserved under the handoff conflict alternative."
        }
      ],
      "owner": "",
      "next_action": ""
    },
    {
      "id": "cleanup",
      "criterion": "Finished probe has verified exit and this checkout has a supported explicit cleanup or deliberate-retention disposition.",
      "evidence": [
        {
          "source": "October14 full native probe-entry/process check and installed merge_cleanup_gate --clear for this exact checkout",
          "result": "Probe identity exited, liveness false, no other claimant; current parent40524 and checkout deliberately retained for explicit continue/active dialogue under loaded policy; no target obligation recorded. Physical removal and parent exit are not claimed."
        }
      ],
      "owner": "",
      "next_action": ""
    }
  ],
  "deliveries": [
    {
      "repository": "tj-agents/core",
      "pr": 247,
      "head": "352312dafd3e6a43f9bc39911a7674868596e3e5"
    }
  ],
  "open_tasks": []
}
```
