# Mistakes

This is core's incident record. Entries describe the observed mistake, its cause where known, and the intended correction. They are proposals for later repair, not additional operating instructions. A dedicated skill is deferred.

Each entry has a stable ID and an open or addressed status. Address entries individually and retain the verification evidence when their status changes. Governing behavior remains owned by canonical `.agents/` definitions and the relevant `.codex/` or `.claude/` adapter.

## M001 ? Same-goal verification treated as a handoff

**Status:** Open. **Observed:** 2026-10-11. **Scope:** shared workflow selection; observed on Codex.

**Mistake:** Sandbox recovery opened an independent native verifier tab for a focused acceptance check, adding ownership, pickup and cleanup work to an already blocking task.

**Why:** I treated the need for a fresh runtime process as a need to transfer task ownership. A captured child CLI was sufficient for the default-model probe; I did not apply that distinction consistently. The governing workflow already allows continued work in the same context. Whether its selection or enforcement needs a source change remains to be established.

**Intended correction:** Keep related work with the existing owner or a bounded subagent. Distinguish fresh-process verification from ownership transfer. Use a handoff for independently owned work or a necessary context transfer, with an observable result.

**Resolved when:** Workflow selection and focused checks demonstrate these different cases on both hosts without creating duplicate owners.

**Related closeout evidence:** After PR #205 merged, the completed native acceptance verifier still claimed the checkout. The finish utility preserved it; supported peer closure refused an ambiguous Windows Terminal target, and actual-tab inventory hit the approval-review metadata HTTP 400. This is additional ownership/cleanup cost from the same verification handoff, not a GitHub merge failure.

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
