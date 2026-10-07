---
name: clip
description: Put text on Tommy's Windows clipboard so he can paste it straight into Teams, an email or a terminal instead of drag-selecting it out of the transcript. Use when drafting a message for someone to paste, and whenever he says "copy that", "put that on my clipboard", "clip that". NOT for GitHub review comments — review drafts are previewed in the reply and posted from here, never pasted. Applies in every repo, personal and work.
kind: utility
domain: machine
---

# clip

Terminal text is awkward to select and picks up stray indentation. Anything Tommy is meant to paste
goes on his clipboard.

## How

Write the exact text to a UTF-8 file in the scratchpad, then:

```powershell
& '<skill-directory>\scripts\copy-draft.ps1' -Path '<absolute-path-to-file>'
```

`copy-draft.ps1` sits beside this file, the same way `handoff-claude` carries its launcher.

The script reads UTF-8, trims trailing blank lines, copies, and reads the clipboard back to verify —
it throws rather than reporting a success it did not achieve. It prints the character count; relay
that, so a silent failure can't pass as done.

**Never pipe the text through the command line.** Quoting mangles backticks, `$`, curly quotes and
emoji, and a heredoc through PowerShell is worse. The file is the interface.

## What goes on the clipboard

**The message with its markdown intact** — that is the point of copying rather than having him
drag-select. Teams renders markdown in the compose box, so backticks around a service, identity,
resource group, role or flag survive as inline code and make the specifics stand out, and a triple
backtick fence renders a command as a block he can copy straight out. Keep them in.

What stays out is anything that belongs to the transcript rather than the message: no "here's the
message:" preamble, no `>` quoting, no bullet markers you added for readability, no surrounding
fence around the whole thing.

One thing at a time. The clipboard holds one item, so if you drafted a message and a command, copy
the one he asked for and say the other is ready on request. Copying overwrites silently, so do it as
the last step before telling him it is there — a later copy in the same turn strands him pasting the
wrong thing.

**The clipboard is volatile and nothing tells you it changed.** Any copy anywhere on the machine
replaces it — a terminal drag-select most of all, which lands plain text with the terminal's own
wrapping and indentation baked in and no HTML flavour. A message copied several turns ago is not
still there. If he says the backticks did not render, do NOT assume you omitted them: read the live
clipboard first (`HTML Format` present? how many `<code>`?) and re-copy. The script verifies both
flavours off the live clipboard at write time and throws if the HTML is missing, so a bare
"Copied ..." line means it truly landed at that moment — not that it survived since.

## A command Tommy has to run himself

**Put it on the clipboard. Never print it for him to copy out of the terminal.** Terminal copy is
where wrapping and indentation get baked in, and it silently breaks a long command on paste. This is
the same failure that put a line break into a Teams message mid-sentence.

Use `-PlainOnly` for a command: no HTML flavour, and backticks stay literal because in a shell they
are syntax, not markup. Show the command in your reply too so he can read it, but the clipboard copy
is the one he runs.

Do not invent a wrapper script to dodge the problem — the clipboard already solves it, and a
throwaway script file is machinery he then has to clean up. Write a script only when the thing is
genuinely worth keeping and re-running.

A command that creates or moves a credential still goes to him to run, and pipes the value straight
to its destination so it never reaches the transcript. Never echo the value, and never run such a
command yourself — a half-finished attempt can leave a live credential stranded.

**Teams messages only, for the HTML flavour.** GitHub review comments (`draft-comment`,
`respond-comments`) are previewed in the reply and posted from here, not pasted, so they never go on
the clipboard.

## Say so in one line

End with a short line naming what is on the clipboard and its size, e.g. "On your clipboard (538
chars)." Not a paragraph about the clipboard.
