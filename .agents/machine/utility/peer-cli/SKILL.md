---
name: peer-cli
description: List, inspect and close the other Claude or Codex CLI sessions and their terminal tabs, addressed by the tab title the user can see rather than an internal session name. Use when asked which CLIs are running, which tab to close, to close a finished session or a stale tab, or to check what another session is doing before continuing.

kind: utility
domain: machine
route: infer
---

# Peer CLI sessions

The runtime is Python 3.9+ on Windows and Linux. Use `python3` on Linux/macOS and `python` on Windows.

Two naming systems describe the same window. A session's own name is derived by the harness from its
branch or directory (`refactor-postgresauthconsumer-ec`), while its tab is titled by whoever launched it
("Postgres sweep: Search"). Naming a peer by the first is naming something the user cannot see on screen.
This skill addresses peers by tab title.

`ListAgents` and `SendMessage` remain the way to enumerate and talk to in-harness peers. This skill is for
the two things they do not do: resolving the title the user sees, and ending a session.

```sh
# Linux/macOS: install Python 3.9+ as python3 before using this utility.
python3 -B <skill-directory>/scripts/peer_cli.py list
python3 -B <skill-directory>/scripts/peer_cli.py list --all
python3 -B <skill-directory>/scripts/peer_cli.py list --under /path/to/some-org
python3 -B <skill-directory>/scripts/peer_cli.py list --include-unrecorded
python3 -B <skill-directory>/scripts/peer_cli.py resolve 'Postgres sweep: Search'
python3 -B <skill-directory>/scripts/peer_cli.py close 'Postgres sweep: Search'
```

```sh
# Windows
python -B <skill-directory>\scripts\peer_cli.py list
python -B <skill-directory>\scripts\peer_cli.py close "Postgres sweep: Search"
```

If that interpreter is not available, install Python 3.9+ and ensure `python` (Windows) or `python3`
(Linux/macOS) is on PATH.

`list` defaults to what the caller plausibly cares about: sessions under the current repository and under
its parent folder (sibling checkouts in the same org). `--under <path>` scopes explicitly instead; `--all`
drops scoping and shows every recorded session on the machine. Outside a git repository, `list` cannot
auto-scope and behaves like `--all`.

`close` prompts unless `--force`. A session records itself at SessionStart, so one started before that hook
existed has no entry — `--include-unrecorded` also reports live `claude.exe`/`codex.exe` processes that own
no entry, so a running CLI is never invisible just because it predates the registry.

Liveness matches the recorded pid and its OS start time. An entry that cannot be matched is unknown, not
dead, and `close` and `close_tab.py` refuse it; an unknown identity is never killed.

## Closing the tab, not just the process

Ending the process is not closing the window. Terminal's default `closeOnExit: automatic` keeps a tab
whose process exited non-zero, and a killed one always does, so `peer-cli close` on its own leaves a dead
pane. Two things fix that, and both are here:

```sh
python3 -B <skill-directory>/scripts/configure_terminal_tab_close.py
python3 -B <skill-directory>/scripts/close_tab.py --list
python3 -B <skill-directory>/scripts/close_tab.py --title 'Postgres sweep: Search'
```

```sh
# Windows
python -B <skill-directory>\scripts\configure_terminal_tab_close.py --preview
python -B <skill-directory>\scripts\close_tab.py --list
```

On Windows, the configurator edits the default Windows Terminal `settings.json` path (or an explicit
`--settings-path`), preserving JSONC layout and making a timestamped backup. Use `--preview` before a
real change; `--close-on-exit` accepts `always`, `graceful`, `automatic`, or `never`. On Linux it is a
no-op unless an explicit disposable `--settings-path` is supplied for a portable test.

`close_tab.py --list` inventories actual tabs in the detected kitty or tmux terminal, or all Windows
Terminal tabs through UI Automation; it also shows registered targets not presently discoverable. The
Konsole rows are registry-backed only because Konsole has no safe global tab inventory. Its recorded full
D-Bus service/session path is re-queried before a verified peer close.

`close_tab.py --title` operates only on exactly one actual tab. A wildcard title (`*`, `?`, or `[...]`)
always refuses unless `--all` is present, even if it happens to match one tab. Live, unrecorded, and
unknown targets refuse unless `--force`; force changes only that terminal-tab liveness decision and never
authorizes a process signal. Linux closes the exact kitty window or tmux pane, preserving siblings. Windows
rescans UI Automation at close time and never uses focus keystrokes. A stale registered peer can be closed
only by this explicit re-enumerated tab path, not by trusting its dead host process.

Its two refusals both exist because they were broken first:

- **Unknown is never dead.** Failed process inspection, malformed identity and PID reuse do not authorize
  a kill or cleanup. Force can select an explicit stale terminal target, but never bypasses pid/start-time
  verification for a process signal.

Closing *this* session's own tab and worktree is not this skill's job: `engineering:merge` Step 5 does
that through `finish.py`, beside these scripts.

For a completed session whose checkout must remain, run exactly
`python3 -B <skill-directory>/scripts/close.py` on Linux/macOS or
`python -B <skill-directory>\scripts\close.py` on Windows, with no
arguments after the completion report. It requires this host's verified registry entry and attachment,
closes only its own host or uniquely identified tab, and records session exit without changing files,
branches or worktree registration. `finish.py` retains ownership of removable linked-worktree cleanup.

## Closing a peer

Close one when it is **finished or duplicating**, and say which and why before you do:

- a handoff you launched has landed its work, so the session it ran in has nothing left to own;
- two sessions hold the same worktree or branch. Concurrent sessions in one working tree overwrite each
  other — one switching branches mid-edit is enough to lose a commit's worth of another's work.

Never close a session holding unpushed work, mid-run validation, or a question waiting on the user. Check
with `list` for its directory, and prefer asking it through `SendMessage` over guessing. When both
sessions are viable, the one holding the live task context is the one that stays.

Closing a CLI is not reversible. Where the user can see the tabs, name the one you mean and let them close
it, unless they have asked you to do it.

## Monitoring a peer

Read another session's progress only when your next step genuinely depends on it — whether a producer PR
merged, whether a handoff has started. It is a poor substitute for the artifacts that already record that:
a PR's checks, a plan ledger, a run log. Prefer those, and ask a peer directly only when nothing durable
answers the question.
