# Tech debt — machine

## Codex close and finish still need acceptance from a registered sandboxed CLI

On 2026-10-11, `close.py` refused the native Codex 0.162.1 session titled
`Linux port: Step 10` with `cannot resolve a verified registry attachment for this host and current
directory`. Its transcript identifies its source as `cli`. Outside the sandbox, its parent chain reaches
the native Codex process and kitty; inside the command sandbox, the visible chain ends at PID 1,
`codex-linux-sandbox`. A missing native process inside that namespace does not establish that the CLI
was never launched.

`session_close.own_host_and_entry` resolves ownership through process ancestry and matches the visible
PID and start time to the registry. It has no supported bridge to the host identity outside the sandbox.
This session initially had no registry entry; the separate installation/adoption gap is recorded in
[plugin debt](../plugins/TECH_DEBT.md#repository-skills-can-be-available-without-core-lifecycle-hooks).
The active profile was subsequently repaired with the native installer, 13 authenticated hook trust
updates, and the shipped SessionStart recorder. With the verified registry entry present, the same
attachment check succeeds outside the sandbox and refuses inside it. Both missing registration and
namespace visibility therefore affected this incident. Host-side execution is now specified by
`machine:peer-cli`, but actual terminal closure and finish cleanup were not performed during the active
task and remain unverified for this execution path.

**Resolution condition.** A freshly launched native Codex session with the machine plugin enabled
records a verified attachment, and its supported close/finish path resolves that same host from normal
sandboxed execution or an explicit host-side mechanism. Verify actual terminal closure and finish
cleanup on Linux and Windows while retaining PID/start-time and terminal identity checks. Missing
registration must be reported as an incomplete attachment, rather than successful closure or evidence
that no native CLI exists.


2026-10-12 follow-up incident (kind: debt, P2, in-progress): completed native session 01a12d05-0e36-7cd2-afac-1936aa63404b retained a verified host attachment but close.py refused an absent/ambiguous Windows Terminal target; its accepted/armed observer cancelled without exit. Current inventory has zero actual tabs. This is a distinct verified-self-close fallback gap, not missing registry or sandbox PID visibility. Canonical causal repair: [B004](../../BUGS.md#b004) and [verified self-close goal](../../plans/verified-self-close/GOAL.md), Fix/VerifiedSelfCloseFallback. Next action: reproduce and correct safe own-host fallback and observed closure accountability. Resolve this incident when focused identity/observer tests, both platform CI and actual registered self-exit prove closure; retain this broader debt until its original Linux/Windows acceptance condition passes.

2026-10-13 follow-up incident (kind: debt, P2, open): a native Claude Code session on Windows was asked to close itself after a completed Codex handoff, from the `tj-agents` org folder. `close.py` refused with `cannot resolve a verified registry attachment for this host and current directory`. That session had loaded machine `4090e7d23875` while `6e2e2db3d1ad` was installed, so its SessionStart registration may predate the current recorder. This is Claude rather than Codex, on Windows rather than in a Linux sandbox. The user had to close the tab by hand. Resolve together with this section's condition, adding a Claude-on-Windows case: a session that was registered before a plugin update must still resolve its own attachment after the update, or report the stale registration as the specific cause.

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

## A locked Codex runtime executable can disable every sandboxed command

Codex's sandbox setup opens ACLs on its bundled `node_repl.exe` before it starts a command. When Windows
returns a sharing violation for that executable, setup refresh fails and even a read-only command cannot
start. The launcher chooses among installed runtimes by version but has no command-runner health check, so
it cannot select a healthy desktop runtime when the CLI runtime is locked.

**Resolution condition.** Codex's sandbox setup tolerates a transient runtime-file lock or exposes a
supported health probe and runtime selection mechanism; then the launcher detects the unhealthy runtime,
uses a healthy supported runtime when available, and has regression coverage for the fallback.

## Windows Terminal option values may be escaped for a parse they never get

`agent_cli._launch_windows_terminal` passes every
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

## A shared parent shell can keep the worktree locked after finish

`finish.py` stops a parent shell only when it is this session's dedicated wrapper. When the CLI was started
by hand from a long-lived shell whose current directory is inside the worktree, that shell survives, Windows
keeps the directory locked, and the reaper records a failed removal; the cleanup reminder then surfaces it.

**Resolution condition.** The reaper can read another process's current directory, or the host records it,
so finish can tell a shell that pins the worktree from one that does not.

## Platform-specific machine integrations lack an explicit source boundary

Windows-only installers, shell profiles and terminal integration currently sit beside shared machine
code. As Linux integration grows, explicit `.windows` and `.linux` adapter directories would make
platform ownership easier to find. Shared Python implementations and capability definitions retain
their canonical home in `.agents`; platform folders should contain only OS-specific integration.

**Resolution condition.** Document the platform adapter layout in `SOURCE_LAYOUT.md`, move the
OS-specific integration into its owning directories, and update installation, packaging and imports
with Windows and Linux verification. Keep this structural change separate from the functional Linux
port so each delivery remains reviewable.

## Repository-config tests fail intermittently under concurrent suites

On 2026-10-10 a full `.agents/hooks/tests` run failed six `test_repo_config` cases with
`Root is not the exact Git checkout: /tmp/tmp…` while two other sessions ran the suites on the same machine.
The file passed alone and on two immediate reruns, and in eight earlier full runs that day.
`plugin-lock`' `repo_config.preflight_paths` raises that error when a parent of the root holds
`.git` (`/tmp` or `/` for these roots) or when `git rev-parse --show-toplevel` disagrees with the root. Which
one fired, and what caused it, was not identified.

Resolve when the failing branch is identified from a reproduction (for example, logging both checks under
two concurrent full suites), its cause is fixed or isolated, and two full suites run concurrently on one
machine pass.
