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

Step 5 owns PR #181 (`Refactor/LinuxPeerCli`) in the linked checkout
`/home/tommy/projects/tj-agents/core/.worktrees/LinuxPeerCliProof`. The originating session retains the
whole goal from the primary checkout. The real native merge/finish acceptance session is not launched.
The user requires one PR for this step; its 40 authored paths keep the shared closure, terminal identity,
observer, callers and host grants atomic. Generated output remains uncommitted.

The Python lifecycle and terminal/orphan ports are implemented and reviewed. Local suites at
`1752aebbdf11da132c342dfb0ce8a8e3dc839c32` passed: 963 source/package tests (17 skips), 990 shared runtime
tests (four skips), 19 focused lifecycle tests, generated-tree, catalog, tier and harness checks.
Native and fresh process-safety reviews are complete in `reviews/Refactor-LinuxPeerCli.md`. Linux CI
passed. Windows CI exposed an undefined wrapper helper and an incompatible handshake fixture, then
rejected the long observer command. The bounded native L4 worker replaced registration with structured
scheduler XML, current-user SID and useful diagnostics. Run 38061315556 now identifies the remaining
registration defect precisely: the Windows scheduler cannot switch the UTF-8 XML encoding. The tiny
follow-up writes UTF-16 with its matching declaration and BOM, with a regression assertion. All 19
lifecycle tests pass locally. The parent owns full validation, fresh review, replacement CI and delivery;
the native implementation lane is available and was used. Windows desktop UI Automation remains
unverified locally.

A disposable Linux Git experiment confirmed that a worktree can be removed while a live process retains
its cwd. The shared observer still waits for verified exit on both platforms so failed closure cannot
race deletion; it already owns that exit check. Step 5 remains unchecked until the real merged CLI closes
its own kitty tab through argument-free `finish.py`, and the parent verifies session exit plus worktree,
branch and matching obligation removal. Causal post-merge regeneration must also succeed.

Previously merged: shared library #106, steps 1 #107, 2 #108, 3 #120/#137, 6 #125, 8 #160 and 9 #162.
Step 3's native Codex handoff was verified in kitty. Step 4, then 7 and 10 remain after Step 5.

## Agent-host coverage

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/machine/utility/peer-cli and .agents/hooks/merge_cleanup_gate.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Merged sessions use the shared Python close/finish lifecycle with verified process and terminal ownership.",
      "source": ".agents/machine/utility/peer-cli/scripts/*.py; .agents/machine/scripts/reap_orphans.py",
      "mapping": ".agents/plugins/sources.json machine mappings and .agents/plugins/harness/machine.json permissions.claude_allow",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Latest reviewed-head Linux source suite: 963 tests, 17 skips; shared runtime suite: 990 tests, four skips; generated-tree, catalog, tier and harness checks passed. Both host permission mappings and lifecycle fixtures were reviewed. Windows observer repair validation/CI and real merged Linux acceptance remain pending; actual Windows desktop UI Automation is unverified locally."
      }
    },
    {
      "host": "codex",
      "behavior": "Merged sessions use the shared Python close/finish lifecycle with verified process and terminal ownership.",
      "source": ".agents/machine/utility/peer-cli/scripts/*.py; .agents/machine/scripts/reap_orphans.py",
      "mapping": ".agents/plugins/sources.json machine mappings and .agents/plugins/harness/machine.json permissions.codex_prefix_rules",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Latest reviewed-head Linux source suite: 963 tests, 17 skips; shared runtime suite: 990 tests, four skips; generated-tree, catalog, tier and harness checks passed. Both host permission mappings and lifecycle fixtures were reviewed. Windows observer repair validation/CI and real merged Linux acceptance remain pending; actual Windows desktop UI Automation is unverified locally."
      }
    }
  ]
}
```

## Next Steps

Land 5 (`peer-cli`, `close` and `finish` first, per the tightened acceptance criterion above, so the
`merge` skill's Step 5 session exit works on Linux) and 4 (terminal start hooks, deleting
`agent-cli.ps1`); then 7 and 10. After `verify-linux` has had a few green runs, ask the user whether the
repository ruleset should require it.
