---
name: failing-tests
description: Diagnose and fix a failing unit, integration, API or UI test, or a stalled browser acceptance flow, from observed evidence and focused reruns. Not for compiler, restore or build errors.

kind: workflow
domain: process
---

# Fix a failing test

Owns the loop after any red test run: run, diagnose, fix, rerun until green. A failure is the trigger; fix
the root cause wherever it lives, whether service, handler, page object, step, fixture or configuration,
instead of reporting the red run back.

```text
python -m pytest tests/test_repository_permissions.py -q
FAILED test_every_ci_verify_command_is_allowed_for_both_shells: 18 != 17
Cause: a CI verify step was removed. Fix: update the expected count to 17, then rerun until green.
```

| Red run | Procedure |
|---|---|
| Unit | The repository's unit-test guidance, otherwise diagnose and fix in the parent |
| In-process .NET integration (`WebApplicationFactory`) | The selected stack's `integration-debug`, when installed and applicable |
| Service E2E (no browser) | The selected stack's `e2e-api-debug`, when installed and applicable |
| Browser E2E | The selected stack's `e2e-ui-debug`, when installed and applicable |
| Both E2E tiers | The selected stack's `e2e-debug`, when installed and applicable |

A tier procedure applies only when its runner matches the red run; otherwise follow the repository's own
test guidance. A test the IDE never discovered, or a build that produced no test result, is not a red run.

Never disable, skip, quarantine, mark flaky or inflate a timeout to get past a failure. A timeout change is a
diagnosis you can state and defend. For a suspected flake or timing failure, apply
`engineering:failure-provenance`. A CI failure is reproduced locally only for its failing scope, then fixed,
pushed once and left to CI.

## Observable browser acceptance

Before launching a browser acceptance flow or handing a browser step to the user, observe the real entry
point in a visible browser in the intended desktop session. Declare the first rendered state, the next
progress state and a deadline for each from the project's acceptance contract. A running server, HTTP 200
or a passing headless fixture does not prove visible launch.

Arm timeout evidence before launch: on a missed deadline, capture a safely scoped screenshot, a redacted
DOM or state snapshot and console and request-failure metadata with timestamps and the expected versus
observed step. Inspect it, repair the cause and rerun through the same entry point. Never ask the user for
evidence the agent can capture. If the browser bridge is unavailable, verify a supported fallback that sees
the actual window, without weakening browser security or copying credentials; otherwise report the missing
capability and the unverified step.

A human sign-in or approval is a waiting state, not a malfunction: keep observing non-secret signals and
resume the deadline afterwards. Evidence never discloses passwords, tokens, authorization codes, cookies or
key material, and omits request bodies.

```text
browser-acceptance --scenario first-run --observe --capture-on-timeout --artifacts artifacts/first-run
Expected: the account-choice page renders before the startup deadline.
On timeout: a safe screenshot, redacted state and console/request-failure metadata; fix, then rerun.
```
