---
name: failure-provenance
description: For a suspected flaky or timing failure, find the last genuine pass in CI job history, diff it against the failure and classify regression, budget race or flake. Use before fixing a suspected flake.

kind: contract
domain: process
---

# Provenance of a suspected flaky or timing failure

Owns the claim "this used to pass" for a failure suspected to be flaky or timing-dependent. A deterministic
failure in the changed area goes straight to its tier's debug skill.

1. Read conclusions per job, never per workflow: a skipped job leaves its workflow green. Only `success` and
   `failure` count, and a tally such as 24 skipped, 0 executed is itself the finding.
2. Page back through runs to the last genuine pass and report the date window searched. A checked-in baseline
   or local log is never evidence.
3. Diff that run against the failure: per-step duration against every fixed budget (token lifetime, lease,
   timeout), build configuration, how the suite is invoked, and `git log -S` on the failing identifiers.
4. Classify before fixing:

| Class | Signature | Fix targets |
|---|---|---|
| Real regression | The same tests fail every run and bisect to a commit | That change |
| Budget or timing race | Whatever runs last fails; the set moves; the faster environment passes | The exceeded budget |
| True flake | Passes and fails on identical code in the same environment | The nondeterminism |

Never reclassify a budget race as a flake to justify raising a limit. After the fix, state the margin it buys.

```bash
gh api "repos/{owner}/{repo}/actions/runs/<run-id>/jobs" \
  --jq '[.jobs[] | select(.name|test("e2e")) | .conclusion] | join(",")'
```
