# Tech debt — machine

## The Codex plugin cache is not reconciled

`~/.codex/plugins/cache/` accumulates orphaned plugin payloads exactly as the Claude cache did, and
`scripts/prune_plugin_cache.py` does not touch it.

Registry-is-truth, the rule the reconcile rests on, does not hold for Codex. Its registry is
`~/.codex/config.toml`, whose plugin entries record `enabled = true` and no install path at all, so a
cached directory cannot be matched to a live install. Those entries are also stale in their own right —
they still name plugins that were renamed away — which makes that registry the wrong copy rather than
the authoritative one. Pruning against it would preserve dead payloads and could remove live ones.

Left deliberately rather than guessed: the alternative is inventing a liveness rule for a source
already verified to be incorrect, shipped in the same change as the reconcile it would undermine.

**Resolution condition.** Either the Codex registry records a per-plugin install path, or its plugin
entries are reconciled against the marketplaces it actually resolves so the installed set can be
trusted. When either holds, add a Codex registry reader behind the same report-by-default,
fail-closed contract and delete this entry.

## Claude keeps a superseded plugin directory for 14 days, not for a session's lifetime

On 2026-09-22 every stop hook in a live session failed with `Plugin directory does not exist` after an
update. Claude Code 2.1.282 instead writes `.orphaned_at` into the superseded version directory and
deletes it 14 days later, so hooks keep their loaded path
([cleanup](https://code.claude.com/docs/en/plugins/loading#cleanup-of-previous-versions)); eight such
directories per core plugin were still present on 2026-09-28. `prune_plugin_cache.py --apply` keeps them
inside that window and `--pin` covers the live sessions it records. A session running longer than 14
days can still lose its hooks, and nothing in this repository sits between the host and its own cleanup.

**Resolution condition.** The host keeps a session's resolved plugin directory for that session's
lifetime, or exposes the resolved set so a supervisor can.

## Codex records no pin

The pin is written by the Claude SessionStart hook only. Codex's `machine-hooks.json` runs
`register_session.py` and not the reconcile, because the reconcile does not read Codex's cache at all
(above). Resolving that entry resolves this one with it.

## Launcher terminal detection trusts inherited environment variables

`agent_cli.launch_tab` picks the terminal from `TMUX`, `KITTY_WINDOW_ID` and `KONSOLE_DBUS_WINDOW`.
A GUI program started from a terminal inherits them, so a launcher run inside, for example, VS Code
started from Konsole opens its tab in that Konsole window, or fails if the window has closed.

Resolve when detection confirms the variable belongs to the terminal the caller is attached to, for
example by matching the terminal's own record of its sessions against the caller's process ancestry,
with a test for an inherited variable.

## Windows Terminal option values may be escaped for a parse they never get

`agent_cli._launch_windows_terminal` (and `agent-cli.ps1`'s `Invoke-AgentTerminalTab`) pass every
`wt.exe` argument through `terminal_argument`, including `--title` and `--startingDirectory`, which are
Windows Terminal's own option values rather than the launched command's arguments. The escaping
`terminal_argument` applies models the second argv parse the tab's command arguments get after Windows
Terminal's own `;`-split re-joins them (`CommandLineToArgvW` quote/backslash rules) — a parse option
values may never receive at all, if Windows Terminal reads them off its own command line after only the
`;` split. If so, a title or starting directory containing a quote or a trailing backslash would show its
escapes literally in the tab (visible cosmetically, not a lost launch, since `;` is still escaped either
way and nothing else in that value is Windows-Terminal-significant).

Left unresolved rather than guessed: changing the escaping for option values without observing the real
behaviour risks trading a cosmetic defect for a functional one.

**Resolution condition.** A real `wt.exe` launch with a `--title` and a `--startingDirectory` containing a
quote and a trailing backslash confirms whether Windows Terminal parses its own option values the same
way as the tab's command arguments. If it does not, give option values their own escaping (likely just the
existing `;` handling, with no `CommandLineToArgvW`-style quoting), with a test pinned to the confirmed
behaviour.

## clip offers one clipboard flavour per copy on Linux

`copy_draft.py`'s POSIX backend sets a clipboard flavour through `wl-copy`/`xclip`, and each of those
tools accepts only one MIME type per invocation. Default mode therefore copies `text/html` only when
the tool supports it — nothing a plain-text target (a terminal, a plain text field) can read from that
same copy. The skill documents the split instead: default mode is for rich targets (Teams, email);
`--plain-only` for everything else. Windows is unaffected — CF_HTML and CF_UNICODETEXT are set in the
same clipboard transaction, so both flavours are always available together there.

`tests/test_copy_draft.py`'s `LinuxSingleFlavourTechDebtTests` pins today's one-call, HTML-only default
so a future change here is deliberate rather than accidental.

**Resolution condition.** A single copy can offer both `text/html` and `text/plain` on Linux — for
example, a small persistent Wayland (`wlr-data-control`) or X11 data source that goes on answering
selection/data-control requests for either MIME type from the same in-memory text, rather than a
one-shot `wl-copy`/`xclip` invocation that exits once the data is handed off. When one exists (or is
written here), default mode copies both flavours from one call and this entry is deleted, with a test
proving a `text/plain` read-back succeeds right after a default-mode copy.

## The pre-launch standards sync has no overall deadline

`agent_cli.sync_claude_standards` runs `claude_standards_sync.py` before every Claude launch and waits
for it with no outer limit, as the PowerShell launcher did. The script bounds each of its own steps
(180 seconds per marketplace update, 120 per plugin, 20 per `git ls-remote`), but those add up across
plugins, and on Windows a `claude plugin` grandchild that keeps the output pipe open can hold the wait
past its own step limit. A slow or wedged check therefore delays the tab, and the launch it was meant
never to block. A plain outer `subprocess` timeout is not the fix: it kills a check that is still
within its own budgets and leaves the grandchild running.

Resolve when the sync runs under one overall deadline that stops its whole process tree on expiry on
both Windows and POSIX, reports a `standards:` line and then launches, with a test that a hung
grandchild cannot hold the launch past that deadline.

## finish.ps1 trusts the starting directory for attachment

Run without arguments, `finish.ps1` treats the worktree containing its starting directory as its own and
refuses only when another live registered session sits there. A session can therefore `cd` into another
merged worktree and finish it. The receipt gates (merged at exactly that head, clean tree, no open PR) mean
nothing unmerged is lost, but an unregistered session still attached there would lose its directory.

**Resolution condition.** Every live CLI is registered with its current directory (the host reports cwd
changes, or the registry records them), so attachment can be proven from the registry alone.

## A shared parent shell can keep the worktree locked after finish

`finish.ps1` stops a parent shell only when it is this session's dedicated wrapper. When the CLI was started
by hand from a long-lived shell whose current directory is inside the worktree, that shell survives, Windows
keeps the directory locked, and the reaper records a failed removal; the cleanup reminder then surfaces it.

**Resolution condition.** The reaper can read another process's current directory, or the host records it,
so finish can tell a shell that pins the worktree from one that does not.
