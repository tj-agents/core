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

## M003 ? Returning blocked delivery without an active continuation owner

**Status:** Open. **Observed:** 2026-10-11. **Scope:** goal continuation; observed on Codex.

**Mistake:** Delivery was returned to Tommy after a lasting blocker without an initialized continuation owner or registered wake, requiring repeated intervention.

**Why:** I treated the blocked operation as the end of task ownership and selected continuation too late. The subsequent owner initialization failed on the protected owner file and its escalation failed automatic review. No PR or CI run existed, so this incident does not establish a CI-waiter bug.

**Intended correction:** Select supported continuation when a lasting wait appears. Claim unattended ownership only after initialization and wake registration are observed. Keep available work moving and expose the actual resolver when the host cannot continue.

**Resolved when:** The workflow demonstrates continued ownership through a delayed result, including correct reporting when continuation is unavailable.

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

**State:** in-progress. **Repair link:** [repository-settings goal](plans/repository-settings/GOAL.md), continuing the released `Feature/RepositoryConfiguration` implementation as one causal repair.

**Ownership evidence:** exact controller `01a122c4-e884-7402-a873-9fa7449e5c37` was recovered and contacted its existing child through native collaboration. The original source goal records the child's explicit release to this successor at `2026-10-11T22:16:13Z`, preserving dirty source and its SHA-256 inventory. Source coordination is resolved.

**Next action:** the bounded L4 writer integrates the released patch and applies the settings contract, followed by validation, independent review and authorized delivery.

**Resolution condition:** public documentation and both shipped host consumers use one Core-owned settings interface; an unrelated disposable repository exercises guarded auto-merge with its existing authorized task and no copied interpretation or legacy-standing-policy boilerplate; Windows/Linux validation, independent review, normal merge and causal publication pass, and completion reports match the observed outcome.

**Verification evidence:** the correction handoff, the existing owner goal and read-only dirty-source inspection, exact child/controller metadata, and the native follow-up result are recorded in the repair goal. No settings behavior, source delivery, consumer adoption or normal-profile activation has been verified.

## M009 - Treating unavailable follow-up as the end of authorized coordination

**Kind:** mistake. **Observed/reported:** 2026-10-11. This settings session identified the existing source controller, received unavailable/no-send-attempted from the supported follow-up helper, and returned a manual source-release obligation to Tommy while the exact-session open-codex recovery utility was available. Tommy called out that implementation remained unfinished and coordination had been offloaded to him.

**Impact and priority:** P2; the authorized settings correction was stalled without exhausting supported automated recovery.

**Source owner:** tj-agents/core machine follow-up/recovery standards. **Cause:** confirmed incomplete manual-only fallback guidance in followup-codex, combined with this agent failing to attempt exact-owner recovery. The endpoint infrastructure failure's cause remains unknown.

**State:** in-progress. **Repair link:** C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-FollowupRecoveryOwnership/plans/followup-recovery/GOAL.md, branch Fix/FollowupRecoveryOwnership, launched native successor 01a12d05-0e36-7cd2-afac-1936aa63404b. The original settings outcome remains owned by plans/repository-settings/GOAL.md and this native session.

**Next action:** the side successor repairs eligible automated recovery before manual fallback while this parent verifies source release from the recovered exact controller and resumes the settings implementation.

**Resolution condition:** the standards repair is reviewed, both-host Windows/Linux validated, merged and causally published, and recovery demonstrates preserved exact identity, one writer, truthful acknowledgment/release evidence and continued ownership of the original outcome.

**Verification evidence:** exact open-codex recovery succeeded for controller 01a122c4-e884-7402-a873-9fa7449e5c37, now registered alive at PID 1216; one disjoint side-workstream launcher confirmed submission, now registered alive at PID 9104. The original controller recorded explicit source release at 2026-10-11T22:16:13Z; the settings writer is implementing that preserved patch. Settings and side standards delivery remain incomplete.

## M010 - Helper exit status mistaken for a focused-test verdict

**Kind:** mistake. **Observed/reported:** 2026-10-11. The implementation worker reported six compact validation calls as exit zero while their saved unittest logs contained failures. Parent and writer inspected the actual artifacts before creating a candidate and corrected the interpretation. **Cause:** confirmed reliance on the helper/transport exit rather than the recorded subprocess/test result; the existing validation contract already requires validating each returned result, so no missing standards rule is established.

**Impact and priority:** P2; an unverified candidate could have been mislabeled passing, but none was committed or delivered from that status.

**Source owner:** this repository-settings execution and its test-evidence reconciliation. **State:** resolved. **Repair link:** [repository-settings goal](plans/repository-settings/GOAL.md); no separate causal repair.

**Correction:** the import and dynamic exception assertion were repaired. Parent read every replacement test summary before freezing; helper status is no longer treated as a verdict.

**Resolution condition:** every required focused scope has an observed passing terminal artifact, failed initial artifacts remain accurately classified, and review/CI claims bind to the real candidate.

**Verification evidence:** saved final repository-settings-l4 artifacts report reader 11, delivery 36, guarded command 10, binding 38, merge-review gate 82, machine 28, harness manifests 14 and source layout 21 tests OK (240 tests; 3 skips). Parent independently read the terminal artifacts. Initial failures retain their failed classification. Generation and generated checks passed. No source candidate or PR was created from the ambiguous helper status.

## M011 - Committing Core's generated catalog digests

**Kind:** mistake. **Observed/reported:** 2026-10-12. The initial settings candidate committed engineering/machine catalog digest regeneration, and exact-head CI38183296901 rejected those two fields. **Cause:** confirmed candidate staging omitted Core's generated-path guard; the existing guard explicitly reserves digest publication for post-merge, so no absent standards rule is established.

**Impact and priority:** P2; the draft PR failed CI, with no normal merge or publication attempted.

**Source owner:** this repository-settings candidate preparation. **State:** in-progress. **Repair link:** plans/repository-settings/GOAL.md and PR208. **Next action:** restore only generated digest values to the merge-base baseline and verify the existing guard before replacement-head validation.

**Resolution condition:** the committed runtime and later guidance slices contain no generated digest or package deltas, the generated-path guard and exact-head CI pass, and causal post-merge publication owns regeneration.

**Verification evidence:** authoritative gh run view38183296901 failed-step logs name .agents/catalog/catalog.json digest of base-agents/engineering and base-agents/machine. scripts/check_generated_paths.py reads merge-base digest values and explicitly rejects these changes.

## M012 - Unverified delayed CLI closure after completed delivery

- Kind: mistake. Observed/reported: 2026-10-12; predecessor ended its report after delegating delayed self-close and did not reconcile the nonzero command/observer cancellation.
- Cause: confirmed unobserved final action; no valid basis to equate a delayed worker promise with completed session exit.
- Impact/priority: P2; completed CLI remained live and Tommy had to call out unfinished closure.
- Source owner: engineering session-guidance terminal lifecycle and machine peer-cli runtime. State: in-progress.
- Repair link: B004, plans/verified-self-close/GOAL.md; one causal repair owner.
- Next action: repair the verified self-close failure and retain accountable closure evidence/reporting.
- Resolution condition: actual registered CLI exit is observed through supported observer/process evidence after completion, without closing another/unknown host or claiming an unverified tab closed.
- Verification evidence: original parent final report followed by worker refusal and cancelled observer; source delivery itself remained verified complete.
