# Proactive coordination with a named blocking owner

## Authorization

Standing standards-repair authority from `engineering:session-guidance`, triggered by M015 on 2026-10-12.
It covers diagnosis, implementation, tests, review, a focused GitHub PR and merge after repository gates
pass. It does not grant permission to message unrelated sessions, create duplicate writers, modify a
consumer repository, or alter a normal profile.

## Scope

This independent guidance slice determines and repairs the smallest existing Core owner that prevents an
agent from asking Tommy to reassign work before it has coordinated with the explicitly named owner of a
blocking dependency. Extend existing guidance and directly affected verification only; do not add a new
skill or duplicate `machine:peer-cli`, `machine:followup-codex`, `machine:open-codex`, or native in-team
collaboration tools.

The repaired path must distinguish an in-team peer from an independent native session, preserve existing
authorization and exact identity requirements for messaging/recovery, and retain one writer. When no
eligible coordination route exists, it must record that evidence and ask only the genuine external question.

## Evidence

- On 2026-10-12, PR #218 was blocked by B006 owned by parent PR #209. The child session asked Tommy to
  take over the parent's work before checking whether the recorded owner could be contacted.
- `machine:peer-cli` later showed no live PR #209 session. The explanation was accurate but came after the
  avoidable escalation.
- `machine:followup-codex` already protects exact thread/cwd/profile identity and requires explicit
  authorization for an independent-session message. The repair must not weaken that boundary.

## Checkout

Worktree: `C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Docs-ProactiveOwnerCoordination`
Branch: `Docs/ProactiveOwnerCoordination`
Base: `origin/main` at `4090e7d238754b3f1a37cd297142a698129cd3c8`
PR: not opened

## Lane

L3: the correct owner, authorization boundary, and machine/in-team routing require bounded investigation
before a narrow, testable guidance change.

## Launch status

- 2026-10-13: the one prepared L3 Codex handoff did not begin. Windows rejected creation of the launcher
  process with `The paging file is too small for this operation to complete. (os error 1455)`. No terminal
  tab or successor was submitted. This is a definite pre-launch capacity failure; do not retry until the
  host can create processes again. Resolver: machine capacity. Resume when a simple host process can start,
  then invoke this same prepared handoff once.

## Launch status

- 2026-10-13: the one prepared L3 Codex handoff did not begin. Windows rejected creation of the launcher
  process with `The paging file is too small for this operation to complete. (os error 1455)`. No terminal
  tab or successor was submitted. This is a definite pre-launch capacity failure; do not retry until the
  host can create processes again. Resolver: machine capacity. Resume when a simple host process can start,
  then invoke this same prepared handoff once.

## Next Steps

1. Acknowledge pickup before deliverable edits. Inspect M015, `base:goal-continuation`,
   `engineering:session-guidance`, `machine:peer-cli`, `machine:followup-codex`, and native collaboration
   interfaces; identify one authoritative escalation rule rather than creating another skill.
2. Define and implement the smallest safe rule: a named blocking owner requires scoped discovery, then
   eligible in-team messaging or independent-session recovery/follow-up before an external takeover or
   manual-fallback question. Preserve explicit-message authority and all no-duplicate-writer protections.
3. Add meaningful focused coverage for reachable, unavailable, and ineligible owner states; run applicable
   Windows/Linux source and generated-harness checks. Review, commit, push, open a focused PR, and merge
   when gates pass.
4. Update M015 and this goal with observed delivery evidence. Do not adopt PR #218, PR #209, or their
   worktrees.

## Completion condition

The authoritative owner-coordination rule is reviewed and merged with observed platform validation; M015
has concrete evidence that a named blocking owner is discovered and an eligible coordination path is tried
before escalation, without weakening messaging or writer-identity protections.
