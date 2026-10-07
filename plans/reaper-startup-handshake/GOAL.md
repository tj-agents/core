# Reaper startup acknowledgement and cancellation

Status: authorized bounded source repair; native pickup pending.

## Authority and ownership

The parent Codex session 01a11794-26f3-7fb2-accb-0df87faa5180 retains the repository layout goal at
C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-RepositoryOwnedLayout/plans/repository-layout/REPOSITORY_LAYOUT_PROPOSAL.md.
The user approved its closeout reliability slice. Selected session-guidance also authorizes this
bounded standards-source repair through implementation, tests, focused PR and merge after normal gates.
This native Claude owner owns only startup acknowledgement/cancellation. It does not own the allocator,
aggregate, adoption, credentials, unrelated cleanup or the parent checkout. Preserve the parent goal.

Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-ReaperStartupHandshake
Branch: Fix/ReaperStartupHandshake
Fresh base: f9f5183eb1f0c5a23532e0106f59c211f89182c5
Launch lane: L1 for the acknowledgement state-machine design; apply L4 for bounded implementation.

## Reproduced source gap and required behavior

The installed finisher for the original layout predecessor passed cleanup proof, timed out waiting five
seconds for the detached reaper's started record, and reported nothing closed. A late reaper remained
and was stopped before the new planning request. Current source finish.ps1 still spawns, waits for
started and throws on timeout without cancelling. finish_reaper.ps1 records started, waits for host
exit and can later remove the worktree without a separate accepted-start handshake.

Repair this as one coherent producer protocol: a failed/late/ambiguous startup must leave the host,
worktree and branch intact and must not leave a cleanup-capable detached process. A stale/foreign
receipt cannot acknowledge this invocation. A timely accepted start may retain the supported exact-host
closeout, only after fresh cleanup and shared-session checks. Bound all waits and preserve useful result
evidence. Design the race behavior explicitly before implementation; increasing five seconds alone is
not a repair. Preserve strict process identity, dirty-work and branch-tip protections.

## Ownership and source boundaries

Read current AGENTS.md, README.md, packaging and peer-cli contracts before writes. Authored implementation
belongs to .agents/machine/utility/peer-cli/scripts/finish.ps1 and finish_reaper.ps1 with focused existing
finish tests and any necessary shipped harness declaration. Do not commit generated plugins output.
Use zero code comments unless a real invariant cannot be expressed in the code.

You are not alone. Preserve/adapt around all existing changes. In particular:
- C:/Users/TommySeery/source/repos/tj-agents/core-transferred-cleanup-obligation,
  Fix/TransferredCleanupObligation at 830c789 has active uncommitted finish_reaper.ps1 changes for
  transferred-obligation/SessionOnly completion and process-exit checks. Its native identity is unknown,
  registry/session metadata did not establish it, and no PR was returned. It does not change startup
  acknowledgement in finish.ps1. Do not edit its checkout, supersede that owner, or duplicate its repair.
  Compare its latest delta before integration and reconcile an eventual PR before overlapping delivery.
- PR #135 Fix/PeerCliSingleTabCount owns close-tab.ps1's PS5.1 Count fix, not this handshake. Preserve it.
- Core policy PR #133, plan checker PR #136, allocator Feature/RepositoryOwnedLayout and bytecode repair
  Fix/WorkflowBytecodeIntegrity have distinct owners; do not edit their paths or close their sessions.

## Acceptance

- Tests reproduce the original failed-start/late-reaper path against prior behavior and pass with repair.
- Exercise delayed readiness on both sides of the deadline, cancellation, launcher exit before accept,
  foreign/stale result identity, failed spawn, accepted normal closeout, shared claims and changed tip.
- Cover Windows PowerShell 5.1 and PowerShell 7 where available; retain existing finish scenarios.
- Test with disposable process/repository fixtures. Do not kill real agents or remove real worktrees
  to prove cancellation. Native-host acceptance uses a separately proven disposable owner only.
- Required source, package, harness and repository checks pass; review and exact-head CI gate merge.
- Return PR/head/merge/test evidence and any unresolved native gate in plans/reaper-startup-handshake/RESULT.md.

## Progress

- 2026-10-07: native Claude pickup recorded in .agents/continuation/reaper-pickup.json (head f9f5183).
- Defect reproduced on disposable fixtures: launcher timeout left an armed late reaper that removed the
  worktree after host exit.
- Protocol specified in [PROTOCOL.md](PROTOCOL.md): three-phase started/accepted/armed handshake with
  explicit cancellation, exclusive started create, command-line accept bound (CIM children inherit no
  environment), identity-checked signals, launcher testability seam, full race table and test plan.
- Independent L2 readiness review completed; verdict "not ready as written" resolved by amending the
  protocol with its two blocking findings (armed acknowledgement before host close; handshake seam for
  deterministic tests) and its should-fix items. Design is now implementation-ready.
- Execution readiness: bounded small/medium slice — stays with this session; implementation delegated at
  lane L4 to a lane worker with exclusive writer lease over finish.ps1, finish_reaper.ps1,
  session_close.ps1 (Start-DetachedReaper only) and tests/finish.tests.ps1; parent owns validation,
  review and delivery. Next action: L4 implementation per PROTOCOL.md.

## Next Steps

Scope: this startup/cancellation source repair through authorized delivery; parent retains the whole goal.
Current slice: focused L4 implementation of PROTOCOL.md, then regression/native proof, review, CI and
normal merge.
Done when: a failed startup cannot later clean up, normal closeout remains verified, and the focused
repair is merged with any unavailable native gate recorded truthfully for parent acceptance.

1. Record harness/session, branch/head, timestamp and actual first action in
   .agents/continuation/reaper-pickup.json, then read the protocol and ownership evidence above.
2. Load plan-execution, lanes and applicable standards. Reproduce with safe fixtures, specify the protocol
   and obtain readiness review before L4 implementation. Keep one writer per checkout.
3. Complete focused delivery under existing authority; routine commit/PR/merge needs no new confirmation.
   Resolve source overlap through existing review ownership and report real gates without abandoning
   independent repair work. Checkpoint this goal and write RESULT.md for the parent.
