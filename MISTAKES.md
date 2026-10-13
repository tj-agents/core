# Mistakes

This is core's incident record. Entries describe the observed mistake, its cause where known, and the intended correction. They are proposals for later repair, not additional operating instructions. `engineering:write-mistake` records incidents and `engineering:address-mistake` reconciles an authorized correction while retaining this learning history.

Each entry has a stable ID and an open or addressed status. Address entries individually and retain the verification evidence when their status changes. Governing behavior remains owned by canonical `.agents/` definitions and the relevant `.codex/` or `.claude/` adapter.

## M001 ? Same-goal verification treated as a handoff

**Status:** Open. **Observed:** 2026-10-11. **Scope:** shared workflow selection; observed on Codex.

**Mistake:** Sandbox recovery opened an independent native verifier tab for a focused acceptance check, adding ownership, pickup and cleanup work to an already blocking task.

**Why:** I treated the need for a fresh runtime process as a need to transfer task ownership. A captured child CLI was sufficient for the default-model probe; I did not apply that distinction consistently. The governing workflow already allows continued work in the same context. Whether its selection or enforcement needs a source change remains to be established.

**Intended correction:** Keep related work with the existing owner or a bounded subagent. Distinguish fresh-process verification from ownership transfer. Use a handoff for independently owned work or a necessary context transfer, with an observable result.

**Resolved when:** Workflow selection and focused checks demonstrate these different cases on both hosts without creating duplicate owners.

## M002 ? Existing merge authority treated as missing permission

**Status:** Open. **Observed:** 2026-10-11. **Scope:** delivery authority; observed on Codex.

**Mistake:** Repeated permission/config explanations made Tommy reauthorize an already authorized merge while automatic approval review was failing before command execution.

**Why:** I conflated user consent, the auto-merge opt-in, and the host's execution gate. The older checkout lacked the new auto-merge field even though PR #188 was already merged. Standing authorization and explicit user instructions already covered delivery.

**Intended correction:** Preserve existing authority through recovery. Establish the actual repository configuration and failing action separately. Describe an execution failure accurately and continue the authorized delivery when its gate opens.

**Resolved when:** An authorized task recovers from an execution failure and reaches its reviewed merge without repeated consent requests, while genuine holds and permission checks remain effective.

**2026-10-12 related evidence:** Exact-owner recovery rejected before launch when the caller supplied a goal and asserted existing authority without its wording/provenance or a tool-approval justification. The bounded repair is on branch `Fix/RecoveryAuthorizationContext`. It carries concrete task authority and preserves real approval gates; this source repair alone does not establish M002's broader resolution condition. M005 and its prior PR207 repair remain distinct.

## M003 ? Returning blocked delivery without an active continuation owner

**Status:** Open. **Observed:** 2026-10-11. **Scope:** goal continuation; observed on Codex.

**Mistake:** Delivery was returned to Tommy after a lasting blocker without an initialized continuation owner or registered wake, requiring repeated intervention.

**Why:** I treated the blocked operation as the end of task ownership and selected continuation too late. The subsequent owner initialization failed on the protected owner file and its escalation failed automatic review. No PR or CI run existed, so this incident does not establish a CI-waiter bug.

**Intended correction:** Select supported continuation when a lasting wait appears. Claim unattended ownership only after initialization and wake registration are observed. Keep available work moving and expose the actual resolver when the host cannot continue.

**Resolved when:** The workflow demonstrates continued ownership through a delayed result, including correct reporting when continuation is unavailable.

**2026-10-13 recurrence:** Tommy again reported that no background watcher means he must keep returning to check progress. In this closeout owner, Windows ScheduledTasks enumeration timed out after eight seconds before wake registration; no scheduler was ever registered. The foreground CI monitor ended after the recorded merge hold. The current owner is blocked on the user-deferred policy repair, with no foreground or child and no unattended wake. Saved ownership alone does not provide background continuation.

**Reconciled kind, impact and ownership:** mistake; P1 because repeated manual follow-up defeats the intended unattended delivery. Source owner: tj-agents/core shared continuation activation, scheduler adapter and completion reporting. State: open. The scheduler timeout mechanism is observed; its environmental root cause is unknown. The existing activation repair owns host claim/activation, while the existing scheduler-timeout repair owns the eight-second query failure; these distinct causes are not merged.

**Repair links:** existing `Fix/ContinuationMonitorActivation`, `plans/continuation-monitor-activation/GOAL.md`; existing `Fix/ContinuationSchedulerVerificationTimeout`, `plans/continuation-scheduler-verification-timeout/GOAL.md`, both in Core's corresponding worktrees. This occurrence is retained in `plans/inert-closeout-cadence/GOAL.md`. B010/M016 cover the separate automatic-merge conflict.

**Next action:** reconcile these existing runtime repair owners and verify actual scheduler registration and wake/recovery in the affected host before claiming unattended continuation. Preserve Tommy's repair deferral and seven-session limit; this recording launches no duplicate repair or watcher.

**Verification evidence and unresolved acceptance:** this goal records the registration timeout and absence of a scheduled wake; the current owner has state blocked, foreground null, child null and launches zero. No background progress or repair acceptance is claimed. Resolve M003 only with observed continuation through a delayed delivery result without Tommy polling or restarting it, truthful capability reporting, and preservation of explicit user deferrals.

## M004 ? Machine repair and repository delivery reported ambiguously

**Status:** Open. **Observed:** 2026-10-11. **Scope:** completion reporting; observed on Codex.

**Mistake:** Reports alternated between ?complete? and ?not merged? without clearly identifying whether they referred to the applied local runtime repair or its unpublished repository records.

**Why:** I reported a completed acceptance phase as though it covered the user's whole requested outcome. No core runtime source changed; the machine repair and documentation delivery had different acceptance criteria.

**Intended correction:** Name the changed artifact and observed acceptance. Keep the overall task open through its authorized terminal delivery and state the actual PR/merge result.

**Resolved when:** Completion reporting distinguishes phase acceptance from the requested outcome without prompting the user to recover ownership.

## M005 ? Asking Tommy to restart before attempting the available recovery skill

**Status:** Open. **Observed:** 2026-10-11. **Scope:** machine recovery and workflow selection; observed on Codex.

**Mistake:** I supplied a manual resume command without first invoking the available `open-codex` skill for the existing session.

**Why:** I assumed the recurring approval-review error left only a manual restart. I had read the utility but did not test its supported action. When finally invoked, it passed approval and refused to create a duplicate because this exact session was still live. A subsequent guarded close-and-reopen preparation reached the approval-review HTTP 400 before its observer could start; no new CLI or observer was launched.

**Intended correction:** Attempt the supported recovery capability before assigning recovery work to the user. Preserve the same goal and context, verify session identity, and retain one writer. A safe restart must reconcile closure and reopening; a duplicate-writer refusal must not be bypassed.

**Resolved when:** Recovery demonstrates supported reopening where eligible and an accountable transition for a live owner that needs restart, without falsely claiming a new session was launched.

## M006 ? One successful Git operation treated as general execution recovery

**Status:** Open. **Observed:** 2026-10-11. **Scope:** acceptance evidence; observed on Codex.

**Mistake:** I described the execution gate as cleared after a Git checkpoint succeeded; subsequent native-review and GitHub CLI actions reproduced the metadata HTTP 400.

**Why:** I generalized one successful observation beyond its action and host state. The cause of the differing outcomes is unproven; retained configuration is a hypothesis.

**Intended correction:** Limit recovery claims to the tested actions and context. Verify the remaining delivery path before declaring execution recovered.

**Resolved when:** Acceptance covers the actual required workflow and reports partial success accurately.

## M007 ? Assuming an error meant no files changed

**Status:** Open. **Observed:** 2026-10-11. **Scope:** tool-result reconciliation; observed on Codex.

**Mistake:** I initially reported that a failed documentation patch had applied no goal correction. Later Git inspection showed the handoff edit and the smaller goal reconciliation were written despite reported approval-review errors.

**Why:** I trusted the error text as proof of atomic failure instead of independently inspecting the working tree. This does not prove successful approval or explain the underlying host behavior.

**Intended correction:** Reconcile actual state after failed or ambiguous mutations before reporting, retrying, rolling back or handing ownership to another agent.

**Resolved when:** The workflow demonstrates accurate state reconciliation for complete, partial and unexecuted failures.

## M008 - Legacy auto-merge preference reported as the completed settings interface

**Kind:** mistake. **Observed/reported:** 2026-10-11. The originating session presented `delivery-authorization.json` as the requested generic configuration and claimed completion despite an unfinished configuration workstream; Tommy corrected the requirement to Core-owned `settings.json` containing a configuration object and clarified that Kit/template is independent. Cause of the completion claim: unknown. The existing implementation's conflicting `.agents/configuration.json` contract is confirmed by its goal and reader.

**Impact and priority:** P2; the public interface and claimed ownership do not meet the requested arbitrary-consumer behavior.

**Source owner:** tj-agents/core repository settings reader, consumers and public documentation.

**State:** resolved. **Repair link:** PR208, continuing the released `Feature/RepositoryConfiguration` implementation as one causal repair.

**Ownership evidence:** exact controller `01a122c4-e884-7402-a873-9fa7449e5c37` was recovered and contacted its existing child through native collaboration. The original source goal records the child's explicit release to this successor at `2026-10-11T22:16:13Z`, preserving dirty source and its SHA-256 inventory. Source coordination is resolved.

**Next action:** none; the requested generic settings behavior is verified and delivered.

**Resolution condition:** public documentation and both shipped host consumers use one Core-owned settings interface; an unrelated disposable repository exercises guarded auto-merge with its existing authorized task and no copied interpretation or legacy-standing-policy boilerplate; Windows/Linux validation, independent review, normal merge and causal publication pass, and completion reports match the observed outcome.

**Verification evidence:** the correction handoff, the existing owner goal and read-only dirty-source inspection, exact child/controller metadata, and the native follow-up result are recorded in the repair goal. Settings behavior and source delivery are now verified. Final reviewed head0f98144fceff5040f6050413e036d26f1cf98ea8 passed guard and Windows/Linux CI38187755625 and independent incremental review. PR208 merged normally at a1a8d051e65e15d639a7a0fb0fc343c7b89fd72d; causal main ci38189303890 and regeneration114618404712 succeeded and published exact-parent bot commitcbe97265fcd8267493c24d18f74a5a0a26b872c9. Parent verified canonical/published engineering and both-host machine payload byte parity. Consumer adoption and normal-profile activation are neither claimed nor required.

## M009 - Treating unavailable follow-up as the end of authorized coordination

**Kind:** mistake. **Observed/reported:** 2026-10-11. This settings session identified the existing source controller, received unavailable/no-send-attempted from the supported follow-up helper, and returned a manual source-release obligation to Tommy while the exact-session open-codex recovery utility was available. Tommy called out that implementation remained unfinished and coordination had been offloaded to him.

**Impact and priority:** P2; the authorized settings correction was stalled without exhausting supported automated recovery.

**Source owner:** tj-agents/core machine follow-up/recovery standards. **Cause:** confirmed incomplete manual-only fallback guidance in followup-codex, combined with this agent failing to attempt exact-owner recovery. The endpoint infrastructure failure's cause remains unknown.

**State:** resolved. **Repair link:** PR207, merged source9954043c5d7b34c59e70cc1df193e370c3f759b6. The original settings runtime was delivered by PR208.

**Next action:** none; standards source repair and original source coordination are verified. This parent continues the separate settings delivery.

**Resolution condition:** the standards repair is reviewed, both-host Windows/Linux validated, merged and causally published, and recovery demonstrates preserved exact identity, one writer, truthful acknowledgment/release evidence and continued ownership of the original outcome.

**Verification evidence:** exact controller recovery and its child release at 2026-10-11T22:16:13Z preserved source identity and one writer; PR208 has now merged the corrected settings source. The disjoint recovery successor completed independent review and Windows/Linux CI38184328113 at9954043c5d7b34c59e70cc1df193e370c3f759b6; PR207 merged atcb7626a35cba664c80cfc987c270129b9e54f3a8. Causal ci38185434091 regeneration job114606626192 succeeded and published mainbdb63914c03e6d5d62dcac7edb556d5a79c90b85 with that exact merge parent and regeneration subject. Its durable goal records fresh completion ready=true, owner complete, scheduler and delivery binding removed. Parent read that record; unavailable native send was not claimed as acknowledgment. Its separately owned self-close investigation is outside this causal repair.

## M010 - Helper exit status mistaken for a focused-test verdict

**Kind:** mistake. **Observed/reported:** 2026-10-11. The implementation worker reported six compact validation calls as exit zero while their saved unittest logs contained failures. Parent and writer inspected the actual artifacts before creating a candidate and corrected the interpretation. **Cause:** confirmed reliance on the helper/transport exit rather than the recorded subprocess/test result; the existing validation contract already requires validating each returned result, so no missing standards rule is established.

**Impact and priority:** P2; an unverified candidate could have been mislabeled passing, but none was committed or delivered from that status.

**Source owner:** this repository-settings execution and its test-evidence reconciliation. **State:** resolved. **Repair link:** PR208; no separate causal repair.

**Correction:** the import and dynamic exception assertion were repaired. Parent read every replacement test summary before freezing; helper status is no longer treated as a verdict.

**Resolution condition:** every required focused scope has an observed passing terminal artifact, failed initial artifacts remain accurately classified, and review/CI claims bind to the real candidate.

**Verification evidence:** saved final repository-settings-l4 artifacts report reader 11, delivery 36, guarded command 10, binding 38, merge-review gate 82, machine 28, harness manifests 14 and source layout 21 tests OK (240 tests; 3 skips). Parent independently read the terminal artifacts. Initial failures retain their failed classification. Generation and generated checks passed. No source candidate or PR was created from the ambiguous helper status.

## M011 - Committing Core's generated catalog digests

**Kind:** mistake. **Observed/reported:** 2026-10-12. The initial settings candidate committed engineering/machine catalog digest regeneration, and exact-head CI38183296901 rejected those two fields. **Cause:** confirmed candidate staging omitted Core's generated-path guard; the existing guard explicitly reserves digest publication for post-merge, so no absent standards rule is established.

**Impact and priority:** P2; the draft PR failed CI, with no normal merge or publication attempted.

**Source owner:** this repository-settings candidate preparation. **State:** resolved. **Repair links:** PR208 and PR213. **Next action:** none; both source slices passed the committed generated-path guard and exact-head CI, and causal post-merge publication completed.

**Resolution condition:** the committed runtime and later guidance slices contain no generated digest or package deltas, the generated-path guard and exact-head CI pass, and causal post-merge publication owns regeneration.

**Verification evidence:** authoritative gh run view38183296901 failed-step logs name .agents/catalog/catalog.json digest of base-agents/engineering and base-agents/machine. scripts/check_generated_paths.py reads merge-base digest values and explicitly rejects these changes.

**2026-10-12 related evidence:** PR210 on `Fix/RecoveryAuthorizationContext` reproduced the same generated-digest mistake at run38189190964: verify-windows and verify-linux succeeded, while the source guard failed on the `base-agents/machine` digest. Commit `f63538d` restored the reviewed digest and retained the authored embedded harness metadata.

**PR210 related repair evidence:** The focused corrected-head source guard passed with artifact `78dd200ee7badf43-corrected-source-guard.log`. PR210 later merged at full head `4577c581214a18b03e28246e09e4fec4cae1f36b`; source CI `38192901173` was green, merge commit `286c747130bdb0440b6b19c5eb28f068528c990d` had successful causal run `38194033253`, and bot publication `7fed153b078c60fa69b6db4b50ab03c0b3f5d025` completed. This records observed repair evidence only; it does not adopt PR210's goal.

**PR208 and PR213 resolution evidence:** PR208's exact reviewed runtime head `0f98144fceff5040f6050413e036d26f1cf98ea8` passed the committed generated-path guard and CI `38187755625`; it merged at `a1a8d051e65e15d639a7a0fb0fc343c7b89fd72d`, with causal run `38189303890` and regeneration job `114618404712` publishing bot commit `cbe97265fcd8267493c24d18f74a5a0a26b872c9`. PR213's exact reviewed guidance head `245e9300526753f62ba860375b52b7635f7ea297` passed the committed guard without generated-path changes and CI `38195921819` (Windows `114638417763`, Linux `114638417829`, guard `114638417670`); it merged normally at `b477125f50c6279e0f993cf3f555346182875136` on `2026-10-12T11:04:33Z`. Causal regeneration run `38240324302`, job `114781040815`, succeeded and published `13751eeb0c740d3e7ddcbb2e236046bbd5abb9ec` with sole parent `b477125f50c6279e0f993cf3f555346182875136` and the expected subject. Shared-policy byte parity, both-host canonical pointers and harness/catalog JSON parity passed. Exact causal full-main run `38240324302` subsequently completed successfully, including Windows `114781040624`, Linux `114781040299` and regeneration `114781040815`.

## M013 - Completed review used an unsupported final judgment token

**Kind:** mistake. **Observed/reported:** 2026-10-12; the guarded merge rejected PR208 with review work order is incomplete although all independent lenses had completed. **Cause:** confirmed parent synthesis wrote clean instead of the review-lifecycle approved final judgment token; the existing merge-review gate accepts approved or changes-requested. No missing standards rule is established.

**Impact and priority:** P3; one authorized merge attempt was rejected safely, with no source change or gate bypass.

**Source owner:** this repository-settings parent review synthesis. **State:** resolved. **Repair link:** PR208, reviewed head0f98144fceff5040f6050413e036d26f1cf98ea8. **Next action:** none.

**Resolution condition:** canonical final judgment agrees with the existing work-order contract and the guarded merge accepts the same independently reviewed source.

**Verification evidence:** local final judgment was corrected to approved while retaining historical pass judgments and resolved findings. Fresh PR body validation passed, the guarded merge returned success, and forge confirmed PR208 MERGED at a1a8d051e65e15d639a7a0fb0fc343c7b89fd72d on 2026-10-12T00:46:32Z.

**Related guidance-delivery evidence:** PR213's guarded merge first rejected the completed review because the review work order's status and judgment fields lacked the required backtick format. The correction added only those required backticks to the existing local canonical review; it did not change the review decision or introduce a missing standards rule or gate bypass. The exact unchanged reviewed head `245e9300526753f62ba860375b52b7635f7ea297` with approved judgment was accepted by the guarded normal merge. PR213 merged at `b477125f50c6279e0f993cf3f555346182875136` on `2026-10-12T11:04:33Z`; exact-head CI `38195921819` passed Windows `114638417763`, Linux `114638417829` and guard `114638417670`.

## M012 - Unverified delayed CLI closure after completed delivery

- Kind: mistake. Observed/reported: 2026-10-12; predecessor ended its report after delegating delayed self-close and did not reconcile the nonzero command/observer cancellation.
- Cause: confirmed unobserved final action; no valid basis to equate a delayed worker promise with completed session exit.
- Impact/priority: P2; completed CLI remained live and Tommy had to call out unfinished closure.
- Source owner: Core terminal task/session ownership and its invocation/enforcement consumers; machine peer-cli owns transport only. State: blocked.
- Repair link: `MISTAKES.md#M012` owns the current invocation/acceptance obligation. Historical B004 and plans/verified-self-close/GOAL.md were delivered by merged PR212; they do not establish the prevention condition for this recurrence. The M003 successor is a related full-contract acceptance candidate, not an acknowledged M012 repair owner.
- Blocker: supported follow-up to live successor01a13562-6a28-73a3-b2bc-d3bbe884dad5 is unavailable/disconnected, with no send or acknowledgment; additional native CLI sessions remain prohibited. blocked_by: capability. Resolver: Core terminal-lifecycle owner and the existing successor's supported coordination path. Resume when: exact M012 ownership is acknowledged through supported coordination or a Core owner resumes its bounded repair within the session limit.
- Next action: reconcile current session-terminal invocation and installed enforcement against this exact record through engineering:address-mistake; require verified exit with a retained deferred checkout before resolution. Do not attribute the omitted invocation to a transport command that was never run.
- Resolution condition: actual registered CLI exit is observed through supported observer/process evidence after completion, without closing another/unknown host or claiming an unverified tab closed.
- Verification evidence: original parent final report followed by worker refusal and cancelled observer; source delivery itself remained verified complete.


**Recurrence - 2026-10-13, PR238 ownership:** The originating closeout session merged documentation PR238, verified main publication and causal generation, and removed its clean Docs-SharedProblemRecords checkout, but returned a final answer without invoking supported self-close. Its separate PR234 checkout was unmerged and explicitly deferred. Cause confirmed by the parent's reasoning: it conflated preservation of that checkout and its incomplete historical goal with retaining a live session after the current authorized work and acknowledged side-workstream handoff were finished. The governing session-guidance close rule was already loaded; this is failure to apply it, not a missing instruction. No close command failed in this occurrence because none was invoked.

**Declarative prevention for this recurrence:** Decide session ownership and checkout retention separately. A retained or user-deferred checkout does not alone justify a live terminal. Once this session has no active authorized work, necessary pending answer or owned verified wait, invoke its supported self-close after reporting; delete only a independently proven removable merged checkout. Observable acceptance covers the retained-unmerged-checkout case and verifies actual exit while preserving its files, branch and other sessions. Reconcile invocation/enforcement with the existing continuation/closure owners; B004's transport fallback and an eight-second scheduler fix alone do not prove this decision error repaired.

## M014 - Explicit mistake-callout repair obligation was not executed

- **Kind:** mistake.
- **Observed/reported:** 2026-10-12; after Tommy called out that no background CI waiter had been launched,
  this session had the governing `engineering:session-guidance` instruction available but did not record the
  incident or launch the required bounded source-owner repair in that same turn. It instead gave an
  explanation of the failure until Tommy explicitly demanded a permanent record.
- **Cause:** confirmed failure to execute an explicit instruction, not an absence of instruction or authority.
- **Impact and priority:** P1; Tommy must repeatedly enforce the workflow himself, and the required repair
  can be skipped despite an unambiguous standing obligation.
- **Source owner:** Core `engineering:session-guidance` callout-repair contract and the host/runtime
  enforcement that must make its required transition observable.
- **State:** blocked.
- **Repair link:** `MISTAKES.md#M014` owns the outstanding callout invocation/acceptance obligation. Historical Fix-StandardsMistakeCallout/session01a11698-c02c-7b72-9f67-ec82fd91efb0 delivered merged PR128; it is not an active repair claim. The M003 successor has general full-contract acceptance scope but has not acknowledged this exact M014 recurrence.
- **Blocker:** the existing successor is live, but its supported follow-up endpoint is unavailable/disconnected; no send or acknowledgment occurred, and no additional native CLI is authorized. **blocked_by:** capability. **Resolver:** Core callout-enforcement owner and supported existing-session coordination. **Resume when:** that owner acknowledges the exact M014 addressing scope or resumes a bounded causal repair within the existing session limit.
- **Next action:** execute engineering:address-mistake for this record, verify actual callout-gate invocation and installed host enforcement, and require observed recording/main publication plus the required source-owner transition or truthful blocker before unrelated work or closure.
- **Resolution condition:** automated host acceptance proves that a user mistake callout causes the required
  incident record and source-owner handoff to be observed before a normal task response can continue; a
  missing launch or record is surfaced as an actionable failure rather than explained away.
- **Verification evidence:** this session read the exact `engineering:session-guidance` rule, then returned
  without either action; the peer registry later showed the active source-repair session cited above.

**Recurrence - 2026-10-13, omitted callout recording:** After Tommy explicitly challenged why PR238's completed owner had not closed, the parent gave explanations and announced self-close without first recording the called-out failure in the canonical main register. Tommy had to interrupt twice and repeat the recording requirement. The session-guidance record-noticed-problems and mistake-callout obligations, the user's explicit main-publication instruction and the freshly merged PR238 publication convention were already available. Cause confirmed from the action sequence: the parent treated an explanation and proposed operational correction as sufficient, instead of completing the required recording and reconciling the causal source owner before closure. This violates an existing requirement; no absence of instruction or authority is established.

**Declarative prevention for this recurrence:** A mistake callout creates an outstanding recording/owner-reconciliation obligation before unrelated work resumes or the session closes. Reconcile the existing stable incident, record cause, violated standard, exact repair owner and observable prevention on main through independent authorized documentation delivery, then verify publication. A promise, apology or local-only note is not completion. Acceptance must demonstrate record publication and the source-owner transition or its truthful capability blocker before a normal response or terminal close. The scheduler handoff's general closure acceptance does not establish enforcement of this callout obligation; Merged PR128 is historical guidance evidence; current invocation/enforcement acceptance remains unverified behind the concrete coordination blocker above.

## M015 - Sandbox terminated with authorized work unfinished
- **Kind:** mistake.
- **Observed/reported:** 2026-10-13; the original event timestamp is 2026-10-12T23:20:52.428Z. Transcript `fed1d447-ae67-4078-99a5-a813156cf86a` records termination after `continuation_stop` and `callout_repair` reported `missingworkflow_route` and `missingworktree_cleanup_gate`, 1584 ms, exit 0, empty stdout. The user asked whether the work was finished. No entities, migrations, endpoints, necessary question, or owned wait blocked the remaining work.
- **Cause:** confirmed observed termination; workflow allowed transcript-only status, and the handoff treated one blocker as blocking the whole task. The specific internal reasoning is unknown.
- **Impact and priority:** P1; the requested repair remained unfinished and the user had to identify that work was incomplete.
- **Source owner:** Core task-continuation and stop-gate behavior, with the dispatcher defect tracked by B009.
- **State:** in-progress.
- **Repair link:** `plans/stop-gate-and-profile-repair/GOAL.md`, branch `Fix/StopGateFailures`; related bug: [B009](BUGS.md#B009).
- **Next action:** continue the authorized goal with focused repair review, Windows/Linux CI, and guarded normal merge.
- **Resolution condition:** authorized work reaches its recorded completion criteria; stop-gate repair is reviewed, required Windows/Linux CI passes, and guarded normal merge completes.
- **Verification evidence:** transcript records the missing workflow route and cleanup gate with exit 0 and empty stdout; investigation found no entities, migrations, endpoints, necessary question, or owned wait that would block continuing. The canonical goal records the next action and branch.

## M016 - Green authorized Core delivery returned another merge question

**Kind:** mistake. **Observed/reported:** 2026-10-13. After reviewing and pushing PR234, observing passing Windows/Linux CI, and marking it ready, this agent asked Tommy to approve a manual merge despite configuration.core.auto_merge=true and the recorded no-reprompt standing instruction. Tommy called out the ineffective configuration and directed that the defect be recorded for later repair.

**Cause:** confirmed process handling error: the agent treated a fresh built-in published-contract classification of canonical workflow instructions as the final human-decision boundary and reported the hold without first recording and owning the configuration/classification conflict as a standards defect. The regex behavior is directly verified; the appropriate future semantic boundary is not yet implemented.

**Impact and priority:** P1; another unnecessary approval interaction interrupts the already green source delivery and undermines the requested automatic workflow.

**Source owner:** tj-agents/core shared delivery classification and session/merge guidance. **State:** deferred. **Repair link:** BUGS.md B010, the single causal repair owner; PR234 and plans/inert-closeout-cadence/GOAL.md retain the source delivery. M015/Fix-RevalidateRecordedMergeGate concerns stale authority and is related, not duplicated here.

**Deferral:** Tommy explicitly requests documentation now and repair later. **blocked_by:** dependency. **Resolver:** Tommy/Core policy owner. **Resume when:** Tommy resumes B010.

**Next action:** execute B010 under a bounded source-owner repair, verify the guarded consumer's actual effective authorization, and resume the original source delivery without treating the mere presence of a configured true value as proof that merge happened.

**Resolution condition:** B010 passes its configuration/classification and preserved-gate regressions, both-host coverage and required delivery checks; an authorized canonical instruction delivery reaches its permitted merge without a repeated routine question.

**Verification evidence:** PR234 reviewed/remote head df36331066f3ac1011415bce0c268f279f6cf771; run38323860505 guard/Windows/Linux green; final user-facing manual-merge question; binder evidence and precise stop regex recorded in B010. The issue is documented, not repaired.

## M017 - Deferred problem records were left only in a feature worktree

- **Kind:** mistake. **Observed/reported:** 2026-10-13; after Tommy asked to retain the automatic-merge and watcher incidents for later repair, this agent updated only Fix/InertCloseoutCadence's BUGS.md, MISTAKES.md and goal, then reported documentation done. PR234 was still unmerged; the shared main records lacked these notes.
- **Cause:** confirmed destination-selection error: the agent interpreted repository-root as the current linked checkout and treated late closeout bookkeeping as sufficient durable publication. The shared problem-record contract specifies root filenames but does not require prompt default-branch publication independent of feature delivery. The agent failed to reconcile main's ledger or verify discoverability there.
- **Impact and priority:** P1; unrelated repairs cannot reliably find deferred defects while the feature branch remains unmerged or is retired, and Tommy must intervene again.
- **Source owner:** Core shared problem-record location/publication contract, write-mistake convention and this agent's completion reporting. **State:** in-progress.
- **Repair link:** Docs/SharedProblemRecords; related main records B010, M003 and M016; the historical branch-local B009 is B010's alias, not main's existing B009.
- **Declarative prevention:** Repository-wide bug, mistake and debt records are published promptly to the source repository's default branch through an independent authorized documentation delivery. Feature goals link to those shared records. A mistake record states the causal decision or confirmed uncertainty, the governing-standard gap or enforcement failure, and a declarative prevention rule with an observable acceptance condition. Documentation is complete only after its canonical main destination is verified.
- **Next action:** reconcile and publish the session records and convention correction independently of PR234, then verify the merged default-branch content. The remaining historical branch-record backlog belongs to .agents/engineering/resources/TECH_DEBT.md#D001.
- **Resolution condition:** the records and prevention rule are on remote main, existing IDs and unrelated edits are preserved, both host entry points consume the same canonical convention, and completion reporting names the verified destination. A local file or open PR alone does not satisfy publication.
- **Verification evidence:** fresh origin/main contains B009 for a Stop dispatcher defect and M015 for sandbox termination; the prior branch used B009 for a different automatic-merge defect and had M016 plus this M003 recurrence absent from main. No merged-delivery result is asserted before observation.

Current ownership verification - 2026-10-13: PR212 and PR128 are merged and contained in the reviewed base. Exact M003 successor PID32000/thread01a13562-6a28-73a3-b2bc-d3bbe884dad5 is live. The supported machine:followup-codex helper returned unavailable/disconnected, no send attempted and acknowledged=false; no daemon or replacement session was started. Original terminal/callout prevention conditions remain open, distinct from the documentation publication delivered by this PR.
