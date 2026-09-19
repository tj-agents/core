---
name: failure-provenance
description: Establish when a failing test last genuinely passed and what was different then, from pipeline job history rather than any checked-in baseline, and classify the failure as a real regression, a budget/timing race, or a true flake before proposing a fix. Covers reading conclusions at job level because a green workflow says nothing when the job was skipped, finding the last real execution by paging workflow runs, diffing that run's configuration and duration against the local one, the three failure classes and the signature that distinguishes them, why a local baseline file is never evidence, and stating the headroom a fix buys instead of declaring victory. Use before fixing any test that "used to pass" or is suspected flaky, and again after the fix to say what margin it restored.

kind: contract
domain: process
model: gpt-5.6-terra
---

# Establishing what changed since it last passed

A failing test invites an immediate fix. Skip that. **First find the last run that genuinely passed, then
find what is different now** — that difference is the bug, and it is very often not in the test.

This is the step that turns "three scenarios are broken" into "the run has a 900-second budget and CI has
four minutes of margin". Without it you fix the symptom that happened to surface, and the real defect
re-emerges later wearing different scenario names.

Run it before proposing a fix, and again after, to state the margin the fix restored.

## Pipeline history is the evidence; a checked-in baseline never is

A baseline, expected-failures list or `*.last.log` committed to the repo records **whatever someone last ran
locally**. It drifts silently, it is updated by hand, and it is nobody's gate. Never date a regression from
it and never cite it as proof a test used to pass.

The pipeline is the only record that is both automatic and adversarial. Read it directly.

## Step 1 — read conclusions at job level, never workflow level

**A green workflow proves nothing about a job inside it.** Change-detection, skip labels and path filters
routinely gate an expensive suite off, and the workflow still reports success. A job that never ran is not a
job that passed.

For each candidate run, pull the conclusion of the specific job:

```bash
gh api "repos/{owner}/{repo}/actions/runs/<run-id>/jobs" \
  --jq '[.jobs[] | select(.name|test("<job-name>")) | .conclusion] | join(",")'
```

Tally the conclusions before drawing any conclusion of your own. A distribution like *24 skipped, 2
cancelled, 0 executed* is itself the finding: the suite is not gating anything, and "it never failed" only
ever meant "it never ran".

## Step 2 — find the last real execution

`success` and `failure` are the only conclusions that count. Page back until you find one — the default
listing window is often only a few days, so check the span you actually covered and say so rather than
implying you searched history:

```bash
gh api "repos/{owner}/{repo}/actions/workflows/<workflow>/runs?created=<<date>&per_page=100&page=<n>" \
  --jq '.workflow_runs[].id'
```

Report the window you searched. "Zero executions in the last 200 runs" is a useful fact only when paired
with the dates those 200 runs span.

## Step 3 — diff that run against the failing one

Once you have a genuinely-passing run, compare it with the failing environment along the axes that change
outcomes. The gap is the hypothesis:

- **Duration**, per step, from `started_at`/`completed_at`. Compare against every fixed budget in play — a
  token or session lifetime, a lease, a cache TTL, a job timeout.
- **Build configuration** — Release on a clean runner against Debug on a loaded workstation is routinely a
  large factor, and it moves a run across a fixed budget without any code changing.
- **How the suite is invoked** — CI may call the runner directly while the local entrypoint adds gates,
  filters or provisioning the other side never performs. Where the local script omits provisioning CI does,
  the local script has drifted and that is its own defect.
- **What actually changed in between**, scoped to the owning paths, via `git log -S` on the failing
  behaviour's identifiers.

## Step 4 — classify before fixing

| Class | Signature | What the fix targets |
|---|---|---|
| **Real regression** | The **same** tests fail every run, and they bisect to a commit | The change that broke them |
| **Budget / timing race** | **Whatever runs last** fails; the set moves between runs; passes in the faster environment | The fixed budget the run now exceeds |
| **True flake** | Passes and fails on **identical** code in the **same** environment | The nondeterminism, or the non-gating quarantine lane |

Distinguishing the first two matters most, because a budget race is the one that masquerades as flake. Its
tell is that the failing set is unstable while the *position* of failure is stable. Confirm it by checking
whether the passing environment merely finishes sooner rather than behaving differently.

**Never reclassify a budget race as a flake to justify raising the limit.** Whether a scenario passes must
not depend on how long the run before it took.

## Step 5 — state the headroom, not just the verdict

A fix for a timing race is only meaningful as a margin. Report the number:

> CI finishes this job in 11m08s against a 15-minute session budget — under four minutes of margin. The fix
> removes the dependency on run duration entirely.

That framing tells the reader whether the defect was latent in CI too, and it converts "works locally" into
a claim someone can check. Where the fix leaves a budget in place, say what still consumes it and what
would exhaust it.

## What this skill does not do

It does not run suites and it does not diagnose a failure's mechanism — the tier's own debug skill owns
both. It runs before that skill's fix step and after its verification, and it is the authority for the
claim "this used to pass".
