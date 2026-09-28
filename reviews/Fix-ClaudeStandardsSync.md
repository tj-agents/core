# Code review — Fix/ClaudeStandardsSync

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `826b883`  `(2026-09-28)`
**Judgment:** `changes-requested`

## Review pass — 2026-09-28 — full

**Candidate base:** `531c0fdcd90c1688e3f0284fd30e96961ccbffc8`
**Candidate head:** `826b8835d30bcbb6c3bc17ee0659e530dde1adb2`
**Candidate branch:** `Fix/ClaudeStandardsSync`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:b76e0e32923da366a60a3239b2774d48b1bac5616c646f686b549b5d5a9097b7` `(35 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\claude-standards-sync-review-1\review\aa0a01f351223938361800c581fe4d1dbbbda7a3cf0ea917440c6d4323adc2b6`
**Candidate bundle identity:** `sha256:e9e9297be4f304ff75f1dfd5c60a494d9149cfc6c22eb5a39d0e88b6c25cb4d3`
**Work-order path:** `reviews/Fix-ClaudeStandardsSync.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

### Findings

- [x] **CS1 — MEDIUM — native-general** — `.agents/machine/scripts/claude_standards_sync.py:239`
  `exclusive()` treats a lock older than `STALE_LOCK_SECONDS` (900 s) as abandoned, but nothing renews
  it while held. One run can legitimately exceed that (180 s per marketplace refresh plus 120 s per
  plugin update, serial), so a second launch unlinks a live lock and both processes write
  `installed_plugins.json` and the same checkout concurrently. Fix: have the lock expose a renewal and
  touch its mtime before every host call, so a live holder is never older than one call's timeout.
- [x] **CS2 — LOW — workflow** — `.agents/machine/handoff-claude/SKILL.md:27`,
  `.agents/machine/open-claude/SKILL.md:43`, `plans/repo-declared-config/CLAUDE_STANDARDS_SYNC.md:55`
  The docs describe one `standards:` line; an update prints a start line and a result line, plus one
  per failure. Fix: describe `standards:` lines, one pair per updated marketplace.
- [x] **CS3 — LOW — workflow** — `README.md:101`
  "Run it directly from any other shell" gives a checkout-relative path to readers who only installed
  the plugins. Fix: say it runs from a core checkout.

Dismissed during synthesis: `shell/agents.ps1` dot-sourcing `..\.agents\machine\scripts\agent-cli.ps1`
is not a packaging breach — `shell/` only runs from a checkout wired by that checkout's own
`install.ps1`, so the sibling tree is always present, and `Sync-ClaudeStandards` already prefers the
installed plugin's refresher. The shell function omitting `-Claude $target` is deliberate: `$target`
may be the npm `claude.ps1` shim, which Python cannot execute, while the script's resolver prefers the
native `claude.exe`.
