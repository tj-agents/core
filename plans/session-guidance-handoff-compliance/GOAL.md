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
- A launch counts only when a paired native launcher call has a successful result containing a
  structured `agent-handoff-submitted` receipt. The receipt must load a goal whose repair workflow,
  source owner, session, callout id, and prompt SHA-256 bind to that exact callout. Intent, echo,
  unpaired output, failed output, a stale receipt, or a mismatched goal cannot release it.
- A current typed disposition is revalidated for every pending obligation and is not cached as
  completion. A successful native launch can be cached only after its exact binding is verified.
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
| Shared callout gate | 19 tests passed | workflow artifact `047202e68c1e7109-callout-gate-green.log` covered the preceding 18-test checkpoint; final local run added receipt-free and nonce-mismatch regressions |
| Handoff admission | 10 tests passed | final local focused run |
| Process standards | 23 tests passed | final local focused run after moving detailed authority to self-repair |
| Generated synchronization | passed, 554 files from 82 definitions | `cd0a081f5a4abc46-generated-sync-final-clean.log` |
| Generated skill packaging | passed | `62634ff46616030d-skill-packaging-final.log` |
| Source layout | 82-skill expectation passed | `0776b6beed3e88c5-source-layout-82-final.log` |

A combined source invariant run found the stale 81-skill expectation after the new selectable
self-repair skill. Updating it to 82 is the only source-layout change; the narrow rerun passed.

Generated catalog output required a local digest refresh before synchronization. It remains
unstaged, as required. The pre-refresh catalog was preserved in
`stash@{0}` (`repair-199-generated-catalog-before-sync`); the earlier main-integration preservation
stash remains `stash@{1}` (`temporary-pr199-main-integration-20261013`). Do not commit generated
`plugins/*` output or `.agents/catalog/catalog.json`.

## Slice assessment

The shared evaluator, self-repair policy/gate, and both-host cutover must land together: splitting
them would expose contradictory admission or enforcement. Scope remains frozen despite the roughly
1,000 substantive-line review trigger. Runtime scheduling and session-registration expansion remain
out of scope.

## Next action

Freeze the authored local commit for independent review against current `origin/main`. The parent
coordinator owns final synchronization, review, publication, and delivery. Do not push from this
lease.
