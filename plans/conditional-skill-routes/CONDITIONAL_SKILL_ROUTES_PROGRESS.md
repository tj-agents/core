# Conditional skill routes — progress

- Plan: `plans/conditional-skill-routes/CONDITIONAL_SKILL_ROUTES_PLAN.md`
- Roadmap: `plans/conditional-skill-routes/CONDITIONAL_SKILL_ROUTES_ROADMAP.md`
- Roadmap item: `conditional-skill-routes/required-and-conditional-tiers`

Status: in progress (2026-09-27, Claude). Slice 1 committed; slice 2 (command routes) next.

Worktree: `.worktrees/Feature-Conditional-Skill-Routes` (core).
Branches: `Feature/ConditionalSkillRoutes` (slice 1, requirements 1-5); `Feature/CommandSkillRoutes`
(slice 2, requirement 7, stacked on slice 1); `tj-agents/cpp` branch for requirement 6 after slice 1.
PRs: none yet.

## Current state

- Slice 1: route `conditional: [{skill, when}]` tier; `skills` stays required. The router blocks only on
  unproven required skills, advises conditional ones once per route per session (Claude: PreToolUse
  `additionalContext` on an allowed call; Codex: only inside a block, recorded in
  `.agents/plugins/TECH_DEBT.md`). Malformed conditional entries make the table unusable (the router's
  existing fail-closed policy for an opted-in table; the plan's "fail-open" wording did not match the code).
  Schema documented in the `skill-routes` contract. Tests: `.agents/hooks/tests/test_skill_router_tiers.py`.
- Verification: `tests/` 189 OK; `.agents/hooks/tests` 616 run, 2 failures in
  `test_merge_review_gate.CanonicalEnvelopeShellTests` only under Git Bash (it derives `bash.exe` from a
  `git` on PATH that resolves to `mingw64/bin`); the same class passes under PowerShell, which CI uses.
- Authorization covers implementation, tests and opening the core and C++ PRs. It does not
  authorize merging, publishing, or hand-editing generated consumer routes.

## Reviews

- The initial plan entered documentation review as part of the repo-declared configuration
  branch at `1f69967`; PLAN1 required this companion ledger and roadmap.

## Next Steps

Scope: current slice only; full plan remains incomplete.
Current slice: open the slice 1 PR, implement requirement 7 on the stacked branch and open its PR, then
implement requirement 6 in tj-agents/cpp and open its PR naming the core dependency.
Remaining scope: merge/publication and generated consumer-route adoption remain unauthorized.
Done when: all three PRs are open, locally verified, and their links and exact review state are recorded here.
