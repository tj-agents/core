---
name: remote-validation
description: Splitting verification between the workstation and CI when several agents share one machine — locally run only the required generators and invariant checks, the smallest affected build, and focused unit tests; let draft-PR CI own the full build, service carves, and complete unit and integration matrices; let the merge queue own selected E2E; wait for remote state outside model inference through a notification or one silent background process; diagnose a red remote check by reproducing only its failing scope; never run an expensive suite "to be safe" or duplicate the queue's E2E ahead of a merge; and treat a Docker daemon that answers `docker ps` but does not move real bytes (the `pre-login handshake` signature) as an environment failure rather than an application bug. Use when deciding what to run before pushing, waiting for CI, a queue, publication or generated sync, when a remote check goes red, before any local integration or E2E run, or when a plan step says to run a full suite.
domain: process
---

# Remote-first validation

Several agents work concurrently on one workstation. **The workstation is the inner loop; CI is the full
validation plane.** Do not turn every worktree into an independent CI runner.

## Who owns which gate

| Gate | Owner |
|---|---|
| Formatting, generators, grep/invariant checks | Local worktree |
| Smallest changed project or surface build | Local worktree |
| Focused unit tests for the changed behaviour | Local worktree |
| Full solution build and standalone service carves | Draft-PR CI |
| Complete unit and integration matrices | Draft-PR CI |
| Selected API and UI E2E | Merge queue |

Local integration and E2E runs are **diagnostic tools, not routine completion gates.** After CI or the queue
reports a failure, run the narrowest failing test, class, module, or scenario locally. A human may explicitly
ask for a broader local run, but **no plan step or skill may add one "to be safe"** — and a written "run the
full E2E regress" step is not a reason to duplicate what the queue will run on the way in.

## The delivery loop

1. Implement in the branch's own worktree.
2. Run the cheapest checks that directly cover the changed code: required generators and invariants, the
   smallest buildable project or surface, focused unit tests.
3. Commit each coherent checkpoint locally. At the first stable candidate that needs remote validation, push
   once and open a draft PR if none exists.
4. Accumulate later related commits and review fixes locally, then push the next stable candidate. Do not
   supersede useful CI for bookkeeping or every small completed slice.
5. Treat CI **on the exact remote head** as the authoritative build, carve, unit, and integration result.
6. On failure, read the remote log first, reproduce only the failing scope locally, fix it, run its focused
   regression, and push once. Do not run every local suite before pushing the fix.
7. Mark the PR ready only once review is clean and exact-head CI is green. Enqueue or merge only on an
   explicit instruction.

Opening a draft PR and pushing checkpoints is part of an authorized implementation workflow. It does not
authorize merge, deployment, destructive operations, or unrelated external changes.

## Persistent continuation owns a future delivery decision

When CI, queue, review, publication, or merge will resolve after this turn, enter the current harness's
persistent-workflow skill and have it read persistent-delivery. It owns the exact repository, PR, worktree,
head SHA, exact check and run IDs, review work order and watermark, authorization, duplicate suppression,
tier-specific repair dispatch, review routing, and terminal cleanup. A terminal watcher is not a persistent
workflow. Harness-specific wake, session, scheduling, and capability behavior belongs only to that host's
persistent-workflow skill.

If the current work must remain foreground and the harness lacks persistent work, launch exactly one silent
background command that owns every query and sleep, exits only on a meaningful transition, terminal result,
polling error, or fixed timeout, and never causes model re-entry at its cadence. On a later human wake, make
one authoritative forge read before acting.

## Resource discipline

- Never build the whole solution, run every unit project, or run the full integration matrix as routine local
  verification.
- **Do not launch local integration or E2E suites concurrently from different worktrees.** While one
  diagnostic run owns the container runtime, other agents keep implementing or wait for remote checks.
- Batch related fixes before pushing, so CI validates useful checkpoints. A newer executable candidate may
  supersede an older executable run; metadata never does.

## Metadata-only synchronization must not impersonate executable validation

The primary control is to eliminate plan-, ledger-, review-, and observation-only pushes. When a repository
still receives an independently meaningful metadata-only synchronization on a code PR, its classifier may
reuse prior executable validation only when it mechanically proves all of these:

- the event is a PR synchronization with resolvable previous and current heads;
- their diff contains only the repository's inert metadata paths;
- the executable tree is identical; and
- that executable tree already has a green required CI result, or its existing validation is allowed to
  finish rather than being cancelled.

Then only classification and the required aggregate run on the new metadata head. Any executable path,
unknown range, changed executable tree, absent/failed validation, PR open/reopen, or merge-group event runs the
normal matrix. Classifier tests must cover metadata-only after green, metadata-only while prior validation is
live, code plus metadata, an unresolvable range, and merge-group validation. Never turn a metadata head green
by silently discarding an unvalidated code candidate.

Workflow-level concurrency cancellation happens before classifier jobs run. Therefore a PR-wide
`cancel-in-progress` group is unsafe for this fallback: either classify in a non-cancelling lightweight
workflow and cancel an older run only after proving the new head is executable, or leave automatic
cancellation disabled and rely on stable push cadence. Tests must prove a metadata classification cannot
request cancellation of a prior executable run.

## Before any local E2E run: Docker must move real bytes

**`docker ps` answering is not proof Docker is healthy.** Docker Desktop can be off, paused, or half-started
with the engine still answering `docker ps` — even listing running containers — while host-to-container
forwarding of real bytes for **new** containers is dead. The signature to recognize: every SQL or health
connection is accepted then reset (`pre-login handshake` errors), services never become ready, and the whole
suite dies at fixture startup in a few minutes with **zero scenarios executed**.

`docker ps`, `docker run hello-world`, and a bare TCP connect are **all insufficient**: `hello-world` needs no
port forwarding, and the host-side `docker-proxy` completes a TCP handshake *locally* even when forwarding
into the container is dead, so a connect "succeeds" while no data flows — which is exactly the
`pre-login handshake` mode. **The only valid check is a real data round-trip to a fresh container** — start
one, publish a port, make an HTTP request, and confirm it stays up.

That check carries no repo-specific value, so it is not re-written per repo. It is
**`./scripts/docker-health.ps1`**, vendored from `tomjseery/base-agents` by its `vendor-hooks.ps1`, and
every repo's E2E entrypoint gates on it automatically. Run it yourself before a local E2E run anyway
(`dotnet:e2e-debug` Step 0), so a bad engine is caught before a doomed boot.

**A suite that dies at startup is an environment problem until proven otherwise.** Stop after the first such
run — do not rerun, and do not debug application code. Verify Docker (and that Docker Desktop shows
**Running**), fix it, then run once.
