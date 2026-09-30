# Code review — Fix/ClaudeLauncherFromPlugin

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `89561a1`  `(2026-09-29)`
**Judgment:** `approved`

## Review pass — 2026-09-29 — full

**Candidate base:** `68979e5137e681c0ac605e0c02917a47f0d122b4`
**Candidate head:** `bdeb4c3`
**Candidate branch:** `Fix/ClaudeLauncherFromPlugin`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:6c551d23fc12babbd25d4250ee3d9b018a96793912f738a75d58f982389a7b3f` `(18 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\claude-launcher-review-1\review\cb7f17c443cc1368c25ce510f60dc1684d365dc48c6e4634661a85c07fe96b16`
**Candidate bundle identity:** `sha256:5312b50d8b804519cd502ba885ebaf72dac7815c6a4bd746c8bbb2b12593f5fd`
**Work-order path:** `reviews/Fix-ClaudeLauncherFromPlugin.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

### Findings

- [x] **CL1 — MEDIUM — native-general** — `.agents/machine/scripts/claude_terminal_profile.py:47`
  `ensure()` decodes every existing profile as UTF-8. A UTF-16 profile written by Windows PowerShell 5.1
  or an ANSI one with a non-ASCII character fails, the hook reports "not installed" into session
  context, and because both paths share one comprehension the second profile is skipped too. Fix:
  detect UTF-8/UTF-16 BOMs, fall back to the system code page, write back in the same encoding, and
  handle each profile independently.
- [x] **CL2 — LOW — native-general** — `.agents/machine/scripts/claude_terminal_profile.py:51`
  The marker check counts but does not order markers, so an end marker before the start marker raises
  an unpacking error instead of the malformed-block message. Fix: also require END after START.
- [x] **CL3 — LOW — test-impact** — `tests/handoff-launchers.tests.ps1:428`
  Typing `claude` was exercised only under pwsh 7. Fix: repeat the plain-subcommand and session
  assertions under Windows PowerShell 5.1 through its own profile.

## Review pass — 2026-09-29 — incremental

**Candidate base:** `bdeb4c3`
**Candidate head:** `89561a1`
**Candidate branch:** `Fix/ClaudeLauncherFromPlugin`
**Candidate scope:** `all`
**Work-order path:** `reviews/Fix-ClaudeLauncherFromPlugin.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

### Findings

No finding retained. UTF-8-BOM, UTF-16 and code-page profiles decode, gain the ASCII block and are
written back in their own encoding; each edition is handled independently; an END before START is
malformed. Seven profile tests, the generator tests and `handoff-launchers.tests.ps1` (including
Windows PowerShell 5.1) pass.
