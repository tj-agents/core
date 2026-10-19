# Repository-declared plugin configuration

Authority: Tommy's 2026-10-20 handoff at
`~/.claude/plans/core/handoff-repo-declared-plugins.md`. Commit, push and open reviewed green PRs;
Tommy merges. The handoff supersedes this plan's previous launch-time refresh, self-heal and
blocking enforcement design.

Every repository commits its marketplace sources and selected plugins. Claude uses
`.claude/settings.json` with `extraKnownMarketplaces`, `autoUpdate: true` and `enabledPlugins`.
Codex uses trusted-project `.codex/config.toml` where supported. Native installation, trust,
credentials and derived caches remain host responsibilities. Record unsupported host behavior.

Use the existing `machine:plugin-selection` generator and Template's new-repository integration.
No new skill, hook, gate or launch-time installer. Automatic updates use Claude's native updater
and core PR #320's scheduled Codex updater. One-time machine setup belongs in `setup.ps1`.

Current scope:

1. Verify native project marketplace discovery, installation and fresh loading independently,
   using empty user plugin declarations. Keep the exact installed host version with each result.
2. Remove rolling refresh, generation, installation, trust rewriting and configuration convergence
   from handoff, open and recovery launchers. Preserve existing handoff acknowledgement and pickup.
3. Give `refresh-cli` a stable skill-local script entry, native fast default and explicit slow verification.
4. Reconcile current Template and consumer mains before migrating declarations. Migrate remaining
   Concertable, Infonetica and other known consumers through their owning repositories.
5. Remove superseded user declarations and legacy marketplaces only after all actual consumers
   have migrated and passed acceptance. Preserve unrelated user settings, credentials and caches
   used by live sessions.
6. Independently review, validate Windows/Linux CI, push and leave PRs ready for Tommy to merge.

Acceptance: a fresh Windows session in a migrated repository loads declared plugins without user
marketplace/plugin declarations. Linux is verified or recorded as incomplete with its exact acceptance
condition. Generated settings and passing unit tests alone do not establish installed-host acceptance.

Progress and dependencies: [REPO_DECLARED_CONFIG_PROGRESS.md](REPO_DECLARED_CONFIG_PROGRESS.md).
Native evidence: [CUTOVER.md](CUTOVER.md).
