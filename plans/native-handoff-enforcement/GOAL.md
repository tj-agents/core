# Enforce native source-owner handoffs after a repeat-prevention callout

## Authorization

This is a bounded standards-defect repair under `engineering:session-guidance`'s standing authorization. It may implement, test, review, publish, and merge the shared tj-agents repair once required checks pass.

## Scope

When a user says that an agent mistake must never happen again, treat it as a standards-repair callout even if they do not repeat the words `standard`, `skill`, or `workflow`. The required repair remains a genuine native `engineering:handoff` side-workstream: a distinct worktree, a source-owner goal, a launcher invocation, and its paired structured receipt. An in-process worker, an answer, a bare success line, or an asserted handoff must not discharge it.

## Findings

`callout_repair_gate.py` only recognizes a narrow mistake-plus-standards phrase. A direct repeat-prevention callout such as “this can never happen again” can therefore miss the callout gate. Its existing launcher validation also does not prove that the worktree differs from the originating checkout and accepts a human-readable success line without the launcher's receipt.

## Execution

Lane: L4 — this is a specified, testable enforcement change with small local judgement.

1. Extend callout detection to cover repeat-prevention wording while preserving explicit user limits and feedback-only requests.
2. Persist the originating checkout and require a successful source-owner launcher to target a distinct checkout.
3. Add focused regression coverage for both cases.
4. Run focused tests, review, required generation/validation, deliver the PR, and merge under the recorded authority.

## Completion

The plugin blocks a repeat-prevention callout from being treated as resolved until a real isolated native source-owner handoff succeeds, and the regression suite proves it.

## Progress

Implemented the callout gate repair. The gate now recognizes explicit repeat-prevention wording, records the originating checkout, and only releases after a structured launcher receipt points to a distinct, Git-verifiable source-owner checkout. A bare success line is an unconfirmed safe fallback and cannot be claimed as a handoff. Focused repeat-prevention, same-checkout rejection, bare-confirmation rejection, successful receipt, and native Codex transcript tests pass; `test_process_standards.py` also passes.

## Next Steps

Run repository generation and validation, review the committed candidate, then deliver and merge it.
