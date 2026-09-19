---
name: failing-tests
description: What to do when a test run comes back red — enter the run/diagnose/fix/re-run loop and drive it to green rather than reporting the failure and waiting, fix the real bug wherever it lives (service, handler, page object, step definition, fixture, config) instead of disabling, skipping, marking flaky, or inflating a timeout to get past it, and for browser or service E2E do proper flaky-versus-real triage by re-running the failed scenario alone on a fresh stack — passing clean proves a host-load blip, failing again proves a real bug. Use the moment any unit, integration, API, or UI test run fails, or when tempted to skip a test or raise a timeout to make a suite pass. A compiler, restore, or build error is not a red run and does not select this skill.

kind: workflow
domain: process
model: claude-sonnet-5
effort: high
---

# A failing test is never just reported

Read and follow the [canonical shared definition](../../../.agents/engineering/workflow/failing-tests/SKILL.md) in full.
This entry point supplies only Claude discovery metadata; the shared procedure is authored once under `.agents/`.
