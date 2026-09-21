# Deliver shared Codex agents once per profile progress

- Plan: `GLOBAL_CODEX_AGENT_DELIVERY_PLAN.md`
- Roadmap: none; this repair was authorized directly
- Roadmap item: `global-codex-agent-delivery/profile-agent-delivery`
- Worktree: `C:\Users\tommy\source\repos\base-agents\.worktrees\Docs-Global-Codex-Agent-Delivery-Closeout`
- Branch: `Docs/Global-Codex-Agent-Delivery-Closeout`
- PR: closeout not opened; implementation PR #20 merged as `8d121fc`
- Dependency/package gates: all satisfied; release 2.1.3 is published, installed, and proven profile-wide
- Last reconciled: 2026-09-21 from release `v2.1.3` and the completed sandbox migration

## Current state

PR #20 merged as `8d121fc`, exact main CI run `35654812492` passed, and immutable release `v2.1.3` is
published. The supported Codex marketplace refresh installed and enabled `base`, `engineering`, and
`machine` 2.1.3. Its packaged installer owns and verifies ten canonical profile roles. A fresh ephemeral
Codex session in an unrelated repository with no local `.codex/agents` advertised all ten roles. The ten
authorized stale sandbox copies and their empty directory are removed, and `sandbox-hwid/docs/next-session.md`
records the migration. Only the single automatic successor launch remains.

## Next Steps

Launch exactly one Codex successor in `C:\Users\tommy\source\repos\sandbox-hwid` from its maintained
continuation note, confirm launcher submission, and release this owner. The plan completes when that launch
is confirmed; no base-agents implementation or release work remains.

Scope: whole plan through all remaining phases and terminal delivery.
Current slice: terminal automatic handoff to the authorized sandbox-hwid refactor.
Remaining scope: one successor launch and submission confirmation.
Done when: the merged release is installed and proven profile-wide, only former base-agents project copies are removed, sandbox-hwid records the migration, and its authorized refactor has a successor owner.

## Completed work

- Reconstructed this ledger from the explicit plan and repository evidence before the first deliverable edit.
- Implemented profile delivery, safe migration, profile-aware host probing, host-divergence coverage,
  documentation, catalog refresh, generated packages, and dynamic launcher dependency closure in this commit.
- Delivered PR #20, published release 2.1.3, upgraded the three installed packages, installed and verified
  ten profile roles, proved fresh-session discovery without repository-local roles, and completed the scoped
  sandbox migration without changing unrelated dirty files.

## Verification

Green corrected candidate: generated-output, catalog-digest, and whitespace checks pass; 44 tests under
`tests` pass; all 551 `.agents/hooks/tests` pass with 8 platform skips; and `install.tests.ps1`,
`cli-session-vault.tests.ps1`, `skill-packaging.tests.ps1`, and `handoff-launchers.tests.ps1` pass. The final
exact-head PR and main CI runs passed. The 2.1.3 installer reports `VERIFIED: 10 profile agent(s)`, and the
fresh-session acceptance probe advertised the same ten roles with its local agent directory absent.

## Reviews

The first frozen pass at `db12fd2` was cancelled rather than finalized: its workflow lens proved that the
helper's recorded path digest did not hash the exact `paths.nul` bytes required by `review-lifecycle`.
That invalid pass also exposed filename-only ownership, removed `-ProjectRoot` compatibility, and incomplete
ancestor reparse protection. Those defects are repaired with focused green regressions. The invalid work
order and disposable bundle were removed; no completed watermark was claimed. A new full pass is required
after the fixing commit. The replacement full pass at `00db7c7` found one medium interrupted-apply ownership
gap. Commit `ce94efa` added a pending ownership journal, atomic staged replacement, exact recovery, and the
upgrade/uninstall regression. Its clean incremental pass is approved at `ce94efa`; all findings are resolved.
## Decisions, discoveries, blockers, and deviations

- Codex and Claude deliberately use different host delivery mechanisms while sharing canonical role bodies.
- The installer must install and verify profile roles before deleting any known project-scoped managed copy.
- The initially advertised installed skill source path was stale; the active 2.1.0 package supplied the canonical workflow instructions.
- A filename is not proof of base-agents ownership. Profile mutations now require the installer ownership
  manifest, while legacy project cleanup requires a shipped historical content digest. Unknown collisions
  are preserved; modified owned files stop with an actionable error.
