# Bugs

## B001 - Windows settings casing bypasses guard classification

**Kind:** bug. **Observed/reported:** 2026-10-12; frozen settings candidate 531c793d285008f0bf8969eeed700b601b9326fe accepts Windows-equivalent `.AGENTS/SETTINGS.JSON`, while stop and security classifiers return no match. **Cause:** confirmed case-sensitive new settings expressions.

**Impact and priority:** P2; an effective settings change can bypass its mandatory classification, reproduced only in disposable fixtures; no real merge was invoked.

**Source owner:** tj-agents/core delivery-runtime stop classification and merge-review security classification. **State:** resolved. **Repair link:** PR208; canonical reviewed source0f98144fceff5040f6050413e036d26f1cf98ea8. **Next action:** none; the objective repair and delivery condition is verified.

**Resolution condition:** canonical and Windows-equivalent spellings receive the settings stop and security classification, guarded authorization rejects the changed settings path, and the repair passes focused checks, independent incremental review and exact-head Windows/Linux CI before normal delivery.

**Verification evidence:** independent security review reproduced preference=True with uppercase Windows settings, unmatched stop/security paths and scoped authorization acceptance. Parent independently confirmed both classifiers miss alternate casing while matching the canonical path. Repair artifacts now pass runtime 36, guarded auto-merge 10 and settings security patterns 10 tests; the fixed expressions and actual guarded-consumer rejection were inspected.

**Final delivery evidence:** Final reviewed head0f98144fceff5040f6050413e036d26f1cf98ea8 passed guard and Windows/Linux CI 38187755625 and independent incremental review. PR208 merged normally at a1a8d051e65e15d639a7a0fb0fc343c7b89fd72d; causal main ci38189303890 and regeneration114618404712 succeeded and published exact-parent bot commitcbe97265fcd8267493c24d18f74a5a0a26b872c9. Parent verified canonical/published engineering and both-host machine payload byte parity.


## B002 - Deep JSON leaves stale conditional machine permissions

**Kind:** bug. **Observed/reported:** 2026-10-12; deep present settings raise RecursionError, causing synchronization to return before removing existing Claude/Codex wrapper grants. **Cause:** confirmed decoder recursion failure excluded from the new reader's parse exception normalization.

**Impact and priority:** P2; stale invocation permissions remain although current settings are invalid. This does not establish a merge bypass; the guarded command retains its other controls.

**Source owner:** tj-agents/core repository settings reader and machine permission synchronization. **State:** resolved. **Repair link:** PR208; canonical reviewed source0f98144fceff5040f6050413e036d26f1cf98ea8. **Next action:** none; the objective repair and delivery condition is verified.

**Resolution condition:** deeply nested invalid present settings produce the reader's public ValueError boundary, existing Claude/Codex conditional grants are removed, and focused checks, independent incremental review and exact-head Windows/Linux CI pass before normal delivery.

**Verification evidence:** security review seeded both hosts' disposable owned grants, replaced settings with a 20,000-level opaque JSON array, observed main return zero with profiles unchanged. Parent independently reproduced the escaped RecursionError and inspected the machine ValueError boundary. Repair artifacts now pass reader 12 tests (2 privilege skips) and machine synchronization 28; parent inspected the strengthened active-grants-before/deep-invalid-settings-after assertions for both Claude and Codex.

**Final delivery evidence:** Final reviewed head0f98144fceff5040f6050413e036d26f1cf98ea8 passed guard and Windows/Linux CI 38187755625 and independent incremental review. PR208 merged normally at a1a8d051e65e15d639a7a0fb0fc343c7b89fd72d; causal main ci38189303890 and regeneration114618404712 succeeded and published exact-parent bot commitcbe97265fcd8267493c24d18f74a5a0a26b872c9. Parent verified canonical/published engineering and both-host machine payload byte parity.


## B003 - Invalid settings escape the no-legacy consumer error boundary

**Kind:** bug. **Observed/reported:** 2026-10-12. In an unrelated repository without delivery-authorization.json, malformed present settings escape workflow_ops.standing_authorization as DeliveryContractViolation; the guarded command's main catches WorkflowOperationError and therefore misses this error. **Cause:** confirmed absent-policy resolve call outside the existing translation boundary. The issue exists in initial candidate531 and remains at178ba; it is outside the latest parser/classifier delta, not a newly introduced incremental finding.

**Impact and priority:** P2; the generic no-legacy consumer rejects invalid settings with an uncaught exception rather than its controlled diagnostic. No merge is invoked and no bypass is established.

**Source owner:** tj-agents/core workflow_ops standing authorization consumer. **State:** resolved. **Repair link:** PR208; canonical reviewed source0f98144fceff5040f6050413e036d26f1cf98ea8. **Next action:** none; the objective repair and delivery condition is verified.

**Resolution condition:** malformed and deeply nested present settings with and without a legacy policy return the guarded command's controlled failure status/diagnostic, invoke no merge command, and pass focused regression, independent incremental review and exact-head Windows/Linux CI before causal delivery.

**Verification evidence:** fresh security lens compared immutable531 and178ba; both malformed no-policy cases escape DeliveryContractViolation and invoke zero merge commands. Parent independently called the actual standing_authorization in disposable repositories: absent legacy yields DeliveryContractViolation/public_workflow_error=False, valid legacy yields WorkflowOperationError/public_workflow_error=True. The new regression failed before with exactly two absent-policy errors and the final artifact passed11 tests, including malformed/deep inputs with both policy states, controlled settings diagnostic and zero merge commands. Delivery-binding38 and harness14 tests plus declaration consistency also passed; parent read the actual terminal artifacts.

**Final delivery evidence:** Final reviewed head0f98144fceff5040f6050413e036d26f1cf98ea8 passed guard and Windows/Linux CI 38187755625 and independent incremental review. PR208 merged normally at a1a8d051e65e15d639a7a0fb0fc343c7b89fd72d; causal main ci38189303890 and regeneration114618404712 succeeded and published exact-parent bot commitcbe97265fcd8267493c24d18f74a5a0a26b872c9. Parent verified canonical/published engineering and both-host machine payload byte parity.

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

**Verification evidence:** PR220 merged reviewed head 40ff30d9e006f37f87201fd38ae1c36de9268dd4 as 441a09ab3894ee0e076f6ff8e97d9c61d4a7aca2. Final review found no remaining defects; exact-head CI 38286569828 passed Windows, Linux and guard. Twenty-two local placement tests completed with two Windows symlink-capability skips. Causal run38288409546 attempt1 passed Windows, Linux and regeneration; generated commit3b41211db4b6349ca74036e0df3a6d8bc91784f2 carries matching hook and dependency bytes and both host mappings. No external feed or version-sync producer exists. Installed native-host trust and adoption remain unverified.
## B008 - Claude normal-profile sync accepts incomplete or misidentified packages
- Kind: bug. Observed/reported: 2026-10-12; profile repair found 208 cached files against 331 source files, including 61 missing skill definitions. Cause: confirmed Claude normal-profile synchronization omits torn-package checks and alias migration; installation discards `installPath` and `gitCommitSha`, and external groups ignores a different ref when `sourceURL` matches.
- Impact and priority: P2; synchronization can accept incomplete packages, discard source identity and pin information, and retain obsolete aliases.
- Source owner: tj-agents/core Claude normal-profile synchronization and profile-repair workflow.
- State: resolved.
- Repair link: PR #235, merged head `9690bff537e90f82c3c3a562c1ffa54a57c334e0`.
- Next action: none for the synchronization defect; fresh Claude-session acceptance remains owned by the existing goal under the user session limit.
- Resolution condition: sync rejects torn packages, preserves and validates `installPath` and `gitCommitSha`, handles differing refs despite matching `sourceURL`, and migrates obsolete aliases; focused checks and Windows/Linux CI pass before guarded merge.
- Verification evidence: canonical `engineering@tj-agents` pinned at v2.1.15 has 52 skills; cached state had 208 files versus 331 source files, with 61 skill definitions missing. Existing `dotnet@dotnet` and `react@react` entries point to nonexistent identities. No fresh Claude-session acceptance is claimed.
- Delivery evidence: independent review approved and exact-head Windows/Linux CI run `38336373168` passed before guarded merge at `8b33980747476f9369c1b39497908226c2990b21`.

## B009 - Stop dispatcher omits a blocking decision when its gate is missing
- Kind: bug. Observed/reported: 2026-10-12; transcript `fed1d447-ae67-4078-99a5-a813156cf86a`, line 1299, records `continuation_stop` and `callout_repair` returning `missingworkflow_route` and `missingworktree_cleanup_gate` in 1584 ms, exit 0, empty stdout. Cause: confirmed dispatcher fails to emit the required blocking decision when a workflow route or cleanup gate is missing (D2).
- Impact and priority: P1; the caller receives no actionable blocking decision and can continue without required stop/callout enforcement.
- Source owner: tj-agents/core stop dispatcher and its workflow/gate dependency checks.
- State: in-progress.
- Repair link: `plans/stop-gate-and-profile-repair/GOAL.md`, branch `Fix/StopGateFailures`.
- Next action: make missing route, gate, or import produce JSON `decision:block` with actionable diagnostics, then review the focused repair.
- Resolution condition: missing route, gate, or import produces JSON `decision:block` with actionable diagnostics; focused regressions and Windows/Linux CI pass before guarded normal merge.
- Verification evidence: original transcript result: `continuation_stop` and `callout_repair` reported `missingworkflow_route` and `missingworktree_cleanup_gate`; elapsed 1584 ms, exit 0, empty stdout.

## B010 - Built-in contract path stop defeats configured Core auto-merging

- Kind: bug. Observed/reported: 2026-10-13; PR234 had clean independent review and required Windows/Linux CI at df36331066f3ac1011415bce0c268f279f6cf771, but the agent asked Tommy for another manual merge decision. Tommy called out that the auto-approval configuration should prevent this interruption and explicitly instructed that the issue be documented and fixed later.
- Confirmed mechanism: .agents/workflows/delivery_runtime.py STOP_CLASSES defines published-contract with `(?:^|/)contracts?/|(?:^|/)(?:package\.json|Directory\.Packages\.props)$|\.nuspec$`, case-insensitive. It matches .agents/engineering/contract/committing/SKILL.md and plan-checkpoint/SKILL.md. DeliveryAuthorizationResolver.stop_patterns retains every class absent from authorized_stop_classes; resolve returns _stopped before its authorized-success result. This preserves auto_merge=true but changes merge_authorization.mode to absent.
- Actual configuration: .agents/settings.json has configuration.core.auto_merge=true. .agents/delivery-authorization.json has standing_authorization=auto and Tommy's 2026-10-09 instruction to merge without asking in tj-agents repositories once review and required checks pass; authorized_stop_classes contains auth only. No explicit user merge hold was observed for PR234. The built-in published-contract class, not an explicit repository path rule, produced the stop.
- Configuration distinction: auto_approve.all/design controls routine design decisions; auto_merge controls the merge preference and standing authorization records merge authority. This checkout does not declare auto_approve, so design delegation defaults false. That default did not cause this PR's merge hold. The merge setting was read; an inherited stop overrode the effective authorization. The resulting precedence and naming do not deliver Tommy's expected automatic workflow.
- Impact and priority: P1; a green, authorized standards delivery stalls on an additional human decision, and the same shared classification affects both Claude and Codex. Asking repeatedly makes the configured automation ineffective for common Core contract instruction edits.
- Source owner: tj-agents/core delivery authorization classification and configuration/merge guidance. State: deferred. Repair link: this canonical B010 record; related delivery plans/inert-closeout-cadence/GOAL.md and PR234; agent incident M016. Active repair executor: none.
- Ownership reconciliation: M008 settings-interface repair is resolved via PR208. Fix/RevalidateRecordedMergeGate and its M015 observation concern stale auth-class gates after authority changes; this case is a fresh published-contract resolution, so it is related but not that same causal defect. Reconcile that owner again before any overlapping enforcement repair.
- Deferral: Tommy explicitly said on 2026-10-13, "this is an issue we need to address later" and "just note it all down". blocked_by: dependency; resolver: Tommy/Core delivery-policy owner; resume when Tommy resumes this recorded repair. No new CLI session, side-workstream executor, implementation, settings edit or additional CI run was started.
- Next action: diagnose and repair the boundary between process instruction directories and actual consumer API/schema/package contracts; reconcile built-in stop precedence with the configured preference and standing instruction. Document the effective configuration and stop reason clearly. Preserve explicit user holds, protected settings/authority edits, current-head review and CI, and genuine public-contract safeguards. Do not fix this by globally exempting every .agents path or quietly rewriting the authorization table.
- Required regression coverage: configured auto_merge=true plus standing auto must not manufacture a manual gate solely because changed canonical process instructions live under .agents/engineering/contract/. Test committing and plan-checkpoint SKILL.md paths, Windows separators/casing, and shared Claude/Codex consumers. Genuine src/contracts/API or .agents/workflows/contract/v2 schema changes, explicit hold labels/stop paths, settings/authority edits and malformed configuration must retain their intended protection. Verify that the guarded merge consumer still requires clean exact-head review and terminal green CI.
- Resolution condition: effective authorization for the canonical instruction case honors the intended configured automatic delivery without another routine approval; real public-contract and explicit human gates remain meaningful; focused regressions, independent review, Windows/Linux source CI and causal generated-package verification pass. Confirm the distinction against the actual guarded consumer, not a settings-reader success alone.
- Verification evidence: actual settings/declaration read; STOP_CLASSES and resolver inspected; delivery-bind returned auto_merge=true, standing=auto, merge_authorization.mode=absent, stopped_by.class=published-contract and path=.agents/engineering/contract/committing/SKILL.md. PR234 run38323860505 guard/Windows/Linux succeeded, review watermark equals its remote head, and the agent nevertheless asked for manual merge. No causal repair has been implemented or verified.

**Record identity:** transferred from branch-local B009 on Fix/InertCloseoutCadence; main B009 already names a different defect, so B010 is this defect's canonical main ID. The earlier branch references remain historical aliases.

## B011 — Stale persistence skill reference after the EF Core cutover

Kind: bug. Observed: 2026-10-18. Priority: P2; public-corpus validation failed for a valid
personal-roster integration because shared routing guidance named a no-longer-shipped skill.
Source owner: tj-agents/core engineering skill-routes guidance. State: resolved.
Evidence: Windows CI 39173332372 rejected `.agents/engineering/convention/skill-routes/SKILL.md`
for missing dotnet:persistence after persistence moved to efcore:persistence.
Cause confirmed: the shared example was not migrated with the skill identity cutover.
Existing repair link: upstream commit ade368b3 (Use shipped skills in the routing example),
retained unchanged when reconciling https://github.com/tj-agents/core/pull/307. The final
example uses shipped dotnet:testing and react:testing identities; no parallel repair remains.
Resolution condition: current public-corpus skill references resolve and Windows/Linux
validation passes with the upstream repair present.
Verification: local check resolves 168 shipped skills across 4 current repositories; exact
Core PR307 run39175205937 and merged-main run39176000363 pass Windows/Linux.
Next action: none for this repaired reference defect. Installed host acceptance remains a
separate personal-project goal criterion.

## B012 — Exact script approvals rejected during project adoption

Kind: bug. Observed: 2026-10-19. Priority: P2; Core cannot adopt its own project settings
without discarding existing approvals or widening fixed commands to wildcard argument grants.
Source owner: machine plugin-selection harness_permissions.py. State: resolved.
Evidence: adopting personal in Core fails on existing Bash(pwsh .agents/sync-generated.ps1 -Check)
with script arguments require :*. The native Claude permission documentation supports exact
command rules: https://code.claude.com/docs/en/permissions.
Cause confirmed: _has_unbounded_script_arguments classifies fixed arguments after a script
as unbounded even when the command has no wildcard.
Repair link: Core Feature/PersonalAdoption, owned by personal-projects/standards; same coupled
slice preserves the repository's82existing approvals through its supported ownership overlay.
No verified live owner was found for the same defect in the related older harness worktree.
Resolution condition: exact command arguments survive generation unchanged, malformed script
wildcard patterns remain rejected, current Core adoption preserves its approval set, and
focused Windows/Linux plus reviewed exact-head CI and source publication pass.
Verification: Core PR313 merged 6b3719505a10690b63e56785777361f7eb949ec9 after corrected exact-head
CI 39308737267 passed Windows/Linux; causal main 39311721736 and policy 39311721852 passed.
39 project-config tests and 20harness-manifest tests passed on Windows/native Linux (three existing
Linux PowerShell-schema skips);13 adoption and 6selection tests passed. Current main canonical and
both packaged helper copies match. Existing82approvals and deny rules were preserved exactly.
Next action: none for this repaired validator defect. Live refresh B013 remains separately owned.

## B013 — Fresh Codex entry starts after rolling refresh exceeds its deadline

**Kind:** bug. **Observed:** 2026-10-19. **State:** blocked.
**Source owner:** Core rolling-plugin launcher; the originating Concertable launch-repair owner
retains implementation authority under the explicit personal-projects handoff. No second repair writer.
**Observation:** A fresh actual Windows Codex invocation through the installed normal launcher emitted
`rolling plugin refresh exceeded its deadline; starting Codex without the standards refresh`.
Thread `01a155a8-d50f-7cf1-b5a0-719e65856188` then quoted the mandatory native personal rule successfully.
Native instruction loading passed; installed plugin refresh convergence did not. Earlier shallow-lock
failure is separate evidence, not a confirmed cause of this deadline.
**Impact and priority:** P2; source/main and native-rule verification cannot establish that installed
registrations and running package generations converged at the entry point users invoke.
**blocked_by:** existing repair ownership and unverified launcher refresh.
**Resolver:** originating Concertable launch-repair owner; Tommy can resume that owner if needed.
**Concrete unblock:** diagnose the normal-launch refresh deadline in that existing repair scope,
repair its cause, and verify an actual fresh Windows/Linux session and installed generations.
**Resume condition:** a fresh normal launcher completes current publisher/package convergence and
loads the mandatory rule; version output or a continued session after refresh failure is insufficient.

## B014 — Project-selection guidance omitted exact Codex repository trust

Kind: bug. Observed: 2026-10-19. Priority: P2. State: resolved.
Source owner: machine:plugin-selection guidance; no launcher implementation change.
The guide claimed a fresh clone installed its declared plugins without machine settings. Actual normal
Concertable session01a15605 loaded its mandatory native policy but lacked personal in the skill catalog.
Native config/read explicitly disabled the project layer until its exact Git root was trusted, despite
existing trusted parent folders; native plugin inventory independently lacked the personal selection.
Correction: the guide distinguishes source settings from native admission, installation and session
loading, states the exact-root trust prerequisite and limits installation changes to existing authority.
Verification: authorized exact-project trust for personal and Concertable source roots through the native
configuration API preserved every unrelated setting and existing project entry. Fresh config/read then
reported enabled personal selection and no disabled project layer for both roots. Declaration checks
alone are expressly insufficient; actual host/catalog acceptance remains tracked in the personal goal.
