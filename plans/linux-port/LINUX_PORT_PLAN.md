# Linux port of the machine utilities

## Outcome and scope

Every machine utility and launcher in core works on Linux and Windows from one Python implementation.
Each skill keeps its name; its PowerShell script is replaced by a Python script in the same skill folder,
and the `.ps1` is deleted in the same PR that ports it. No parallel copies, no renames.

Out of scope: `.agents/sync-generated.ps1` and the repository's own test and install tooling, which are
repo maintenance rather than shipped behaviour and already run under pwsh on Linux.

## Authorization

The user authorized the whole port, one PR per step, including review and merge of each step
(2026-10-05/06). Each step ends merged before the next starts. Independent steps may run in parallel
on separate branches; each still lands as its own reviewed PR.

## Decisions and evidence

- Python, not pwsh: every hook already requires Python; pwsh would be an extra Linux dependency.
- Launchers open a tab, never a window. Detect the terminal we run inside and use its own new-tab command:
  `WT_SESSION` -> the existing `wt.exe --window 0 new-tab` path with its argument escaping; `TMUX` ->
  `tmux new-window`; `KITTY_WINDOW_ID` -> `kitty @ launch --type=tab`; `KONSOLE_DBUS_WINDOW` -> Konsole
  D-Bus `newSession`. Only with no terminal detected: open a new window and print a warning.
- On POSIX the environment changes travel inside the launched command
  (`sh -c 'cd "$1" && shift && exec "$@"' sh <dir> env -u ... AGENT_CLI_TAB_TITLE=<t> <exe> <args>`), because a
  tab is started by the terminal's own process. Launch detached with stdio on `/dev/null`. Never force or
  clear `TERM` on POSIX.
- The launched CLI always gets normal colour: `NO_COLOR` is in the cleared session environment.
- Kitty reaches its window over `listen_on unix:/tmp/kitty-{kitty_pid}` with
  `allow_remote_control socket-only`, in the user's dotfiles (tomjseery/dotfiles `a908963`). Only kitty
  processes started after that change have the socket.
- Catalog digests are generated output. PRs leave them uncommitted; CI's guard rejects them (step 1).
- On Windows with no detected terminal but `wt.exe` present, keep today's `wt.exe --window 0 new-tab`:
  still a tab, in the most recently used Windows Terminal window (user decision, 2026-10-06).
- The Windows Terminal handler runs only on Windows; `WT_SESSION` reaching WSL through `WSLENV` is ignored.

## Steps and acceptance criteria

Every step: tests pass, `pwsh .agents/sync-generated.ps1 -Check` passes, reviewed, merged; the PR lists
what still needs checking on Windows.

- [x] Shared library `.agents/machine/scripts/agent_cli.py`: environment scrub, Claude/Codex executable
  discovery, standards sync, lane lookup, Windows Terminal argument escaping (#106).
- [x] Kitty remote control in dotfiles, verified from a fresh kitty.
- [x] 1. CI guard rejects committed catalog digests, so concurrent PRs stop conflicting on them (#107).
- [x] 2. `open-claude` -> `scripts/open_claude.py` with the tab handlers; SKILL.md updated; `.ps1`
  deleted. Verified by opening a real tab in kitty on this machine (#108).
- [x] 3. `handoff-claude` -> Python, then `handoff-codex` -> Python (`codex_marketplace_sync.ps1` with it).
  `engineering:handoff` works on Linux from here; verified with a real handoff.
- [ ] 4. Terminal start hooks: `claude-profile.ps1`/`claude_terminal_profile.py` and `codex-profile.ps1`
  refresh standards when `claude`/`codex` is typed, wired for bash as well as PowerShell (looking for
  both `python3` and `python`); `agent-cli.ps1` deleted.
- [ ] 5. `peer-cli` -> Python: `close.py` and `finish.py` (with `finish_reaper`/`session_close` ported) let
  a merged session on Linux remove its linked worktree and branch, clear its merge-cleanup obligation,
  record verified session exit, and close its own kitty/tmux/Konsole tab; `merge_cleanup_gate`'s message
  gives the per-platform Python commands. Verified by a real merge on Linux whose own tab closes itself.
  Linux can remove a worktree out from under a live cwd, so the reaper may only be needed for the tab
  close -- confirm before porting it. Then the rest of `peer-cli` (list and close in the detected
  terminal); `reap_orphans.py` stops assuming `wt.exe` is the parent.
- [x] 6. `clip` -> Python, using the platform clipboard (#125).
- [ ] 7. `persistent-workflow`'s `delivery-continuation.ps1` -> Python, verified on Linux.
- [x] 8. Tests that failed only on Linux pass: POSIX shell collapsed the Codex snapshot loader's escaped
  backslashes into NULs (now embedded as base64); a test plugin URL only git on Windows resolves; pwsh 7
  `Split` binding skipped the installer's ancestor reparse-point check (#160).
- [x] 9. CI runs the generated-tree checks and both Python suites on Linux as well as Windows
  (`verify-linux`, #162); it blocks a PR once the repository ruleset lists it as a required check,
  which awaits the user's decision after a few green runs.
- [ ] 10. Shipped instructions follow `CODE_CONVENTIONS.md`'s Supported platforms: no shipped Markdown
  under `.agents/`, `.claude/` or `.codex/` tells an agent to run bare `python`, `powershell.exe`, `pwsh`
  or `wt.exe` without naming the platform (including the session exit in `merge` Step 5 and in
  `merge-docs`' Report), every unported skill says it is Windows-only, and the PowerShell test suite of
  each shipped script retires with that script's port or gains a Linux counterpart.

## Current progress

Step 5 is owned by `Refactor/LinuxPeerCli` in the primary checkout; PR not opened. The implementation
worker uses L4 from the canonical Codex table through the native CLI. The parent uses L3 for the
remaining bounded terminal/cleanup investigation. A disposable Linux Git check confirmed that a linked
worktree can be removed while a live process retains its cwd there; Linux needs an exit observer, but
no wait-before-removal reaper. Windows retains waiting before removal.

Initial runtime port, direct caller/permission migration and first identity-safety repair implemented.
The identity checkpoint passes 149 tests (two platform skips). Actual stale-tab/title controls and
the Windows settings configurator are restored; their focused suite passes 29 tests. Remaining before
publication: unknown-owner handling in Linux orphan recovery, then the final validation/review gates.
Observer binding, refreshed preflight/cancellation, Windows wrapper qualification and disposable close/
finish process coverage are implemented. The process integration cases now also execute on Windows CI;
real Windows UI Automation remains unverified locally. Cleanup reminder commands select the platform's
interpreter. The combined peer lifecycle suite and cleanup gate suite pass.
These specified repairs select L4 with serialized path ownership. Then regenerate packages, run both
full suites, review, Windows/Linux CI, and the real merged-session acceptance. Step 5 remains unchecked
until that acceptance succeeds. Although Linux permits removal before exit, cleanup will follow verified
exit so a failed close cannot race deletion; the shared observer already owns that exit check.

Delivery slice: all Step 5 Python replacements, terminal handlers, registry identity, orphan recovery,
cleanup-gate commands, matching machine harness permissions and regression tests, based on
`b4b576fa6a999fd43031e8c49aefaf32aa3a7d05`.
The shared finish/close/observer/caller cutover stays atomic to preserve cleanup and exit guarantees.
Review the measured runtime/test size before publication. Verification requires both Python suites,
generated-tree checks, Windows/Linux CI, and a real merged Linux session closing its own tab.
The machine harness currently grants the retired PowerShell close/finish commands; migrate those grants
with the scripts and review the permission boundary explicitly before delivery.
The workflow helper needs explicit canonical skill paths, for example
`--lifecycle plan-execution=.agents/engineering/workflow/plan-execution/SKILL.md`;
its default `.agents/skills/` lookup predates the source-layout migration.

Shared library merged (#106, after the interim path fix #105). Kitty configured. Steps merged: 1 (#107),
2 `open-claude` (#108), 3a `handoff-claude` (#120, a real handoff tab verified on this machine), 6 `clip`
(#125), 8 Linux-only test failures (#160), 9 Linux CI (#162). #166 makes the cross-platform direction a written
convention in `CODE_CONVENTIONS.md`, labels `peer-cli` Windows-only, and adds step 10 for the rest of the
shipped instructions. Step 3b `handoff-codex` merged as #137; step 3 complete, verified by a real Codex
tab opened on this machine from the Python launcher right after the merge (new kitty tab, native
`codex-cli` resolved and launched, handoff receipt printed).

## Next Steps

Land 5 (`peer-cli`, `close` and `finish` first, per the tightened acceptance criterion above, so the
`merge` skill's Step 5 session exit works on Linux) and 4 (terminal start hooks, deleting
`agent-cli.ps1`); then 7 and 10. After `verify-linux` has had a few green runs, ask the user whether the
repository ruleset should require it.
