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

## Current M014 recurrence - 2026-10-14

Repair workflow: engineering:self-repair
Source owner: tj-agents/core engineering callout-repair invocation and enforcement
Originating session: 01a13725-d930-7340-8425-8eca8d8e37f0
Callout nonce: local-incident-20261014-M014-session-registration (no current hook-issued nonce was observed)
Callout prompt SHA-256: 0939eb3378682b024a6368de3058a6911d33745b199e6bb1b58ed9e06a569764
Canonical record: C:/Users/TommySeery/source/repos/tj-agents/core/MISTAKES.md#M014
Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-NativeHandoffEnforcement
Branch: Fix/NativeHandoffEnforcement
PR: https://github.com/tj-agents/core/pull/196
Exact existing native owner: 01a12abb-8562-7f83-abb8-4401ab40e82b, recorded exited on 2026-10-14.
Local writer budget: one source owner; the originating parent owns only recording, cancellation and user dialogue.

The originating Core session diverted into unrelated career work, read self-repair in full after a scope callout, then answered normally and continued unrelated execution without recording or a repair handoff. The user repeatedly identified this as exactly the failure self-repair exists to prevent. This is an ignored explicit instruction. The installed callout state's latest prompt remained an old unrelated prompt with pending=false; the cause of missing interception is unknown. Do not declare it a missing rule or rewrite the skill simply to restate existing instructions.

Standing standards-repair authority and Tommy's explicit request cover diagnosis, bounded implementation, tests, review, delivery and publication once real gates pass. This extends the existing causal callout repair and its existing PR, not a new unrelated source rewrite. Preserve all source/PR ownership. The current worktree has generated/catalog modifications and an untracked review; do not discard or commit generated distribution files. Fetch and reconcile its stale actual base before source edits; preserve its own implementation. PR199 is already merged. Read current README, CODE_CONVENTIONS and relevant canonical contracts before selecting the correction.

First acknowledge exact-session recovery here and inspect this M014 recurrence. Trace actual event delivery, input parsing, mistake detection, pending-state persistence and tool/Stop interception on Codex and Claude. Establish a reproducing case for a callout received after an earlier user prompt, and for an agent reading self-repair but resuming unrelated work or a normal final response without the required record/transition. Distinguish absent invocation from parser/detection defects, and preserve explicit user stop/answer-only limits. A local nonce above is an incident locator only; do not treat it as a runtime gate nonce or manipulate persisted gate state to claim success.

Scope remains callout repair and its observed host boundary. Coordinate any overlap with other active repairs before source writes. Publish the new main M014 record through a separate scoped docs PR (preserve other dirty primary records); local notes or promises do not establish publication. Parent's original SQLite registration PR247 is already merged and must not acquire unrelated source changes. Do not touch career or employer projects, launch extra independent sessions, install profiles, or close any other CLI.

Investigation lane: L3, unresolved actual host enforcement cause. Reselect implementation/review lanes under the canonical table after diagnosis. Report truthful limited host acceptance if real fixtures/installed observations are unavailable; do not falsely resolve M014.

## Next Steps

Acknowledge recovery in this goal, inspect the canonical M014 recurrence and trace the current installed callout state against the native originating transcript. Diagnose and reproduce the missed self-repair invocation, integrate the bounded correction with this existing PR, validate and review both-host behavior, publish the scoped record independently, and deliver the authorized source repair. Do not resume unrelated career work.
