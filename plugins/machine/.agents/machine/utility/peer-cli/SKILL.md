---
name: peer-cli
description: List, inspect and close the other Claude CLI sessions running on this machine, addressed by the tab title the user can see rather than an internal session name. Use when asked which CLIs are running, which tab to close, to close a finished session, or to check what another session is doing before continuing.

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
& '<skill-directory>\scripts\peer-cli.ps1' list -IncludeUnrecorded
& '<skill-directory>\scripts\peer-cli.ps1' resolve 'Postgres sweep: Search'
& '<skill-directory>\scripts\peer-cli.ps1' close 'Postgres sweep: Search'
```

`close` prompts unless `-Force`. A session records itself at SessionStart, so one started before that hook
existed has no entry — `-IncludeUnrecorded` also reports live `claude.exe` processes that own no entry, so
a running CLI is never invisible just because it predates the registry.

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
