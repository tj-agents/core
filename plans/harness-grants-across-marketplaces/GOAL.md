# Goal — apply harness permission grants from every tj-agents marketplace

## Defect

`harness_permissions_sync.py` only discovers `base-agents` packages: Claude roots are filtered to
`installed_plugins.json` identities ending `@base-agents`, Codex roots to `plugins/cache/base-agents`, and
the Codex rules land in `base-agents.rules`. Grants declared in any other tj-agents marketplace's
`harness.json` (`work-agents/work`, `infonetica/infonetica`, react, dotnet, …) never reach host settings.

Observed 2026-10-08: posting a pending GitHub review for `draft-comment` was refused by Claude Code's
auto-mode classifier as an unapproved external write. The grant belongs in `work-agents/work`'s
`harness.json` (companion goal: `tj-agents/work` branch `Fix/PendingReviewGrant`), but this sync would ignore it.

## Required behaviour

The sync applies `requires.permissions` from every installed plugin whose marketplace source repository
is owned by `tj-agents`, on both hosts. A plugin from any other owner is never read: an allow rule is a
trust grant. Keep the sidecar contract (user-authored rules are never touched, removed grants are
withdrawn) and the `--apply` / `--check` / `--print` behaviour.

## Authorization

Tommy's explicit request (2026-10-08) plus the standing standards-defect authorization. Covers editing,
tests, commit, push and opening the PR. Merging is Tommy's.

## Checkout

`C:\Users\TommySeery\source\repos\tj-agents\core.worktrees\Fix-HarnessGrantsAcrossMarketplaces`, branch
`Fix/HarnessGrantsAcrossMarketplaces` off `origin/main` `ab32149`.

## Next Steps

1. Read the sync, its tests and how Claude's `known_marketplaces.json` and the Codex marketplace config
   record each marketplace's source repository. Derive trust from that, not from a hardcoded name list.
2. Implement, update the packaged copies via the repository's generation step, add tests for: a
   `tj-agents` non-base marketplace's grant applied, a foreign marketplace's grant ignored, and a removed
   grant withdrawn on both hosts.
3. Run the repository's test suite, commit, push, open the PR. Do not merge.

Lane: L4 (specified implementation with code-level judgement). The trust boundary above is decided.

## Progress

- 2026-10-08: goal written and Codex launched by the cris-preaward-app review session.
- 2026-10-08: implemented marketplace-source trust discovery for Claude and Codex. Installed packages from every GitHub marketplace owned by `tj-agents` now contribute harness grants; foreign marketplaces and unregistered Codex cache entries do not.
- 2026-10-08: added cross-marketplace application, foreign-marketplace rejection, and grant-withdrawal coverage for both hosts. Focused suite (19 tests), full Python suite, shared-runtime suite, generation, catalog and manifest checks, and local PowerShell CI suites passed. The CLI recovery vault suite passed on a fresh isolated retry after one non-reproducing timing-bound failure.
