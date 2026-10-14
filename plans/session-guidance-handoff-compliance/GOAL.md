# Self-repair handoff compliance

Status: implementation and focused validation are complete; the local candidate is ready for independent review.

Checkout: `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-SessionGuidanceHandoffCompliance`
Branch: `Fix/SessionGuidanceHandoffCompliance`
PR: https://github.com/tj-agents/core/pull/199
Updated: 2026-10-14
Implementation lane: L4
Delivery/review owner: parent coordinator

## Authority and scope

Tommy authorized the existing PR #199 owner to complete the bounded Core standards-repair
cutover. A user callout about a mistake caused or not prevented by a consumed Core standard must
answer the direct question, then create or reconcile one bounded repair. The repair may continue
only with a verified launched Core repair owner, a verified existing owner, or current typed
capability/dependency/conflict/capacity evidence. Explicit user limits still control.
Existing authority continues through independent review, PR #199 update, required Windows/Linux CI,
merge, causal generated publication, and cleanup.

This slice owns the selectable `engineering:self-repair` workflow, shared handoff admission,
shared callout gate, both-host manifest wiring, focused regressions, source-layout expectation,
and the session-guidance pointer. It excludes session-registration repair, the
`Feature-WorkItemSessions` checkout, continuation runtime recovery, scheduler/background waiter
work, committing generated plugin/catalog output, and installation into other scopes.

## Acceptance boundary

Every covered callout must have one verified repair owner or launch, or a current typed disposition
with its exact blocker, resolver, and observable resume condition, before normal continuation or
terminal close. Forged, stale, unrelated, or unverified evidence does not release the obligation.
Capacity requires an explicit numeric source of truth and verified occupancy; four live machine
sessions alone never establish exhaustion.

## Current implementation

- `engineering:self-repair` is the sole standing repair owner. It records the affected `Source
  owner`, `Repair workflow: engineering:self-repair`, and callout session/id/prompt digest before
  launch. `session-guidance` now remains a concise lifecycle pointer to that workflow.
- The shared callout gate keeps every distinct pending callout in state, reuses the saved id for a
  repeated identical callout, and does not let a neutral prompt, automatic feedback, or Stop bypass
  the obligation.
- A launch counts only when one parsed native launcher invocation has a successful paired result
  containing a structured `agent-handoff-submitted` receipt. The receipt worktree and prompt must
  match that invocation and load a goal whose repair workflow, source owner, session, callout id,
  and prompt SHA-256 bind to that exact callout. Intent, echo, compound command, unpaired output,
  failed output, stale receipt, or mismatched goal cannot release it.
- A current typed disposition is revalidated for every pending obligation and is not cached as
  completion. Its problem record must be the source repository primary checkout's root `BUGS.md`
  or `MISTAKES.md`, or a tracked primary `TECH_DEBT.md`; a delivery-worktree repair goal remains
  valid. A successful native launch can be cached only after its exact binding is verified.
- While a repair is pending, the gate admits only repair research, canonical record editing,
  supported isolated-checkout preparation, and admission checks. It rejects compound commands,
  normal continuation tools, unrelated patches, and patch payloads containing file deletions.
  Claude `Write`/`Edit` record operations are admitted only when their target is a canonical
  problem record or `GOAL.md`.
- Codex routes every `PreToolUse` call through the shared gate; Claude already has universal
  PreTool dispatch. Both hosts retain shared Stop coverage.

## Base and runtime evidence

`origin/main` was reconciled without discarding prior work in merge commit `e1c4c7c`. Generated
output and the supplied `RESUME_PROMPT.md` remain uncommitted. The previous PR #199 remediation
head was preserved through this reconciliation.

The continuation owner `17877fd10dfe84f96751c57e` still records head `259e022`; its supported
claim rejected `owner-head-changed` after the source advanced to `ffeecf7`. No foreground or child
claimant was observed. Do not overwrite, reinitialize, extend, or otherwise mutate that owner.
`docs/workflows/TECH_DEBT.md` D002 owns the related pending-continuation recovery condition:
launch and verify a background waiter for an exact pending CI head, or persist a typed gate with a
resolver and observable resume condition.

## Focused validation

| Check | Result | Evidence |
| --- | --- | --- |
| Shared callout gate | 21 tests passed | `callout-gate-p3-p4.log`: both-host compound-launch and receipt-path mismatch regressions passed |
| Handoff admission | 12 tests passed | `e6c24d5420235d2d-admission-p3-p4-rerun.log`: canonical primary registers, feature-local/temporary lookalikes, and tracked-area debt registers passed |
| Process standards | 23 tests passed | `3f7a05007dd3792a-process-standards-p3-p4.log` |
| Generated synchronization | passed, 554 files from 82 definitions | `cd0a081f5a4abc46-generated-sync-final-clean.log` |
| Generated skill packaging | passed | `62634ff46616030d-skill-packaging-final.log` |
| Source layout | 82-skill expectation passed | `0776b6beed3e88c5-source-layout-82-final.log` |

A combined source invariant run found the stale 81-skill expectation after the new selectable
self-repair skill. Updating it to 82 is the only source-layout change; the narrow rerun passed.

Generated catalog output required a local digest refresh before synchronization. It remains
unstaged, as required. The pre-refresh catalog was preserved in
`8ad78e78955a1734fa75e93905d342e2f83a17f3`; final-review generated output and the supplied
`RESUME_PROMPT.md` are preserved in `cfbe7bf4a4266c908634459e45b5b115c3587519`; the earlier
main-integration preservation stash is `5edfcb10a0a87783409ef42521e6b6df8e335d66`. Do not commit
generated `plugins/*` output or `.agents/catalog/catalog.json`.

## Slice assessment

The shared evaluator, self-repair policy/gate, and both-host cutover must land together: splitting
them would expose contradictory admission or enforcement. Scope remains frozen despite the roughly
1,000 substantive-line review trigger. Runtime scheduling and session-registration expansion remain
out of scope.

## Next action

Commit the frozen-review remediation, then give the parent coordinator the exact commit and focused
artifacts for an immutable incremental review against current `origin/main`. The parent owns final
synchronization, review, publication, and delivery. Do not push from this lease.
