---
name: search
description: Search Codex transcript history (.jsonl under ~/.Codex/projects) for a pattern, via the Search-ClaudeHistory PowerShell command. Use whenever Tommy says "/search", "search for X", "search my history/transcripts/sessions for X", or "find where I/we discussed X" referring to past Codex conversations.

kind: operation
domain: machine
---

Search Tommy's Codex transcript history by running `Search-ClaudeHistory`.
The function lives in a standalone script that is NOT loaded by his profile, so
dot-source it first, then call it.

The search term is whatever follows `/search` (or what Tommy asked to search for).
It is a regex passed to `Select-String -Pattern`, so escape regex metacharacters
if he means them literally.

## Default call — which sessions mention it

Run exactly ONE tool call:

```powershell
. "$env:USERPROFILE\.Codex\Search-ClaudeHistory.ps1"; Search-ClaudeHistory -Pattern '<term>' | Format-Table -AutoSize
```

This returns one row per session (Session id, Hits, Modified, Project), newest
first — the right default for "where did we talk about X".

## Variations

- **He wants the actual matching text**, not just which sessions: add `-ShowLines`.
  ```powershell
  . "$env:USERPROFILE\.Codex\Search-ClaudeHistory.ps1"; Search-ClaudeHistory -Pattern '<term>' -ShowLines | Format-Table -AutoSize -Wrap
  ```
- **Limit to one project**: add `-Project '<substring>'` (matches the project-hash
  folder name, e.g. `-Project 'winwrap'` or `-Project 'source-repos'`).
- **Case-sensitive**: add `-CaseSensitive`.

## Rules

- Pass the term in single quotes; if it contains a single quote, double it (`''`).
- Don't pre-list files or `Test-Path` anything — the function handles missing
  history itself.
- After the call, summarise the result briefly: how many sessions/hits, and the
  most relevant ones. If `-ShowLines` output is dense JSONL, pull out the
  human-readable gist rather than dumping raw lines.
- If nothing matched, say so and suggest a broader/looser pattern.
