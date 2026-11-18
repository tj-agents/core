# Weighted default handoff targets

Status: prepared for one independent Codex handoff, 2026-10-12.
Authorization: Tommy explicitly requested a handoff to update handoff conventions so unspecified agent choices select Codex 2/3 of the time and Claude 1/3 of the time. Implement, test, review and deliver this bounded Core standards change through its normal gates. Standing source-owner standards repair authority includes opening and merging the owning PR when those gates pass. No installation in other scopes or mutation of installed caches is authorized.
Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Docs-WeightedHandoffDefaults
Branch: Docs/WeightedHandoffDefaults
Base: freshly fetched origin/main c91b60c955ad4a3f0f7a9383fc20f1c4a6b58510.
PR: not opened.
Lane: L3 for bounded investigation of the existing host-selection contract and its smallest enforceable change. Reroute subsequent phases using engineering:lanes.

## Requested behavior

When the user does not specify an agent or harness, default handoff selection chooses Codex with probability 2/3 and Claude with probability 1/3. Explicit Codex or Claude requests always take precedence. The weighted draw applies to actual handoff selection, not merely advisory prose, and one dispatch must retain its recorded selection across retries or recovery. Use the existing ownership and launcher mechanisms; preserve one successor per transfer, truthful submission and pickup reporting, permissions, and lane selection. Keep both shipped host definitions consistent. Resolve contradictory always-Codex defaults in the relevant shared conventions rather than leaving instructions that defeat the requested mix.

## Existing record and separate owners

The same requirement already has a record in .agents/engineering/policy/lanes/TECH_DEBT.md on Docs/LanesHostSplitDebt, commit e4bbf8f213e8f61178e5cea64539a247cb6c8f79, PR #227 in tj-agents/core. Its title is 'The default delegation host is all-or-nothing instead of a weighted split'. That docs-only owner records debt; this newly authorized implementation owns the repair. Reconcile its actual latest PR/merge state and use that same record, never a duplicate ledger or competing repair. Its recorded requirement includes a reproducible per-dispatch selection and explicit-choice override. Preserve other active Core writers and edits. Assess whether guidance and supporting runtime changes need separate PR slices under git-branching.

The independent headless continuation repair is already submitted to Claude in Fix/HeadlessContinuationTurnRelease. Do not adopt it, its goal, Kit source, Kit continuation or their owned paths. This handoff has its own checkout and outcome.

## Acceptance and validation

Canonical handoff and applicable host-selection conventions express the requested 2:1 default and explicit override. Existing supported runtime selection enforces it where applicable, with meaningful deterministic tests of both draw outcomes, the weighting and explicit requests; avoid flaky distribution sampling. Preserve portability on Windows and Linux. Follow AGENTS.md, CODE_CONVENTIONS.md, SOURCE_LAYOUT.md, packaging and generated-source rules. Update the existing harness manifest if shipped requirements change. Zero comments by default. Use focused tests for changed behavior and required CI on stable delivery candidates; do not run full Windows/Linux checks after each edit. Source tests do not prove installed host acceptance; record limits honestly. Do not install or publish into consuming repositories.

## Pickup context

Only setup and this goal were written here. No implementation, assessment of alternatives, tests or review has occurred. The idea assessment remains pending; perform it once under the existing idea-initialization convention and record it here. The checkout was verified clean at creation, with the exact branch and head above. No open generated-sync branch was returned by the branch-time PR inventory. Routine design delegation is false in .agents/settings.json: configuration.core.auto_merge=true is present, and auto_approve / auto_approve_design are absent. The user explicitly selected the behavior above; implementation choices must remain within that authorization.

## Next Steps

1. Acknowledge pickup here, verify checkout/branch/head and current remote base, and read governing guidance plus the existing debt record and PR #227. Preserve its owner and reconcile any delivery already completed.
2. Enter the owning bounded feature or standards-defect lifecycle. Inspect engineering:handoff, engineering:lanes, session-guidance and their actual routing callers. Complete the once-per-idea assessment, then implement the smallest suitable 2:1 default with explicit-choice precedence and recorded per-dispatch selection. Preserve capability constraints and user choices; identify any genuine unsupported target rather than silently replacing the requested default with all-Codex routing.
3. Validate, independently review the stable source-only candidate, open its owning PR and merge normally once required gates pass. Keep this goal current with actual delivery evidence and reconcile the existing debt record. Leave generated output uncommitted for the main publisher. Finish only this independent session when its authorized outcome is complete.

Codex predecessor stops writing this checkout before launcher invocation. One successful launcher submission proves launch only; the successor records pickup above before deliverable edits. Do not launch another successor because startup is slow.