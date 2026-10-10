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

```powershell
python3 -B <skill-directory>/scripts/peer_cli.py list
python3 -B <skill-directory>/scripts/peer_cli.py list --all
python3 -B <skill-directory>/scripts/peer_cli.py list --under /path/to/some-org
python3 -B <skill-directory>/scripts/peer_cli.py list --include-unrecorded
python3 -B <skill-directory>/scripts/peer_cli.py resolve 'Postgres sweep: Search'
python3 -B <skill-directory>/scripts/peer_cli.py close 'Postgres sweep: Search'
```

`list` defaults to what the caller plausibly cares about: sessions under the current repository and under
its parent folder (sibling checkouts in the same org). `-Under <path>` scopes explicitly instead; `-All`
drops scoping and shows every recorded session on the machine. Outside a git repository, `list` cannot
auto-scope and behaves like `-All`.

`close` prompts unless `--force`. A session records itself at SessionStart, so one started before that hook
existed has no entry — `-IncludeUnrecorded` also reports live `claude.exe`/`codex.exe` processes that own
no entry, so a running CLI is never invisible just because it predates the registry.

Liveness matches the recorded pid and its OS start time. An entry that cannot be matched is unknown, not
dead, and `close` and `close_tab.py` refuse it; an unknown identity is never killed.

## Closing the tab, not just the process

Ending the process is not closing the window. Terminal's default `closeOnExit: automatic` keeps a tab
whose process exited non-zero, and a killed one always does, so `peer-cli close` on its own leaves a dead
pane. Two things fix that, and both are here:

```powershell
python3 -B <skill-directory>/scripts/configure_terminal_tab_close.py
python3 -B <skill-directory>/scripts/close_tab.py --list
```

The configurator gives the Windows Terminal settings path and is a no-op on Linux. `close_tab.py` resolves
an actual terminal target before acting: the registered host must belong to the exact kitty window, tmux
pane on its recorded server, or Konsole session process ancestry. On Windows it rescans UI Automation and
uses either a recorded automation id or a unique registered/live title; it never uses focus or wildcard
title matching. Konsole has no supported D-Bus close method: it signals the verified session root process,
so the terminal profile must be configured to close a tab when that process exits.

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
