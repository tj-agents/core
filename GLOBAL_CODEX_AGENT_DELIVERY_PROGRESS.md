# Deliver shared Codex agents once per profile progress

- Plan: `GLOBAL_CODEX_AGENT_DELIVERY_PLAN.md`
- Roadmap: none; this repair was authorized directly
- Roadmap item: `global-codex-agent-delivery/profile-agent-delivery`
- Worktree: `C:\Users\tommy\source\repos\base-agents\.worktrees\Fix-Global-Codex-Agent-Delivery`
- Branch: `Fix/Global-Codex-Agent-Delivery`
- PR: not opened
- Dependency/package gates: install and verify the merged release locally before removing project-scoped agents
- Last reconciled: 2026-09-21 from the green release 2.1.3 merge candidate over `origin/main` at `6dbee6d`

## Current state

The candidate installs canonical Codex roles into the resolved profile, records files it actually owns,
verifies them before digest-proven managed-project cleanup, and makes the host runtime probe profile and intentional project surfaces.
Claude remains plugin-native. Generated packages and catalog digests are current. Current origin/main and
the installed 2.1.0 machine package already contain the shared launcher resource; dynamic generated-layout
coverage now guards every `agent-cli.ps1` consumer. The candidate includes origin/main's portable digest
repair. Origin/main published a separate UTF-8 bootstrap repair as 2.1.2 before review, so this candidate now
includes that baseline and advances the package set to immutable release 2.1.3.

## Next Steps

Review and push the Windows CI assertion fix to PR #20, monitor its exact head, and merge the approved
candidate when green. After merge, install and verify the released profile roles before the
scoped sandbox migration and successor handoff.

Scope: whole plan through all remaining phases and terminal delivery.
Current delivery sequence: CI portability fix and incremental watermark, then PR/CI/merge delivery.
Remaining scope: PR/CI/merge, local release installation and fresh-session proof, sandbox cleanup, and automated return.
Done when: the merged release is installed and proven profile-wide, only former base-agents project copies are removed, sandbox-hwid records the migration, and its authorized refactor has a successor owner.

## Completed work

- Reconstructed this ledger from the explicit plan and repository evidence before the first deliverable edit.
- Implemented profile delivery, safe migration, profile-aware host probing, host-divergence coverage,
  documentation, catalog refresh, generated packages, and dynamic launcher dependency closure in this commit.

## Verification

Green corrected candidate: generated-output, catalog-digest, and whitespace checks pass; 44 tests under
`tests` pass; all 550 `.agents/hooks/tests` pass with 8 platform skips; and `install.tests.ps1`,
`cli-session-vault.tests.ps1`, `skill-packaging.tests.ps1`, and `handoff-launchers.tests.ps1` pass. The final
actionable-error wording was followed by two focused ownership/collision tests and another generation and
catalog check. The committed-source revision digest gate is intentionally rerun after this working tree is
committed because it validates `HEAD`, not uncommitted content.

## Reviews

The first frozen pass at `db12fd2` was cancelled rather than finalized: its workflow lens proved that the
helper's recorded path digest did not hash the exact `paths.nul` bytes required by `review-lifecycle`.
That invalid pass also exposed filename-only ownership, removed `-ProjectRoot` compatibility, and incomplete
ancestor reparse protection. Those defects are repaired with focused green regressions. The invalid work
order and disposable bundle were removed; no completed watermark was claimed. A new full pass is required
after the fixing commit. The replacement full pass at `00db7c7` found one medium interrupted-apply ownership
gap. Commit `ce94efa` added a pending ownership journal, atomic staged replacement, exact recovery, and the
upgrade/uninstall regression. Its clean incremental pass is approved at `ce94efa`; all findings are resolved.
The first PR #20 run then exposed a Windows-only test assertion coupled to exact temporary-path rendering;
all preceding gates passed and the installer operations themselves completed. The active fix asserts the
semantic profile `ADD` precedes the project `REMOVE` without depending on the rendered root path.

## Decisions, discoveries, blockers, and deviations

- Codex and Claude deliberately use different host delivery mechanisms while sharing canonical role bodies.
- The installer must install and verify profile roles before deleting any known project-scoped managed copy.
- The initially advertised installed skill source path was stale; the active 2.1.0 package supplied the canonical workflow instructions.
- A filename is not proof of base-agents ownership. Profile mutations now require the installer ownership
  manifest, while legacy project cleanup requires a shipped historical content digest. Unknown collisions
  are preserved; modified owned files stop with an actionable error.
