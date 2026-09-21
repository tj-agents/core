# Deliver shared Codex agents once per profile progress

- Plan: `GLOBAL_CODEX_AGENT_DELIVERY_PLAN.md`
- Roadmap: none; this repair was authorized directly
- Roadmap item: `global-codex-agent-delivery/profile-agent-delivery`
- Worktree: `C:\Users\tommy\source\repos\base-agents\.worktrees\Fix-Global-Codex-Agent-Delivery`
- Branch: `Fix/Global-Codex-Agent-Delivery`
- PR: not opened
- Dependency/package gates: install and verify the merged release locally before removing project-scoped agents
- Last reconciled: 2026-09-21 from the green uncommitted implementation candidate based on `b62a8ed`

## Current state

The uncommitted candidate installs canonical Codex roles into the resolved profile, verifies them before
optional managed-project cleanup, and makes the host runtime probe profile and intentional project surfaces.
Claude remains plugin-native. Generated packages and catalog digests are current. Current origin/main and
the installed 2.1.0 machine package already contain the shared launcher resource; dynamic generated-layout
coverage now guards every `agent-cli.ps1` consumer.

## Next Steps

Commit the green implementation candidate, run independent review over that immutable head, resolve any
findings, and complete full delivery. After merge, install and verify the released profile roles before the
scoped sandbox migration and successor handoff.

Scope: whole plan through all remaining phases and terminal delivery.
Current slice: commit and independently review the locally green release candidate.
Remaining scope: PR/CI/merge, local release installation and fresh-session proof, sandbox cleanup, and automated return.
Done when: the merged release is installed and proven profile-wide, only former base-agents project copies are removed, sandbox-hwid records the migration, and its authorized refactor has a successor owner.

## Completed work

- Reconstructed this ledger from the explicit plan and repository evidence before the first deliverable edit.
- Implemented profile delivery, safe migration, profile-aware host probing, host-divergence coverage,
  documentation, catalog refresh, generated packages, and dynamic launcher dependency closure in this commit.

## Verification

Green candidate: `pwsh .agents/sync-generated.ps1 -Check`; 42 tests under `tests`; 547 tests under
`.agents/hooks/tests` with 8 platform skips; `cli-session-vault.tests.ps1`, `skill-packaging.tests.ps1`, and
`handoff-launchers.tests.ps1` all pass.

## Reviews

No review candidate yet.

## Decisions, discoveries, blockers, and deviations

- Codex and Claude deliberately use different host delivery mechanisms while sharing canonical role bodies.
- The installer must install and verify profile roles before deleting any known project-scoped managed copy.
- The initially advertised installed skill source path was stale; the active 2.1.0 package supplied the canonical workflow instructions.
