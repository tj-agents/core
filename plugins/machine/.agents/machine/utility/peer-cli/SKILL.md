---
name: peer-cli
description: List, inspect and close the other Claude CLI sessions and their Windows Terminal tabs, addressed by the tab title the user can see rather than an internal session name. Use when asked which CLIs are running, which tab to close, to close a finished session or a stale tab, or to check what another session is doing before continuing.

kind: utility
domain: machine
route: infer
---

# Peer CLI sessions

Two naming systems describe the same window. A session's own name is derived by the harness from its
branch or directory (`refactor-postgresauthconsumer-ec`), while its tab is titled by whoever launched it
("Postgres sweep: Search"). Naming a peer by the first is naming something the user cannot see on screen.
This skill addresses peers by tab title.

`ListAgents` and `SendMessage` remain the way to enumerate and talk to in-harness peers. This skill is for
the two things they do not do: resolving the title the user sees, and ending a session.

```powershell
& '<skill-directory>\scripts\peer-cli.ps1' list
& '<skill-directory>\scripts\peer-cli.ps1' list -All
& '<skill-directory>\scripts\peer-cli.ps1' list -Under 'C:\Users\name\source\repos\some-org'
& '<skill-directory>\scripts\peer-cli.ps1' list -IncludeUnrecorded
& '<skill-directory>\scripts\peer-cli.ps1' resolve 'Postgres sweep: Search'
& '<skill-directory>\scripts\peer-cli.ps1' close 'Postgres sweep: Search'
```

`list` defaults to what the caller plausibly cares about: sessions under the current repository and under
its parent folder (sibling checkouts in the same org). `-Under <path>` scopes explicitly instead; `-All`
drops scoping and shows every recorded session on the machine. Outside a git repository, `list` cannot
auto-scope and behaves like `-All`.

`close` prompts unless `-Force`. A session records itself at SessionStart, so one started before that hook
existed has no entry — `-IncludeUnrecorded` also reports live `claude.exe` processes that own no entry, so
a running CLI is never invisible just because it predates the registry.

## Closing the tab, not just the process

Ending the process is not closing the window. Terminal's default `closeOnExit: automatic` keeps a tab
whose process exited non-zero, and a killed one always does, so `peer-cli close` on its own leaves a dead
pane. Two things fix that, and both are here:

```powershell
& '<skill-directory>\scripts\configure-terminal-tab-close.ps1'          # once per machine
& '<skill-directory>\scripts\close-tab.ps1' -List
& '<skill-directory>\scripts\close-tab.ps1' 'Postgres sweep: Search'
```

The configurator sets `closeOnExit: always` on Terminal's profile defaults, so from then on a session
takes its tab with it. `close-tab.ps1` is for tabs already left behind: Terminal exposes no command-line
verb for closing one, so it drives UI Automation — it finds the `TabItem` whose Name matches and invokes
that tab's own `CloseButton`, never a keystroke that would land on whichever tab has focus.

Its two refusals both exist because they were broken first:

- **A wildcard reports and stops.** A pattern written to match several can match exactly one and close it
  silently. `-All` opts in; an exact title is itself the decision.
- **A live tab is refused.** Liveness is per tab, read from the session registry, so a stale tab is still
  closable in a window full of busy ones. A title with no registry entry predates the hook and counts as
  live, because unknown is not dead. `-Force` overrides.

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
