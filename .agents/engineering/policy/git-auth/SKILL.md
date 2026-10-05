---
name: git-auth
description: Getting access an agent does not already have — scope every credential to the single organization that owns the work, never an account-wide scope reaching every organization the account belongs to. Use when a call is refused for lack of permission, or before requesting, creating or widening any token.

kind: policy
domain: process
---

# One organization's access, never the account's

A call refused for lack of permission is an obstruction to diagnose, not a cue to widen the token. The
credential that clears it must reach **the one organization that owns the work and nothing else** — the
account is in other organizations, including employers', and they are not ours to touch.

## Never add an account-wide scope

`gh auth refresh -s <scope>` and every other classic OAuth scope apply to every organization the token can
reach. `admin:org` to read one organization's Actions policy grants organization administration across all
of them. There is no per-organization form of a classic scope, so there is no safe way to use one here.

## Ask for the narrow credential instead

A **fine-grained** personal access token has exactly one resource owner. Ask for one owned by the
organization that owns the repository, carrying only the permission the call needs, and use it for that
call alone:

```
GH_TOKEN=<fine-grained token> gh api <endpoint>
```

Name three things when asking: the organization, the exact permission, and the single call it is for. That
is what makes the request reviewable rather than a blanket "I need more access".

## When the narrow credential is not available

Record the check as unavailable, say what it would have told us, and continue with what can be established
without it. A broader credential is never the fallback, and a refused check is never a reason to guess and
present the guess as a finding.
