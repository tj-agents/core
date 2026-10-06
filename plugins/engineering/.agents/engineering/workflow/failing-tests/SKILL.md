---
name: failing-tests
description: What to do when a test run comes back red — enter the run/diagnose/fix/re-run loop and drive it to green rather than reporting the failure and waiting, fix the real bug wherever it lives (service, handler, page object, step definition, fixture, config) instead of disabling, skipping, marking flaky, or inflating a timeout to get past it, and for browser or service E2E do proper flaky-versus-real triage by re-running the failed scenario alone on a fresh stack — passing clean proves a host-load blip, failing again proves a real bug. Use the moment any unit, integration, API, or UI test run fails, or when tempted to skip a test or raise a timeout to make a suite pass. A compiler, restore, or build error is not a red run and does not select this skill.

kind: workflow
domain: process
---

# A failing test is never just reported

Whenever **any** test run comes back red — unit, integration, API, or UI — the next action is the
diagnose-and-fix loop, **not** a status report back to the human. **A failure *is* the trigger**; don't make
someone ask for it.

The loop is yours end to end: **run → diagnose → fix → re-run until green.** Find the root cause and fix it in
code, wherever the real bug lives — service, handler, page object, step definition, fixture, configuration.

This is hook-enforced. `.agents/hooks/red_run_gate.py` fires on a runner that exited non-zero
(PostToolUseFailure) and on a `gh run view` / `gh pr checks` read reporting a failed CI or merge-queue run
(PostToolUse), naming this skill and the tier below that owns the failure; on Stop it blocks the turn from
ending while a red run is unanswered. It stays silent for a build, restore or compile error, for a command
that merely exited non-zero, and once every named skill is proven loaded this session.

**Route by tier.** Each tier has its own procedure, and entering it *is* the next action; picking through the
failure by hand is how a tier's known traps get rediscovered one at a time.

| Red run | Procedure |
|---|---|
| Unit | Use the repository's unit-test guidance when present; otherwise the parent diagnoses the smallest failure, fixes its cause, and reruns it |
| In-process .NET integration using `WebApplicationFactory` | the selected stack or IDE's `integration-debug` procedure, when installed and applicable |
| Service E2E (no browser) | the selected stack or IDE's `e2e-api-debug` procedure, when installed and applicable |
| Browser E2E | the selected stack or IDE's `e2e-ui-debug` procedure, when installed and applicable |
| Both E2E tiers at once | the selected stack or IDE's `e2e-debug` procedure, when installed and applicable |

A repository-specific tier procedure applies only when its described runner and harness match the red run.
Otherwise keep diagnosis in the parent and follow the repository's own test guidance; never force a generic
unit runner into an unrelated ecosystem's integration workflow.

A test the IDE never discovered is not a red run at all — that is
the selected IDE's test-discovery repair procedure, when installed and applicable.

**Neither is a compiler, restore, or generator error.** A build that never produced a test result has nothing
to triage: fix it in the ordinary diagnose/fix/rebuild loop and enter here only once a run happens and a test
fails. That holds when the thing that stopped compiling is the test project itself.

## Never bypass instead of fixing

Do not disable, skip, quarantine, mark-as-flaky, build-skip, or inflate a timeout to get past a failure. That
is bypassing, not fixing, and it converts a caught bug into an uncaught one plus a lie in the suite. If a
timeout genuinely needs raising, that is a diagnosis you can state and defend, not a knob to turn until the
red goes away.

## Flaky-versus-real triage, for E2E only

Re-run the **failed scenario alone on a fresh stack**:

- **Passes clean** → a host-load blip. That is now *proven*, not assumed.
- **Fails again** → a real bug. Fix it.

Where a runner already does this for you — an isolated retry of just the failures
of just the failures — that *is* this triage, and its verdict stands. Re-running by hand afterwards proves
nothing that has not already been proven.

Before that re-run, rule out the environment: a suite that died at fixture startup with zero scenarios
executed is an environment failure, and the container-runtime check in the `remote-validation` skill comes
first.

## Where the failure came from a merge queue

Don't drive a heavy local suite inline. Reproduce **only** the failing scope, from a dispatch prompt carrying
the worktree path, branch, PR, failing scenarios, and the failure signature — then fix and push, and let the
queue re-run the required suites on the way back in.
