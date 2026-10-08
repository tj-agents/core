# Completion is reported only at the verified user outcome

Status: focused local verification passed. Candidate publication, review, CI and merge are active.

## Authority

Standing `engineering:session-guidance` standards-defect authorization: diagnose, implement, test, open the
PR and merge in tj-agents/core once its gates pass. Installing into other scopes, publishing elsewhere and
destructive operations stay gated. Originating session: Claude `core/main`, which owns the separate goal
`plans/close-finished-sessions/GOAL.md` on `Fix/CloseEveryFinishedSession`. Do not touch that goal, its
checkout, `.worktrees/Fix-ReaperStartupHandshake`, `core-transferred-cleanup-obligation` (PR #142) or
any peer-cli/finish/reaper/cleanup_proof script.

Checkout: `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-OutcomeVerifiedCompletion`
Branch: `Fix/OutcomeVerifiedCompletion` from `origin/main` 984ab5f.

## Defect

Tommy asked for one outcome: every finished CLI closes itself, and a merged worktree is removed. For three
days, sessions reported that outcome done while it was not:

- PR #121 merged with `- [ ] Exact-head PR CI` and `- [ ] Post-install acceptance on both hosts`
  unchecked in its own test plan, and was reported complete. No owner carried the acceptance afterwards.
- Follow-up PRs (#134, #135, the reaper-handshake branch, #142) were each scoped to one slice. Each was
  reported done, but no single goal tracked the user-level outcome. On 2026-10-07, 9 merged worktrees
  remained, two sessions sat open hours after their PR merged, and most reaper result records were
  `failed` or never finished.
- The standards already say this. `base:plan-artifacts` and `engineering:session-guidance` require
  reporting completion only at the user's actual outcome. They also say a slice must not narrow the goal,
  and that source generation does not establish adoption. Nothing enforces any of it, and the merge
  workflow's terminal report treats `MERGED` as the end.

## Completion expectation

Design (L1), then implement, the smallest enforceable change so that a session cannot report a goal
complete in either of these cases:

- its delivered PR's own test plan or acceptance items are unchecked;
- the requested user-observable outcome has no observed evidence.

Those items must remain as owned next actions in the goal, and the final report must name them as open.
Prefer a mechanical check in the existing merge/terminal-report path (for example, the PR body's unchecked
`- [ ]` items at merge, and the goal's acceptance section) over more prose. Keep every-prompt policy files
at minimum words. Cover it with tests in the existing suites, then review, CI, PR and merge per the
repository's gates. Return the outcome to Tommy in the final report.

## Next Steps

Scope: whole bounded standards-defect goal through review and authorized merge.
Current slice: shared outcome completion check and continuation terminal enforcement.
Remaining scope: implement, focused tests, generation checks, independent review, exact-head CI, merge and generated distribution verification.
Done when: the delivered runtime rejects unsupported completion, with evidence and any installed-host limitations reported explicitly.

1. Commit and publish the assessed slice; focused continuation, completion, PR-body and generation checks pass.
2. Independently review the immutable candidate and repair findings while exact-head CI runs.
3. Require exact-head CI, merge, observe generated distribution, and assess this goal with the completion check.

## Design decision

L1 design selected one shared `completion-check`, implemented as the narrowly permitted standalone
`.agents/workflows/completion.py` (packaged as `workflows/completion.py`), enforced by
`continuation_runtime.apply_receipt` before every `complete` transition, including foreground checkpoints,
child receipts, and recovered receipts. Merge admission stays unchanged because post-merge acceptance
cannot be completed before landing. Merge reporting and plan closeout consume the check before claiming
the user outcome complete or deleting its goal. An incomplete result names owned next actions.

The canonical goal contains exactly one fenced `completion` JSON object with this shape:

```completion
{
  "outcome": "The shared completion workflow rejects unverified success on both host runtimes and preserves unresolved acceptance as owned actions.",
  "acceptance": [
    {"id": "enforcement", "criterion": "Foreground and child completion reject unchecked PR acceptance or missing outcome evidence.", "evidence": [{"source": "Git-private outcome-root-verify artifacts: final-completion-parser, final-pr-body, resumed-continuation and external-goal-fixed", "result": "Completion and PR-body suites pass. Focused foreground/child rejection, released binding, repaired binding, external goal, bytecode and alias cases passed across the recorded runs after fixture repairs."}], "owner": "current execution owner", "next_action": "Review the implementation and require the full CI matrix."},
    {"id": "delivery", "criterion": "The reviewed candidate passes exact-head CI, merges, and is generated into the distribution.", "evidence": [], "owner": "current execution owner", "next_action": "Review, run CI, merge, and verify post-merge generation."}
  ],
  "deliveries": [],
  "open_tasks": []
}
```

Each evidence entry is `{ "source": "artifact or observation reference", "result": "concrete observed result" }`.
Each delivery is `{ "repository": "owner/repo", "pr": 123, "head": "full forty-character SHA" }`.
Each open PR task records those same identity fields plus `text`, `owner`, and `next_action`.
The implementation validates nonempty strings, identities, duplicate IDs/records, and visible Markdown
tasks (excluding fenced/commented/quoted examples). Empty or invalid evidence prevents success; pending
criteria require owner and next action. Every delivery is fetched fresh and must have the recorded head,
be merged, and have no unchecked tasks. Unchecked tasks are included even when their ownership is missing.
The runtime adds its bound PR identity to validation so omitting it from the goal cannot bypass the check.

The check verifies the presence and shape of recorded observations, not their semantic truth. Review
assesses whether the observations establish the requested outcome. Codex has no terminal-response hook
wired in this package: arbitrary final prose outside the supported workflow is not intercepted. This slice
must document that host boundary and must not claim installed-host adoption from source tests.

## Delivery slice and verification

One atomic source/runtime/test slice on `Fix/OutcomeVerifiedCompletion`, based on
`984ab5f336a06f38a250a676da82150d4c9461be` (`origin/main` at pickup). PR: not opened.
Expected under 1,000 substantive changed lines; reassess before exceeding that size. The validator,
terminal enforcement, tests, and directly coupled workflow instructions must ship together so consumers
can produce the required evidence before the new gate is applied. No always-loaded policy edits planned.

Ownership: the L4 worker owns completion/runtime/PR parsing, their focused tests, coupled workflow docs,
and the engineering harness declaration; this parent owns the goal, review, delivery and continuation.
Standards read: root AGENTS.md, README.md, SOURCE_LAYOUT.md, PACKAGING.md, plan-execution, lanes,
git-branching, plan-artifacts, session-guidance, plans, plan-checkpoint, committing, docs-and-debt,
remote-validation, open-pr, merge, persistent-workflow and persistent-delivery.

Local gates: focused completion, PR parsing and continuation tests; generated package import/operation;
generation and harness consistency; whitespace and instruction-pair checks. Full matrices belong to CI.

## Current ownership

Continuation owner `422a5f9d227cb0dda91faa61` is initialized and claimed by Codex PID 22364;
the shipped scheduler is registered and its first wake observed the foreground lease. No second writer.
The existing oversized repo-declared-config ledger warning is outside this bounded goal and unchanged.

## Verification and remaining repairs

- Root verification artifacts are under the repository-private Git path
  `agent-workflow/runs/outcome-root-verify/artifacts/`.
- Observed passes: final completion suite (10 tests), final PR-body suite, final catalog/package generation
  and consistency, harness consistency and harness manifest tests.
- The first completion fixture accidentally supplied two real records; it was corrected to test an outer
  fenced example separately. The isolated worker-receipt case rejected completion and kept the owner; its
  assertion now expects the runtime's existing exit-0 blocked-state result.
- The new test wrapper bypassed the runtime's script-level error handler and could generate bytecode before
  the runtime disabled it. Both fixtures now use the real script entry point with bytecode disabled early.
- The full local continuation file was interrupted after 1,348 seconds. A three-case diagnostic then hit
  existing 30-second subprocess budgets and a child-log teardown lock. Do not call this a green run or
  silently increase timeouts. An unchanged-base comparison of the release-success case passed; final candidate
  success and denial boundaries are being rerun after the fixture repairs.
- CI provenance: main run `37688259069`, verify job, actually executed shared runtime tests successfully
  from `2026-10-07T21:33:30Z` to `21:40:45Z`.
- Foreground refusal coverage, repaired/external goal fixture evidence, generated-helper execution coverage,
  and visible nested checklist parsing are implemented. Root owns process handles and all reruns.
- Disk exhaustion interrupted approval review. Removing the task's disposable baseline copy released
  695 KB temporarily; C: returned to zero free bytes. Git reported allocation failure; continuation tests
  encountered process startup and Git setup failures. No unrelated files were removed.
- The final 8-case continuation run passed direct rejection, child rejection, bytecode and alias checks.
  Three cases failed during system/Git startup. Foreground rejection correctly preserved the claim but its
  test wrongly expected the emitted error to replace the persisted reason; that assertion is fixed and needs
  rerunning. Log: `a12b6f7f2554ff1b-final-continuation-boundaries.log`. This run is not green.
- After disk space became available, foreground rejection and both released-binding success cases passed
  (`8bf14d5069886857-resumed-continuation.log`). The external-goal fixture lacked its completion record;
  the fixture now copies it and repairs the actual canonical goal path. Its isolated rerun passed
  (`caefe8508918dcdb-external-goal-fixed.log`). All selected boundaries now have passing evidence.
- No source commit, PR or review exists yet. Generated outputs and `.verification-baseline/` are disposable
  local verification material and must not be staged. No excluded cleanup/reaper source has changed.

## Progress

- 2026-10-07: goal recorded and launched by the originating Claude session.
- 2026-10-07: pickup confirmed; origin fetched, branch current, PR #115 inspected; L1 design complete.
- 2026-10-08: implementation and coupled workflow/harness changes present; focused verification found fixture
  regressions and a nested-list parsing gap. Repair and verification remain owned in this checkout.
