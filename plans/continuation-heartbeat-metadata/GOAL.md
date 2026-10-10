# Preserve current continuation recovery instructions during heartbeat

## Defect and authority

The shared continuation CLI accepts `heartbeat --reason` and `--next-action`, but `operate()` only updates foreground activity. Both arguments are silently ignored. An actively owned multi-phase goal therefore retains obsolete recovery steps after its canonical plan changes. Releasing the foreground lease through yield merely to refresh those steps creates a second-owner launch window.

Standing source-repair authority is engineering:session-guidance: diagnose, implement, test, review, open a source PR and normally merge after repository gates pass. The user requires every agent fix to cover Claude and Codex. This is a bounded side workstream; its specified implementation worker owns this checkout only until the stable candidate release. Parent owns review and delivery. The originating Rust/docs rollout remains active under its existing owner. No normal-profile installation, billing, permission or authorization expansion is authorized.

## Ownership and compatibility

Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-ContinuationHeartbeatMetadata
Branch: Fix/ContinuationHeartbeatMetadata
Base: 2dc76412f0794584e36b7440e5cde0bf7a0ce5ac

Existing Core PR161/Fix-ContinuationMonitorActivation is blocked with no foreground or child. Its runtime changes are confined to claim PID/executable validation and parser claim arguments; the heartbeat defect exists unchanged there. Preserve that owner, its held PR and all files in its checkout. This separate heartbeat hunk must compose with its published claim changes. Do not adopt, merge, rebase or write PR161. Core184/ContinuationEnforcement and Feature/ConfigurableAutoMerge have live independent owners and must remain untouched.

## Accepted repair boundary

After the existing exact foreground token/process validation, a heartbeat with a nonempty supplied reason or next action updates the corresponding saved metadata while retaining the foreground token, PID, creation identity, working state and all goal/repository/branch/head/authority/limit bindings. Omitted/empty flags retain prior metadata. Invalid ownership refuses before mutation. Do not use yield, initialize a replacement owner, directly patch owner JSON or modify installed plugin caches.

Own only `.agents/workflows/continuation_runtime.py`, its existing focused runtime test file, any directly governing heartbeat instruction that actually needs correction, and this goal. Do not modify launch, scheduler, claim, checkpoint, authorization/configuration, Stop or merge-gate behavior. Generated output is refreshed for tests and left outside source PR commits per Core guidance. Expected atomic source diff is well below 1000 substantive changed lines.

## Next Steps

Scope: this bounded source defect through verified merged publication.
Lane: L4, specified small shared-runtime repair with meaningful ownership regressions; reroute later phases under engineering:lanes.

1. Acknowledge the parent-assigned bounded writer pickup here before deliverable edits. Read root AGENTS.md/CODE_CONVENTIONS.md and the selected bugfix/lane contracts. Confirm branch/base and the exact ignored-argument path.
2. Repair heartbeat metadata through the existing supported operation without releasing its lease. Add focused behavioral coverage for both Claude and Codex initialized owners: updated recovery metadata persists, omitted/empty flags preserve it, lease and goal bindings remain identical, wrong token/dead identity cannot mutate. Use shared source and existing fixtures; no new host-specific authored copies.
3. Run the focused runtime suite and applicable package/generation checks. Commit only authored source/tests/goal at a stable boundary and release the candidate to the parent without publishing. Parent owns exact frozen review and any serialized correction lease. Record actual both-host evidence and platform limits in this goal before release.
4. Parent review/delivery phase: open a plain GitHub PR in tj-agents/core, preserve repository checks and existing authorization rules, observe the complete exact-head CI, normally merge once reviewed/green, then verify its causally linked main CI and generated publication. No stacked PR or installation. Safely retire only this merged checkout via the supported lifecycle, retaining required evidence.
5. Record terminal delivery or the exact genuine gate/resolver/resume condition. A launch, commit, draft PR or started CI does not satisfy completion. Leave the parent rollout and its foreground owner untouched.

## Completion

Done when: the supported shared heartbeat retains its live lease while updating supplied recovery metadata for both hosts, focused tests and exact-source review pass, the source PR is merged, and causal generated publication succeeds. Source publication alone does not establish installed-profile activation. The parent will use the reviewed published source operation to refresh its own metadata, without installation.

## Host coverage

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/workflows/continuation_runtime.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Update owned continuation recovery metadata during heartbeat without releasing foreground ownership.",
      "source": ".agents/workflows/continuation_runtime.py",
      "mapping": "Shared continuation runtime shipped through engineering harness sources.",
      "verification": {"level": "source", "result": "passed", "evidence": "ContinuationTests.test_heartbeat_refreshes_recovery_metadata_without_releasing_foreground initializes a Claude owner, uses the supported CLI, and verifies metadata refresh, lease and binding preservation, omitted and empty retention, and invalid-owner no-mutation."}
    },
    {
      "host": "codex",
      "behavior": "Update owned continuation recovery metadata during heartbeat without releasing foreground ownership.",
      "source": ".agents/workflows/continuation_runtime.py",
      "mapping": "Shared continuation runtime shipped through engineering harness sources.",
      "verification": {"level": "source", "result": "passed", "evidence": "ContinuationTests.test_heartbeat_refreshes_recovery_metadata_without_releasing_foreground initializes a Codex owner, uses the supported CLI, and verifies metadata refresh, lease and binding preservation, omitted and empty retention, and invalid-owner no-mutation."}
    }
  ]
}
```

## Verified pre-pickup handoff failure and recovered writer boundary

Exactly one native submission created session01a12745-ab05-7d12-8a0c-0d6bfc04ee41 in this checkout. Its recorded turn ended2026-10-10T19:29:19Z after every attempted command failed before launch with helper_unknown_error setup refresh. Its final response explicitly confirms no access to the handoff and no action. Read-only reconciliation finds no pickup acknowledgment, owner file or deliverable edits; only this parent-authored untracked goal exists. Launcher submission did not establish an active writer. No duplicate native launch or messaging probe is permitted. That original idle native session must not begin edits while the recovered bounded worker lease below exists.

Parent /root recovers this unclaimed side implementation through a single bounded L4 collaboration worker, implement_continuation_heartbeat_metadata. The functioning exec path is sandbox_permissions=require_escalated, login=false; ordinary commands currently fail setup before launch. Worker exclusively owns .agents/workflows/continuation_runtime.py, .agents/hooks/tests/test_continuation_runtime.py, a directly necessary existing continuation runtime test fixture, and this goal. All other sources, owners, profiles, launcher/scheduler operations, native sessions, PR161 and Core184 remain outside its lease. Acknowledge pickup, implement the accepted repair, qualify and commit, then stop before review/push/PR/merge so parent can own the next phase. No initialization of another continuation owner or source installation.

## Bounded pickup acknowledgment

The recovered implementation worker accepted this sole writer lease on 2026-10-10. It will make only the bounded heartbeat metadata repair, its focused shared-runtime coverage, and this goal update before returning the candidate to parent /root.

## Implementation verification

The supported CI-style command `python -B -m unittest discover -s .agents/hooks/tests -p test_continuation_runtime.py -v` ran 36 tests and exited 1 after 873.117 seconds. The new both-host heartbeat test passed. Two unrelated process-boundary tests failed on their timing waits: `test_owner_state_read_and_save_tolerate_an_open_reader` and `test_recover_final_launch_receipt_before_budget_gate`. Each immediately passed in isolation with exit 0 (4.903 seconds and 14.819 seconds respectively), so no runtime timeout or unrelated repair was changed.

`python -B scripts/update_catalog_digests.py` exited 0 and refreshed one generated catalog digest. `pwsh .agents/sync-generated.ps1` exited 0 with 3 generated changes, and `pwsh .agents/sync-generated.ps1 -Check` exited 0 after checking 504 package files from 75 shared definitions. Generated output remains unstaged.
