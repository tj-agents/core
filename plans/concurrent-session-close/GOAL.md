# Prevent duplicate Stop hooks from corrupting session closure

## Authorization and ownership

Tommy explicitly requested repair on18 October2026 after this session reported closure refused.
Owner codex:01a1415f-6448-7123-8b17-c7fb67aee637; work item lifecycle/concurrent-session-close.
Source owner: Core machine close utility. Branch Fix/ConcurrentSessionClose.
Baseline dc1f7415e; isolated checkout .worktrees/Fix-ConcurrentSessionClose.
Problem record: primary Core BUGS.md B019. Migration and tracker skills retain their own owners.

## Evidence and scope

Two installed machine Stop callbacks returned contradictory verdicts for one armed attempt:
one advanced its ticket to reported; another returned prepared closure was cancelled or replaced.
Current source compares the stale armed ticket before acquiring the existing exclusive attempt claim,
then its exception handler overwrites the advanced ticket with refused. PR296 fixed identity/cwd
refresh, not this ordering. No verified live owner of this distinct repair was found.

One bounded source PR: acquire the attempt claim before validation can publish a refusal, preserve
a cancelled or replaced ticket, and regress the actual interleaving on both native-host payloads.
Keep process identity, user-prompt cancellation, Stop-gate acknowledgement and one-close checks.
No publisher configuration, peer termination, profile installation or unrelated lifecycle redesign.

## Progress and next action

Task claimed; current source inspected. Reproduce the overlapping Stop callbacks deterministically,
apply the smallest causal correction, run focused close and packaging checks, commit and obtain
independent review, pass required Windows/Linux CI, merge and verify causal package publication.
Do not claim a native host exited until an exit observer verifies it.

## Verified repair and validation blocker

The duplicate Stop regression failed for Codex and Claude before repair. The corrected claim order,
expiry boundary and cancellation/replacement tests pass: 24 focused tests. Native independent review
and parent workflow fallback found no defects at 970bdc09. The configured workflow review model is
unsupported by this account; the documented parent fallback was used without repeated dispatch.

Exact-head CI39172700988 passed Linux. Windows stopped before close tests because the public dotnet
plugin has moved persistence elsewhere, leaving the existing skill-routes example unresolved.
Update that example to the shipped dotnet:testing and react:testing identities, review the one-line delta and let
required CI validate the final candidate. No check is weakened or skipped.

The skills runtime lifecycle loader also expects a legacy .agents/skills/bugfix path absent from this
layout. Canonical bugfix guidance was loaded directly; this unrelated compatibility limitation stays
recorded here rather than blocking the source repair.