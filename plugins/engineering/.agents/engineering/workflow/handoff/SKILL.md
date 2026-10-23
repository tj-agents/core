---
name: handoff
description: Transfer the current goal or a distinct authorized side workstream to one selected harness session. Checkpoint and launch for a handoff request; format text only when explicitly asked for a prompt.
kind: workflow
domain: process
---

# Transfer a context or bounded side workstream

An explicit request to hand off means performing the transfer, even when the current session could do
the work. Without an explicit request, hand off only when the work needs a separate session. Preparing a
pointer alone does not complete a handoff. Respect an explicitly named target harness; otherwise select
`machine:handoff-codex`.
The machine plugin and that launcher's documented platform
and CLI prerequisites must be available. Resolve the skill using native discovery and load its
instructions; do not guess a sibling-plugin or author-checkout path.

After the identity, authority and capability checks below, dispatch the unresolved work immediately.
Capture its objective, known context, constraints and open questions; the successor owns the delegated
technical decisions and execution setup. Do not perform that investigation first or require a completed
design, implementation plan or new delivery checkout before launching. Use a verified existing repository
checkout as the starting directory when delivery setup is unresolved; the successor must establish
appropriate isolation and ownership before deliverable writes. Preserve explicit user limits.

```text
Request: Hand off the architecture decision; keep this CLI and checkout open.
Predecessor: Launch one successor with the objective, constraints and unresolved questions.
Successor: Decide the architecture and establish isolated execution before deliverable writes.
```

When the user authorizes an independent successor for a distinct side workstream, select this workflow
in **bounded side-workstream** mode. Give that workstream one successor and isolate its deliverable
writes; the originating session retains its active goal and remains its only writer.
`engineering:self-repair` owns whether an internal source repair is eligible and keeps it in the
originating session unless the user requests a handoff.
This is not a full-goal transfer. Do not offload a step that is inseparable from the original task's next
action, create duplicate writers, or hand off work that overlaps the original checkout's owned paths.

Before launching the successor, capture the side-workstream authorization, exact starting checkout and branch,
the useful source context, and a concrete completion expectation in its canonical goal or brief. Respect
explicit user limits and existing external-action gates. A prior authorization to hand off that workstream
does not require repetitive permission. Prompt-only requests remain prompt-only. If the launcher is
unavailable or fails, preserve the side-workstream task and report that fact honestly while the original
session continues its independent active task.

## Admit work before dispatch

Resolve an existing canonical repair owner, exact native session, goal, worktree, and launch attempt
before a new handoff. Reuse an in-flight owner. Reopen a verified closed context through its supported
open skill. An unknown identity, ambiguous launch, or pending attempt keeps the existing reservation for
reconciliation and never permits a second writer.

Check authority, supported capabilities, concrete dependency evidence, conflicting owners and paths, and
the goal's explicitly declared local writer budget before ranking work. Do not infer capacity from a
machine-wide process count. Rank only eligible independent work by P0 through P3, then authorized work
unblocked, then age. A dependency is reconsidered on a supported foreground action or existing supported
continuation after its observed fingerprint changes; no record or skill creates a scheduler or dispatches
work by itself.

When work cannot run, use the selected profile under
[the recording contract](../../resources/problem-records.md) to update its canonical record with its
resolver and resume condition.

## Full context transfer

1. Resolve the current goal and its owning review under `engineering:git-branching`, then its worktree
   and branch. Preserve the review URL in the goal or ledger's `PR:` field when execution moves.
   Update the existing canonical plan with observed state,
   verification, remaining scope, next action, authorization and transfer ownership. A standalone goal
   does not need a second ledger or an engineering runtime. Checkpoint the effective
   design-approval value resolved from `configuration.core.auto_approve` or its legacy alias, its exact
   settings provenance, and every decision the
   user explicitly reserved when routine design delegation applies; the successor rereads the actual
   checkout before acting.
2. Apply `engineering:handoff-format` for a selected engineering lifecycle. For a standalone goal, make a
   two-line pointer: `cd <absolute-working-directory>`, followed by a request to read the absolute goal
   path and execute its `## Next Steps`. Keep the actual work instructions in that same goal file.
3. For an explicit prompt-only request, return the text without launching or reserving an executor.
   For a critical plan selected by `plan-authoring`'s readiness decision, use the verified execution
   pickup procedure below. Otherwise write the prompt
   to a UTF-8 file and invoke the selected launcher's packaged script once, following its loaded
   instructions. Preserve a user-selected model, effort or frontier request; otherwise choose and pass the
   cheapest suitable lane for the remaining work per `engineering:lanes`. A merge, handoff, file count or
   delivery operation does not raise it: use L5 for small already-decided file deletion or move, config or
   docs cleanup, and L4 only for specified implementation that still needs code-level judgement.
   L7 is in-session only and cannot open either handoff launcher. Claude handoff also requires an explicit
   L1–L6 lane, frontier tier, or non-Haiku model; never leave that choice to the CLI default.
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
2. Run the helper from the owning checkout, using its absolute path for every command. Use `python` on
   Windows and `python3` on Linux/macOS:

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

1. Keep the original goal, worktree, branch, and next action with the current session. Use the side
   workstream's verified checkout when one exists; otherwise launch from a verified repository checkout
   and delegate setup. Before deliverable writes, the successor creates or selects a separate isolated
   checkout through `engineering:open-worktree` and reconciles ownership. It must not write the side
   workstream's deliverables in the original active checkout.
2. Create or update the side workstream's canonical goal or brief with its authorization, starting checkout,
   relevant context, completion expectation, gates, and the one next action. The successor owns only that
   workstream and returns its outcome; it does not adopt, close, or rewrite the originating goal.
3. Write the self-contained side-workstream prompt to UTF-8 and invoke the selected launcher once. An
   explicit prompt-only request returns that prompt without launching. Preserve an explicit model, effort,
   or frontier request; otherwise select a lane under `engineering:lanes` when the remaining work warrants it.
4. Verify submission. Success proves launch, not that the successor has read its goal. Release only the
   side-workstream writer lease, retain the original task's writer lease, and continue the original task.
   On failure, retain both task records and continue only work independent of the unlaunched side task.

This transfer is the fallback when the owner cannot run `engineering:merge` Step 5's `finish` itself; for a
transfer whose purpose is to release the current checkout before it is moved, renamed, or deleted, put that
exact operation and its final filesystem verification in the successor's `## Next Steps`. The
predecessor must not perform the operation after launch: it ends repository-scoped activity and emits a
recorded release marker. Without `finish` it cannot end its own host process or close its own window, so the
successor's `## Next Steps` must gate the operation on that marker, then close the predecessor itself with
`machine:peer-cli`: resolve the registry entry whose `cwd` is the target checkout (and the recorded session
id or tab title when the goal names one); `close` verifies the recorded host pid and start time against the
live process, `close_tab.py` takes only its exact native terminal identity, and an unverifiable entry stays open with the user named as
resolver. The successor then performs the operation from the target checkout and treats a command error or
residual path as incomplete rather than accepting partial Git cleanup.

If discovery cannot resolve the launcher, report the missing capability and required selection. Continue
independent authorized work where possible. Never claim transfer occurred or silently substitute a
prompt-only response. Installing or changing a normal profile requires its own authorization.
