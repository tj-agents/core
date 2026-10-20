# Repository-declared plugin cutover

Authority: Tommy's 2026-10-20 handoff at ~/.claude/plans/core/handoff-repo-declared-plugins.md.
Commit/push/open PRs; Tommy merges. The handoff supersedes launch-time refresh/self-heal and the
repository's standing auto-merge policy for this goal. No automatic merge binding is armed.

Core PR tj-agents/core#321 at 19bb7b20a4027791f836a0d94f40a37d6d1ac70c is green,
independently reviewed and ready. Sandbox consumer PR tomjseery/sandbox-dotnet#2 at
055b118706c0aaeff1d91355fce50a4b2aeeba43 is green, independently reviewed and ready.
This session merged neither.

Assessment complete: reuse the existing plugin-selection generator and Template integration, native
host operations and core #320's existing updater/setup. Repository settings declare selection and
marketplaces. Native trust, installation, authentication and caches remain host responsibilities.
No new skill, hook, gate or launch-time installer.

Delivered: handoff/open/recovery launch native CLIs without rolling refresh, configuration convergence
or trust rewriting. Acknowledgement, cancellation and cleanup remain. Refresh-cli has a packaged
entry point, native fast default and explicit slow verification. The background Codex updater reads
native effective configuration for exact trusted projects, bootstraps snapshots and follows external
publisher revisions, including stale-catalog selections and superseded publisher recovery.

Windows evidence: a fresh Codex 0.163.0-alpha.1 profile with exact project trust only installed the
declared base plugin from the published unified marketplace; a fresh app-server loaded its five skills
without user declarations. Final-code update/current and verify-only package-byte checks passed.
Normal-profile Claude 2.1.282 handoff/open/recovery verified native SessionStart or history pickup.
Real Codex handoff failed its ACK deadline with native hooks marked modified; trust was not bypassed.

Remaining: sixteen work consumers are prepared and pass adoption/check, but automatic approval review
requires explicit work-commit authority before commit/push/PR. Isolated authenticated Claude acceptance
requires explicitly authorized memory-only OAuth use; no credential was read or copied. Infonetica's
Codex publisher PR #8 has a pre-start GitHub billing failure. Linux native host acceptance remains
unverified; acceptance requires fresh trusted repository-only sessions and real entry-point pickup.
Both Windows and Linux source CI passed for the final core commit; that is separate evidence.

Keep user fallback wiring until merged consumers, actual stale local callers and host acceptance are
reconciled. Original checkouts are preserved. Exact scope, receipts, review proof and unblock actions:
[REPO_DECLARED_CONFIG_PROGRESS.md](REPO_DECLARED_CONFIG_PROGRESS.md) and
[WORK_CONSUMER_MIGRATIONS.md](WORK_CONSUMER_MIGRATIONS.md).
