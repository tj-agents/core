# Standards composition progress

- Plan: `plans/standards-composition/STANDARDS_COMPOSITION_PLAN.md`
- Roadmap: `plans/standards-composition/STANDARDS_COMPOSITION_ROADMAP.md`
- Roadmap item: `standards-composition/scoped-selection`

- Worktree: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Docs-StandardsCompositionPlan
- Branch: Docs/StandardsCompositionPlan
- PR: not opened

## Current state

Requirements/discovery plan authored from inspected core, kit, dotnet, work configuration and unfinished source-owner worktrees. No refactor runtime or live hook changes made. The current slice publishes this plan; the authorized standards goal remains open across later implementation slices. Tommy provisionally prefers shared technical requirements with personal conventions explicitly selected, and requested inspection of the previous implementation before schema decisions.

## Verification

Initial plan graph and diff checks passed. Existing core selection-profile tests passed (11); existing .NET source-layout/profile pin tests passed (3). Documentation review at `500415f5027c37d55b61b27eb1e753f33f790109` passed without retained findings, including native Codex review and parent documentation checks. Frozen documentation reachability passed with zero errors/warnings. The ledger-format correction requires incremental review before publication.

## Reviews

Canonical work order: `reviews/Docs-StandardsCompositionPlan.md`. Documentation review approved `500415f5027c37d55b61b27eb1e753f33f790109`. The configured fresh lens was unavailable, so its bounded check returned to the parent. The plan is not yet implementation-ready for runtime changes; incremental review of the ledger-format correction is pending.

## Decisions, discoveries, blockers, and deviations

Personal plan publication is selected by Tommy; it supplies no work-repository publication authority. Current disabled hooks and other active writer worktrees are preserved. Merged .NET PR24/32 and core PR140 contain real tested separation and a finite-profile adapter; C++ PR37 remains draft. The current .NET routes bypass profile selection, and no production caller of the core adapter was found in inspected source. Existing mechanisms and owners must be reconciled before adding missing consumers. No new handoff is selected.

## Next Steps

Scope: whole plan through all remaining design, implementation, verification and delivery phases, within recorded owner and installation gates.
Current slice: validate, review and merge the requirements/discovery plan to core's main branch.
Remaining scope: resolve the detailed selection design, refactor selected owner contracts and consumers, qualify both hosts, repair personal planning delivery and reconcile the existing auto-merge owner.
Done when: the plan is visible on main for this slice; the whole goal remains incomplete until its completion conditions pass.

1. Review the final ledger-format correction and confirm delivery preflight; the plan graph, diff and reference checks already pass.
2. Publish the reviewed personal plan to main, preserving explicit owner and host gates.
3. Resolve the Phase 1 owner/schema inventory using the existing separation in the same plan, then publish reviewed implementation-ready owner designs before code changes.
