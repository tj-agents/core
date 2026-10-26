---
name: handoff
description: Transfer the current goal or a distinct authorized side workstream to one selected harness session. Checkpoint and launch for a handoff request; format text only when explicitly asked for a prompt.
kind: workflow
domain: process
---

# Transfer a context or bounded side workstream

An explicit request to hand off means performing the transfer, even when the current session could do the
work. Without an explicit request, hand off only when the work needs a separate session. Preparing a
pointer alone does not complete a handoff. Respect an explicitly named target harness; otherwise select
Codex through `agent:handoff --host codex`. The Agent publisher and that launcher's documented platform and CLI
prerequisites must be available. Resolve the selected launcher through native discovery and load its
instructions; do not guess a sibling-plugin or author-checkout path.

After the identity, authority, capability, dependency, owner, path, and local writer-budget checks below,
dispatch unresolved architecture immediately from a verified existing repository checkout for repository
work or a verified task directory for non-repository work. Capture its objective, known context, constraints,
and open questions. The successor owns the delegated technical
decisions and execution setup, including isolation before deliverable writes. Do not investigate first or
require a completed design, implementation plan, new delivery checkout, or prepared critical receipt before
launching. Preserve explicit user limits.

```text
Request: Hand off the architecture decision; keep this CLI and checkout open.
Predecessor: Launch one successor with the objective, constraints, and unresolved questions.
Successor: Decide the architecture and establish isolated execution before deliverable writes.
```

When an active task surfaces a distinct independently actionable side workstream with separate authorization,
select this workflow in **bounded side-workstream** mode immediately. Give the side workstream one successor
and isolate its deliverable writes; the originating session retains its active goal and remains its only
writer. This is not a full-goal transfer. Do not offload a step inseparable from the original task's next
action, create duplicate writers, or hand off work that overlaps the original checkout's owned paths.

Prompt-only requests remain prompt-only. They return a self-contained pointer or prompt without launching or
reserving an executor. Preserve a user-selected model, effort, frontier, or harness choice. Otherwise select
the appropriate lane through `agent:lanes`; L7 is in-session only and cannot launch either handoff tool.
Claude launch requires an explicit L1-L6 lane, frontier tier, or non-Haiku model. Record the chosen lane and
one-line reason beside the next action when a lane is selected.

## Admit work before dispatch

Resolve an existing canonical repair owner, exact native session, goal, worktree, and launch attempt before a
new handoff. Reuse an in-flight owner. Reopen a verified closed context through its supported open skill. An
unknown identity, ambiguous launch, or pending attempt keeps the existing reservation for reconciliation and
never permits a second writer.

Check authority, supported capabilities, concrete dependency evidence, conflicting owners and paths, and the
goal's explicitly declared local writer budget before ranking work. Do not infer capacity from a machine-wide
process count. Rank only eligible independent work by P0 through P3, then authorized unblocked work, then
age. A dependency is reconsidered on a supported foreground action or existing supported continuation after
its observed fingerprint changes; no record or skill creates a scheduler or dispatches work by itself.

When a selected profile record cannot run, update its canonical record with its resolver and resume condition
through [the shared recording contract](../../resources/problem-records.md). A generic handoff has no tracker
dependency.

## Pointer shape

A transfer pointer identifies input already sent to the successor. It is not a request for the user to paste it
or proof that an executor accepted it. Readiness, receipt identity, and pickup instructions live in the
canonical goal under the verified pickup procedure.

For a plan-managed transfer, introduce the pointer with one `Why:` line derived from the first paragraph of
the current `## Next Steps`, then end with an opener and read line. The actual work instructions remain in the
same owning goal or ledger.

```text
Why: `<LEDGER>_PROGRESS.md` owns unfinished work from this turn: <short next-action reason>
cd <absolute-worktree-path>
Read @<absolute-owning-worktree-goal-or-plan-path> and @<absolute-owning-worktree-ledger-path> and do what its `## Next Steps` says.
```

Use `/open-worktree <Type>/<Name>` as the opener only when the required worktree does not exist. Both read
paths are absolute and identify the same owning worktree. Nothing follows the pointer. A non-plan dispatch is
self-contained: name the branch or PR, relevant working files, objective, known context, constraints,
authority, open questions, and exact next responsibility. For a selected record-addressing discipline, name
its canonical URI, stable ID, and kind; require the applicable `engineering:address-bug`,
`engineering:address-mistake`, or `engineering:address-debt` operation before repair.

A blocked or paused goal emits no continuation pointer. First do safe authorized work that can remove its
gate. Then preserve the concrete blocker, resolver, unblock action, and observable resume condition. When a
transfer is selected, emit one pointer for the worktree owned by this turn; dependency inputs and return
handoff edits do not claim other owners. Otherwise continue in the current context without emitting one.

## Full context transfer

1. Resolve the current goal, worktree, branch, and existing execution owner. For a selected Engineering
   software delivery lifecycle, also reconcile its owning review, preserve its review URL in the goal or
   ledger's `PR:` field, and apply its Git, worktree, delivery, and record-addressing rules. A standalone
   goal needs no Engineering runtime, second ledger, review, or Git identity. Update the existing canonical
   goal with observed state, verification, remaining scope, next action, authorization, transfer ownership,
   and every decision the user explicitly reserved. The successor rereads the actual checkout before acting.
2. Build the pointer once using the shape above. For a standalone goal, use `cd <absolute-working-directory>`
   followed by a request to read the absolute goal path and execute its `## Next Steps`. Keep actual work
   instructions in that goal. For plan-managed work, preserve the plan and ledger as the executable source;
   do not restate their branch checks, gates, commands, or next action in the prompt.
3. For an explicit prompt-only request, return the pointer or prompt without launching or reserving an
   executor. For a substantial-design execution transfer selected by `workflow:plan`, use the verified
   execution pickup procedure below. Otherwise write the prompt to a UTF-8 file and invoke the selected
   launcher's packaged script once, following its loaded instructions. Never launch a second successor
   because startup is slow or acknowledgement is delayed.
4. Stop owned-path writes before invoking the launcher. Verify the launch result. A definite failure before
   invocation leaves ownership here; an interrupted or ambiguous invocation requires reconciliation.
   Successful launcher submission proves launch, not that the successor has read the goal. Report that
   distinction. Never keep two implementation writers active.

## Verified execution pickup

Use this procedure for the substantial-design execution transfer selected by `workflow:plan`. The packaged
`scripts/transfer.py` beside this skill requires Python 3.9+. It validates identity and serializes receipt
changes; it does not evaluate design quality, grant authority, launch a host, schedule work, or enforce a
general writer lease. Hook and prompt delivery are guidance; only observed host execution establishes host
acceptance.

1. Select the existing artifact that owns `## Next Steps` as `--goal`: the standalone goal, or the progress
   ledger for a selected Engineering managed plan. Keep design in its linked plan and reference it from the
   readiness assessment. Finish checkpoint edits and commits before preparing the receipt. Add these four
   literal lines under `## Execution readiness`, alongside the assessment's evidence and section references:

   ```text
   Verdict: ready
   Execution authorization: implementation
   Transfer: required
   Receipt: <absolute-path-to-this-goal's-transfer-receipt.json>
   ```

   Preserve `## Next Steps` as the single executable instruction owner. Include the helper's absolute
   installed path, acknowledgement before deliverable writes, the first action, its evidence destination,
   and the full authorized completion boundary. Keep the receipt outside tracked source; it contains
   transport evidence only. Set an explicit pickup observation budget in the goal, honoring tighter user
   limits; without a user limit, allow five minutes of bounded read-only observations. Planning-only,
   prompt-only, and inline work create no receipt.
2. Run the helper from the owning checkout, using its absolute path for every command. Use `python` on
   Windows and `python3` on Linux/macOS:

   ```text
   python -B <skill-directory>/scripts/transfer.py prepare --goal <absolute-goal> --worktree <absolute-checkout> --receipt <absolute-receipt> --predecessor <current-session-identity> --harness codex
   python -B <skill-directory>/scripts/transfer.py begin --receipt <absolute-receipt> --attempt <returned-attempt-id> --predecessor <same-session-identity>
   ```

   Select `claude` when appropriate. Stop writing owned paths before `begin`; the prepared checkpoint stays
   unchanged. The helper binds the goal digest, checkout, and available Git branch and head. Preparation
   fails when an attempt already exists. After `begin`, invoke exactly one supported machine launcher with
   the pointer and selected execution lane. Keep the goal unchanged until pickup.
3. Capture actual launcher output in an evidence file and record successful submission:

   ```text
   python -B <skill-directory>/scripts/transfer.py submitted --receipt <absolute-receipt> --attempt <attempt-id> --evidence-file <launcher-output>
   ```

   The successor reads the goal and receipt, validates its authorization and next action, and runs from the
   exact checkout:

   ```text
   python -B <skill-directory>/scripts/transfer.py acknowledge --receipt <absolute-receipt> --attempt <attempt-id> --successor <distinct-session-identity> --harness <selected-harness>
   ```

   One matching claimant succeeds. Acknowledgement may arrive before launcher output; a late submission
   preserves the acknowledged state. The successor executes the authorized next action immediately,
   checkpoints its result or concrete gate in the goal, and records actual nonempty evidence:

   ```text
   python -B <skill-directory>/scripts/transfer.py progress --receipt <absolute-receipt> --attempt <attempt-id> --successor <same-session-identity> --harness <selected-harness> --evidence-file <first-action-evidence>
   ```
4. The predecessor retains read-only pickup accountability. Use `status --receipt <absolute-receipt>` to
   observe it; matching `acknowledged` proves pickup and `active` separately records first-action evidence.
   Report precisely which evidence exists. A phase, acknowledgement, or tool exit does not prove completion
   of the goal. Human and dependency gates name their resolver and resume condition while independent
   authorized work continues under the execution owner.
5. If launch has not begun, record a definite pre-launch failure:

   ```text
   python -B <skill-directory>/scripts/transfer.py fail --receipt <absolute-receipt> --attempt <attempt-id> --outcome failed --reason <cause>
   ```

   After `begin`, interruption, ambiguous output, or elapsed pickup budget uses `--outcome uncertain`.
   Preserve the reserved attempt; absent acknowledgement is not evidence that no successor exists. Never
   retry, reclaim writing, or delete a receipt or lock merely because time elapsed. Report the exact attempt
   and evidence needed to reconcile its existing successor.

When a continuation owner already exists, carry its reference with `prepare --owner-reference <reference>`
and use that owner's supported foreground release or claim procedure. This receipt is not its ownership lock,
job, completion record, or delivery binding. If that interface is unavailable, keep the transfer
capability-gated instead of launching outside its exclusion mechanism. Without such an owner, the
predecessor's stopped writes and matching successor acknowledgement define this bounded transfer.

Existing runtime-managed ledgers retain `Transfer:`, `Transfer to:`, `Resume stage:`, and `Resume when:` and
point to this receipt. The successor restores their normal actionable next step after pickup. On an
interrupted predecessor, inspect the same receipt; do not prepare a second attempt. For a later distinct
transfer, reconcile the completed attempt and current owner before recording a new receipt.

## Bounded side-workstream handoff

1. Keep the original goal, worktree, branch, and next action with the current session. Use the side
   workstream's verified working directory when one exists; otherwise use a verified repository checkout
   for repository work or task directory for standalone work and delegate setup. Before deliverable writes,
   the successor creates or selects separate isolation through
   the selected Engineering worktree operation when that software lifecycle applies. It must not write side
   workstream deliverables in the original active checkout.
2. Create or update the side workstream's canonical goal or brief with its authorization, starting checkout,
   relevant context, completion expectation, gates, and one next action. The successor owns only that
   workstream and returns its outcome; it does not adopt, close, or rewrite the originating goal.
3. Write the self-contained side-workstream prompt to UTF-8 and invoke the selected launcher once. An
   explicit prompt-only request returns that prompt without launching. Preserve an explicit model, effort,
   frontier, or harness request; otherwise select a lane under `agent:lanes` when remaining work warrants
   it.
4. Verify submission. Success proves launch, not that the successor has read its goal. Release only the
   side-workstream writer lease, retain the original task's writer lease, and continue the original task.
   On failure, retain both task records and continue only work independent of the unlaunched side task.

For a selected Engineering delivery lifecycle, follow `engineering:merging` under Transferred checkout
cleanup when the handoff must release a checkout before it is moved, renamed, or deleted. Put the exact operation and final filesystem
verification in the successor's `## Next Steps`. The predecessor must not perform it after launch. A generic
handoff neither requires nor invents those Engineering capabilities.

If native discovery cannot resolve the launcher, report the missing capability and required selection.
Continue independent authorized work where possible. Never claim transfer occurred or silently substitute a
prompt-only response. Installing or changing a normal profile requires its own authorization.
