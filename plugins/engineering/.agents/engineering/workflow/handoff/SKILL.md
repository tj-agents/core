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
3. For an explicit prompt-only request, return the text without launching. Otherwise write the prompt
   to a UTF-8 file and invoke the selected launcher's packaged script once, following its loaded
   instructions. Preserve a user-selected model, effort or frontier request; otherwise choose the lane the
   remaining work is worth per `engineering:lanes` and pass it, or inherit defaults when no lane is clear.
   Record the lane and a one-line reason beside the next action in the goal.
   Never launch a second successor because startup is slow or acknowledgement is delayed.
4. Verify the launch result. On failure ownership stays here: diagnose and preserve the checkpoint.
   Successful launcher submission proves launch, not that the successor has read the plan. Report that
   distinction, release writing ownership after launch, and let the successor acknowledge in the goal.
   Never keep two implementation writers active.

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
