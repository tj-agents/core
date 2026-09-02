---
name: integration-debug
description: Run the in-process integration suite (xUnit over WebApplicationFactory, one real SQL container per fixture with Respawn between tests, every external mocked) and drive each failure to green. Covers discovering this repo's projects and scopes from the entrypoint's own listing rather than a remembered roster, reading the failure block in the one order that works — assertion message, then the per-test server-side log block, then the stack trace only if the test threw — the status-assertion message that already carries URL, status and response body, tracing a missing side-effect from its capturing mock back to a handler that was never invoked, seed data lost to reset ordering, and a foreign-key violation naming another module's table. Use whenever an integration test fails, a module's integration tests need rerunning, or a CI integration job needs narrowing to its smallest failing scope.
domain: process
---

# Driving the integration suite to green

The in-process tier: xUnit over `WebApplicationFactory`, one real SQL container per fixture through
Testcontainers with Respawn between tests, and **every** external mocked. Run it, then diagnose and fix each
failure from the per-test server-side log output, the status-assertion failure message, the captured mock
state, and — last — the stack trace.

The two full-stack tiers are [`e2e-api-debug`](../e2e-api-debug/SKILL.md) and [`e2e-ui-debug`](../e2e-ui-debug/SKILL.md); this tier is neither,
and a failure here is never diagnosed by reaching for one of those.

## Run autonomously — fix the failures, do not report them

The whole run → diagnose → fix → verify loop is delegated. Fix each failing test, then re-run only that test
until it is green. [`failing-tests`](../failing-tests/SKILL.md) is the general form: never skip a test,
disable a fixture or widen a wait to get past a failure.

## Input

- **A fully-qualified test name** — run Step 0, then jump to Step 2 for that test alone.
- **A scope name** — a service or a module the entrypoint recognises. Run Step 0, then that scope.
- **A CI failure with no explicit test** — inspect the failing job and derive the **narrowest** project or
  test scope before Step 0. Run the whole suite only when the user explicitly asks, or when the failure is in
  shared integration infrastructure and no narrower proof exists.

## The entrypoint owns the commands, and `list` is how you discover this repo's projects

```powershell
./scripts/integration.ps1 run        # every integration project
./scripts/integration.ps1 <scope>    # one service, or one module across whichever services have it
./scripts/integration.ps1 list       # every integration project this repo has, by scope
./scripts/integration.ps1 <scope> -- <extra dotnet test args>
```

`list` is the discovery mechanism: never guess a project path or a module name, and never hard-code a roster
that the next module makes wrong. The entrypoint runs each project in turn and writes a last-run log beside
each one, so a completed run can be re-read without re-running it.

What holds everywhere:

- Each service owns its integration projects — commonly one per module — plus a fixtures project holding the
  application fixture every test class in that service shares.
- The mocks for that service's externals live under that fixtures project, and the shared test library
  provides the tier's machinery: the SQL container fixture with Respawn, the header-driven test
  authentication handler, the in-memory bus transport, and the reset contract that flushes mocks between
  tests.
- **The roster of real fixtures, mocks and shared harness members is the integration-testing standard's, not
  this doc's.** This doc is how you *read a failure*; that one is what the harness contains.

## Step 0 — pre-flight

A test result, environment failure, or status report is not by itself a ledger checkpoint. If it creates a
genuine blocker or the context must end with state that cannot be reconstructed safely, apply the material
checkpoint procedure the repository's plan floor names.

This tier needs Docker for the SQL container, and here the cheap check is the right one:

```powershell
docker ps 2>&1
```

If that errors or the daemon is unreachable, stop and tell the user to start Docker Desktop. Do not proceed.
The heavier gate [`e2e-api-debug`](../e2e-api-debug/SKILL.md) mandates exists because a published port must carry real bytes for
a *booted stack*; reach for it here only in the one case it diagnoses — the cheap check passes but every
database connection is accepted and then reset.

State the exact local scope being reproduced. If it is the explicitly requested full suite, say that each
project starts its own SQL container.

## Step 0b — watch for startup hangs

Run as a **background** shell task and note the output file. Use the harness's recurring monitor or listener
when available, bound to that exact process and output file, at roughly 60-second intervals for the first few
minutes. If no monitor primitive exists, use a single capped background loop around this read:

```powershell
$lines = Get-Content "<output-file>" 2>&1
Write-Host "Lines so far: $($lines.Count)"
$lines | Select-String "=== |Passed!|Failed!|error|fail:|Test Run|MsSql|Container started|timed out" | Select-Object -Last 20
```

Confirm the process and file directly when the monitor wakes before classifying the outcome.

Startup problems that recur:

- **Testcontainers cannot reach Docker** — a daemon-not-running or socket error. Fix Docker Desktop, retry.
- **A port is already in use** — a previous run's SQL container did not clean up. List containers, then
  force-remove the ones from the SQL image.
- **A first-run image pull** — the SQL image is well over a gigabyte, so a fresh machine can sit for several
  minutes before any test executes. That is not a hang.
- **Out of memory** — containers exit before the tests run. Raise the Docker Desktop memory limit.

Diagnose, fix, re-run. Never keep waiting on a stuck startup.

## Step 1 — run the narrowest scope asked for

Then parse each project's last-run log for its counts and present a summary before going further:

| # | Scope | Passed | Failed | Skipped | Result |
|---|---|---|---|---|---|

Show the totals across projects, name the failing test cases, and proceed to Step 2.

## Step 2 — re-run each failure alone

The `Failed!` lines in a project's log carry the fully-qualified name. Re-run each alone so the assertion
message and captured mock state are not buried under thousands of other tests:

```powershell
dotnet test '<project>.IntegrationTests.csproj' --filter "FullyQualifiedName~<Class>.<Method>" --logger "console;verbosity=detailed"
```

Use PowerShell rather than a POSIX shell for this: backtick continuation is PowerShell-only and a POSIX shell
mangles the quoted filter.

## Step 3 — diagnose from the failure block

xUnit renders three things together, and they are worth reading in this order:

1. **The assertion or exception message.** For a status mismatch this is the shared status assertion's
   message (below); otherwise the standard xUnit one.
2. **The server-side output block** — every log line the API emitted *during this test*, piped through the
   shared test logger provider. Passing tests hide this block; failing tests render it.
3. **The stack trace** — useful only when the test itself threw rather than asserted.

### The status-assertion failure format

Every HTTP status check goes through the shared status assertion, which throws with full context:

```
Expected 201 Created, got 400 BadRequest.
Request: POST http://localhost/api/Application/3/accept
Body:
{"errors":{"PaymentMethodId":["The PaymentMethodId field is required."]}}
```

URL, status, request method and response body are always there, so a wrong-status failure needs no added
logging — a validation or problem-details envelope is already in front of you. Seeing a bare
`EnsureSuccessStatusCode` or a raw status equality assertion instead is a defect to fix, not a shape to
follow; the authoring standard owns that rule.

### Cross-referencing the server log block

When the status says 400 but the body does not say why, scan the server log block for the matching request:

- warning and failure lines from the product's own namespaces — application code logging a guard or a
  validation failure;
- ASP.NET Core infrastructure lines around the same request — model-state failures, filter rejections;
- ORM warnings — concurrency conflicts, missing entities.

### A missing side-effect assertion

When a test asserts something *happened* and the captured list is empty, the production code never fired it.
Two places to look, in order:

1. **The mock that owns that side-effect.** Find it on the fixture and read what it captured. Which mocks
   exist, and which one owns which side-effect, is the integration-testing standard's inventory.
2. **The server log block.** If the handler that should have fired the side-effect logged nothing, it was
   never invoked — work backwards: is the event raised, is the handler registered, is the bus transport
   flushed?

### Database state

Every test class shares one SQL container per fixture, and Respawn resets between tests. Missing seed data
means either the seeder is not registered on the fixture or Respawn ran after seeding. To inspect state
mid-test, resolve the scoped context accessor from the fixture's services and run a read through it rather
than newing a context.

### A foreign-key violation naming another module's table

Check that the principal table's migration runs before the dependent's. A cross-context foreign key is
stripped from the dependent's migration by convention, so a violation of this shape is usually a strip that
was missed.

## Bounded reads when many tests fail at once

Step 2 stays serial for one failure. For a large failing set the parent may dispatch independent read-only
Workflow v2 roles over the same immutable run — `log-analyst` to reduce each project's last-run log to
signatures and chronology, `test-impact-analyst` to map the affected projects and their exact filters — using
the semantic dispatch/result envelopes in `.agents/workflows/contract/v2`, or the packaged
`../../workflows/contract/v2` bundle. Never name an agent or model.

Readers never diagnose. Step 3's read order, the cause, and the fix stay with the parent, and an invalid,
incomplete, or unavailable result falls back to reading the failure block directly.

## Step 4 — fix and verify

1. Fix the cause — application code, fixture setup, or the test.
2. Re-run that test with an exact-match filter to confirm it is green.
3. Re-run the whole module's integration project to catch regressions in sibling tests.
4. If the change is broader — shared kernel, shared infrastructure, a fixture or a mock — push the focused
   green fix and let PR CI run the complete integration matrix. Run the full suite locally only when
   explicitly asked, or when the remote logs cannot isolate a shared-infrastructure failure.
5. **Do not add a local E2E run.** Push; the merge queue owns E2E, and a specific queue failure is reproduced
   through the matching tier above ([`remote-validation`](../remote-validation/SKILL.md)).

## Filter grammar

| Goal | Filter |
|---|---|
| One test, exactly | `FullyQualifiedName=<namespace>.<Class>.<Method>` |
| One test, substring | `FullyQualifiedName~<Method>` |
| A whole class | `FullyQualifiedName~<Class>` |
| Every integration test in a project | `Category=Integration` — each project declares that assembly trait |
| Everything except one test | `FullyQualifiedName!~<Method>` |

The last row is for narrowing a diagnosis, never for shipping around a red test.

## Notes

- Tests run against a **real** SQL Server through Testcontainers, not an in-memory provider, so side-effects,
  foreign keys and triggers behave realistically.
- **Every external is mocked** — payments, the bus, email, geocoding, image upload, notifications. Tests make
  no real network calls; that is what separates this tier from [`e2e-api-debug`](../e2e-api-debug/SKILL.md).
- Each project boots its own factory, which costs seconds of warm-up per project. Running the projects
  sequentially is deliberate: collection-level parallelism inside a project is fine, but cross-project
  parallelism races on the Docker daemon.
- **Server-side logs are captured per test** because each test class takes the xUnit output helper and
  attaches it to the fixture, which wires the host's logging to the shared test logger provider. A new test
  class that omits that constructor shape still works — it just sees no server logs when it fails.
- **A red unit test lands here too**, because this is the nearest procedure and there is no separate one.
  What carries over is everything about *reading* the failure — the same runner, the same filter grammar,
  and Step 3's assertion-then-output-then-stack order. What does not is everything about the environment:
  a unit project boots no host, no container and no database (a build guard enforces that), so it has no
  pre-flight, no startup watch and no fixture state to inspect. Run it directly against its own project.
