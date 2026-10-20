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

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/machine/scripts/startup_binding.py, plugin_autoupdate.py and refresh_cli.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Committed repository selection with native autoUpdate and native launcher; explicit fast refresh",
      "source": ".agents/machine/scripts/startup_binding.py and refresh_cli.py",
      "mapping": ".claude/settings.json and machine host adapter through .agents/plugins/sources.json",
      "verification": {
        "level": "installed",
        "result": "limited",
        "evidence": "Real normal-profile Windows Claude handoff returned verified SessionStart receipt; source tests pass on Windows and Linux."
      },
      "exception": {
        "constraint_evidence": "Isolated authenticated repository-only acceptance requires explicitly authorized memory-only OAuth use; automatic approval review rejected credential access.",
        "supported_other_host_outcome": "Fresh Windows native Codex profile loaded all five base skills from repository-only declarations after native installation."
      }
    },
    {
      "host": "codex",
      "behavior": "Trusted effective repository selection drives automatic native installation/update; launch waits for native SessionStart receipt",
      "source": ".agents/machine/scripts/plugin_autoupdate.py and startup_binding.py",
      "mapping": ".codex/config.toml and machine package resources through .agents/plugins/sources.json",
      "verification": {
        "level": "installed",
        "result": "limited",
        "evidence": "Real fresh Windows profile installed and loaded base skills, passed verify-only source/cache checks and reported current on second update. Final remediation CI passed on Windows and Linux at 19bb7b20."
      },
      "exception": {
        "constraint_evidence": "Changed installed native hook definitions remain modified, so actual handoff lacked SessionStart ACK. Linux native host session acceptance is unverified.",
        "supported_other_host_outcome": "Normal authenticated Windows Claude handoff returned verified SessionStart ACK without rolling refresh."
      }
    }
  ]
}
```
