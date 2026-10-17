# Close completed CLI sessions through a public Core operation

Status: In progress
Source owner: machine/close and base/goal-continuation
Repair workflow: engineering:self-repair

## Problem

After completing PluginScoping, the originating agent reported "Done" but never invoked the required
session-close helper. Worktree cleanup and a successful completion check were mistaken for the terminal
operation. Existing merge-command-triggered cleanup obligations did not cover Tommy's manual merges.
The close instruction was buried in engineering delivery and peer-session guidance.

## Authorization

Tommy requested a fix and explicitly approved a dedicated skill. He clarified that a CLI must close
whenever all its owned work is done, in every repository consuming Core, regardless of PR or plan use.
This work owns only generic session-close behavior. Preserve other sessions' checkouts and their
OpenCli, HandoffScope, rolling-dependency and harness-injection changes. No force or hook bypass.

## Implementation

- Public machine:close operation and host adapters; prepare before report, route at Stop, execute the
  foreground complete operation only after every other Stop-gate verdict has been accepted.
- Base-owned terminal requirement, selected by ordinary tasks and engineering deliveries alike.
- Sequential machine-hook chain updates turn state before using existing verified close helpers.
- Missing preparation on a direct "Done" completion report routes back to the skill; wording alone
  never authorizes a process signal. This heuristic is a backstop, not proof of task completion.
- Default retains checkout. Removal still needs the existing merged-worktree proof and helper.
- New prompts cancel preparation; exact host identity, attachment, activity and observer checks remain.

## Validation

The focused operation suite passed 18 regressions. Distribution generation and -Check pass
after updating the skill roster and declared machine hook. Run the existing closure regressions,
packaging and source suites, independent review, and both native host acceptance checks before claiming
the operation has been verified on real CLIs. Tests with mocked helpers do not establish native closure.

## Next Steps

1. Finish regression and disposable-host acceptance coverage, including cancellation and refusal.
2. Address native review findings on Stop-gate ordering and preparation permissions, then freeze and
   independently review the repaired candidate. The workflow lens is unavailable (unsupported model),
   so its check returns to the parent as required by the review contract.
3. Publish one Core PR and deliver through the repository's guarded merge workflow and configuration.
4. Observe generated publication, finish checkout cleanup, report the actual terminal state and invoke
   the close operation if supported in this originating host. Do not call preparation successful closure.
