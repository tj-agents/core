# Close out only when the owning work is done

## Outcome and authority

A PR merge is a slice checkpoint. Keep the owning CLI and checkout available while authorized work remains. Demand cleanup and verified close only at whole-work completion or an explicit close request. Preserve cleanup proofs, non-forced removal and a concise stale-worktree inventory.

Tommy requested execution of `C:/Users/TommySeery/.claude/plans/tj-agents-core/merge-cleanup-close-gating-handoff.md` on 2026-10-19. This authorizes implementation, focused tests, push, a plain GitHub PR, Windows/Linux CI and merge through the repository flow. No installation or unrelated session cleanup is authorized.

## Ownership and delivery slice

- Worktree: `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-CloseoutOnlyWhenDone`
- Branch: `Fix/CloseoutOnlyWhenDone`
- Base: `281303c399046273be7b9d129daf8a9d4bde4d5b`
- PR: not opened
- One focused slice: merge cleanup timing, its proof boundary, shared instructions and host regressions. Expected below 1,000 substantive changed lines. Instructions describe the runtime contract and must remain consistent with it.
- Preserve other owners' edits. Exclude `close_session.py`, `test_session_close_operation.py`, `plans/concurrent-session-close/`, `startup_binding.py` and terminal launchers.
- `scripts/worktrees.ps1` is absent; the documented native Git fallback created this clean isolated checkout from fetched `origin/main`. No open generated-sync PR was present.

## Decisions and investigation

Use existing continuation and close state; do not create another completion store. Investigation selected L3 because owner and explicit-close association needed resolution. Specified implementation and ordinary review select L4. Mechanical delivery selects L7 or L6 for a monitor loop.

The resolved cleanup signal is canonical owner `state == complete`, validated checkout/binding identity and a fresh `completion_check(...).report_ready is True`. The fetched runtime and continuation Stop already use that outcome-ready distinction: full `ready` additionally requires cleanup, so requiring it before cleanup would create a cycle. No unchecked acceptance, goal or PR task may pass report readiness. Explicit close remains owned by the existing machine close arm/verified exit procedure. A known unfinished or invalid owner preserves the checkout before proof can archive/reset it; no owner retains the established manual cleanup-proof behavior. Shared completion resources resolve relative to the shipped helper, never the target checkout.

The reported defect is in `merge_cleanup_gate.py`: a merge records `session_exit_required=True`, Stop blocks solely on confirmed merge, and repository reminders demand unrelated sessions close. `cleanup_proof.py` also needs inspection because invoking it inside a dirty merged checkout can archive/reset remaining work before checking whole-work completion.

The handoff supplies the established defect and accepted use of existing state; this is an existing component repair, with no new reusable component selection. Read README, AGENTS, CODE_CONVENTIONS and SOURCE_LAYOUT. Shared sources under `.agents/` are authoritative; generated distribution stays uncommitted.

## Steps and acceptance

- [x] Resolve a validated existing completion/explicit-close signal with exact owner scope.
- [ ] Implement quiet continuation after merge and concise nonblocking inventory; preserve proof and safe close paths when finished.
- [ ] Cover ongoing work, verified completion, explicit close, stale/foreign state, and both Claude/Codex paths with focused tests.
- [ ] Update affected shared instructions and shipped harness manifests with the contract change.
- [ ] Commit a focused green candidate, independently review, publish, observe green Windows/Linux CI and merge through guarded delivery.
- [ ] Verify causal main regeneration and whole-goal completion, then perform only this session's safe closeout.

## Current progress and verification

Fresh worktree created from the fetched base. The L3 investigation completed. After the native session resumed, its former process and delegated contexts were absent; partial changes were reconciled from Git. One replacement L4 worker owns the remaining runtime/tests and one L5 worker owns disjoint instruction/harness validation. The existing foreground owner was safely reclaimed by the resumed Codex process after verifying the old process had exited; no scheduler writer is registered while those leases are active. The workflow inspection works; canonical skills were read directly after an earlier skills resolver failure. Current helper help exposes the required review-path and review-record operations. The plan host-coverage validator and plan graph passed (one pre-existing oversized-ledger warning). No implementation tests claimed yet. Canonical defect record: primary checkout `BUGS.md#B022`.

## Reviews

Pending implementation and immutable candidate.

## Next Steps

Scope: whole plan through all remaining phases and terminal delivery.
Current slice: remove merge-triggered forced close timing while retaining cleanup safety.
Remaining scope: implementation, host regressions, review, CI, merge and safe whole-work closeout.
Done when: all acceptance checks pass, the source PR is merged with green Windows/Linux checks and causal publication succeeds.

Qualify the completed runtime and instruction edits, commit one stable candidate, then obtain independent frozen-head review before publication and guarded delivery.

## Host coverage

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/hooks/merge_cleanup_gate.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Continue after a merged slice while work remains; enforce safe closeout only when owning work is complete.",
      "source": ".agents/hooks/merge_cleanup_gate.py",
      "mapping": "Shared merge hook through the engineering Claude harness.",
      "verification": {"level": "planned", "result": "pending", "evidence": "Focused Stop, completion, explicit-close and inventory regressions will exercise Claude hook payloads."}
    },
    {
      "host": "codex",
      "behavior": "Continue after a merged slice while work remains; enforce safe closeout only when owning work is complete.",
      "source": ".agents/hooks/merge_cleanup_gate.py",
      "mapping": "Shared merge hook through the engineering Codex harness.",
      "verification": {"level": "planned", "result": "pending", "evidence": "Focused PreToolUse and Stop regressions will exercise Codex payloads without merge-triggered nagging."}
    }
  ]
}
```
