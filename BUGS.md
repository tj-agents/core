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

## B004 - Verified self-host remains alive after Windows Terminal discovery refuses

- Kind: bug. Observed/reported: 2026-10-12; exact close.py invocation refused Windows Terminal target is absent or ambiguous after observer acceptance/arming; observer cancelled because host did not exit.
- Cause: confirmed self-close/finish catches TerminalUnavailable only, while absent/ambiguous actual target raises TerminalRefusal. Own PID/start/attachment verified; current UI inventory has zero actual tabs. Infrastructure cause of UI discovery failure remains unknown.
- Impact/priority: P2; completed CLIs remain open and cleanup completion is unreliable.
- Source owner: machine peer-cli close.py/finish.py and directly causal closure guidance. State: in-progress.
- Repair link: plans/verified-self-close/GOAL.md, Fix/VerifiedSelfCloseFallback.
- Next action: independently reproduce refusal and repair verified self-process fallback while preserving peer-tab and unknown/PID-change refusal.
- Resolution condition: focused observer/process/identity regressions and Windows/Linux CI pass; reviewed source repair merged and causal generated packages verified.
- Verification evidence: exact registry entry PID9104/start1791756662.4871101; predecessor observer 1f29421b77f448e39c489f380948dbc2.json accepted/armed then cancelled; current actual_tab_count=0.

## B005 - Task recovery omits concrete authority evidence

**Kind:** bug. **Observed:** 2026-10-12. **State:** in-progress.

**Observation:** Exact-owner recovery was rejected before launch for insufficient task-specific authority. The original call named a goal and asserted authorization but omitted the authority wording/provenance and an execution justification. The existing machine recovery template asks only for the blocker and ownership reconciliation. These are confirmed evidence-carrying gaps; whether different evidence would have changed the original automatic-review decision is unknown.

**Impact and priority:** P2; recovery of an already owned task incurred another human interruption and could stall authorized work.

**Source owner:** tj-agents/core machine task-recovery guidance and no-send follow-up advice.

**Repair link:** PR210, branch `Fix/RecoveryAuthorizationContext`; private diagnostic evidence is retained locally and excluded from Git. Related incident: [M002](MISTAKES.md); prior M005/PR207 is a separate fallback repair.

**Next action:** Complete final review and corrected-head CI while preserving live-owner, uncertain-send and automatic-review gates.

**Resolution condition:** Both native hosts receive unchanged recovery instructions containing existing authority evidence; supported caller guidance carries exact task/scope/provenance into approval review without adding authority or overriding rejection; focused regressions, independent review and Windows/Linux CI pass, and the source correction plus causal generated packages reach main.

**Verification evidence:** Baseline recovery/follow-up/Claude-launcher suites passed on Windows. Delivery and new-regression evidence remains pending.

## B006 - Plan workflow fixture teardown races detached Git maintenance

- Kind: bug. Observed/reported: 2026-10-12; causal CI run 38266381371 attempt 1 failed on Linux with `Errno 39` deleting the fixture's `admin/.git`; attempt 2 passed. Reviewed PR head 110d0bc5 and merge 5f876750 have identical trees.
- Cause: unknown; detached Git maintenance is the leading hypothesis supported by four bounded TRACE2 child starts, but the exact failed writer was not observed. Existing `tests/test_check_generated_paths.py` disables automatic GC and maintenance for a similar cleanup race.
- Impact/priority: P2; intermittent PlanWorkflowHarness acceptance setup/cleanup failure.
- Source owner: tj-agents/core PlanWorkflowHarness test fixture. State: blocked.
- Repair link: branch `Fix/PlanFixtureMaintenanceRace`; canonical goal `plans/plan-fixture-maintenance-race/GOAL.md` in that branch.
- blocked_by: capability; the supported native handoff requires normal-profile refresh and permission convergence, excluded by current authorization.
- Resolver: machine handoff capability owner, or explicit authority for the required profile installation.
- Resume when: a supported successor can launch without profile changes, or Tommy explicitly authorizes the required profile and permission changes.
- Next action: set repository-local `gc.auto=0` and `maintenance.auto=false` before the first fixture commit; add a TRACE2 regression through `pr-slice-rollover`.
- Resolution condition: the independent repair is reviewed and merged, required Windows/Linux checks pass, teardown succeeds, and the bounded lifecycle trace starts no detached maintenance child.
- Verification evidence: four bounded TRACE2 child starts and the analogous existing fixture guards support the inferred cause; causal CI attempt 2 passed. The repair has not been made.

## B007 - Native worktree creation bypasses repository placement

**Kind:** bug. **Observed/reported:** October 8, 2026 creation records, reconciled October 12, 2026. Native Git created a sibling worktree despite internal-placement guidance. **Cause:** confirmed absence of a creation gate in both host engineering manifests.

**Impact and priority:** P2; new worktrees spread outside repository-owned layout.

**Source owner:** tj-agents/core engineering shared hooks and both host wiring. **State:** resolved. **Repair link:** [PR #220](https://github.com/tj-agents/core/pull/220). The allocator and migration remain owned by Feature/RepositoryOwnedLayout.

**Next action:** none; the objective repair and delivery condition is verified.

**Resolution condition:** supported Claude/Codex shell events reject sibling, nested and ambiguous allocation; verified internal creation works from linked checkouts; executable regressions, packaging, independent review and exact-head CI pass; source merges and causal generated distribution is verified.

**Verification evidence:** PR220 merged reviewed head 40ff30d9e006f37f87201fd38ae1c36de9268dd4 as 441a09ab3894ee0e076f6ff8e97d9c61d4a7aca2. Final review found no remaining defects; exact-head CI38286569828 passed Windows, Linux and guard. Twenty-two local placement tests completed with two Windows symlink-capability skips. Causal run38288409546 attempt1 passed Windows, Linux and regeneration; generated commit3b41211db4b6349ca74036e0df3a6d8bc91784f2 carries matching hook and dependency bytes and both host mappings. No external feed or version-sync producer exists. Installed native-host trust and adoption remain unverified.

## B008 - Final record commits restart a frozen delivery candidate

- Kind: bug. Observed/reported: 2026-10-12; the dotnet scaffold owner planned a status-only commit/push and another review/CI cycle after its final executable head was green. That extra loop was stopped before execution.
- Cause: confirmed policy conflict. Committing includes every verified documentation closeout, while merge requires local HEAD to match the reviewed remote head. The no-bookkeeping-push rule does not provide a sequence for late problem-record and final evidence updates. The agent's exact reasoning is not established by this source inspection.
- Impact/priority: P2; inert closeout records can trigger avoidable delivery cycles. Earlier scaffold compilation and security fixture repairs remain substantive work.
- Source owner: tj-agents/core engineering committing, problem-record and merge closeout contracts. State: blocked.
- Repair link: branch Fix/InertCloseoutCadence; plans/inert-closeout-cadence/GOAL.md.
- Next action: resolve PR234 published-contract merge decision, then verify merged source and causal generated distribution. blocked_by: dependency; resolver: Tommy/repository authorization owner. Resume when the contract merge stop is explicitly resolved.
- Resolution condition: shared guidance preserves the frozen source candidate through terminal delivery, allows timely local records and terminal checkpoints without a bookkeeping push, retains exact-head review/security/CI gates, and passes focused checks plus required Windows/Linux CI before merge.
- Verification evidence: reviewed and pushed df36331066f3ac1011415bce0c268f279f6cf771 in PR234; final independent native-general/workflow review clean; focused process/completion/cleanup and both-host packaging checks pass. Exact-head run38323860505 guard/Windows/Linux passed. Source merge held by the repository published-contract class, recorded as the deferred configuration/classification defect B009 after Tommy's callout; this late status record does not advance source HEAD.


## B009 - Built-in contract path stop defeats configured Core auto-merging

- Kind: bug. Observed/reported: 2026-10-13; PR234 had clean independent review and required Windows/Linux CI at df36331066f3ac1011415bce0c268f279f6cf771, but the agent asked Tommy for another manual merge decision. Tommy called out that the auto-approval configuration should prevent this interruption and explicitly instructed that the issue be documented and fixed later.
- Confirmed mechanism: .agents/workflows/delivery_runtime.py STOP_CLASSES defines published-contract with `(?:^|/)contracts?/|(?:^|/)(?:package\.json|Directory\.Packages\.props)$|\.nuspec$`, case-insensitive. It matches .agents/engineering/contract/committing/SKILL.md and plan-checkpoint/SKILL.md. DeliveryAuthorizationResolver.stop_patterns retains every class absent from authorized_stop_classes; resolve returns _stopped before its authorized-success result. This preserves auto_merge=true but changes merge_authorization.mode to absent.
- Actual configuration: .agents/settings.json has configuration.core.auto_merge=true. .agents/delivery-authorization.json has standing_authorization=auto and Tommy's 2026-10-09 instruction to merge without asking in tj-agents repositories once review and required checks pass; authorized_stop_classes contains auth only. No explicit user merge hold was observed for PR234. The built-in published-contract class, not an explicit repository path rule, produced the stop.
- Configuration distinction: auto_approve.all/design controls routine design decisions; auto_merge controls the merge preference and standing authorization records merge authority. This checkout does not declare auto_approve, so design delegation defaults false. That default did not cause this PR's merge hold. The merge setting was read; an inherited stop overrode the effective authorization. The resulting precedence and naming do not deliver Tommy's expected automatic workflow.
- Impact and priority: P1; a green, authorized standards delivery stalls on an additional human decision, and the same shared classification affects both Claude and Codex. Asking repeatedly makes the configured automation ineffective for common Core contract instruction edits.
- Source owner: tj-agents/core delivery authorization classification and configuration/merge guidance. State: deferred. Repair link: this canonical B009 record; related delivery plans/inert-closeout-cadence/GOAL.md and PR234; agent incident M016. Active repair executor: none.
- Ownership reconciliation: M008 settings-interface repair is resolved via PR208. Fix/RevalidateRecordedMergeGate and its M015 observation concern stale auth-class gates after authority changes; this case is a fresh published-contract resolution, so it is related but not that same causal defect. Reconcile that owner again before any overlapping enforcement repair.
- Deferral: Tommy explicitly said on 2026-10-13, "this is an issue we need to address later" and "just note it all down". blocked_by: dependency; resolver: Tommy/Core delivery-policy owner; resume when Tommy resumes this recorded repair. No new CLI session, side-workstream executor, implementation, settings edit or additional CI run was started.
- Next action: diagnose and repair the boundary between process instruction directories and actual consumer API/schema/package contracts; reconcile built-in stop precedence with the configured preference and standing instruction. Document the effective configuration and stop reason clearly. Preserve explicit user holds, protected settings/authority edits, current-head review and CI, and genuine public-contract safeguards. Do not fix this by globally exempting every .agents path or quietly rewriting the authorization table.
- Required regression coverage: configured auto_merge=true plus standing auto must not manufacture a manual gate solely because changed canonical process instructions live under .agents/engineering/contract/. Test committing and plan-checkpoint SKILL.md paths, Windows separators/casing, and shared Claude/Codex consumers. Genuine src/contracts/API or .agents/workflows/contract/v2 schema changes, explicit hold labels/stop paths, settings/authority edits and malformed configuration must retain their intended protection. Verify that the guarded merge consumer still requires clean exact-head review and terminal green CI.
- Resolution condition: effective authorization for the canonical instruction case honors the intended configured automatic delivery without another routine approval; real public-contract and explicit human gates remain meaningful; focused regressions, independent review, Windows/Linux source CI and causal generated-package verification pass. Confirm the distinction against the actual guarded consumer, not a settings-reader success alone.
- Verification evidence: actual settings/declaration read; STOP_CLASSES and resolver inspected; delivery-bind returned auto_merge=true, standing=auto, merge_authorization.mode=absent, stopped_by.class=published-contract and path=.agents/engineering/contract/committing/SKILL.md. PR234 run38323860505 guard/Windows/Linux succeeded, review watermark equals its remote head, and the agent nevertheless asked for manual merge. No causal repair has been implemented or verified.
