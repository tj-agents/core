---
name: last-conversation
description: Show Tommy's most recent Codex conversation(s) for the current project and the exact `Codex --resume <id>` command to reopen one, via the Get-LastClaudeConversation PowerShell command. Use whenever Tommy says "/last-conversation", "what was my last conversation", "which session do I resume", "resume the latest", or when `Codex --resume` won't show his newest session.

kind: utility
domain: machine
---

Show Tommy's most recent Codex conversations by running
`Get-LastClaudeConversation`. It reads the transcripts under
`~/.Codex/projects` directly, so it always surfaces the genuine latest session
— the built-in `--resume` picker caps its list and hides the just-active /
summary-less sessions, which is why his newest one keeps not appearing.

The function lives in a standalone script that is NOT loaded by his profile, so
dot-source it first, then call it.

## Default call — recent conversations for THIS project

Run exactly ONE tool call:

```powershell
. "$env:USERPROFILE\.Codex\Get-LastClaudeConversation.ps1"; Get-LastClaudeConversation | Format-Table Modified, Session, Branch, Msgs, Preview -AutoSize -Wrap
```

Returns one row per session (Modified, Session id, Branch, Msgs, Preview, and a
`Resume` command), newest first, for the project matching the current directory.

## Variations

- **More/fewer rows**: add `-Count N` (default 5).
- **A specific project**: add `-Project '<substring>'` of the project-folder name
  (e.g. `-Project 'Concertable'`).
- **Across all projects**: add `-AllProjects`.
- **A different directory's project**: add `-Path 'C:\...'`.

## Rules

- Don't pre-list files or `Test-Path` anything — the function handles missing
  history and empty sessions itself.
- After the call, tell Tommy the newest conversation and give him the exact
  command to reopen it — read the `Resume` field (`Codex --resume <id>`).
  Surface it explicitly since `Format-Table` above omits that column:
  the top row's session id is what he types.
- **The very top row may be the session he's currently in.** If he just exited a
  chat and wants "the last one", that's usually row 1 (if run from outside) or
  row 2 (if run from within the live session). Point out which is which when it's
  ambiguous, using the Preview to disambiguate.
- If nothing matched for the current directory, suggest `-AllProjects` or
  `-Project`.
