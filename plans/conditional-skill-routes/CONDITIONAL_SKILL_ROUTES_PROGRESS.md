# Conditional skill routes — progress

- Plan: `plans/conditional-skill-routes/CONDITIONAL_SKILL_ROUTES_PLAN.md`
- Roadmap: `plans/conditional-skill-routes/CONDITIONAL_SKILL_ROUTES_ROADMAP.md`
- Roadmap item: `conditional-skill-routes/required-and-conditional-tiers`

Status: planned; implementation has not started (2026-09-27).

Worktree: none; the planning artifact is being checkpointed with the active repo-declared
configuration branch before this separate workstream receives its own branches.
Branch: none.
PRs: none.

## Current state

- The generic core schema/router work and the C++ policy/generator work are designed in the
  companion plan.
- Existing route files remain backward-compatible and continue treating every `skills` entry
  as required until a stack pack regenerates them.
- Authorization covers implementation, tests and opening the core and C++ PRs. It does not
  authorize merging, publishing, or hand-editing generated consumer routes.

## Reviews

- The initial plan entered documentation review as part of the repo-declared configuration
  branch at `1f69967`; PLAN1 required this companion ledger and roadmap.

## Next Steps

Scope: current slice only; full plan remains incomplete.
Current slice: create a core branch for requirements 1–5, implement and test the generic route
schema/router behavior, open its PR, then create the dependent C++ branch for requirement 6 and
open its PR with the dependency recorded.
Remaining scope: merge/publication and generated consumer-route adoption remain unauthorized.
Done when: both PRs are open, locally verified, and their links and exact review state are recorded here.
