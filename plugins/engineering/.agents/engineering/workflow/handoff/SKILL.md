---
name: handoff
description: Perform a context transfer by checkpointing the current goal, preparing a UTF-8 prompt and invoking one selected harness launcher. Unqualified handoff uses Codex; an explicit prompt-only request formats text without launching.
kind: workflow
domain: process
---

# Transfer the current context

An unqualified request to hand off means performing the transfer. Preparing a pointer alone does not
complete it. Respect an explicitly named target harness; otherwise select `machine:handoff-codex`.
For Claude select `machine:handoff-claude`. The machine plugin and that launcher's documented platform
and CLI prerequisites must be available. Resolve the skill using native discovery and load its
instructions; do not guess a sibling-plugin or author-checkout path.

1. Resolve the current goal, worktree and branch. Update the existing canonical plan with observed state,
   verification, remaining scope, next action, authorization and transfer ownership. A standalone goal
   does not need a second ledger or an engineering runtime.
2. Apply `engineering:handoff-format` for a selected engineering lifecycle. For a standalone goal, make a
   two-line pointer: `cd <absolute-working-directory>`, followed by a request to read the absolute goal
   path and execute its `## Next Steps`. Keep the actual work instructions in that same goal file.
3. For an explicit prompt-only request, return the text without launching. Otherwise write the prompt
   to a UTF-8 file and invoke the selected launcher's packaged script once, following its loaded
   instructions. Preserve a user-selected model and effort; otherwise inherit defaults. Never launch a
   second successor because startup is slow or acknowledgement is delayed.
4. Verify the launch result. On failure ownership stays here: diagnose and preserve the checkpoint.
   Successful launcher submission proves launch, not that the successor has read the plan. Report that
   distinction, release writing ownership after launch, and let the successor acknowledge in the goal.
   Never keep two implementation writers active.

If discovery cannot resolve the launcher, report the missing capability and required selection. Continue
independent authorized work where possible. Never claim transfer occurred or silently substitute a
prompt-only response. Installing or changing a normal profile requires its own authorization.
