# Bugs

## B001 - Windows settings casing bypasses guard classification

**Kind:** bug. **Observed/reported:** 2026-10-12; frozen settings candidate 531c793d285008f0bf8969eeed700b601b9326fe accepts Windows-equivalent `.AGENTS/SETTINGS.JSON`, while stop and security classifiers return no match. **Cause:** confirmed case-sensitive new settings expressions.

**Impact and priority:** P2; an effective settings change can bypass its mandatory classification, reproduced only in disposable fixtures; no real merge was invoked.

**Source owner:** tj-agents/core delivery-runtime stop classification and merge-review security classification. **State:** resolved. **Repair link:** PR208; canonical reviewed source0f98144fceff5040f6050413e036d26f1cf98ea8. **Next action:** none; the objective repair and delivery condition is verified.

**Resolution condition:** canonical and Windows-equivalent spellings receive the settings stop and security classification, guarded authorization rejects the changed settings path, and the repair passes focused checks, independent incremental review and exact-head Windows/Linux CI before normal delivery.

**Verification evidence:** independent security review reproduced preference=True with uppercase Windows settings, unmatched stop/security paths and scoped authorization acceptance. Parent independently confirmed both classifiers miss alternate casing while matching the canonical path. Repair artifacts now pass runtime 36, guarded auto-merge 10 and settings security patterns 10 tests; the fixed expressions and actual guarded-consumer rejection were inspected.

**Final delivery evidence:** Final reviewed head0f98144fceff5040f6050413e036d26f1cf98ea8 passed guard and Windows/Linux CI38187755625 and independent incremental review. PR208 merged normally at a1a8d051e65e15d639a7a0fb0fc343c7b89fd72d; causal main ci38189303890 and regeneration114618404712 succeeded and published exact-parent bot commitcbe97265fcd8267493c24d18f74a5a0a26b872c9. Parent verified canonical/published engineering and both-host machine payload byte parity.


## B002 - Deep JSON leaves stale conditional machine permissions

**Kind:** bug. **Observed/reported:** 2026-10-12; deep present settings raise RecursionError, causing synchronization to return before removing existing Claude/Codex wrapper grants. **Cause:** confirmed decoder recursion failure excluded from the new reader's parse exception normalization.

**Impact and priority:** P2; stale invocation permissions remain although current settings are invalid. This does not establish a merge bypass; the guarded command retains its other controls.

**Source owner:** tj-agents/core repository settings reader and machine permission synchronization. **State:** resolved. **Repair link:** PR208; canonical reviewed source0f98144fceff5040f6050413e036d26f1cf98ea8. **Next action:** none; the objective repair and delivery condition is verified.

**Resolution condition:** deeply nested invalid present settings produce the reader's public ValueError boundary, existing Claude/Codex conditional grants are removed, and focused checks, independent incremental review and exact-head Windows/Linux CI pass before normal delivery.

**Verification evidence:** security review seeded both hosts' disposable owned grants, replaced settings with a 20,000-level opaque JSON array, observed main return zero with profiles unchanged. Parent independently reproduced the escaped RecursionError and inspected the machine ValueError boundary. Repair artifacts now pass reader 12 tests (2 privilege skips) and machine synchronization 28; parent inspected the strengthened active-grants-before/deep-invalid-settings-after assertions for both Claude and Codex.

**Final delivery evidence:** Final reviewed head0f98144fceff5040f6050413e036d26f1cf98ea8 passed guard and Windows/Linux CI38187755625 and independent incremental review. PR208 merged normally at a1a8d051e65e15d639a7a0fb0fc343c7b89fd72d; causal main ci38189303890 and regeneration114618404712 succeeded and published exact-parent bot commitcbe97265fcd8267493c24d18f74a5a0a26b872c9. Parent verified canonical/published engineering and both-host machine payload byte parity.


## B003 - Invalid settings escape the no-legacy consumer error boundary

**Kind:** bug. **Observed/reported:** 2026-10-12. In an unrelated repository without delivery-authorization.json, malformed present settings escape workflow_ops.standing_authorization as DeliveryContractViolation; the guarded command's main catches WorkflowOperationError and therefore misses this error. **Cause:** confirmed absent-policy resolve call outside the existing translation boundary. The issue exists in initial candidate531 and remains at178ba; it is outside the latest parser/classifier delta, not a newly introduced incremental finding.

**Impact and priority:** P2; the generic no-legacy consumer rejects invalid settings with an uncaught exception rather than its controlled diagnostic. No merge is invoked and no bypass is established.

**Source owner:** tj-agents/core workflow_ops standing authorization consumer. **State:** resolved. **Repair link:** PR208; canonical reviewed source0f98144fceff5040f6050413e036d26f1cf98ea8. **Next action:** none; the objective repair and delivery condition is verified.

**Resolution condition:** malformed and deeply nested present settings with and without a legacy policy return the guarded command's controlled failure status/diagnostic, invoke no merge command, and pass focused regression, independent incremental review and exact-head Windows/Linux CI before causal delivery.

**Verification evidence:** fresh security lens compared immutable531 and178ba; both malformed no-policy cases escape DeliveryContractViolation and invoke zero merge commands. Parent independently called the actual standing_authorization in disposable repositories: absent legacy yields DeliveryContractViolation/public_workflow_error=False, valid legacy yields WorkflowOperationError/public_workflow_error=True. The new regression failed before with exactly two absent-policy errors and the final artifact passed11 tests, including malformed/deep inputs with both policy states, controlled settings diagnostic and zero merge commands. Delivery-binding38 and harness14 tests plus declaration consistency also passed; parent read the actual terminal artifacts.

**Final delivery evidence:** Final reviewed head0f98144fceff5040f6050413e036d26f1cf98ea8 passed guard and Windows/Linux CI38187755625 and independent incremental review. PR208 merged normally at a1a8d051e65e15d639a7a0fb0fc343c7b89fd72d; causal main ci38189303890 and regeneration114618404712 succeeded and published exact-parent bot commitcbe97265fcd8267493c24d18f74a5a0a26b872c9. Parent verified canonical/published engineering and both-host machine payload byte parity.
