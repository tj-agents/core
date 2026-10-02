---
name: handoff
description: Transfer the current goal or a distinct authorized side workstream to one selected harness session. Checkpoint and launch for a handoff request; format text only when explicitly asked for a prompt.
kind: workflow
domain: process
---

# Transfer a context or bounded side workstream

An unqualified request to hand off means performing the transfer. Preparing a pointer alone does not
complete it. Respect an explicitly named target harness; otherwise select `machine:handoff-codex`.
For Claude select `machine:handoff-claude`. The machine plugin and that launcher's documented platform
and CLI prerequisites must be available. Resolve the skill using native discovery and load its
instructions; do not guess a sibling-plugin or author-checkout path.

When an active task surfaces a distinct, independently actionable, separately authorized side workstream,
select this workflow in **bounded side-workstream** mode immediately. Give the side workstream one isolated
checkout and one successor; the originating session retains its active goal and remains its only writer.
This is not a full-goal transfer. Do not offload a step that is inseparable from the original task's next
action, create duplicate writers, or hand off work that overlaps the original checkout's owned paths.

Before launching the successor, capture the side-workstream authorization, the exact checkout and branch,
the useful source context, and a concrete completion expectation in its canonical goal or plan. Respect
explicit user limits and existing external-action gates. A prior authorization to hand off that workstream
does not require repetitive permission. Prompt-only requests remain prompt-only. If the launcher is
unavailable or fails, preserve the side-workstream task and report that fact honestly while the original
session continues its independent active task.

## Full context transfer

1. Resolve the current goal and its owning review under `engineering:git-branching`, then its worktree
   and branch. Preserve the review URL in the goal or ledger's `PR:` field when execution moves.
   Update the existing canonical plan with observed state,
   verification, remaining scope, next action, authorization and transfer ownership. A standalone goal
   does not need a second ledger or an engineering runtime.
2. Apply `engineering:handoff-format` for a selected engineering lifecycle. For a standalone goal, make a
   two-line pointer: `cd <absolute-working-directory>`, followed by a request to read the absolute goal
   path and execute its `## Next Steps`. Keep the actual work instructions in that same goal file.
3. For an explicit prompt-only request, return the text without launching or reserving an executor.
   For a critical plan selected by `plan-authoring`'s readiness decision, use the verified execution
   pickup procedure below. Otherwise write the prompt
   to a UTF-8 file and invoke the selected launcher's packaged script once, following its loaded
   instructions. Preserve a user-selected model, effort or frontier request; otherwise choose the lane the
   remaining work is worth per `engineering:lanes` and pass it, or inherit defaults when no lane is clear.
   Record the lane and a one-line reason beside the next action in the goal.
   Never launch a second successor because startup is slow or acknowledgement is delayed.
4. Stop owned-path writes before invoking the launcher. Verify the launch result. A definite failure
   before invocation leaves ownership here; an interrupted or ambiguous invocation requires reconciliation.
   Successful launcher submission proves launch, not that the successor has read the plan. Report that
   distinction and let the successor acknowledge in the goal. For critical execution, observe the receipt
   below until pickup is verified or the recorded observation limit produces a concrete resumption gate.
   Never keep two implementation writers active.

## Verified execution pickup

Use this procedure for the substantial-design execution transfer selected by `plan-authoring`.
The packaged `scripts/transfer.py` beside this skill requires Python 3.9+. It validates identity and
serializes receipt changes; it does not evaluate design quality, grant authority, launch a host,
schedule work or enforce a general writer lease. Hook/prompt delivery is guidance; only observed
host execution establishes host acceptance.

1. Select the existing artifact that owns `## Next Steps` as `--goal`: the standalone goal, or the
   progress ledger for a managed plan. Keep the design in its linked plan and reference it from the
   readiness assessment. Finish all checkpoint edits and commits before preparing the receipt.
   Add these four literal lines under
   `## Execution readiness`, alongside the assessment's evidence and section references:

   ```text
   Verdict: ready
   Execution authorization: implementation
   Transfer: required
   Receipt: <absolute-path-to-this-goal's-transfer-receipt.json>
   ```

   Preserve `## Next Steps` as the single executable instruction owner. Include the helper's absolute
   installed path, a requirement to acknowledge before deliverable writes, the first action, its evidence
   destination and the full authorized completion boundary. Keep the receipt outside tracked source; it
   contains transport evidence only. Set an explicit pickup observation budget in the goal, honoring
   tighter user limits; absent a user limit, allow five minutes of bounded read-only observations.
   Planning-only, prompt-only and inline work creates no receipt.
2. Run the helper from the owning checkout, using its absolute path for every command:

   ```text
   python -B <skill-directory>/scripts/transfer.py prepare --goal <absolute-goal> --worktree <absolute-checkout> --receipt <absolute-receipt> --predecessor <current-session-identity> --harness codex
   python -B <skill-directory>/scripts/transfer.py begin --receipt <absolute-receipt> --attempt <returned-attempt-id> --predecessor <same-session-identity>
   ```

   Select `claude` when appropriate. Stop writing owned paths before `begin`; the prepared checkpoint
   stays unchanged. The helper binds the goal digest, checkout and available Git branch/head. Preparation
   fails when an attempt already exists. After `begin`, invoke exactly one supported machine launcher
   with the normal two-line pointer and selected execution lane. Keep the goal unchanged until pickup.
3. Capture the actual launcher output in an evidence file and record successful submission:

   ```text
   python -B <skill-directory>/scripts/transfer.py submitted --receipt <absolute-receipt> --attempt <attempt-id> --evidence-file <launcher-output>
   ```

   The successor reads the goal and receipt, validates its authorization and next action, and runs from
   the exact checkout:

   ```text
   python -B <skill-directory>/scripts/transfer.py acknowledge --receipt <absolute-receipt> --attempt <attempt-id> --successor <distinct-session-identity> --harness <selected-harness>
   ```

   One matching claimant succeeds. Acknowledgement may arrive before launcher output; a late submission
   preserves the acknowledged state. The successor then executes the authorized next action immediately,
   checkpoints its result or concrete gate in the goal, and records an actual nonempty evidence file:

   ```text
   python -B <skill-directory>/scripts/transfer.py progress --receipt <absolute-receipt> --attempt <attempt-id> --successor <same-session-identity> --harness <selected-harness> --evidence-file <first-action-evidence>
   ```

4. The predecessor retains read-only pickup accountability. Use `status --receipt <absolute-receipt>`
   to observe it; matching `acknowledged` proves pickup and `active` separately records first-action
   evidence. Report precisely which evidence exists. A phase, acknowledgement or tool exit does not prove
   completion of the goal. Human and dependency gates name their resolver and resume condition while
   independent authorized work continues under the execution owner.
5. If launch has not begun, `fail --receipt ... --attempt ... --outcome failed --reason <cause>` records
   a definite pre-launch failure. After `begin`, interruption, ambiguous output or elapsed pickup budget
   uses `--outcome uncertain`. Preserve the reserved attempt; an absent acknowledgement is not evidence
   that no successor exists. Never retry, reclaim writing or delete a receipt/lock merely because time
   elapsed. Report the exact attempt and the evidence needed to reconcile its existing successor.

When a continuation owner already exists, carry its reference with `prepare --owner-reference <reference>`
and use that owner's supported foreground release/claim procedure. This receipt is not its ownership
lock, job, completion record or delivery binding. If that interface is unavailable, keep the transfer
capability-gated instead of launching outside its exclusion mechanism. Without such an owner, the
predecessor's stopped writes and the matching successor acknowledgement define this bounded transfer.

Existing runtime-managed ledgers retain `Transfer:`, `Transfer to:`, `Resume stage:` and `Resume when:`
and point to this receipt. The successor restores their normal actionable next step after pickup.
On an interrupted predecessor, inspect the same receipt; do not prepare a second attempt. For a later
distinct transfer, reconcile the completed attempt and its current owner before recording a new receipt.

## Bounded side-workstream handoff

1. Keep the original goal, worktree, branch, and next action with the current session. Create or select a
   separate isolated checkout for the side workstream using `engineering:open-worktree`; do not reuse the
   original active checkout.
2. Create or update the side workstream's canonical goal or plan with its authorization, exact checkout,
   relevant context, completion expectation, gates, and the one next action. The successor owns only that
   workstream and returns its outcome; it does not adopt, close, or rewrite the originating goal.
3. Write the self-contained side-workstream prompt to UTF-8 and invoke the selected launcher once. An
   explicit prompt-only request returns that prompt without launching. Preserve an explicit model, effort,
   or frontier request; otherwise select a lane under `engineering:lanes` when the remaining work warrants it.
4. Verify submission. Success proves launch, not that the successor has read its goal. Release only the
   side-workstream writer lease, retain the original task's writer lease, and continue the original task.
   On failure, retain both task records and continue only work independent of the unlaunched side task.

For a transfer whose purpose is to release the current checkout before it is moved, renamed, or deleted,
put that exact operation and its final filesystem verification in the successor's `## Next Steps`. The
predecessor must not perform the operation after launch: it ends repository-scoped activity and releases the
host session. The successor waits until that host attachment is gone, then performs the operation from the
target checkout and treats a command error or residual path as incomplete rather than accepting partial Git
cleanup.

If discovery cannot resolve the launcher, report the missing capability and required selection. Continue
independent authorized work where possible. Never claim transfer occurred or silently substitute a
prompt-only response. Installing or changing a normal profile requires its own authorization.
