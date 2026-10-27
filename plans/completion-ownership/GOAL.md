# Completion ownership

Authority: Tommy's October 27, 2026 callout identifies the Core closeout workflow as defective after the
plugin-refresh delivery stayed open for separately owned publisher PRs. Repair that reusable boundary in
Core; preserve the existing publishers' ownership and Agent's merged refresh implementation. Core's
recorded standing merge authorization applies after its normal review and validation gates.

Outcome: a verified owned delivery can finish and enter Agent's close decision while preserving independent
follow-up with its owner, next action and scope evidence. A true unmet requirement remains blocking even
when an external owner implements it. Native frontend attribution and termination remain Agent/CLI owned.

Evidence: the originating task requested reviewed refresh PRs and later authorized their merge. Agent
PRs27/28 merged with combined Windows/Linux/host CI success. The completion record nevertheless added
separate publisher PRs20/34 to blocking open_tasks and invented an empty live-publishing acceptance item.
Core's completion contract instructed recording every unresolved PR task, and its exact schema provided
no separate follow-up representation. Its check rejected that record; Agent close was never armed.

Repair: extend the existing completion record with optional follow_up entries, reusing task validation.
Require exact PR/head, owner, next action and scope_evidence; reject overlap with any owned delivery/open
task, including another head of the same PR. Return the follow-up snapshot without claiming fresh forge
state or allowing it to waive acceptance. Clarify the boundary once in persistent-delivery.

Delivery: one focused Core PR from 4688da60304a1f5fe10625f46bfe3a29b5d9ded4 on
Fix/CompletionOwnership at core.worktrees/Fix-CompletionOwnership. Existing PR147 only addresses status
report wording and explicitly excludes completion enforcement; this repair does not change its scope.
Source/runtime is .agents/workflows/completion.py; generated plugins output is refreshed for tests and
excluded from the PR. No new repository, service, module or terminal control implementation is needed.

Verification: baseline rejects the new follow-up record with exit2; repaired checker returns exit0 and
retains its owner/action. Twenty completion tests pass, including the exact two-PR refresh/publisher
case, unchanged blocking conditions and generated-package CLI behavior. Process standards (19), Workflow
session hooks (5), generation freshness, digest check and changed guidance examples pass. Continuation
runtime verification passed all 43 tests, including foreground claim release with independent follow-up.
The repaired checker also reread the actual merged Agent PR27/28 goal and returned both readiness values
true while retaining publisher ownership. Independent frozen review and exact-head Windows/Linux CI are next.

Additional observation retained without widening this repair: the documented source agent_recovery.py
inventory entry raised ModuleNotFoundError for its host adapter. No source or install was changed for
that separate issue. Read-only central session-store inventory found no completion-titled owner; GitHub
also has no existing PR owning this runtime boundary.

Standards applied: Core AGENTS.md and CODE_CONVENTIONS.md, engineering:bugfix, engineering:docs,
engineering:branching, python:modules and python:imports. Reuse the existing completion validator and
continuation integration; do not duplicate Agent's completion or CLI process binding.
