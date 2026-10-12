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

## B004 - Stop rejects a matching delivery binding as head-changed

**Kind:** bug. **Observed/reported:** 2026-10-12; the active controller association owner and delivery binding both named `93803964be31d8283fe2f9e79ef12ad02ed3f9e2`, yet Stop emitted `binding-head-changed`. **Cause:** confirmed: `continuation_stop.binding_active` compared the normalized delivery binding's absent `head` key rather than its canonical `remote_head_sha` key.

**Impact and priority:** P1; an active, correctly bound continuation cannot finish a turn and repeatedly reports a false reconciliation gate.

**Source owner:** tj-agents/core continuation Stop hook. **State:** in-progress. **Repair link:** plans/controller-goal-association/GOAL.md and PR209. **Next action:** commit the canonical-field correction, obtain a fresh frozen review, and rerun exact-head CI.

**Resolution condition:** Stop accepts an identity-matching delivery artifact containing `remote_head_sha`, rejects a genuinely different SHA, and the repair passes focused tests, independent review and exact-head Windows/Linux CI.

**Verification evidence:** direct invocation of `binding_active` raised `binding-head-changed` before the repair despite matching local and artifact SHAs. The focused Stop suite now covers both matching and divergent `remote_head_sha` values and passes.

## B005 - An explicitly continued exhausted owner cannot resume

**Kind:** bug. **Observed/reported:** 2026-10-12; the controller owner reached `continuation-budget-exhausted` while the goal remained active and the user explicitly directed continued work. **Cause:** confirmed: the runtime had no operation to record a new finite deadline for the same exhausted owner.

**Impact and priority:** P1; an unfinished authorized delivery remains blocked or requires unsafe owner replacement after an expired finite budget.

**Source owner:** tj-agents/core continuation runtime. **State:** in-progress. **Repair link:** plans/controller-goal-association/GOAL.md and PR209. **Next action:** commit the guarded renewal transition, renew the exact owner under the user's recorded authority, then complete fresh review and CI.

**Resolution condition:** only an exhausted, lease-free owner can accept an explicit finite renewal; it retains its identity and existing limits, returns to waiting, and passes focused runtime tests, independent review and exact-head Windows/Linux CI.

**Verification evidence:** the exact controller owner was blocked with `continuation-budget-exhausted` after its deadline elapsed. The new focused test proves a one-hour explicit renewal succeeds without changing owner identity or counters and rejects a duplicate renewal.
