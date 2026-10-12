# Bugs

## B001 - Windows settings casing bypasses guard classification

**Kind:** bug. **Observed/reported:** 2026-10-12; frozen settings candidate 531c793d285008f0bf8969eeed700b601b9326fe accepts Windows-equivalent `.AGENTS/SETTINGS.JSON`, while stop and security classifiers return no match. **Cause:** confirmed case-sensitive new settings expressions.

**Impact and priority:** P2; an effective settings change can bypass its mandatory classification, reproduced only in disposable fixtures; no real merge was invoked.

**Source owner:** tj-agents/core delivery-runtime stop classification and merge-review security classification. **State:** in-progress. **Repair link:** plans/repository-settings/GOAL.md and reviews/Fix-RepositorySettingsContract.md R001, PR208. **Next action:** commit the focused-green case-insensitive matching and guarded-consumer regressions, then independently review and deliver the corrected PR208 head.

**Resolution condition:** canonical and Windows-equivalent spellings receive the settings stop and security classification, guarded authorization rejects the changed settings path, and the repair passes focused checks, independent incremental review and exact-head Windows/Linux CI before normal delivery.

**Verification evidence:** independent security review reproduced preference=True with uppercase Windows settings, unmatched stop/security paths and scoped authorization acceptance. Parent independently confirmed both classifiers miss alternate casing while matching the canonical path. Repair artifacts now pass runtime 36, guarded auto-merge 10 and settings security patterns 10 tests; the fixed expressions and actual guarded-consumer rejection were inspected.

## B002 - Deep JSON leaves stale conditional machine permissions

**Kind:** bug. **Observed/reported:** 2026-10-12; deep present settings raise RecursionError, causing synchronization to return before removing existing Claude/Codex wrapper grants. **Cause:** confirmed decoder recursion failure excluded from the new reader's parse exception normalization.

**Impact and priority:** P2; stale invocation permissions remain although current settings are invalid. This does not establish a merge bypass; the guarded command retains its other controls.

**Source owner:** tj-agents/core repository settings reader and machine permission synchronization. **State:** in-progress. **Repair link:** plans/repository-settings/GOAL.md and reviews/Fix-RepositorySettingsContract.md R002, PR208. **Next action:** commit the focused-green decoder normalization and verified both-host grant revocation regression, then independently review and deliver the corrected PR208 head.

**Resolution condition:** deeply nested invalid present settings produce the reader's public ValueError boundary, existing Claude/Codex conditional grants are removed, and focused checks, independent incremental review and exact-head Windows/Linux CI pass before normal delivery.

**Verification evidence:** security review seeded both hosts' disposable owned grants, replaced settings with a 20,000-level opaque JSON array, observed main return zero with profiles unchanged. Parent independently reproduced the escaped RecursionError and inspected the machine ValueError boundary. Repair artifacts now pass reader 12 tests (2 privilege skips) and machine synchronization 28; parent inspected the strengthened active-grants-before/deep-invalid-settings-after assertions for both Claude and Codex.

## B003 - Invalid settings escape the no-legacy consumer error boundary

**Kind:** bug. **Observed/reported:** 2026-10-12. In an unrelated repository without delivery-authorization.json, malformed present settings escape workflow_ops.standing_authorization as DeliveryContractViolation; the guarded command's main catches WorkflowOperationError and therefore misses this error. **Cause:** confirmed absent-policy resolve call outside the existing translation boundary. The issue exists in initial candidate531 and remains at178ba; it is outside the latest parser/classifier delta, not a newly introduced incremental finding.

**Impact and priority:** P2; the generic no-legacy consumer rejects invalid settings with an uncaught exception rather than its controlled diagnostic. No merge is invoked and no bypass is established.

**Source owner:** tj-agents/core workflow_ops standing authorization consumer. **State:** in-progress. **Repair link:** plans/repository-settings/GOAL.md and PR208. **Next action:** commit the verified shared error translation and actual guarded-command main regression, then independently review and validate the final head before delivery.

**Resolution condition:** malformed and deeply nested present settings with and without a legacy policy return the guarded command's controlled failure status/diagnostic, invoke no merge command, and pass focused regression, independent incremental review and exact-head Windows/Linux CI before causal delivery.

**Verification evidence:** fresh security lens compared immutable531 and178ba; both malformed no-policy cases escape DeliveryContractViolation and invoke zero merge commands. Parent independently called the actual standing_authorization in disposable repositories: absent legacy yields DeliveryContractViolation/public_workflow_error=False, valid legacy yields WorkflowOperationError/public_workflow_error=True. The new regression failed before with exactly two absent-policy errors and the final artifact passed11 tests, including malformed/deep inputs with both policy states, controlled settings diagnostic and zero merge commands. Delivery-binding38 and harness14 tests plus declaration consistency also passed; parent read the actual terminal artifacts.

## B004 - Verified self-host remains alive after Windows Terminal discovery refuses

- Kind: bug. Observed/reported: 2026-10-12; exact close.py invocation refused Windows Terminal target is absent or ambiguous after observer acceptance/arming; observer cancelled because host did not exit.
- Cause: confirmed self-close/finish catches TerminalUnavailable only, while absent/ambiguous actual target raises TerminalRefusal. Own PID/start/attachment verified; current UI inventory has zero actual tabs. Infrastructure cause of UI discovery failure remains unknown.
- Impact/priority: P2; completed CLIs remain open and cleanup completion is unreliable.
- Source owner: machine peer-cli close.py/finish.py and directly causal closure guidance. State: in-progress.
- Repair link: plans/verified-self-close/GOAL.md, Fix/VerifiedSelfCloseFallback.
- Next action: independently reproduce refusal and repair verified self-process fallback while preserving peer-tab and unknown/PID-change refusal.
- Resolution condition: focused observer/process/identity regressions and Windows/Linux CI pass; reviewed source repair merged and causal generated packages verified.
- Verification evidence: exact registry entry PID9104/start1791756662.4871101; predecessor observer 1f29421b77f448e39c489f380948dbc2.json accepted/armed then cancelled; current actual_tab_count=0.
