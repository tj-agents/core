# Machine events progress

Plan: MACHINE_EVENTS_PLAN.md
Branch: Feature/MachineEvents
Worktree: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-MachineEvents
PR: not opened
Status: review candidate

## Current state

Publisher/reconcile and personal scheduler-removal commits exist. Core listener, setup migration and fixtures are implemented. All 62 callers are prepared under core/.worktrees/machine-event-callers; runtime inventory is kept outside public source. No production topic, publisher variable, service, task or ruleset has been changed.

Verification: core 20 listener/setup and 34 updater fixtures pass; packaging and catalog digest checks pass. github-actions 8 publisher/reconcile fixtures, 13 existing policy fixtures and 102 scaffold tests pass (14 platform-specific skips). Personal's 7 identity fixtures pass. One bounded ntfy-to-GitHub check passed for tj-agents/core without a ruleset write or agent session. Linux installed acceptance remains unverified.

## Next Steps

Workflow lint passed. Freeze the three candidates for source/security review; resolve findings, publish the source reviews and deliver the prepared fleet caller artifact.

Scope: whole-plan
Current slice: core listener/setup and publisher integration
Remaining scope: independent review, source delivery and prepared caller rollout
Done when: the full requested event channel is shipped and setup owns its lifecycle; any platform or deployment gate is recorded explicitly

## Reviews

The configured review-lens model is unsupported in this account. The review workflow explicitly routes role/model unavailability to the parent over the same immutable candidate; use that fallback for the native-general and security checks. Parent inspection found and fixed Linux setup failing when crontab is absent, and pins administrative gh requests to github.com. Final frozen-candidate review is pending. The legacy workflow helper's skill lookup is incompatible with the canonical layout; use the workflow's native-tool fallback.
