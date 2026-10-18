# Verify native handoff startup

Tommy explicitly authorized causal repair on 18 October 2026 after the tracker-aware skills launch
printed success without a claimed successor. Owner: codex:01a1415f-6448-7123-8b17-c7fb67aee637.
Work item: handoff/verified-startup. Source: tj-agents/core machine launchers and startup wrapper.
Checkout: .worktrees/Fix-VerifiedHandoffStartup; branch Fix/VerifiedHandoffStartup; base 728ea8b2.
Repair workflow: engineering:self-repair. One foreground writer; unrelated sessions retain ownership.

## Evidence and boundary

Both native handoff launchers emit agent-handoff-submitted after terminal submission without observing
startup_binding. The tracker-aware task remains proposed with no registered sessions and its pickup
pending. No status receipt was passed for that failed attempt, so its underlying native startup error
is not retained. PR291 addresses bootstrap package recovery; merged PR294 addresses resumed-session
receipts. Neither connects new handoffs to verified startup. This repair reuses launch_status and
hook_dispatch's existing per-attempt SessionStart acknowledgement. Normal idle CLI launch behavior is
preserved. Confirmation means native SessionStart, never a claim that a successor read the goal.

## Outcome and validation

One focused delivery: both launcher integrations, shared waiter, Codex opt-in SessionStart acknowledgement,
regressions for startup failure, early CLI exit, missing wrapper, ambiguous preparation, acknowledgement
and preserved ordinary idle startup; existing terminal tests and required Windows/Linux CI.
No runtime/session relaunch until the correction passes. Then reconcile the failed tracker-aware attempt
and verify real pickup separately. The migration task and its docs plan are outside this writer's scope.

## Progress

- Isolated source checkout created from fetched main; task claimed by this foreground session.
- Initial focused Windows suites passed: handoff startup6, Codex39, Claude41, startup binding17,
  shared agent CLI84 and open Claude27. Native review found two bounded polling/receipt defects;
  both are being corrected with regressions. Independent workflow lens unavailable (unsupported
  reviewer model); its same bounded check returns to this parent under the documented fallback.
- Native acceptance: corrected source launcher verified SessionStart on the single retry attempt
  Temp/tj-agents-handoff-3pd8lh3y/status.json. Preparation began1792328535.86 and native acknowledgement
  completed1792328715.33, approximately179.5 seconds. Startup slowness remains the existing B016 concern.
- Actual successor codex:01a14f1d-abd0-74e0-9b75-b814a208ea87 claimed work-items/record-writers as active
  owner and began source-skill discovery. The second handoff is picked up; no further retry is needed.
- Review preparation took several minutes while materializing/verifying its bundle; preserve as
  evidence for the existing validation-efficiency investigation, not a second repair workstream.

## Next Steps

Finish the two review corrections, validate and review their delta, then deliver through normal source
gates. Preserve the now-active source-skill successor and the separate migration owner.
