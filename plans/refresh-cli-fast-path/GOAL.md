# Get merged tj-agents standards into Claude sessions in seconds, automatically

Source request: `~/.claude/plans/tj-agents/refresh-cli-fast-path-handoff.md` (Tommy, 19 Oct 2026).
Authorized: implement, test and commit locally on `Fix/RefreshCliFastPath`. Pushing or opening a PR
needs Tommy's go-ahead. No new skill. Claude first; Codex goes to one `machine:handoff-codex` (L3).

## Evidence (19 Oct 2026, Claude Code 2.1.282, this PC)

- `refresh_cli.py` default path: six `claude plugin marketplace update` calls (39 s serial), then the
  full rolling `run_session` (fetch every selected repository, native install of every changed package
  in a disposable profile, promote, `plugin list`, pin, prune). That step ran 70 s and then failed
  with Node `ENOMEM`. Nothing prints until a final JSON report.
- The marketplace update is useless for "core merged": every catalog entry is `git-subdir` at
  `ref: main`, so the catalog does not change when a source repository merges.
- Native `claude plugin update <id> --scope user --json` installs the source's current main for these
  entries in about 20 s per plugin (two in parallel took 37 s, so parallelism buys nothing). It names
  the install `<sha12>-<path hash>` and records the full `gitCommitSha`.
- Native auto-update runs once per interactive session, up to ten minutes after the first message
  ([loading reference](https://code.claude.com/docs/en/plugins/loading#when-auto-update-runs)). It never
  rechecks a long-running session. Only the user can run `/reload-plugins`.
- PR 311 (merged 12:26 today, session `fix-livesessionpluginrefresh-8d`) added the UserPromptSubmit
  `plugin_generation.py` gate: it tells a session its machine root is superseded by a newer *recorded*
  generation and asks the user to `/reload-plugins`. It treats a native `<sha12>-<hash>` root as
  "no verifiable generation", and native installs never write the generation record.
- The SKILL.md path `<skill-directory>/../../resources/...` resolves correctly only from the plugin's
  `skills/refresh-cli/` entry point; from the shared `.agents/machine/utility/refresh-cli/` body it
  points nowhere. The same wording is in eight other machine skills.

## Decisions

1. Fast path is the default and uses the native update. `refresh_cli.py` reads the registry and
   enabled set locally, resolves each owned source repository's `main` once with parallel
   `git ls-remote`, and runs `claude plugin update <id> --scope <scope> --json` only for stale
   installs, printing one progress line per step to stderr. It holds the rolling host lock so it never
   races a launcher's refresh, then records the installed revisions in the host's generation record so
   every running session's gate reports them. No marketplace update.
2. Refresh is event-driven, never polled (Tommy, 19 Oct: no timer). The merging session runs the fast
   path as soon as the merge's publication is on main (`engineering:merge` Step 6, `merge-docs` Step 7);
   the launcher still refreshes every new session. `refresh-cli` by hand is the last resort. Each open
   session's PR 311 gate then states the superseded generation at its next prompt. `/reload-plugins`
   stays with the user: Claude runs it only when typed, or when the `/plugin` panel closes with changes,
   and refuses it over remote connections. Native `autoUpdate` stays off: a second background writer
   would race the launcher's registry repoint.
3. The gate accepts a native install root: its revision is the registry record's `gitCommitSha` for
   that `installPath`.
4. `--full` keeps the old verified refresh and repair (marketplace update, rolling launch, registry
   repair), and now prints each stage as it starts. `--verify-only` is unchanged and accepts native
   installs whose `gitCommitSha` is main.
5. SKILL.md names the script from the plugin root, defined as the directory that holds
   `.claude-plugin/` or `.codex-plugin/`. The eight sibling machine skills get the same fix.
6. Codex in the fast path: it has no in-process reload, and its launcher binds `main` at every launch.
   The fast path reports that for Codex and does nothing else. The remaining Codex decision goes to
   one Codex L3 handoff.

7. A Claude launch's rolling prune keeps a non-SHA (native update) install for 14 days, the host's own
   retention, because a session that reloaded onto it is not in any pin.

## Acceptance

- Unit tests: stale vs current selection, native update invocation and scope, lock, generation record
  written only after success, offline `ls-remote` failure, background throttle, gate accepts a native
  root by `gitCommitSha`, verify accepts native installs.
- Native: run the fast path on this PC against the real registry. It must finish in seconds when
  current and print progress. A gate run with `CLAUDE_PLUGIN_ROOT` set to a native root must not
  report "no verifiable generation".

## Progress

- 2026-10-19: investigation complete (above). Worktree
  `core/.worktrees/Fix-RefreshCliFastPath` from origin/main `281303c3`.
- 2026-10-19: decisions 1-7 implemented. Native acceptance on this PC: current case 2.7 s; a stale
  `base@tj-agents` (forced to `dc1f7415`) natively updated to `281303c3` in 15 s with progress lines; the gate
  is silent for the native root and reports the old root with the `/reload-plugins` instruction.
  Unit tests: refresh, gate and prune cases pass.
- Next: commit locally; Tommy decides push/PR. Codex side handed to one Codex L3 session.
