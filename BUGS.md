# Bugs

```agent-handoff-disposition
{"schema_version":1,"record_id":"B011","kind":"bug","state":"deferred","callout":{"session_id":"01a1362c-5751-75f3-a54d-9bb37f25a41a","callout_id":"9c4f5441-05ea-4f6c-8928-b4ad73154ef1","prompt_sha256":"6f4ed91c3a8224e79afdb944f48f7c7783b0703d04075ac947b59bc3340ac34c"},"source_owner":"tj-agents/core engineering:self-repair, engineering:handoff, persistent-workflow, and callout PreToolUse enforcement","repair_goal":"C:\\Users\\TommySeery\\source\\repos\\tj-agents\\core\\plans\\self-repair-admission-deadlock\\GOAL.md","disposition":"deferred","reason":"The active callout gate rejects the isolated-checkout Git command and exact admission validator; duplicate stale hook prompts have also been delivered as user turns.","blocked_by":"capability","resolver":"tj-agents/core callout-gate repair owner","resume_condition":"The bound repair admits its declared Git and admission-validator commands while duplicate hook events are discarded.","next_action":"Create the isolated Core checkout, reproduce admission and duplicate-event paths, repair the gate predicate, and add end-to-end regressions.","evidence":{"kind":"executable-failure","executable":"python","operation":"execute","error":"PreToolUse rejected the exact required admission.py check command with the active CALLOUT REPAIR message."}}
```

```text
{"schema_version":1,"record_id":"B011","kind":"bug","state":"deferred","callout":{"session_id":"01a1362c-5751-75f3-a54d-9bb37f25a41a","callout_id":"9c4f5441-05ea-4f6c-8928-b4ad73154ef1","prompt_sha256":"6f4ed91c3a8224e79afdb944f48f7c7783b0703d04075ac947b59bc3340ac34c"},"source_owner":"tj-agents/core engineering:self-repair, engineering:handoff, persistent-workflow, and callout PreToolUse enforcement","repair_goal":"C:\\Users\\TommySeery\\source\\repos\\tj-agents\\core\\plans\\self-repair-admission-deadlock\\GOAL.md","disposition":"deferred","reason":"The active callout gate rejects the isolated-checkout Git command and exact admission validator; duplicate stale hook prompts have also been delivered as user turns.","blocked_by":"capability","resolver":"tj-agents/core callout-gate repair owner","resume_condition":"The bound repair admits its declared Git and admission-validator commands while duplicate hook events are discarded.","next_action":"Create the isolated Core checkout, reproduce admission and duplicate-event paths, repair the gate predicate, and add end-to-end regressions.","evidence":{"kind":"executable-failure","executable":"python","operation":"execute","error":"PreToolUse rejected the exact required admission.py check command with the active CALLOUT REPAIR message."}}
```

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

## B005 - Task recovery omits concrete authority evidence

**Kind:** bug. **Observed:** 2026-10-12. **State:** in-progress.

**Observation:** Exact-owner recovery was rejected before launch for insufficient task-specific authority. The original call named a goal and asserted authorization but omitted the authority wording/provenance and an execution justification. The existing machine recovery template asks only for the blocker and ownership reconciliation. These are confirmed evidence-carrying gaps; whether different evidence would have changed the original automatic-review decision is unknown.

**Impact and priority:** P2; recovery of an already owned task incurred another human interruption and could stall authorized work.

**Source owner:** tj-agents/core machine task-recovery guidance and no-send follow-up advice.

**Repair link:** PR210, branch `Fix/RecoveryAuthorizationContext`; private diagnostic evidence is retained locally and excluded from Git. Related incident: [M002](MISTAKES.md); prior M005/PR207 is a separate fallback repair.

**Next action:** Complete final review and corrected-head CI while preserving live-owner, uncertain-send and automatic-review gates.

**Resolution condition:** Both native hosts receive unchanged recovery instructions containing existing authority evidence; supported caller guidance carries exact task/scope/provenance into approval review without adding authority or overriding rejection; focused regressions, independent review and Windows/Linux CI pass, and the source correction plus causal generated packages reach main.

**Verification evidence:** Baseline recovery/follow-up/Claude-launcher suites passed on Windows. Delivery and new-regression evidence remains pending.

## B006 - Native handoff sessions display generic read-instruction names

- **Kind:** bug.
- **Observed/reported:** 2026-10-12, Tommy reports the visible terminal/session names say `Read handoff...`
  rather than describing the work. Native Codex session_index.jsonl confirms `Read handoff instructions`
  for problem-skills session `01a12c10-0de6-7152-a9f2-9e5f374021f8` and
  `Read and follow handoff instructions` for priority/deferral session
  `01a12ad4-3f5b-7c72-ad11-ea65007cdd0c`.
- **Cause:** confirmed mismatch between the descriptive launcher/peer-registry title and the persisted
  native session name. The installed prompt_file_argument sends a generic `Read the file at ...`
  instruction; open_session passes its descriptive label to launch_tab without setting the native
  session name. Windows Terminal receives --title and --suppressApplicationTitle. The host's precise
  automatic-name derivation has not been inspected; the matching prompt/name pattern alone is not proof
  of that internal algorithm. The resumed session still has its old generic native name.
- **Impact and priority:** P2; distinct agents appear indistinguishable by task, making supervision and
  recovery unnecessarily dependent on opening their chats. Two concrete sessions are verified.
- **Source owner:** core machine native handoff/recovery integration and task-name propagation, with
  engineering handoff supplying the concrete task description.
- **State:** open.
- **Repair link:** this record owns the runtime repair. Related naming debt:
  [.agents/machine/TECH_DEBT.md](.agents/machine/TECH_DEBT.md#d-machine-task-titles-terminal-names-must-explain-the-current-task).
  No separate repair session is assigned; the ongoing priority/deferral repair retains its existing owner.
- **Next action:** find the supported native session naming/renaming interface and propagate the selected
  task title for creation and exact-session resume. Reconcile #117's terminal-title protection; it does not
  establish native session-name correctness. Do not directly rewrite a live host's internal index as a fix.
- **Resolution condition:** handoffs show names such as `Add bug and mistake skills` and
  `Launch, reuse or defer repair handoffs` in the native session list and terminal surfaces the user sees.
  Verify the names after initialization and resume, including persisted native names and the visible UI;
  a launcher argument or peer-registry title alone is insufficient. Preserve session IDs, transcript,
  worktree/PR ownership and pending continuation. Verify supported Codex/Claude paths separately.
- **Verification evidence:** the two exact native-index entries above, the supplied descriptive resume
  title, peer-cli's matching descriptive registry title, and inspected installed prompt/launch/resume code.
  The failure is recorded and diagnosed to the title-path mismatch; no title repair is claimed.

## B007 - Headless capability probe repeatedly blocked at Stop

- **Kind:** bug. **Observed:** 2026-10-12; a read-only native Codex `exec` capability probe in the Docs/ExistingSolutions checkout returned `Available.` and then repeated `hook: Stop Blocked` and no-active-owner replies rather than exiting. This task stopped only that uniquely identified probe process after the answer.
- **Cause:** unknown. The blocking hook identity and full reason were not captured. The shared checkout had an active foreground continuation owner for a separate delivery; that fact does not establish which hook blocked the child. Do not attribute this to a particular source implementation without the hook verdict.
- **Impact and priority:** P2; an otherwise completed headless probe consumed further turns and required caller cancellation.
- **Source owner:** unknown pending identification of the blocking installed hook and its source package.
- **State:** open. **Repair link:** this record; related coverage owner is plans/continuation-enforcement/PLAN.md, without reopening or duplicating its completed delivery.
- **Next action:** capture the exact Stop verdict for a disposable quick-answer child alongside a live unrelated foreground owner, then route its verified source cause to the existing owner or a bounded source repair.
- **Resolution condition:** the completed quick-answer child exits normally while the independent live delivery retains its foreground ownership; the identified hook has a meaningful regression if it caused the refusal.
- **Verification evidence:** local continuation-probe.log under the handoff-comparison-36325574a6604d778c69a347660ffa99 temporary directory contains the answer and repeated Stop blocks; caller ancestry identified only the task's probe PID 40936. The model answered, but full unattended child acceptance is not established by that probe.

## B008 - Existing-solution assessment belongs to idea initialization

- **Kind:** bug. **Observed:** 2026-10-12; Tommy clarified that the public-alternative check should run once when a new idea is introduced and must not be invoked again during handoff or resume.
- **Cause:** confirmed lifecycle-owner mistake in PR 221: the parent added the convention to base goal-continuation instead of idea initialization. Existing reuse wording reduces repetition but retains an automatic material-change reassessment exception inconsistent with the clarified requirement. No repeated search was observed.
- **Impact and priority:** P2; shared instructions can misclassify continuation as initialization and repeat completed research.
- **Source owner:** core shared base convention and its delivery mapping. **State:** in-progress.
- **Repair link:** .worktrees/Fix-IdeaInitialization/plans/idea-initialization/GOAL.md; one standing-authorized bounded source workstream on Fix/IdeaInitialization.
- **Next action:** move the small convention to the appropriate shared initialization owner, carry the completed decision across handoffs, and verify both host mappings before review and delivery.
- **Resolution condition:** all core consumers receive one canonical, brief once-per-idea rule; resumes and handoffs consult the saved decision without another search; required checks, independent review, source merge and causal generated package verification pass.
- **Verification evidence:** current origin/main and PR 221 retain the assessment under goal-continuation; the user's same-session correction establishes the intended lifecycle. The isolated repair goal is prepared; launcher submission and recipient pickup must be observed separately.

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

## B011 - Callout repair gate blocks the commands required to admit a repair (canonical)

2026-10-14 career-session evidence: session `01a135fb-ec26-76f3-abd8-398ba45127b4` reproduced the repeating Stop binding and rejection of broad preparation commands. Single-segment reads, plain `git log`/`git diff`, record-only `apply_patch`, and plain `git worktree add` succeeded. Prepared isolated checkout `C:\Users\TommySeery\source\repos\tj-agents\core.worktrees\Fix-CalloutAdmissionCareer` owns a bounded repair goal at `plans/self-repair-admission-deadlock/GOAL.md`. Automatic approval review rejected its native successor launch before process creation, citing absent explicit user authority for autonomous Core enforcement modification and delivery. No successor was launched or implementing writer assigned. Resume requires Tommy's explicit authorization and successful approval review; do not bypass the rejection. The proposed closeout/write-wi/write-feature work remains planning-only.

- **Kind:** bug. **Observed/reported:** 2026-10-14. After a user called out an agent's failure to preserve another delivery owner's boundary, the active Codex callout gate required `engineering:self-repair` admission but rejected `git rev-parse --show-toplevel`, `Get-ChildItem`, and the exact required `admission.py check` with its own callout-repair message. It then injected the same stale `<hook_prompt>` repeatedly; the session incorrectly treated those duplicates as user turns and emitted blank final responses. Direct reads of already-known skill files remained possible. A foreground 50-second sleep loop was also used to keep the session open, producing status churn instead of a bound background continuation. **Cause:** confirmed replay behavior and admission-command rejection; the responsible host/gate deduplication boundary is unknown pending source diagnosis.
- **Impact and priority:** P1; a standards-caused mistake cannot be recorded, isolated, admitted, or handed off through the required workflow. The gate turns the mandated repair path into a deadlock.
- **Source owner:** tj-agents/core `engineering:self-repair`, `engineering:handoff`, and the callout PreToolUse enforcement path.
- **State:** deferred.
- **Repair link:** `plans/self-repair-admission-deadlock/GOAL.md`.
- **Next action:** when the callout gate permits the declared Git and admission-validator commands, create the isolated Core checkout, diagnose the gate predicate, add a regression covering repair admission and wait handling, and deliver through the normal Core workflow.
- **Resolution condition:** a called-out session can read governing rules, record the incident, run `admission.py check`, resolve/create its isolated Core checkout, and launch exactly one bounded repair without bypassing the callout gate; unrelated commands remain protected. A repeated or stale hook payload with an already-processed `(session_id, callout_id, prompt_sha256)` binding is discarded with no user-visible reply, record update, command, or new binding; a genuine new user message remains actionable. On a user `wait` or `keep open` instruction, the runtime either binds exactly one durable monitor to an exact owned delivery or enters one quiet idle state. It never uses foreground sleep polling, repeated status messages, or a second monitor for another agent's delivery.
- **Verification evidence:** this session read the governing `engineering:self-repair`, `engineering:handoff`, and `engineering:open-worktree` contracts. The observed commands `git -C 'C:\Users\TommySeery\source\repos\tj-agents\dotnet' rev-parse --show-toplevel`, `Get-ChildItem -Force 'C:\Users\TommySeery\source\repos\tj-agents'`, and the exact required `python -B ...\admission.py check --record ...\BUGS.md --id B011` were each rejected by the same PreToolUse callout-repair message.

```text
{"schema_version":1,"record_id":"B011","kind":"bug","state":"deferred","callout":{"session_id":"01a1362c-5751-75f3-a54d-9bb37f25a41a","callout_id":"7c3e57e0-bd1e-4752-9934-f1fb852b68ca","prompt_sha256":"4f67d7dfe612f03cb41e53186976086c2fa7c1706355da5e2abde68b4df5c443"},"source_owner":"tj-agents/core engineering:self-repair, engineering:handoff, persistent-workflow, and callout PreToolUse enforcement","repair_goal":"C:\\Users\\TommySeery\\source\\repos\\tj-agents\\core\\plans\\self-repair-admission-deadlock\\GOAL.md","disposition":"deferred","reason":"The active callout gate rejects both the Git command required by engineering:open-worktree to resolve an isolated Core checkout and the exact admission validator required to release a deferred disposition; the missing admitted transition also led to foreground wait polling instead of a bound durable monitor or quiet idle state.","blocked_by":"capability","resolver":"tj-agents/core callout-gate repair owner","resume_condition":"The active callout gate permits the declared git and admission-validator commands for this bound repair without permitting unrelated work.","next_action":"Create the isolated Core checkout, reproduce the admission and wait paths, repair the callout-gate predicate, and add end-to-end regressions.","evidence":{"kind":"executable-failure","executable":"python","operation":"execute","error":"PreToolUse rejected the exact required admission.py check command with the active CALLOUT REPAIR message."}}
```

### Historical duplicate of B011

- **Kind:** bug. **Observed/reported:** 2026-10-14. After a user called out an agent's failure to preserve another delivery owner's boundary, the active Codex callout gate required `engineering:self-repair` admission but rejected `git rev-parse --show-toplevel` and `Get-ChildItem` with its own callout-repair message. Direct reads of already-known skill files remained possible. A foreground 50-second sleep loop was then used to keep the session open; it produced repeated user-visible status churn instead of a bound background continuation.
- **Impact and priority:** P1; a standards-caused mistake cannot be recorded, isolated, admitted, or handed off through the required workflow. The gate turns the mandated repair path into a deadlock.
- **Source owner:** tj-agents/core `engineering:self-repair`, `engineering:handoff`, and the callout PreToolUse enforcement path.
- **State:** deferred.
- **Repair link:** `plans/self-repair-admission-deadlock/GOAL.md`.
- **Next action:** when the callout gate permits the declared Git and admission-validator commands, create the isolated Core checkout, diagnose the gate predicate, add a regression covering repair admission and wait handling, and deliver through the normal Core workflow.
- **Resolution condition:** a called-out session can read governing rules, record the incident, run `admission.py check`, resolve/create its isolated Core checkout, and launch exactly one bounded repair without bypassing the callout gate; unrelated commands remain protected. On a user `wait` or `keep open` instruction, the runtime either binds exactly one durable monitor to an exact owned delivery or enters one quiet idle state. It never uses foreground sleep polling, repeated status messages, or a second monitor for another agent's delivery.
- **Verification evidence:** this session read the governing `engineering:self-repair`, `engineering:handoff`, and `engineering:open-worktree` contracts. The observed commands `git -C 'C:\Users\TommySeery\source\repos\tj-agents\dotnet' rev-parse --show-toplevel`, `Get-ChildItem -Force 'C:\Users\TommySeery\source\repos\tj-agents'`, and the exact required `python -B ...\admission.py check --record ...\BUGS.md --id B011` were each rejected by the same PreToolUse callout-repair message.

```text
{"schema_version":1,"record_id":"B011","kind":"bug","state":"deferred","callout":{"session_id":"01a1362c-5751-75f3-a54d-9bb37f25a41a","callout_id":"7c3e57e0-bd1e-4752-9934-f1fb852b68ca","prompt_sha256":"4f67d7dfe612f03cb41e53186976086c2fa7c1706355da5e2abde68b4df5c443"},"source_owner":"tj-agents/core engineering:self-repair, engineering:handoff, persistent-workflow, and callout PreToolUse enforcement","repair_goal":"C:\\Users\\TommySeery\\source\\repos\\tj-agents\\core\\plans\\self-repair-admission-deadlock\\GOAL.md","disposition":"deferred","reason":"The active callout gate rejects both the Git command required by engineering:open-worktree to resolve an isolated Core checkout and the exact admission validator required to release a deferred disposition; the missing admitted transition also led to foreground wait polling instead of a bound durable monitor or quiet idle state.","blocked_by":"capability","resolver":"tj-agents/core callout-gate repair owner","resume_condition":"The active callout gate permits the declared git and admission-validator commands for this bound repair without permitting unrelated work.","next_action":"Create the isolated Core checkout, reproduce the admission and wait paths, repair the callout-gate predicate, and add end-to-end regressions.","evidence":{"kind":"executable-failure","executable":"python","operation":"execute","error":"PreToolUse rejected the exact required admission.py check command with the active CALLOUT REPAIR message."}}
```
<!-- Current B011 disposition: replaces stale duplicate bindings above. -->
```text
{"schema_version":1,"record_id":"B011","kind":"bug","state":"deferred","callout":{"session_id":"01a1362c-5751-75f3-a54d-9bb37f25a41a","callout_id":"9c4f5441-05ea-4f6c-8928-b4ad73154ef1","prompt_sha256":"6f4ed91c3a8224e79afdb944f48f7c7783b0703d04075ac947b59bc3340ac34c"},"source_owner":"tj-agents/core engineering:self-repair, engineering:handoff, persistent-workflow, and callout PreToolUse enforcement","repair_goal":"C:\\Users\\TommySeery\\source\\repos\\tj-agents\\core\\plans\\self-repair-admission-deadlock\\GOAL.md","disposition":"deferred","reason":"The active callout gate rejects the isolated-checkout Git command and exact admission validator; duplicate stale hook prompts have also been delivered as user turns.","blocked_by":"capability","resolver":"tj-agents/core callout-gate repair owner","resume_condition":"The bound repair admits its declared Git and admission-validator commands while duplicate hook events are discarded.","next_action":"Create the isolated Core checkout, reproduce admission and duplicate-event paths, repair the gate predicate, and add end-to-end regressions.","evidence":{"kind":"executable-failure","executable":"python","operation":"execute","error":"PreToolUse rejected the exact required admission.py check command with the active CALLOUT REPAIR message."}}
```
<!-- Current B011 disposition: replaces stale duplicate bindings above. -->
```text
{"schema_version":1,"record_id":"B011","kind":"bug","state":"deferred","callout":{"session_id":"01a1362c-5751-75f3-a54d-9bb37f25a41a","callout_id":"9c4f5441-05ea-4f6c-8928-b4ad73154ef1","prompt_sha256":"6f4ed91c3a8224e79afdb944f48f7c7783b0703d04075ac947b59bc3340ac34c"},"source_owner":"tj-agents/core engineering:self-repair, engineering:handoff, persistent-workflow, and callout PreToolUse enforcement","repair_goal":"C:\\Users\\TommySeery\\source\\repos\\tj-agents\\core\\plans\\self-repair-admission-deadlock\\GOAL.md","disposition":"deferred","reason":"The active callout gate rejects the isolated-checkout Git command and exact admission validator; duplicate stale hook prompts have also been delivered as user turns.","blocked_by":"capability","resolver":"tj-agents/core callout-gate repair owner","resume_condition":"The bound repair admits its declared Git and admission-validator commands while duplicate hook events are discarded.","next_action":"Create the isolated Core checkout, reproduce admission and duplicate-event paths, repair the gate predicate, and add end-to-end regressions.","evidence":{"kind":"executable-failure","executable":"python","operation":"execute","error":"PreToolUse rejected the exact required admission.py check command with the active CALLOUT REPAIR message."}}
```

## B012 - Listing no-match diagnostic denies repository plans

**Kind:** bug. **Observed/reported:** 2026-10-15; the extracted list-work no-match branch says `~/.claude/plans is the whole corpus` and a repo roadmap is never searched, while `repo_plans()` actually scans repository plans. The same diagnostic and assertion already exist in the pre-extraction workboard implementation. **Cause:** confirmed stale output string after repository-plan discovery was added.

**Impact and priority:** P3; a search with no matches gives misleading coverage information. Listing and repository discovery still run. **Source owner:** tj-agents/core engineering listing script and its reporting regression. **State:** open. **Repair link:** BUGS.md#B012; no separate repair executor.

**Next action:** assess a bounded correction to the no-match diagnostic and its existing reporting assertion after the approved behavior-preserving extraction. **Resolution condition:** no-match output accurately names the searched corpus and the focused reporting/discovery tests pass before normal review and delivery. **Verification evidence:** inspection of the unchanged extracted branch and its inherited reporting test in Refactor/ListWork at cddb671; repository-plan tests pass. Recording does not expand the current extraction or authorize a separate source repair/publication.

## B013 - Agent reads guessed skill locations and stale goal paths

- **Kind:** bug. **Observed/reported:** 2026-10-15; Tommy identified the two failed `Read SKILL.md` / `Read GOAL.md` operations in the tool log of Codex session `01a13fa0-a1c6-7051-b3ce-a63fb26916da`.
- **Cause:** confirmed incorrect path selection at the agent call site: `write-mistake` was guessed under `engineering/utility` although its advertised entry links to `engineering/convention`; the cached `plans/always-latest-plugins/GOAL.md` path was used after the active goal moved to `plans/rolling-plugin-sync/GOAL.md`. A later package-resource read repeated the guessed-layout error. No missing skill or broken file-reader runtime is established. The deeper reason existing discovery guidance did not prevent this remains unverified.
- **Impact and priority:** P2; avoidable failed tools and repeated discovery slow the active task and its repair, and can produce false missing-capability claims.
- **Source owner:** tj-agents/core skill-source discovery and goal-recovery guidance; this session's enforcement of those instructions. The personal problem-record publication policy is a separate design concern.
- **State:** open. **Repair link:** this record; incident context `plans/rolling-plugin-sync/GOAL.md` in `Fix/RollingPluginSync`. No separate implementation executor is claimed.
- **Next action:** use the advertised skill entry and resolve its actual relative link; refresh the current goal path from the work-item record after a rename; assess the smallest prevention change in the owning discovery/recovery guidance.
- **Resolution condition:** advertised skills and renamed goals resolve through observed metadata instead of invented directory layouts; focused discovery/rename cases and an observed replay find the existing files without false missing-capability reports.
- **Verification evidence:** incorrect reads returned path-not-found; the advertised `codex-skills/write-mistake/SKILL.md` exposed the correct canonical link, and work-item status plus a successful read identified `plans/rolling-plugin-sync/GOAL.md`. A source prevention fix has not yet been verified.
- **17 October recurrence:** guessed canonical directories caused additional avoidable path-not-found reads in this same session. The operating correction is to read the advertised host entry and follow its exact canonical link, or enumerate the path before reading. A durable source prevention change and replay remain pending.
- **Publication:** Tommy explicitly requested accumulation in the primary checkout without committing each observation. Leave this record uncommitted for a later batch; do not open a per-record docs PR.

## B014 - Unfinished goal ends without a verified continuation or actionable blocker

- **Kind:** bug. **Observed/reported:** 2026-10-17, Codex session `01a13fa0-a1c6-7051-b3ce-a63fb26916da`. The always-latest publisher rollout ended with several authorized migrations unfinished, no pending question, no continuing owner/listener, and no concrete unblock action or observable resumption mechanism. Tommy explicitly requested a prevention repair. The reason stated was repeated Windows process-creation error26.
- **Cause:** the observed failure to enforce continuation is confirmed; its live host cause is still under investigation. Current source `continuation_stop.outcome` would block this exact session/worktree because a delivery binding exists, yet no route receipt or continuation owner exists and no refusal appeared in the transcript. Do not substitute a source-only predicate test for host acceptance or blame a prompt matcher without causal evidence.
- **Impact and priority:** P1 shared lifecycle failure; unfinished authorized work can silently lose active ownership and force Tommy to rediscover what remains.
- **Source owner:** tj-agents/core shared continuation and host hook delivery/adoption.
- **State:** in-progress.
- **Repair link:** parent-owned `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-AlwaysLatestPlugins/plans/rolling-plugin-sync/GOAL.md`, branch `Fix/RollingDependencyActivation`, Core PR284. The former `Fix-VerifyStopEnforcement/plans/stop-enforcement-recovery/GOAL.md` is retained as historical failed-successor evidence; no native successor remains active.
- **Next action:** capture the actual native Stop delivery/payload and installed hook identity, establish the causal failure, and repair it with a regression through the real host boundary.
- **Resolution condition:** an unfinished accepted goal cannot finish a turn with an unactionable status alone; it retains working ownership, a verified continuation, a real user question, or a whole-goal blocker with resolver, unblock action, observable resume condition and next action. Genuine completion, explicit pause/cancel and unrelated quick-answer sessions remain valid. Source checks, independent review, Windows/Linux CI, guarded merge and causal publication pass; native host acceptance demonstrates the actual correction.
- **Verification evidence:** parent source/live-state probes plus the read-only stop_repair_evidence investigation. Prior PR237 merged 2026-10-13 as `e1fe101a1acd217c360dc02bc734d2f4822ebdab`; its old BUGS B009 status is stale, and the old repair checkout is absent. Current primary problem IDs were reconciled through B013 before reserving B014. Callout prompt SHA-256: `9057815574d0bf21ea3ffbc380e9b9d41d041614e2612b7857095d29ba151e38`. No host callout nonce was found; this absence must remain explicit rather than fabricated.
- **Additional native/transport evidence (17 October):** the isolated sibling-import crash is corrected in current PR284, alongside bounded Windows child cleanup and preservation of startup errors. The failed successor had no assistant/tool actions and was terminated by verified process handle. A normally trusted disposable native0.163 SessionStart fixture confirmed snake-case event name and startup environment delivery; Core Stop acceptance is still unproven. The PR reviewer exposed an unavailable Store PowerShell hook shell; the same immutable candidate is being reviewed using process-local discovery of working Windows PowerShell, retaining hooks and trust. Separately, the 20-second post-spawn SessionStart deadline can kill an idle CLI before its first turn and requires lifecycle correction. Source tests pass but neither this record nor PR284 alone closes B014.
- **Current repair checkpoint:** PR284 merged as `c978ef030e4dbed4c4b49b0be055c85212a3760e` after clean exact-head reviews and Windows/Linux CI39037681354; causal publication39039256296 is monitored. Actual native0.163 Stop, using one local mock completion and normal fixture trust, returned `blocked` with the canonical unfinished-binding reason (Temp/tj-native-core-stop-7k6zp3vs/rpc-observation.jsonl). This proves native predicate behavior, not the original historical catalog or packaged adoption. Exact old0.162.0-alpha.17.2 source supports Stop and defaults hooks on; absent retained startup evidence leaves original adoption unresolved. The parent owns the idle-safe runtime binding implementation here; no second repair successor is active.
- **17 October follow-up:** published packaged Core adoption was verified unchanged at e86326e73956e3980a38d5e708bffd3cc7bffd24: actual SessionStart and UserPromptSubmit completed, then actual Stop blocked the unfinished binding with the canonical reason. Evidence is Temp/tj-native-packaged-core-stop-r7uckfnt/rpc-observation.jsonl; normal read-only/approval-never policy and all ten normally trusted engineering hooks were retained. Owned cleanup completed after the child exited. PR284 causal publication39039256296 succeeded as 2bc7f61b2ebcd6b3b45615597093d3b3a9d8fa42. Idle-safe private runtime binding is being delivered separately in PR286 at f42b21ce980f42108bae0f86f4731680e394729c after native review caught and remediation corrected coordinator freshness, active-root discovery, unmanaged versions and blocking receipt errors. Final incremental review and GitHub Windows/Linux suites remain pending. Original historical non-invocation remains unproven; this record is not closed from source tests.
- **Publication:** Tommy's standing instruction is to accumulate observations in the primary checkout uncommitted for a later batch. This entry is not a per-record docs PR.

## B015 - Resumed Codex sessions never refresh their live-session registration

**Kind:** bug. **Observed/reported:** 2026-10-18; Codex session `01a1415f-6448-7123-8b17-c7fb67aee637` was reopened through `agent_recovery.py reopen` and verified (by native history growth) on 2026-10-17 21:27 and 22:33 and on 2026-10-18 04:36 and 12:12. After every reopen, `~/.agents-state/cli-sessions/<id>.json` and the `sessions.db` row still held the original pid 28032 and `started_at` 1792116160. **Cause:** unknown; `register_session.py` runs from the Codex SessionStart hook, but whether a resumed Codex fires it, or the hook fails within its 7-second dispatch deadline, is unverified.

**Impact and priority:** P1; `liveness()` reports a running resumed session as `closed`, so open-cli cannot focus it and peer-cli cannot list or close it. This was also the root cause of reopen refusing permanently ("pending or ambiguous"), mitigated by PR #294's process-tracked launch receipts. **Source owner:** tj-agents/core machine `peer-cli` registration hook and Codex SessionStart wiring. **State:** open. **Repair link:** none; PR #294 removes the receipt dependency only.

**Next action:** resume a Codex session with hook logging enabled and observe whether SessionStart fires and whether `register_session.py` completes. **Resolution condition:** after a verified `codex resume`, the registry and `sessions.db` record the resumed process's pid and start time, covered by a regression. **Verification evidence:** registry and `sessions.db` contents read on 2026-10-18 after the 12:12 reopen; launch receipts `.failed-20261017` and `.stale-20261017` in `~/.agents-state/recovery-launches` show the earlier repeats.

## B016 - Codex reopen spends minutes in startup preflight before the CLI starts

**Kind:** bug. **Observed/reported:** 2026-10-18; the 12:12 reopen of `01a1415f-…` wrote the startup wrapper status `preparing` at created_at 1792321914 and `running` at 1792322169, so about 255 seconds passed before native Codex launched. The pickup then did not verify within 480 seconds. **Cause:** unknown; the time is inside `startup_binding.run_session` preflight (plugin selection, convergence and trust), which is not yet broken down.

**Impact and priority:** P2; reopening a session takes over four minutes and makes `open-cli` report an unverified launch. **Source owner:** tj-agents/core machine `startup_binding.py` and rolling-plugins preflight. **State:** open. **Repair link:** none.

**Next action:** time each preflight stage on a Codex reopen and identify the dominant cost. **Resolution condition:** a Codex reopen reaches `running` within the 45-second wrapper window on this machine, shown by timing evidence. **Verification evidence:** status file `codex-aaa9f5ae849419cc-01a1415f-…91825ffc10a6b454.status.json` read on 2026-10-18.

## B017 - Continuation owner cannot be reclaimed after a foreground commit

**Kind:** bug. **Observed/reported:** 2026-10-18; while delivering PR #294, the foreground session yielded the continuation owner at head `c5b1a787`, then reclaimed it and committed `00827872`. After that commit, the owner's recorded head no longer matched the worktree. `claim` then returned `{"state": "blocked", "reason": "owner-head-changed"}`, and `checkpoint --rebind` needs a held lease, so neither the foreground session nor any other path could rebind the owner. The Stop hook demanded reconciliation, and the only route was to remove the scheduled task, retire `owner.json`, then `init`, `claim`, `yield` and `register` again. **Cause:** confirmed in `continuation_runtime.py`: `claim` rejects a changed head before granting the lease that `checkpoint --rebind` requires.

**Impact and priority:** P2; any foreground repair commit made while the owner is yielded strands the owner and forces a manual re-initialization. **Source owner:** tj-agents/core engineering `workflows/continuation_runtime.py` and the `persistent-workflow` contract. **State:** open. **Repair link:** none.

**Next action:** let `claim` accept a same-repo, same-branch, same-worktree head advance and record the rebind, or document a foreground rebind operation. **Resolution condition:** after yield, commit and claim on the same branch, the owner rebinds to the new head without re-initialization, covered by a regression. **Verification evidence:** the claim output above and `.agents/continuation/owner.c5b1a787.retired.json` in the `Fix-OpenCliAlwaysOpens` worktree. **Additional evidence (2026-10-18, after merge):** releasing the delivery binding (`delivery-release --reason merged`) before checkpointing `complete` made `claim` return `binding-removed`, and a merged PR cannot be re-bound, so the owner could not record completion and was retired by renaming it to `owner.710e2b96.merged.json`. Using `checkpoint --rebind` while holding the lease rebinds a new head correctly.

## B018 - Handoff reports success before native startup

- Kind: bug. Observed/reported: 2026-10-18; tracker-aware skills handoff printed Launched and agent-handoff-submitted, but its task remains proposed with no registered successor and pickup pending.
- Confirmed cause: both handoff launchers return success after terminal submission, without passing or observing startup_binding status. The underlying historical startup failure is unknown because no receipt was requested.
- Impact and priority: P1; handoff ownership and reported completion cannot be trusted.
- Source owner: tj-agents/core machine handoff launchers and startup binding. State: resolved.
- Repair link: .worktrees/Fix-VerifiedHandoffStartup/plans/verified-handoff-startup/GOAL.md; branch Fix/VerifiedHandoffStartup; owner codex:01a1415f-6448-7123-8b17-c7fb67aee637.
- Next action: require per-attempt native SessionStart before emitting successful handoff events; test and deliver the correction, then recover the pending source task without duplicate writers.
- Resolution condition: refresh failure, early CLI exit, a missing wrapper and uncertain startup cannot produce success; both hosts retain correct ambiguity and retry behavior; focused regression tests, independent review and Windows/Linux CI pass with source publication and observed native acceptance.
- Verification evidence: both current launcher sources inspected at 728ea8b2; exact task status read from Feature-TrackerAwareSkills returned proposed and sessions empty. Migration owner is separate and preserved.
- Publication: primary-checkout observation retained for the next authorized batch; no per-record bookkeeping PR.

- Recovery checkpoint (18 October): corrected source launch verified native SessionStart through
  Temp/tj-agents-handoff-3pd8lh3y/status.json; successor codex:01a14f1d-abd0-74e0-9b75-b814a208ea87
  claimed work-items/record-writers and acknowledged its separate goal. No second retry is needed.
  Source repair PR297, final candidate a72f7bc1, CI39132352084; review-found receipt/exit races have
  passing regressions. Publication is still pending. The approximately179.5-second native preparation
  remains existing B016; review-bundle preparation and repeated substantive CI are recorded with the
  validation-efficiency investigation boundary. Stale installed versions are not an established cause.

- Resolved (18 October): PR297 merged as e91ba610 after clean exact-head review and Windows/Linux
  CI39132352084. Causal regenerate job117694084942 succeeded and published bot commit86dbae8a;
  both host launchers and shared startup binding were verified in generated output. Native corrected
  launch and actual source-skill pickup were observed. H01–H04 have focused passing regressions.

- Independent tracker-source review follow-up (18 October, 14:30 UTC): both frozen-delta reviewers found
  that Codex `startup_binding.py:260-268` waits for required SessionStart while the child stays alive
  without a deadline or cleanup. `await_handoff_startup` reports uncertainty after480seconds, leaving
  a later acknowledgement possible. Static control flow confirms the missing bound; no live hung child
  was reproduced. Cause: the new Codex runtime branch omits the bounded acknowledgement/termination
  path already used by the other native branch. Impact: startup uncertainty can outlive handoff
  ownership; P1 under the shared lifecycle rule. Source owner remains machine startup binding.
  This source is byte-identical on main86dbae8a and tracker candidate4e4342a; tracker routing neither
  exposes nor worsens it. Repair remains with the independent verified-handoff-startup owner
  codex:01a1415f-6448-7123-8b17-c7fb67aee637 (verified live by recovery inventory).
  Follow-up state: blocked; blocked_by: conflict. Resolver: that source owner. Resume condition:
  owner reconciles this evidence and releases or repairs the startup paths. Next action: add a
  deterministic missing-Codex-ack regression, enforce the remaining startup deadline, terminate the
  owned child tree and clean its runtime before reporting failed startup. Resolution condition:
  a live non-acknowledging Codex child cannot survive the deadline or produce a later successful
  handoff; focused regression, current independent review and required Windows/Linux checks pass.
  Verification: exact frozen incremental bundle5cde5f9c471106fc04c416da9dcc55fc2efb8a6d5e0092e96bb982d06ca852ac;
  original source review and publication evidence above remains historical. No second writer launched.

## B019 - Concurrent Stop hooks corrupt a prepared session-close ticket

- Kind: bug. Observed/reported:18 October2026; duplicate base-agents and tj-agents machine Stop hooks
  returned report-delivered and prepared-closure-cancelled-or-replaced for the same armed session.
- Cause: the initial ticket comparison precedes the exclusive attempt claim, and a losing callback
  can publish a stale refused state over another callback's reported state. The current published source is corrected.
- Impact and priority: P1; valid completion cannot close and the lifecycle verdict is untrustworthy.
- Source owner: tj-agents/core machine close utility. State: resolved.
- Repair link: .worktrees/Fix-ConcurrentSessionClose/plans/concurrent-session-close/GOAL.md;
  owner codex:01a1415f-6448-7123-8b17-c7fb67aee637; work item lifecycle/concurrent-session-close.
- Next action: reproduce the overlapping callbacks, claim before validating and guard stale failure writes.
- Resolution condition: duplicate Stop callbacks preserve reported state and only one close execution;
  new prompts, replacements and invalid identities still prevent close; focused regressions, independent
  review, Windows/Linux CI and source publication pass.
- Verification evidence: original Stop35/Stop38 verdicts, current source at dc1f7415 and PR296 inspection.


- Resolved: PR306 merged as65335d83; final candidateade368b3 passed independent native review,
  parent workflow fallback and Windows/Linux CI39173536462. All24 focused close tests pass, including
  deterministic overlapping Stop payloads for both hosts and expiry-boundary/cancellation coverage.
  Causal publication job117814315014 succeeded; generated commit5588eb13 has identical corrected
  close utilities in both host packages. Existing-session stale consumption is separate B020.
## B020 - Long-running sessions silently retain stale published plugin behavior

- Kind: bug. Observed/reported:18 October2026; an existing Codex session still advertises a handoff
  launcher without the already-published PR297 startup confirmation and receives old session-snapshot
  hook guidance after terminal startup refresh was installed.
- Cause: stale consumption is confirmed; supported live-host refresh/adoption boundary remains to diagnose.
- Impact and priority: P1; users and agents cannot reliably tell which lifecycle behavior is actually active.
- Source owner: Core machine rolling/plugin coordination and hook/skill generation selection.
- State: handoff prepared. Repair owner: one Claude successor; parent retains separate PR306.
- Repair link: .worktrees/Fix-LiveSessionPluginRefresh/plans/live-session-plugin-refresh/GOAL.md.
- Resolution condition: deterministic generation A-to-B transition with coherent selected behavior,
  clear automatic adoption or supported checkpoint/resume, both-host coverage and native acceptance
  evidence; independent review, required Windows/Linux CI and causal source publication.
- Next action: one native Claude launch and verified pickup; no duplicate writer or blind snapshot rewrite.
## B021 - Stop gate demands a continuation init the harness never permits

- Kind: bug. Observed/reported: 19 October 2026 in claude:a727fe94-883c-4713-b4f9-13351c5374aa
  (lifecycle/live-session-plugin-refresh). `continuation_stop.py` blocked every Stop with "Initialize
  persistent-workflow for the active delivery binding"; the required `continuation_runtime.py init` was
  refused twice by the Claude auto-mode classifier (Instruction Poisoning, then Auto-Mode Bypass).
- Cause: confirmed at source dc1f7415: `.agents/plugins/harness/engineering.json` declares
  `completion.py` and other helpers in `claude_allow` but no `continuation_runtime.py init|claim|yield`
  rule, so a mandatory Stop gate requires an undeclared, classifier-gated command.
  `continuation_stop.py` releases only on an owner or a direct `pause|stop|cancel` prompt
  (`workflow_route.direct_control`); it has no recorded-capability-refusal exit.
- Impact and priority: P2; every turn end loops on the Stop gate and durable continuation cannot start.
- Source owner: tj-agents/core engineering harness permissions and persistent-workflow Stop gate.
- State: loop repaired on Fix/LiveSessionPluginRefresh (PR311): continuation_stop honours
  stop_hook_active and blocks at most once per turn end. The undeclared init permission remains open.
- Next action: declare the bounded continuation-runtime commands for both hosts, or make the gate accept a
  recorded capability refusal. Resolution: init/claim succeed or the gate stops looping on refusal.

## B022 - Merging a slice forces closeout before the owning work is done

- Kind: bug. Observed/reported: 19 October 2026; Tommy's merge-cleanup-close-gating handoff reports PR311's merge blocked Claude Stop while refresh verification, B021 and goal closeout remained. SessionStart also demanded self-close for unrelated merged PRs.
- Cause: confirmed; `merge_cleanup_gate.py` marks merge observations as session exit obligations and enforces them without checking whole-work completion. `worktree_cleanup_gate.py` also blocks on repository inventory without session ownership. `cleanup_proof.py` can archive/reset unfinished work inside a merged checkout without checking its continuation owner.
- Impact and priority: P1; remaining authorized work can be interrupted or removed from its active checkout.
- Source owner: tj-agents/core engineering merge workflow and cleanup hooks.
- State: in-progress.
- Repair link: `.worktrees/Fix-CloseoutOnlyWhenDone/plans/closeout-only-when-done/GOAL.md`; branch `Fix/CloseoutOnlyWhenDone`; parent Codex session `788a0620b3754612e08c00773488032f`.
- Next action: gate closeout on existing verified completion state, keep merged-slice inventory advisory, and preserve unfinished work before cleanup proof mutates files.
- Resolution condition: both-host ongoing-work, verified-completion, explicit-close and foreign-inventory regressions pass; reviewed source repair merges after green Windows/Linux CI and causal generation succeeds.
- Verification evidence: user handoff plus read-only source inspection; no repaired behavior claimed yet.

## B022 - Merging a slice forces closeout before the owning work is done

- Kind: bug. Observed/reported: 19 October 2026; Tommy's merge-cleanup-close-gating handoff reports PR311's merge blocked Claude Stop while refresh verification, B021 and goal closeout remained. SessionStart also demanded self-close for unrelated merged PRs.
- Cause: confirmed; `merge_cleanup_gate.py` marks merge observations as session exit obligations and enforces them without checking whole-work completion. `worktree_cleanup_gate.py` also blocks on repository inventory without session ownership. `cleanup_proof.py` can archive/reset unfinished work inside a merged checkout without checking its continuation owner.
- Impact and priority: P1; remaining authorized work can be interrupted or removed from its active checkout.
- Source owner: tj-agents/core engineering merge workflow and cleanup hooks.
- State: in-progress.
- Repair link: `.worktrees/Fix-CloseoutOnlyWhenDone/plans/closeout-only-when-done/GOAL.md`; branch `Fix/CloseoutOnlyWhenDone`; parent Codex session `788a0620b3754612e08c00773488032f`.
- Next action: gate closeout on existing verified completion state, keep merged-slice inventory advisory, and preserve unfinished work before cleanup proof mutates files.
- Resolution condition: both-host ongoing-work, verified-completion, explicit-close and foreign-inventory regressions pass; reviewed source repair merges after green Windows/Linux CI and causal generation succeeds.
- Verification evidence: user handoff plus read-only source inspection; no repaired behavior claimed yet.

## B023 - Unselected stack capabilities and hooks leak into unrelated repositories

- Kind: bug. Observed/reported: 19 October 2026; Codex session 01a14f1d-abd0-74e0-9b75-b814a208ea87 in Core's Feature-TrackerAwareSkills checkout advertises C++/MSVC/Win32 capabilities and receives the injected instruction "This is a C++ repository" plus Win32 detection advice during Python/Markdown tracker work.
- Cause: installed cpp/local/hooks/session_context.py confirms file-extension detection can emit C++ guidance without an explicit selection check. The effective host configuration that activated this hook and exposed unrelated skills is not yet reconciled; global marketplace registration alone is not proof of activation.
- Impact and priority: P1; incorrect standards contaminate unrelated codebases and may cross personal/employer capability boundaries.
- Source owner: Core Machine repository capability selection, effective host activation and affected stack publishers; exact activation cause remains under investigation.
- State: blocked; blocked_by: capability. The single requested Claude launch exited 1 with failed native SessionStart confirmation; no successor identity or pickup was confirmed.
- Repair link: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-RepositoryCapabilityIsolation/plans/repository-capability-isolation/GOAL.md; branch Fix/RepositoryCapabilityIsolation. Predecessor codex:01a14f1d-abd0-74e0-9b75-b814a208ea87 owns only handoff preparation and the separate tracker goal.
- Next action: Claude reconciles this record and existing source owners, then investigates effective Codex/Claude skill, hook and MCP selection and repairs repository isolation, including locally excluded Work adoption.
- Resolution condition: audited personal and Infonetica consumer configurations activate only their selected capability closure in both fresh hosts; work-local tj-agents files are Git-excluded; shared Work policy enforces this; regression coverage, independent review and applicable delivery checks pass with actual adoption evidence.
- Verification evidence: current host skill catalogue and repeated injected C++/Win32 messages; installed hook inspection; repository-selection tooling already documents --scope local and exact Git exclusions. No repair or fresh-host isolation acceptance is claimed.


- Handoff blocker evidence: C:/Users/TommySeery/AppData/Local/Temp/tj-agents-handoff-uzg732g8/status.json is state failed; no duplicate launch. Resolver: Machine startup-binding/generation owner. Resume condition: reconcile the failed attempt and restore supported native SessionStart confirmation, then one verified Claude pickup.

## B024 - Interactive Claude handoffs stall before startup acknowledgement

- Kind: bug. Observed/reported: 19 October 2026; two packaged handoff-claude attempts showed an unusable black terminal and exited1 after missing native SessionStart acknowledgement.
- Cause: reproduced preparation/native deadline starvation: healthy child acknowledgement after0.15 seconds is killed when slow plugin preparation leaves0.01 seconds on its deadline. The source correction preserves a separate existing20-second native budget. Original failed receipts lack phase timing, so attribution of both historical failures remains unproven. Normal-tools interactive startup and an actual reply were observed; trust/hooks are not established as the original cause.
- Priority: P1; shared handoff and ownership cannot be relied on. Source owner: Core Machine native startup and handoff launchers. State: in-progress.
- Repair owner: codex:01a14f1d-abd0-74e0-9b75-b814a208ea87. Repair link: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-HandoffStartupReliability/plans/handoff-startup-reliability/GOAL.md.
- Next action: complete exact-head incremental review and Windows/Linux CI for CorePR315 atd66477e6bfccf52c62e074614ada3d5c7e881054, then authorized source publication and packaged Claude goal-pickup acceptance.221 focused tests pass with24 skips, including the real-child regression that fails before correction. The original tracker goal has one acknowledged fresh Codex successor. Broader hook/capability cleanup remains deferred and separately owned by B023.
- Resolution condition: reproduced mechanism corrected without bypassing trust or disabling hooks, preserved diagnostics and exact-child recovery, independent review and required Windows/Linux checks, actual packaged interactive startup and task pickup.


## B015 - Terminal-close refusal kills the CLI and is reported as a closed tab

Kind: bug. Observed/reported: 2026-10-20. Priority: P1; a live usable session is destroyed while its terminal remains. State: resolved. Source owner: machine `close.py`, `finish.py` and `close_watcher.py`. Repair owner: session `01a15a14-d110-7b71-b7b7-9b2436ddb4db`, branch `Fix/CloseTabAndCalloutRepair`.

Cause confirmed in source: both close helpers catch `TerminalRefusal` and send SIGTERM to the verified host and optional wrapper. The watcher then writes `closed`; its host-exit deadline also returns success without confirming exit. Existing fallback tests require this process-only behavior. The user observed a dead tab; the receipt says `closed`. The exact swallowed terminal-refusal diagnostic was not retained, so its original trigger is unknown. This corrects a consequence of historical B004; its original observation and delivery history remain intact.

Correction: terminal refusal propagates, preserving the host and wrapper; closure requires the existing adapter's exact-tab disappearance check plus confirmed host exit. Remove the process-only environment bypass. Next action: none for this runtime repair; retain refusal diagnostics and preserve sessions when terminal identity is unavailable. Resolution condition: ambiguous, missing or unsupported terminal identity never signals a process, never triggers cleanup and never yields a closed receipt; successful exact-tab closure still works. Verification evidence: watcher/refusal/receipt, exact-tab adapter and disposable-host integration fixtures passed; all 41 close/finish and 26 generation tests passed. PR330 merged at `90d88d08eece435818961299a2de7a36f101c453`; exact-head Windows/Linux CI `39501123185` passed for `7eb4783a7c57512d4fc1ce303fa75beb921fdef0`. Independent full and incremental reviews completed, including the machine-only dependency correction. Causal main CI `39503414516` regenerated packages successfully at `096dbc84cd74bea0f6c2a9ebd726c7a317a2c083`; both generated host runtimes and shared guidance match source byte for byte. No additional real agent sessions were launched. Installed-host acceptance remains untested; the bounded refusal behavior is verified with deterministic scripts and disposable processes.
