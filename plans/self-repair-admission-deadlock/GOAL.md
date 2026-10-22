# Repair the callout-admission deadlock

## Scope

Repair the Core callout enforcement path so a user-called-out session can complete the required `engineering:self-repair` admission and bounded source handoff without disabling or bypassing callout protection.

Repair workflow: engineering:self-repair

Source owner: tj-agents/core engineering:self-repair, engineering:handoff, persistent-workflow, and callout PreToolUse enforcement

Callout binding:

- Session: `01a1362c-5751-75f3-a54d-9bb37f25a41a`
- Callout ID: `7c3e57e0-bd1e-4752-9934-f1fb852b68ca`
- Prompt SHA-256: `4f67d7dfe612f03cb41e53186976086c2fa7c1706355da5e2abde68b4df5c443`

Problem record: `C:\Users\TommySeery\source\repos\tj-agents\core\BUGS.md#B011`

## Authorization

The standing standards-defect authorization in `engineering:session-guidance` authorizes the bounded Core source repair through normal Core delivery gates. The user has explicitly required that the current CLI and worktree remain open; this repair must not close either.

## Observed blocker

The active callout PreToolUse gate accepted direct reads of known skill files but rejected `git rev-parse --show-toplevel` and ordinary directory inventory with its generic instruction to perform the work that the same rejection made impossible. `engineering:handoff` requires an isolated checkout, and `engineering:open-worktree` requires Git resolution before creating it.

Required executable: git

Required executable: python

## Expected completion

The repaired gate admits the minimal, bound commands required to record and validate a callout repair, reconcile or allocate its isolated checkout, and launch one successor. It still blocks unrelated work until admission, does not create duplicate writers, and treats an already-processed hook binding as an idempotent machine event rather than a new user turn.

## Required duplicate-hook invariant

The runtime fingerprints a callout hook event by `(session_id, callout_id, prompt_sha256)`. After it has processed that binding, an identical or stale repetition must be discarded without a user-visible reply, record update, command execution, new disposition binding, or workflow restart. A genuinely new user message remains actionable. Regression coverage proves one repair route and zero duplicate side effects for repeated payloads.

## Required wait invariant

When the user says to wait, keep open, or monitor, the runtime must select exactly one of these states:

1. A durable monitor bound to an exact delivery that this session owns.
2. A quiet idle checkpoint when there is no owned delivery or a scheduler is unavailable.

It must not issue foreground sleep loops, repeated status messages, or create a monitor for another agent's delivery. Regressions cover all three forbidden behaviors.

## Lane

L3: bounded investigation of a host-enforcement/admission conflict before specified implementation.

## Next Steps

1. From an isolated Core checkout, reproduce the gate's decision for the bound callout and identify the allowlist/predicate boundary between repair-admission commands and unrelated commands.
2. Add end-to-end regressions proving `admission.py check`, Git checkout resolution, and one launcher preparation are admitted while an unrelated command remains blocked; repeat the exact hook payload and prove there is no second reply, record update, command, or successor.
3. Implement the minimal enforcement repair, run the focused Core checks and generated-output verification, then use the normal review and delivery workflow.
