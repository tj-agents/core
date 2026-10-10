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
- [ ] 4. Terminal start hooks: Python terminal-profile installers refresh standards when `claude`/`codex`
  is typed, wired for Bash on Linux and PowerShell on Windows/Linux (discovering `python3`, `python`, and
  Windows `py -3` without Store stubs); the retired PowerShell launchers are deleted.
- [x] 5. `peer-cli` -> Python: `close.py` and `finish.py` (with `finish_reaper`/`session_close` ported) let
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
  which the user approved requiring on 2026-10-10; enabling it awaits a supported publishing-app exception.
- [ ] 10. Shipped instructions follow `CODE_CONVENTIONS.md`'s Supported platforms: no shipped Markdown
  under `.agents/`, `.claude/` or `.codex/` tells an agent to run bare `python`, `powershell.exe`, `pwsh`
  or `wt.exe` without naming the platform (including the session exit in `merge` Step 5 and in
  `merge-docs`' Report), every unported skill says it is Windows-only, and the PowerShell test suite of
  each shipped script retires with that script's port or gains a Linux counterpart.

## Current progress

- PR: not opened

Step 4 was picked up on `Refactor/LinuxTerminalStartHooks` with the boundary limited to terminal-start
standards refresh, its tests and documentation. Its successor remains Step 7; Steps 7 and 10 are not
implementation scope for this slice.

The primary acknowledged the handoff and completed bounded L3 discovery. Native L4 implementation
uses the canonical Codex lane table. Independent review found five
confirmed defects; all five are repaired. Final local validation passed 1,001 source tests (17 skips)
and 1,001 hook tests (four skips), plus generated-tree, catalog, harness and tier checks. The completed incremental review found one further maintenance-child isolation defect; that repair is
complete and both full suites passed again. Real packaged session fixtures cover maintenance and
permission convergence under hostile PYTHONPATH while preserving native CLI environment. Fresh review
and Windows/Linux CI remain before delivery. The existing single-file legacy plan remains the recovery owner, without adding a roadmap
solely to satisfy a separate ledger's graph requirements.

The current cutover includes 28 authored paths in the trunk diff, including
320 retired PowerShell runtime lines and 412 retired PowerShell test lines; generated output is excluded.
Separate Claude/Codex ports could be shipped, but the user explicitly selected one reviewed PR per step.
Keep this exception focused on the one shared profile/bootstrap/dispatch contract, validate actual shell
integration, and include independent correctness/security review plus Windows/Linux CI. No additional
runtime concern joins this slice. Historical references in other plans retain their original Windows acceptance evidence;
they are deliberate historical survivors of the deleted scripts, not current launch instructions.

GitHub inspection found no active main rulesets or classic branch protection. The user explicitly approved
requiring `verify-linux` with a GitHub Actions exception on 2026-10-10. GitHub rejected that exception
with HTTP 422: its built-in Actions integration cannot bypass this repository ruleset. The repository
has no existing publishing-app credential (only `TJ_AGENTS_READ_TOKEN`). Protection remains unchanged
to preserve the current post-merge generated-package publisher. An installed publishing app or a separate
validated publishing-workflow change is required before enabling the approved check requirement.

Step 5 is complete in merged PR #181: reviewed head `97bc4ffeacd1d05fbf3dc4deb235631f17150b1e`, merge
`3ff817a923362ac21dbe6aae9fc14a3d4d787c6f`. Exact-head run 38069524094 passed `verify-windows` and
`verify-linux`. Full local suites passed: 971 source tests (17 skips), 990 shared runtime tests
(four skips), 29 close-tab tests and 23 lifecycle tests, plus generated-tree, catalog, tier and
harness checks. Generated output was excluded from the PR.

Real native Linux Codex session `01a126cd-2e74-7583-81a4-e8e5a2b1e12a` (PID 1949195,
start 1791652342.1, kitty window 13) merged this PR and executed
argument-free `finish.py`. The primary independently verified its exit and tab closure, linked
worktree and local branch removal, and matching obligation clearance. Final receipt:
`/home/tommy/.agents-state/merge-cleanup/results/d8f69af9dfb740a0bcd44a5b083bccdf.json`. Causal post-merge regeneration run 38070819051
succeeded and produced `2dc76412f0794584e36b7440e5cde0bf7a0ce5ac`. Windows CI exercises the shared runtime;
actual Windows desktop UI Automation remains unverified locally. Native Linux evidence uses the
canonical authored source; it does not claim installation acceptance for either host.

The Windows job is now `verify-windows`. Both platform jobs are required for this port’s delivery
validation while the approved protection change awaits the publishing dependency above. The proposed
`.windows`/`.linux` organization remains separate design debt in `.agents/machine/TECH_DEBT.md`;
shared logic stays canonical in `.agents`.

Previously merged: shared library #106, steps 1 #107, 2 #108, 3 #120/#137, 6 #125, 8 #160 and 9 #162.
Step 4, then 7 and 10 remain. The primary checkout is reused sequentially on
`Refactor/LinuxTerminalStartHooks` for one fresh Step 4 session; its local checkpoint belongs in that
next substantive PR, with no separate Step 5 metadata PR.

## Agent-host coverage

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/machine/scripts terminal-profile installers, bootstrap and Python command dispatch",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Typed claude commands resolve the active machine package and refresh standards before sessions; Bash/Linux and PowerShell/Windows/Linux use shared Python dispatch.",
      "source": ".agents/machine/scripts/claude_terminal_profile.py; claude_terminal_launcher.py; terminal_command.py",
      "mapping": ".agents/plugins/manifests/claude/machine-hooks.json; .agents/plugins/sources.json resources/machine/scripts mapping",
      "verification": {
        "level": "source",
        "result": "passed",
            "evidence": "42 focused terminal tests (one Windows-only skip), 37 Codex-sync regressions, 1001 complete source tests (17 skips) and 1001 complete shared-runtime tests (four skips) passed locally. Bash and PowerShell, including legacy argument mode, used disposable profiles. Generated-tree, catalog, harness and tier invariants passed. Windows CI, installed-host adoption and a real Windows desktop remain pending."
      }
    },
    {
      "host": "codex",
      "behavior": "Typed codex commands resolve the active machine package and refresh standards before sessions; Bash/Linux and PowerShell/Windows/Linux use shared Python dispatch.",
      "source": ".agents/machine/scripts/codex_terminal_profile.py; codex_terminal_launcher.py; terminal_command.py",
      "mapping": ".agents/plugins/manifests/codex/machine-hooks.json; .agents/plugins/sources.json resources/machine/scripts mapping",
      "verification": {
        "level": "source",
        "result": "passed",
            "evidence": "42 focused terminal tests (one Windows-only skip), 37 Codex-sync regressions, 1001 complete source tests (17 skips) and 1001 complete shared-runtime tests (four skips) passed locally. Bash and PowerShell, including legacy argument mode, used disposable profiles. Generated-tree, catalog, harness and tier invariants passed. Windows CI, installed-host adoption and a real Windows desktop remain pending."
      }
    }
  ]
}
```

## Reviews

Independent full review of `fa5f7f3def036948fa30823adb6d31e2c1f72022` completed at
`reviews/Refactor-LinuxTerminalStartHooks.md`: three HIGH and two MEDIUM findings require repair
(import isolation, profile modes, PowerShell shims/arguments, and hook-control interpreter selection).
The native reviewer and independent security/workflow lenses ran; parent verified evidence. Incremental
review through `5301acfa8e40edcf0c2983ede33cbade36e35937` confirmed one further HIGH maintenance-child
isolation finding. The parent reproduced hostile PYTHONPATH startup in both hosts; all maintenance
children now use isolated Python, with real packaged-session and permissions-convergence coverage.

## Next Steps

All six confirmed findings are repaired and both full local suites passed. Independently review the
maintenance-isolation repair before publishing for Windows/Linux CI in the primary
checkout `/home/tommy/projects/tj-agents/core`, branch `Refactor/LinuxTerminalStartHooks`. Its successor
owns Step 7 only after Step 4 lands. Do not implement Steps 7 or 10 in this session. The whole port
remains authorized one reviewed PR per step.

Scope: current slice only; full plan remains incomplete.
Current slice: Step 4 terminal-start refresh and its authorized Linux-check requirement.
Remaining scope: Steps 7 and 10, handed to a fresh session after Step 4 delivery.
Done when: one reviewed Step 4 PR is merged with Windows/Linux CI green and its successor is launched.

Step 4 has implemented Python terminal-profile installers and launchers for both hosts, wired for Bash on Linux
and PowerShell on Windows/Linux. They discover `python3`, `python`, and Windows `py -3`, skip Store stubs,
and replaced the retired PowerShell launchers. Platform directory reorganization is separate recorded debt
and is outside this functional port.

The user approved making `verify-linux` a required PR check with an Actions exemption on 2026-10-10.
GitHub rejected the built-in Actions identity; do not enable the rule until an installed publishing app
or a separately validated publishing-workflow change preserves generated-package publication.
This approval does not add unrelated branch protection requirements. Windows CI is named
`verify-windows`; both jobs must pass for the port's delivery validation.

Use the repository workflow and one existing owning review for this step. Never commit generated
`plugins/*` or catalog digests. The full local `tests/` and `.agents/hooks/tests/` suites remain required
before every stable push, including repairs. The native specialist was rejected by the account in the
previous session; the declared native terra/medium review fallback succeeded. Preserve all unrelated
worktrees/sessions. No additional Step 5 PR is needed; its completed checkpoint rides in Step 4.
