---
name: e2e-debug
description: Run and fix both end-to-end tiers in one pass — the service tier (xUnit over the full Aspire stack, no browser) first, then the browser tier (Reqnroll over Playwright) — because the browser tier exercises the same services plus a browser, so a backend event flow that is red fails both and costs a browser timeout to diagnose instead of a resource log. Covers the shared pre-flight, why the two E2E applications must never boot concurrently, what each tier's failures look like once the other is green, and the per-tier verdict. Use when the user wants a complete E2E sweep, asks whether the E2E tests are green, or wants to know whether a browser failure is really a backend one — and prefer e2e-api-debug or e2e-ui-debug for a single tier.
domain: process
---

# Sweeping both end-to-end tiers in one pass

There are two full-stack E2E tiers over the same backend:

1. **The service tier** — xUnit over a full Aspire `DistributedApplication`, no browser. Drives services over
   HTTP and polls real database and payment state until the async event chain settles. Mechanics:
   [`e2e-api-debug`](../e2e-api-debug/SKILL.md).
2. **The browser tier** — Reqnroll over Playwright, proving the user-facing flows on top of that same
   backend. Mechanics: [`e2e-ui-debug`](../e2e-ui-debug/SKILL.md).

This procedure runs and fixes **both**, in the order that makes debugging cheapest: **service tier first,
then browser tier.** That mirrors CI, where the browser job depends on the service job, and it reflects the
dependency — the browser tier exercises the same services plus a browser. A broken backend event flow fails
*both* tiers, but diagnosing it at the service tier (resource logs and polled state) is far faster than
through a browser timeout. Get the service tier green first and any remaining browser failure is genuinely
browser-layer work.

## Run autonomously — fix every failure across both tiers

The whole run → diagnose → fix → verify loop is delegated for both suites. Fix each failure in code and
re-run only that failing test in isolation until it is green. Pause only for a genuine product-behaviour
ambiguity the code cannot resolve.

## Never disable or bypass a step to get past its failure

The same hard rule both tiers carry. "Fix" means make the failing step work, never make it stop running. No
build suppression for a slow or hung build; no widening a polling, health or browser timeout to make a flaky
wait pass — not for a "hang", a "slow webhook" or "CI load", because a blown bound is a real failure to fix
(or, for a *proven* browser flake, a quarantine-lane entry with its tech-debt note); no disabling a resource,
handler or scenario to go green. If something hangs with no output, reproduce and observe it live rather than
removing it. A bypass is legitimate only when the user asks for it after seeing the diagnosis.

## Input

- **Nothing, and no failures already reported by CI or the merge queue** — one full two-tier discovery sweep.
  After fixing, verify only the affected tests individually.
- **One tier** — run only that tier; this procedure adds nothing over its own doc, but is a convenient entry
  point.
- **A specific test or scenario name** — identify its tier from the shape of the name (an xUnit
  fully-qualified name is the service tier, a scenario sentence is the browser tier) and follow that doc's
  single-test path.

## Step 0 — shared pre-flight

A test result, environment failure, or status report is not by itself a ledger checkpoint. If it creates a
genuine blocker or the context must end with state that cannot be reconstructed safely, apply the material
checkpoint procedure the repository's plan floor names.

Both tiers need Docker — SQL containers, the Service Bus emulator, the payment CLI — and the same real
secrets CI injects. `docker ps` answering is **not** proof Docker is healthy; the reasoning and the
`pre-login handshake` signature are in [`remote-validation`](../remote-validation/SKILL.md). Run the real
gate yourself first, so a bad engine is caught before anything else:

```powershell
./scripts/docker-health.ps1   # fresh container + published port + real HTTP round-trip + stability; exit 1 = unhealthy
```

It is vendored from `tomjseery/process-agents`, so that path is the same in every repo. The entrypoint
runs it too and refuses to boot on failure. If it reports unhealthy, **stop**: tell the user Docker is
half-started or down and to wait for Docker Desktop to show **Running**, then retry. Do not re-run the suite
and do not debug application code — it is an environment failure. If a run dies instantly with a payment-auth
or missing-configuration error, confirm the secrets are set before debugging anything else —
[`e2e-api-debug`](../e2e-api-debug/SKILL.md) Step 0 names them.

Tell the user exactly what is being run. Give the two-tier cost estimate only for an explicitly requested
discovery sweep with no failures already known.

**The two E2E applications must never run concurrently** — they starve each other for CPU and front-end dev
servers and share one payment account. Running the tiers sequentially, which is what service-then-browser
gives you, is the whole mitigation. Never kick both off at once.

## Step 1 — the service tier, first

Run and fix it to green through the full [`e2e-api-debug`](../e2e-api-debug/SKILL.md) flow:

```powershell
./scripts/e2e.ps1 api run
```

- Watch startup for hangs — the bus-emulator subscription failure, a stalled provisioning wait, a workers
  host with no address.
- For each failure, re-run that test alone and diagnose by **failure shape**: a synchronous status mismatch,
  a polling timeout pointing at the forwarded resource logs, or a completed flow with a wrong value.
- Fix the root cause — service, handler, dispatcher or fixture — then re-run only that test until green.

**Do not start the browser tier until this one is green.** A backend flow that is red here will also fail its
corresponding browser scenario, and you would be debugging it the slow way.

Skip this step only if the user scoped the request to the browser tier.

## Step 2 — the browser tier, after

Run and fix it to green through the full [`e2e-ui-debug`](../e2e-ui-debug/SKILL.md) flow:

```powershell
./scripts/e2e.ps1 ui run
```

- Same AppHost, so the same startup-hang playbook applies.
- For each failed scenario, re-run it alone and diagnose **HTTP 4xx/5xx first**, then a gRPC error in the
  *callee's* resource log, then the browser console and on-screen errors, then the failure screenshot.
- Fix the real bug — service, page object, step definition or test support — then re-run only that scenario.
- If a scenario **crossed the line** against the baseline, prompt the user to update it as
  the CI job's history records ([`failure-provenance`](../failure-provenance/SKILL.md)); neither tier keeps a local baseline.

Skip this step only if the user scoped the request to the service tier.

## Step 3 — the verdict

Report per tier, concisely: the counts, and one line per fix. Once every originally-failing test is green in
isolation, return to the merge flow **without another local suite run** — the merge queue verifies both tiers
once ([`remote-validation`](../remote-validation/SKILL.md)). If anything is still red because it needs a
product decision, state exactly what decision is needed.

## Why service-first is a discipline, not a preference

- **Cheaper signal.** A service-tier failure points at a resource log and polled state in seconds; the same
  broken flow in the browser tier is a minute-plus timeout and a screenshot of a spinner.
- **No double debugging.** Fix the event chain once at the service tier and the browser scenario that
  depended on it usually goes green for free.
- **Honest browser failures.** Once the service tier is green, a remaining browser red is genuinely the
  browser layer — selectors, navigation, render, front-end environment wiring — and not a backend failure
  wearing a browser costume.

## Which doc for which request

| Want | Doc |
|---|---|
| Both tiers, full sweep and fix | this one |
| Service-layer flows only, no browser | [`e2e-api-debug`](../e2e-api-debug/SKILL.md) |
| Browser scenarios only | [`e2e-ui-debug`](../e2e-ui-debug/SKILL.md) |
| Dating the last real pass before fixing a failure | [`failure-provenance`](../failure-provenance/SKILL.md) |
| In-process module tests, every external mocked | [`integration-debug`](../integration-debug/SKILL.md) |
