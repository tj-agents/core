---
name: e2e-ui-debug
description: Run the browser end-to-end suite (Reqnroll scenarios over Playwright against the full Aspire stack) and drive every failure to green — discover failures, re-run each one alone for the enriched output, and diagnose HTTP 4xx/5xx first, then a gRPC error in the callee's forwarded resource log, then browser console and on-screen errors, then the failure screenshot. Covers the entrypoint's command grammar and how to discover this repo's suites from it, headless as the default and why a direct dotnet test run is headed unless told otherwise, the startup-hang watch and the four causes that recur, preserving scenario semantics when changing a shared fixture or page object, and why widening a timeout or suppressing a build is banned rather than discouraged. Use whenever the user wants a browser E2E failure debugged, the full suite run, newly-passing or newly-failing scenarios discovered, or a flaky scenario investigated.
domain: process
---

# Driving the UI end-to-end suite to green

The browser tier: Reqnroll scenarios over Playwright against the full Aspire stack. Run it, then diagnose
and **fix** every failure using the enriched HTTP and Playwright output the fixtures already emit. For a
establishing when a failure last genuinely passed, before you fix it, use
[`failure-provenance`](../failure-provenance/SKILL.md); for the service tier under it use [`e2e-api-debug`](../e2e-api-debug/SKILL.md); to sweep both tiers in one pass use
[`e2e-debug`](../e2e-debug/SKILL.md).

## Run autonomously — fix the failures, do not report them

The whole run → diagnose → fix → verify loop is delegated. Fix each failing scenario without stopping for
permission, then re-run only that scenario until it is green. The branch's scope is not
permission to leave a failure broken. Pause only for a genuine product-behaviour ambiguity the code cannot
resolve. [`failing-tests`](../failing-tests/SKILL.md) is the general form of this rule.

## Never disable or bypass a step to get past its failure

The suite tests the **current** state of the code. A failing scenario, build, service startup or health
check *is* the thing to debug. "Fix" means make the failing step work — never make it stop running.

- **Never suppress builds** (`--no-build`, `SuppressBuild`, any skip-build flag) because a build hung or was
  slow. That swaps the failure for silently running stale binaries, which is worse than the failure.
- **Never raise a timeout or wait to make a flaky step pass** — not for a "hang", not for a "slow
  dependency/webhook", not for "CI load". Relabelling a slow wait as "not a hang" to justify a bigger number
  is the exact rationalisation this bans. A wait that blows its bound is either a real failure (the awaited
  thing is broken or slow — fix *that*) or a **proven** non-deterministic flake (passes and fails on
  identical code), which goes into the non-gating `Category=quarantine` lane and is logged in the owning
  `TECH_DEBT.md`. Padding the number is neither; it only hides the signal.
- Never disable, skip or stub the failing resource, step or check so the rest goes green.

If a step hangs with no useful output, **reproduce it and observe it live** — process trees, what the child
processes are doing, file locks, CPU — rather than removing the step. A bypass is legitimate only when the
user asks for it after seeing the diagnosis.

## Diagnostics must preserve scenario semantics

Before changing a shared fixture, page object or test helper, enumerate every call site and classify its
success, expected-failure and challenge flows. A diagnostic improvement must not change which outcomes those
callers accept. If it does, it is a regression, not a debugging aid.

- Keep transport plumbing generic: click, await, capture, return the response.
- Keep outcome validation explicit at the test DSL boundary. Prefer a named operation such as
  `PayWithDeclinedCardAsync` over a boolean or enum mode threaded through a generic confirm helper.
- Put reusable response validation in a focused extension or helper, never a private copy in one page
  object, and never special-case an expected HTTP status inside generic browser plumbing.
- When a diagnostic change breaks previously-passing scenarios, remove or redesign **that change** before
  touching the scenarios. Do not patch each caller around the altered helper semantics.

## Input

Arguments are full scenario names exactly as they appear in the test output. Run Step 0, skip Step 1, and go
straight to Step 2, running each one alone with `DisplayName~` and the full name as the filter value.

Scenarios already reported by CI or the merge queue count as arguments. Run Step 1 to discover failures only
when there are no arguments and no known failures.

## Headless by default

Always run headless unless the user explicitly asks to watch the browser. Headless is faster and costs
nothing diagnostically: failure screenshots, Playwright traces and the enriched HTTP/console logs all work
identically.

- The repo's entrypoint (below) sets headless itself unless passed `-Headed`.
- A direct `dotnet test` run does **not** inherit that default — the fixture runs headed with `SlowMo`
  unless the environment says otherwise, so prefix every Step 2 command with `$env:HEADLESS='true'; `.
- Only when the user wants to watch: pass `-Headed` to the entrypoint, or leave `HEADLESS` unset for a
  direct run.

## The entrypoint owns the commands, and it is how you discover this repo's suites

```powershell
./scripts/e2e.ps1 ui run        # every UI scenario
./scripts/e2e.ps1 ui trace      # open the latest Playwright trace
./scripts/e2e.ps1               # no arguments: prints every command this repo actually has
```

**Never call `dotnet test` for a whole suite** — the entrypoint owns the mandatory Docker gate below and the
run settings that stop two E2E applications booting at once. A direct `dotnet test` is for a *single*
scenario re-run, in Step 2.

A repo with more than one UI suite adds a scope per suite; in a single-service repo `ui run` *is* the whole
suite and there is nothing to scope. Read the argument-less listing rather than assuming either shape. What
holds everywhere:

- Each suite's project follows the Reqnroll layout — `Features/`, `Steps/`, `PageObjects/`, and
  `Fixtures/` + `Hooks/` for the harness.
- The entrypoint writes a last-run log **beside each project it ran**, so the previous run can be re-read
  without re-running it.
- Which scenarios are expected to pass is the CI job's history, never a checked-in list
  ([`failure-provenance`](../failure-provenance/SKILL.md)).
- Ad-hoc `dotnet test` output you capture for later grepping goes in the git-ignored scratch log directory
  the shared E2E test library owns — **never the repo root**. The entrypoint's own last-run logs stay where
  it writes them; leave those alone.

## Which command the user actually wants

- **"Has my change broken anything?"** → `ui run`, the whole suite. There is no baseline-subset shortcut:
  a local list of expected passes is stale by construction, so the suite itself is the check.
- **"Which scenarios newly pass or newly fail?"** → also `ui run`. Do *not* use it after fixing a known
  failure; re-run that one scenario and let the merge queue do the full-suite verification.
- **A failure that "used to pass"** → [`failure-provenance`](../failure-provenance/SKILL.md) first, before any fix.
  It dates the last real pass from CI job history and classifies the failure as a regression, a
  budget/timing race, or a flake — and those three take different fixes.

## Step 0 — pre-flight

A test result, environment failure, or status report is not by itself a ledger checkpoint. If it creates a
genuine blocker or the context must end with state that cannot be reconstructed safely, apply the material
checkpoint procedure the repository's plan floor names.

`docker ps` answering is **not** proof Docker is healthy; why the cheap checks miss a half-started engine,
and the `pre-login handshake` signature it produces, are in [`remote-validation`](../remote-validation/SKILL.md).
Run the real gate:

```powershell
./scripts/docker-health.ps1   # fresh container + published port + real HTTP round-trip + stability; exit 1 = unhealthy
```

It is vendored from `tomjseery/process-agents`, so that path is the same in every repo. The entrypoint
runs it automatically and refuses to boot on failure. If it reports unhealthy, **stop** — tell the user
Docker is half-started or down and to wait for Docker Desktop to show **Running**, then retry. Do not re-run
and do not debug application code: it is an environment failure.

Tell the user whether this is a targeted scenario run or a full discovery run, and give a full-suite duration
estimate only for discovery.

## Step 0b — watch for startup hangs

Run the suite as a **background** shell task and note its output file. Use the harness's recurring monitor or
listener when available, bound to that exact process and output file, at roughly 60-second intervals for the
first five minutes, looking for resources reaching `Running`. If no monitor primitive exists, use a single
capped background loop around this read:

```powershell
$lines = Get-Content "<output-file>" 2>&1
Write-Host "Lines so far: $($lines.Count)"
$lines | Select-String "AppFixture|Running|Waiting|Exited|fail:|error:|Passed|Failed|healthy" | Select-Object -Last 20
```

Three or four observations over the first four minutes is enough. Confirm the process and file directly when
the monitor wakes. If after two or three minutes resources are
still `unknown`/`Waiting` and none reach `Running`, diagnose immediately — find the `Exited` resources and
read the line after each one's `Resources.<name>[0]` marker, then:

```powershell
docker ps -a --format "table {{.ID}}`t{{.Image}}`t{{.Status}}`t{{.Names}}" 2>&1
```

Causes that recur:

- **The Service Bus emulator exits with code 139** — "At least one subscription required per topic" means a
  topic is declared in the stack composition with no subscriptions for the current service flags. Gate the
  topic creation on the *subscriber* flag, not the publisher flag.
- **A workers host crashes with "address not configured"** — a project reference is missing from the
  AppHost's workers registration.
- **The SQL container will not start** — port conflict or volume corruption; `docker volume prune` and retry.
- **Out of memory** — a container died before the readiness window; raise the Docker Desktop memory limit.

Fix the root cause before re-running. Never keep waiting on a stuck startup.

## Step 1 — run the suite

```powershell
./scripts/e2e.ps1 ui run
```

Parse each suite's last-run log for pass/fail counts and present a results table before going further:

| # | Suite | Scenario | Result |
|---|---|---|---|
| 1 | … | … | ✅ Passed / ❌ Failed |

Show the totals, name the failures, and proceed to Step 2 for each.

## Step 2 — re-run each failure alone

Identify which project owns the scenario from the feature it belongs to, then run it by itself so the verbose
HTTP-logger and Playwright page-error output is not buried:

```powershell
$env:HEADLESS='true'; dotnet test '<suite>.Ui.csproj' --filter "DisplayName~<scenario name substring>" --logger "console;verbosity=normal"
```

Use PowerShell rather than a POSIX shell for this: backtick continuation and `$env:` assignment are
PowerShell-only, and a POSIX shell mangles the quoted filter. To keep the output for grepping, tee it into
the scratch log directory — never the repo root:

```powershell
$env:HEADLESS='true'; dotnet test '<csproj>' --filter "DisplayName~<scenario>" --logger "console;verbosity=normal" | Tee-Object -FilePath "<scratch-logs>/<scenario-slug>.log"
```

The fixtures emit **HTTP request/response logs** for every API call the scenario made with status codes and
bodies, **browser console errors** from the Playwright page, and **on-screen error text** captured by the
failure hook. Read the `Standard Output Messages` block for that detail — it is far more informative than
the stack trace.

## Step 3 — diagnose from logs and screenshots

**Mandatory first check: HTTP 4xx/5xx.** Before screenshots, stack traces or console logs, grep the run
output for HTTP errors. They are almost always the root cause.

```powershell
Select-String -Path "<suite>/<last-run-log>" -Pattern "HTTP [45][0-9][0-9]" | Select-Object -First 50
Select-String -Path "<suite>/<last-run-log>" -Pattern "\[console warn\]|On-screen error" -CaseSensitive:$false | Select-Object -First 50
```

For a Step 2 single-scenario re-run the enriched output is in the `dotnet test` console output **only** — the
last-run log is written by the entrypoint, not by a direct run. Search what you captured instead.

Then work the output in this order:

1. **HTTP 4xx/5xx** — which endpoint failed, and what is in the response body?
2. **gRPC errors** — a web host returning 500 with `Status(StatusCode=...)` carries no exception of its own.
   The real stack trace is in the **callee's** forwarded resource log; grep that resource's `fail:`/`error:`
   lines. Always chase a gRPC failure to the service that threw.
3. **Browser console** — `[console warn]` / `[console error]` lines from the page console.
4. **Visible page errors** — the on-screen error text the failure hook captured.
5. **Stack trace** — last, filtered to the product's own frames.

### Failure screenshots

Every scenario failure saves a full-page screenshot under the project's build output
(`bin/<config>/<tfm>/playwright-failures/`), anchored to `AppContext.BaseDirectory` so it lands there
whatever the runner's working directory. The `Failure screenshot: <path>` line in the output gives the exact
filename; read the image directly. Use it **after** ruling out HTTP and gRPC errors — a screenshot shows
visual state (a disabled button, a missing element) while the logs identify the cause.

### When the logs do not pinpoint the cause, add tracing

If HTTP and gRPC errors, console output and screenshots still do not explain *why* — an endpoint 404s
because a row is missing and you cannot tell whether a projection handler ran, skipped or threw — add
`ILogger` tracing to the server-side class rather than guessing. Every message, **a one-off probe
included**, is a source-generated log method on the project's `Log.cs`; an inline `logger.Log*` call does not
compile where `CA1848` is an error. Generic, future-useful lines (handler invoked/skipped/wrote, processor
lifecycle) are kept permanently; delete the probe's entry once the bug is fixed. Then re-run the single
scenario and read your new lines from the forwarded resource output.

## Step 4 — fix and verify

1. Fix the cause in the service, page object, step definition or test support.
2. Re-run that scenario alone to confirm it is green.
3. **A single-scenario re-run is not proof when the failure was a budget or timing race** — the scenario
   passes in isolation whether or not the fix works, because a short run never reaches the budget. Where
   [`failure-provenance`](../failure-provenance/SKILL.md) classified it that way, the verification is a run long enough
   to exceed the budget, and the report states the margin restored.
4. **Otherwise do not re-run the full suite locally.** Once every originally-failing scenario passes in
   isolation, push; the merge queue is the single full-suite verification
   ([`remote-validation`](../remote-validation/SKILL.md)).

## Filter grammar

Reqnroll tests are matched on `DisplayName`, which is the scenario's own sentence:

| Goal | Filter |
|---|---|
| One scenario | `DisplayName~"<a distinctive substring of the sentence>"` |
| One scenario, exactly | `DisplayName=<the full scenario name>` |
| A themed group | `DisplayName~<a word every scenario in the group carries>` |

`~` is a substring match, which is what makes the themed-group row work at all — scenario sentences are
written so a shared word groups them. A count or a list of this repo's scenarios would be wrong by the next
one anyone writes, so derive both from `--list-tests`.

## Notes

- Each suite writes its own last-run log; re-read it instead of re-running.
- The service-tier E2E suite runs the same stack without a browser — [`e2e-api-debug`](../e2e-api-debug/SKILL.md) — and the two
  must never run concurrently ([`e2e-debug`](../e2e-debug/SKILL.md) owns the ordering).
- In-process module tests are a different tier entirely: [`integration-debug`](../integration-debug/SKILL.md).
- Scenario *authoring* — one behaviour per scenario, fast-forward through seeded state, what cannot be
  seeded — is not this doc. This doc starts once a scenario is red.
