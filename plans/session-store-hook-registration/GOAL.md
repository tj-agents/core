# Codex SessionStart store registration

Status: active
Date: 2026-10-13
Branch: Fix/SessionStoreHookRegistration
PR: not opened
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

One focused delivery slice will strengthen `tests/test_register_session.py` using the real store in source and all supported package layouts, including Windows/Linux CI. Existing loader tests use marker-only stubs and cannot prove persistence. Expected size is below 200 substantive lines, with no runtime, hook, generated distribution or dependency changes. Base remains fresh `origin/main` at `4f760f460ef5fd5ee9362a38e2023093e93ea2fe`. Review is not opened yet. L4 implementation is assigned to one bounded worker; this parent retains goal, review and delivery ownership.

Primary incident reconciliation has a preserved conflict: `C:/Users/TommySeery/source/repos/tj-agents/core/MISTAKES.md` is still user-owned and untracked in that checkout. Its M012 history includes separately owned terminal-close obligations and an older limit on additional native sessions. This workstream will not overwrite that record or resolve its separate closure condition. Resolver: primary-register owner/Tommy. Resume condition: release or explicit permission to append this dated registration evidence to M012. The authorized diagnosis and regression delivery proceed independently. This goal retains the exact recurrence evidence and its link to `MISTAKES.md#M012` as requested by the handoff's conflict alternative.

The `workflow_ops skills` legacy flat-layout defect is already owned by `docs/workflows/TECH_DEBT.md`; the supported `name=canonical/path` argument successfully recorded the lifecycle. `plan_graph.py` reports zero errors and one pre-existing oversized-ledger warning outside this goal.

## Scope

- Establish why a newly started Codex session can be absent from `sessions.db`.
- Repair the canonical source or generated-hook installation path that caused it.
- Add regression coverage that proves the SessionStart path records a matching `host:session_id` row.
- Obtain fresh-host acceptance: a newly launched Codex session through the supported wrapper must produce its own row before any completion claim.
- Reconcile the dated evidence into `MISTAKES.md#M012` without overwriting the primary checkout's currently untracked user-owned record.

## Verification

Continuation owner: `.agents/continuation/owner.json`, owner `04547d86b9a44797e4a82de6`. Foreground claimed and one Windows receipt-owned scheduler registered; observed wake reported `working` while the foreground writer retained its lease. No unattended completion is claimed.

Focused registration/store/snapshot checks passed: 78 tests, four platform-specific skips, on Windows. Full output is Git-private artifact `5e41be3673b5993b-registration-focused.log`; the package-integrity rejection printed by a negative test is expected. The focused source/store test uses disposable paths containing spaces and non-ASCII characters. Native fresh wrapper acceptance and independent review remain next, followed by the exact-head Windows/Linux CI matrix.

## Next Steps

Scope: whole plan through all remaining phases and terminal delivery.
Current slice: regression coverage and fresh native acceptance of the existing registration path.
Remaining scope: focused verification, fresh wrapper acceptance, independent review, Windows/Linux CI and delivery; primary M012 append remains with the named register owner.
Done when: exact native SessionStart persistence is verified and the regression PR is merged, with the M012 conflict preserved rather than overwritten.

1. Finish the actual-store regression, run focused source and package checks, and checkpoint the tests-only candidate.
2. Run independent native Codex review through the supported terminal wrapper; inspect its fresh SessionStart row read-only and retain its exact host/session, worktree, HEAD and verified PID/start time. A source test does not substitute for this native evidence.
3. Complete independent review, open one focused PR, observe Windows/Linux CI and merge after repository gates pass. Reconcile the preserved primary M012 conflict without editing that user-owned register.

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
        "evidence": "Actual-store SessionStart integration regression passed for Claude process identity, source layout, native registry and exact SQLite/Git metadata on Windows; Linux CI remains the remote gate."
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
        "evidence": "Current native session codex:01a13725-d930-7340-8425-8eca8d8e37f0 has exact checkout, branch, HEAD and independently verified PID30012/start1791926587.123207 in sessions.db."
      }
    }
  ]
}
```
