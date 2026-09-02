---
name: e2e-api-debug
description: Run the service end-to-end suite (xUnit over a full Aspire DistributedApplication with no browser, real payment test mode and a real Service Bus emulator) and drive every failure to green. Covers the three failure shapes and how to tell them apart — a synchronous status mismatch that already carries URL, status and response body; a polling timeout, which is the common one and means a downstream reaction never completed; and a completed flow that computed the wrong value — plus mapping the state that never appeared to the resource that owed it, why a gRPC error surfaces only in the callee's log, the startup-hang watch, and why widening a polling window is banned in a tier that has no baseline and no quarantine lane. Use whenever the user wants a service-layer E2E failure debugged, that suite run, or a settlement, payment or event-propagation flow investigated below the browser.
domain: process
---

# Driving the service end-to-end suite to green

The service tier: xUnit tests over a full Aspire `DistributedApplication` with **no browser**. It boots the
real stack — every web and workers host the service needs, a Service Bus emulator, SQL containers, Stripe in
test mode — drives the backends directly over HTTP, then polls real database and Stripe state until the
asynchronous outbox → inbox → event / gRPC / webhook chain settles. It exists to prove those chains actually
complete across services.

Browser scenarios are [`e2e-ui-debug`](../e2e-ui-debug/SKILL.md); in-process module tests are [`integration-debug`](../integration-debug/SKILL.md);
both E2E tiers in one pass is [`e2e-debug`](../e2e-debug/SKILL.md).

## Run autonomously — fix the failures, do not report them

The whole run → diagnose → fix → verify loop is delegated. Fix each failing test without stopping for
permission, then re-run only that test until it is green. Pause only for a genuine product-behaviour
ambiguity the code cannot resolve. [`failing-tests`](../failing-tests/SKILL.md) is the general form.

## Never disable or bypass a step to get past its failure

- **Never suppress builds** (`--no-build`, `SuppressBuild`, any skip-build flag) because a build hung. That
  swaps the failure for silently running stale binaries.
- **Never widen a polling or wait window to make a flaky wait pass** — not for a "hang", a "genuinely slow
  webhook", or "CI load". A blown polling window is *the signal that the async chain did not complete*: chase
  the chain and fix the slow or broken thing. This tier has **no quarantine lane and no baseline** — every
  test here must pass — so a genuine flake is a determinism bug to fix or surface, never a window to widen.
- Never disable, skip or stub the failing resource, handler or check so the rest goes green.

If a step hangs with no useful output, reproduce it and observe it live — process trees, Aspire resource
states, Docker containers — rather than removing the step. A bypass is legitimate only when the user asks for
it after seeing the diagnosis.

## How this tier differs from the other two — read this first

| | [`integration-debug`](../integration-debug/SKILL.md) | **this tier** | [`e2e-ui-debug`](../e2e-ui-debug/SKILL.md) |
|---|---|---|---|
| Host | in-process `WebApplicationFactory` | **full Aspire `DistributedApplication`** | full Aspire `DistributedApplication` |
| Externals | all mocked (payments, bus, email) | **real**: Stripe test mode, Service Bus emulator, SQL containers | real, plus a browser |
| Driver | the factory's `HttpClient` | **a plain `HttpClient` against deployed service URLs** | Playwright |
| Filter | xUnit `FullyQualifiedName~` | **xUnit `FullyQualifiedName~`** | Reqnroll `DisplayName~` |
| Signature failure | wrong HTTP status, synchronously | **a polling timeout: the async chain never settled** | an element or visual timeout |
| Server logs | per-test xUnit output | **forwarded Aspire resource logs in the test output** | forwarded Aspire resource logs |

The consequential row is the failure signature. Here a failing test usually means the synchronous call
returned 200 but a downstream handler, outbox dispatcher, gRPC settlement or payment webhook never
completed, so the polling helper eventually timed out. **The root cause is almost never in the test — it is
in a service resource log.** Diagnosis is therefore one question: which resource was supposed to react, and
what did its log say?

## Input

- **A fully-qualified test name** — run Step 0, then jump to Step 2 for that test alone.
- **A scope** the entrypoint offers — run Step 0, then that scope.
- **Nothing, and no failures already reported by CI or the merge queue** — run Step 0, then the whole tier
  once to discover failures, then Step 2 per failure.

## The entrypoint owns the commands

```powershell
./scripts/e2e.ps1 api run       # every service-tier E2E test; non-zero exit on any failure
./scripts/e2e.ps1               # no arguments: prints every command this repo actually has
```

**Never call `dotnet test` for a whole suite.** The entrypoint owns the Docker gate below and passes the
repo's run settings, which cap the runner's parallelism — two E2E applications must never boot at once. A
direct `dotnet test` is for a single test in Step 2, and it must pass those same run settings itself.

A repo with more than one such suite adds a scope per suite; in a single-service repo `api run` *is* the
whole tier. Read the argument-less listing rather than assuming either shape. What holds everywhere:

- Each suite owns an application fixture that boots that service's AppHost, seeds through the dev seeding
  path, and exposes the HTTP client, the polling helper, the raw-SQL database helpers and the seed state the
  tests assert against.
- Stack composition — which sibling services and containers this suite pins — lives in the suite's own
  distributed-application builder extensions, never in the shared harness.
- **Time-based flows are triggered, not waited for.** The suite's workers fixture fires a timer function
  through the Workers host admin API (`POST /admin/functions/{name}`). Acceptance is `202` and
  fire-and-forget, so assert on the state the function produces, never on the trigger call.
- The entrypoint writes a last-run log beside each project it ran, and ad-hoc captures go in the git-ignored
  scratch log directory the shared E2E test library owns — **never the repo root**.

## Step 0 — pre-flight

A test result, environment failure, or status report is not by itself a ledger checkpoint. If it creates a
genuine blocker or the context must end with state that cannot be reconstructed safely, apply the material
checkpoint procedure the repository's plan floor names.

These tests need Docker for the SQL containers, the Service Bus emulator and the payment CLI. `docker ps`
answering is **not** proof Docker is healthy; why the cheap checks miss a half-started engine, and the
`pre-login handshake` signature it produces, are in [`remote-validation`](../remote-validation/SKILL.md). Run
the real gate:

```powershell
./scripts/docker-health.ps1   # fresh container + published port + real HTTP round-trip + stability; exit 1 = unhealthy
```

It is vendored from `tomjseery/process-agents`, so that path is the same in every repo. The entrypoint
runs it automatically and refuses to boot on failure. If it reports unhealthy, **stop** — tell the user
Docker is half-started or down and to wait for Docker Desktop to show **Running**, then retry. It is an
environment failure: do not re-run and do not debug application code.

This tier also needs the same real secrets CI injects (`Stripe__SecretKey`, `GoogleApiKey`). A run that dies
immediately with a payment-auth error or a missing-configuration exception is that, not a product bug —
confirm they are set before debugging anything else.

Tell the user whether this is a targeted test run or a full discovery run, and give a duration estimate only
for discovery.

## Step 0b — watch for startup hangs

Run the suite as a **background** shell task and note its output file. Use the harness's recurring monitor or
listener when available, bound to that exact process and output file, at roughly 60-second intervals for the
first five minutes. If no monitor primitive exists, use a single capped background loop around this read:

```powershell
$lines = Get-Content "<output-file>" 2>&1
Write-Host "Lines so far: $($lines.Count)"
$lines | Select-String "Initializing|FixtureReady|Running|Waiting|Exited|fail:|error:|Passed|Failed|healthy|payout" | Select-Object -Last 20
```

Three or four observations over the first four minutes is enough. Confirm the process and file directly when
the monitor wakes. If after two or three minutes nothing has
reached `Running`, diagnose immediately:

```powershell
docker ps -a --format "table {{.ID}}`t{{.Image}}`t{{.Status}}`t{{.Names}}" 2>&1
```

Causes that recur — the first three are shared with the browser tier, which boots the same AppHost:

- **The Service Bus emulator exits with code 139** — "At least one subscription required per topic": a topic
  is declared in the stack composition with no subscriptions for the current service flags. Gate topic
  creation on the *subscriber* flag, not the publisher flag.
- **A workers host crashes with "address not configured"** — a project reference is missing from the
  AppHost's workers registration.
- **The SQL container will not start** — port conflict or volume corruption; `docker volume prune` and retry.
  **Out of memory** — raise the Docker Desktop memory limit.
- **A fixture wait for provisioned payment accounts never reaches its expected count** — those rows are
  created by a handler reacting to a credential-registration event, so a stalled count means that event
  chain is broken. Grep the payment and auth resource logs. **Do not "fix" it by seeding those rows
  directly**: the seeding standard forbids writing a row whose only legitimate author is the flow.

Fix the root cause before re-running. Never keep waiting on a stuck startup.

## Step 1 — run the tier

```powershell
./scripts/e2e.ps1 api run
```

The entrypoint prints a per-test pass/fail list and a summary. Build a results table from it before going
further, show the totals, name the failures, and proceed to Step 2 for each.

## Step 2 — re-run each failure alone

```powershell
dotnet test '<suite>.csproj' --filter "FullyQualifiedName~<Class>.<Method>" --settings <run-settings> --logger "console;verbosity=normal"
```

**Resolve `<run-settings>` from the entrypoint, never by guessing or omitting it** — it is the `--settings`
argument the entrypoint passes (`grep -i runsettings scripts/e2e.ps1`). Omitting it is how two E2E
applications end up booting at once, which is the failure the paragraph above describes.

Use PowerShell rather than a POSIX shell: backtick continuation is PowerShell-only and a POSIX shell mangles
the quoted filter. `FullyQualifiedName~` is a substring match — drop the method to run a whole class. To keep
the output for grepping, tee it into the scratch log directory, never the repo root.

The enriched detail — HTTP failure bodies, the product's own log lines, and the forwarded Aspire **resource**
logs — is in this run's console output, not in the entrypoint's last-run log.

## Step 3 — diagnose: identify the failure shape first

### Shape A — a synchronous status mismatch

The test's own HTTP call returned the wrong status. The shared status assertion throws with full context:

```
Expected 204 NoContent, got 400 BadRequest.
Request: POST http://localhost:7083/api/Application/3/accept
Body:
{"errors":{"PaymentMethodId":["The PaymentMethodId field is required."]}}
```

URL, status, request method and response body are always present, so a wrong-status failure needs no extra
logging. If the body alone does not say *why*, cross-reference the service's resource log for the same
request.

### Shape B — a polling timeout: the async chain did not settle. The common one

The synchronous call returned 200 or 204 but a poll waiting on database or Stripe state timed out. The
synchronous half worked; a **downstream reaction never completed**. The state you polled for names the
missing reaction — now find the resource that owns it and read its log.

**Mandatory: grep the forwarded resource logs.** Each service's output is forwarded into the test output
prefixed `Resources.<resource-name>`:

```powershell
Select-String -Path "<captured-log>" -Pattern "Resources\.[a-z-]+\b" | Select-Object -First 80
Select-String -Path "<captured-log>" -Pattern "fail:|error:|Exception|StatusCode=" | Select-Object -First 80
```

Map the missing state to the reaction that produces it, then to the resource that owns that reaction:

| State that never appeared | Reaction that is broken | Where to look |
|---|---|---|
| A settlement's payment-intent id | booking accepted or finished → gRPC settlement call → payment transfer | the payment web host's gRPC handler; the producing service's outbox dispatcher |
| An application or booking lifecycle state | domain event → outbox → handler advancing the state machine | that service's workers host: outbox dispatcher, then the handler |
| A customer's ticket after a purchase | payment webhook → payment-succeeded event → ticket handler | the payment CLI's delivery, then the consuming web host or workers handler |
| Search projection rows | a changed-event over the bus → projection handler | the search workers host |

**A gRPC error surfaces in the wrong place.** A caller logging `Status(StatusCode=...)` holds no exception
of its own; the real one is in the **callee's** resource log. Always chase it to the service that threw.

### Shape C — the flow completed but a value is wrong

An amount or destination mismatch means the settlement *ran* and computed the wrong number. Look at the
settlement calculation for that deal shape, and at the resolver that maps a seeded participant to a payment
destination. **Known trap:** that resolver is generally incomplete — only some seeded users are wired — so a
missing destination may be a resolver gap rather than a settlement bug. Confirm the participant under test
is actually wired before blaming the calculation.

### When the logs still do not pinpoint it, add tracing

Add `ILogger` tracing to the server-side class rather than guessing. Every message, **a one-off probe
included**, is a source-generated log method on the project's `Log.cs`; an inline `logger.Log*` call does not
compile where `CA1848` is an error. Generic, future-useful lines (handler invoked/skipped/wrote, dispatcher
lifecycle) are kept; delete the probe's entry once the bug is fixed. Then re-run the single test and read
your new lines from the resource log in the console output.

## Step 4 — fix and verify

1. Fix the cause in the service, handler, fixture or test.
2. Re-run that test alone to confirm it is green.
3. **Do not run a broader E2E suite locally afterwards.** Once every originally-failing test passes in
   isolation, return to the merge flow; the queue is the single full-suite verification
   ([`remote-validation`](../remote-validation/SKILL.md)).

## Filter grammar

| Goal | Filter |
|---|---|
| One test, substring | `FullyQualifiedName~<Class>.<Method>` |
| A whole class | `FullyQualifiedName~<Class>` |
| Exactly one test | `FullyQualifiedName=<namespace>.<Class>.<Method>` |

## Notes

- These tests make **real payment-provider test-mode calls** against a **real Service Bus emulator**, so
  they are not hermetic the way the integration tier is. Flakiness is either a genuinely slow or unreliable
  dependency — a webhook that occasionally lands late — or cross-suite contention. **Never run a service-tier
  and a browser-tier E2E application at the same time**: they starve each other and share one payment
  account. The entrypoint and its run settings serialise them. The fix is to make the dependency reliable or
  to serialise the suites, never to widen the polling window.
- The HTTP client here is a plain client against a deployed URL, so there is **no** per-test server-log
  capture the way the integration tier has. Server-side detail comes from the forwarded resource logs.
- Seeding runs through the **dev** seeding path, not the test-seeder path. If seed state is wrong, fix the
  dev seeders, and never seed event-sourced, read-model or payment-account rows directly — the seeding
  standard owns that list.
- This tier has **no baseline file**. That is a browser-tier artefact keyed on Reqnroll scenario names; here
  every test is expected to pass, which is why the entrypoint exits non-zero on any failure.
