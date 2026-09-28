# Claude standards sync before plugin load

Slice of `REPO_DECLARED_CONFIG_PLAN.md` design item 5 and phase 3, for Claude Code only. Codex CLI
synchronization is owned by a separate branch and worktree (`Fix/CodexStandardsSync`).

## Requirement (Tommy, 2026-09-28)

1. After standards are pushed from another PC, the next Claude CLI session on this PC acquires the
   intended standards before it loads plugins.
2. A running session keeps its hooks when Claude replaces a plugin cache directory.

PRs #48 and #59 did not provide either for Claude: #59 snapshots Codex hook packages only.

Authorized scope: implementation, tests, live acceptance on this PC, review, PR and merge on
`Fix/ClaudeStandardsSync`. Not in scope: Codex, consumer adoption, user-scope cleanup.

## Host evidence (Claude Code 2.1.282)

- Plugins load at session start from `installed_plugins.json` and the cache, without network.
  Background auto-update runs only after the first message plus a random delay of up to ten minutes,
  is off by default for non-Anthropic marketplaces, and applies at the next launch
  ([loading reference](https://code.claude.com/docs/en/plugins/loading#when-auto-update-runs)).
  No hook, including SessionStart, can make the first session load newer plugin files.
- `CLAUDE_CODE_SYNC_PLUGIN_INSTALL` applies to `-p` installs, not updates of installed plugins.
- The supported pre-load path is the shell CLI before the session starts:
  `claude plugin marketplace update <name>`, then `claude plugin update <id> --scope <scope>`; the
  new version "loads in your next session"
  ([CLI reference](https://code.claude.com/docs/en/plugins/cli-reference#plugin-update)).
- An update or uninstall writes `.orphaned_at` into the previous version directory and removes it in
  a background cleanup 14 days later, "so a session that already loaded the old version keeps
  running". Hook commands keep the previous path until `/reload-plugins`
  ([cleanup](https://code.claude.com/docs/en/plugins/loading#cleanup-of-previous-versions)).
  Observed here: eight orphaned versions of each core plugin since 2026-09-23 are still on disk.
- This PC's failure: `base-agents` is registered without `autoUpdate`; `base`, `engineering` and
  `machine` are installed at `04d626b3e8ea` (2026-09-26) while `tj-agents/core` main is `531c0fd`.
- `git ls-remote` against the private GitHub remotes costs 2-5 s each through the credential
  helper; each `claude plugin` invocation costs about 3.5 s.

## Design

1. `.agents/machine/scripts/claude_standards_sync.py`, shipped by the machine plugin under
   `resources/machine/scripts/`.
   - Candidates: installs already recorded in `installed_plugins.json` whose scope applies to the
     launch directory (user, managed, or project/local with that project) and that the merged
     user, project and local `enabledPlugins` enable, from marketplaces already registered in
     `known_marketplaces.json` with a git or GitHub source.
   - It never adds a marketplace, installs a plugin, or passes `--yes`, so workspace trust and
     command/`headersHelper` acceptance stay with Claude.
   - Detection: one parallel `git ls-remote` per marketplace against its checkout's origin at the
     registered ref, or the tracked branch. An install is current when the checkout is at the
     remote commit and the install was last reconciled at that commit.
   - Update, serialized by a lock under `~/.agents-state/`: marketplace update when its checkout
     lags, then `plugin update --scope <scope> --json` for each stale install, from the install's
     project directory. State is recorded only after success.
   - Output: silent when current; a start and a result line per updated marketplace; one warning
     when a remote is unreachable or an update fails, naming the version the session will load.
     Launch continues.
2. Launch integration: the typed `claude` command, the `handoff-claude` and `open-claude`
   launchers through `agent-cli.ps1`, and `cli-session-recovery` resume. Each runs the sync before
   starting a session; plain subcommands such as `claude plugin` skip it.
   - Tommy, 2026-09-28: typing `claude` must refresh with no `git pull` or other manual step on any
     developer's machine. The `claude` function therefore ships in the machine plugin
     (`resources/machine/scripts/claude-profile.ps1`), not in a checkout. A machine SessionStart hook
     keeps one fixed, marked block in both PowerShell profiles that loads that script from the
     currently installed `machine@base-agents`, so every later terminal gets the wrapper and the sync
     updates the wrapper along with the rest of the plugin. `BASE_AGENTS_CLAUDE_PROFILE=off` opts out.
3. Running sessions: the host's orphan retention keeps loaded hook paths valid. The sync deletes
   nothing, and `prune_plugin_cache.py --apply` keeps host-orphaned directories younger than
   14 days so it never shortens that window.

## Acceptance

- Automated: fake `claude` executable and local bare remotes cover stale, current, unreachable,
  disabled, foreign-project and failed-update cases, launcher wiring, and prune retention.
- Live on this PC: run the launcher path; installed core plugins move from `04d626b3e8ea` to the
  current main commit; a new session's SessionStart source paths name the new version; this
  already-running session's hooks keep executing from the orphaned directory.

## Limits

- Offline, or a private remote without a stored credential: the session loads what is installed
  and the warning says so.
- Launches that bypass the integrations (desktop app, IDE extension, a raw `claude.exe`, `cmd` or
  Git Bash) keep host behaviour. On a new machine the first session after installing the plugin
  wires the profile; terminals opened after that refresh first.
- A committed project marketplace source or ref change is applied by Claude after workspace trust,
  in the background; that first session needs `/reload-plugins`.
- A plugin whose update needs command or `headersHelper` acceptance is reported, not accepted.
- A session older than 14 days can outlive its orphaned directory.

## Progress

- 2026-09-28: evidence gathered, design recorded.
- 2026-09-28: implemented the script, the four launch integrations and the prune orphan window.
  Focused suites pass: 14 sync tests, 26 prune tests, and `handoff-launchers.tests.ps1` covering both
  packaged launchers, the profile `claude` function and Windows PowerShell session recovery.
- 2026-09-28 live acceptance on this PC, through the launchers' `Sync-ClaudeStandards` against the real
  profile: `--check` found 7 stale marketplaces in 3.9 s. The update moved `base`, `engineering` and
  `machine` from `04d626b3e8ea` to `531c0fdcd90c`, `cpp` 0.4.2 to 0.4.6 and `msvc` 0.3.2 to 0.3.3
  (first run 202 s; the rerun was silent, exit 0, 4.4 s). A new `claude -p` session's init listed
  `cache/base-agents/*/531c0fdcd90c`, `cpp/0.4.6` and `msvc/0.3.3`. This running session kept executing
  its hooks from `04d626b3e8ea`, which the host had marked `.orphaned_at` and kept.
- The first live run found that `~/.claude` is itself a git repository here and the official
  marketplace is a downloaded copy with no `.git`; `git -C` read the enclosing repository. Marketplaces
  whose location is not its own checkout are now left to the host, with a regression test.
- 2026-09-28: PR #61 merged at `3a647a5`. The next refresh moved core `531c0fd` to `3a647a5` in 29 s,
  and the installed machine plugin now ships the refresher. That installed copy, run in `winwrap`,
  moved the project-scope cpp installs 0.4.2 to 0.4.6, and a new session loaded
  `base-agents/*/3a647a5014c0`. Result lines now label project and local installs, which printed
  as duplicates.
- Remaining on this PC, awaiting Tommy: the profile still loads the retired `base-agents` checkout at
  `71afb60`, whose uncommitted `shell/cr.ps1` change is his and whose `claude` function predates this
  work. The primary `tj-agents/core` checkout cannot fast-forward past its own uncommitted plan edits and
  untracked roadmap. Once he settles those, `git pull` there and `install.ps1` rewire the bare `claude`
  command; the launchers and session recovery already refresh through the installed plugin.
