# Code review — Fix/ExternalPluginSourceSync

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `f550b6ae07f252f0254eb749e9e7a4f83da30315`  `(2026-10-04)`
**Judgment:** `approved`

## Review pass — 2026-10-04 — full

**Candidate base:** `06480cfbdf376fac825e4b0581f3b4b6a8e0f5a2`
**Candidate head:** `f550b6ae07f252f0254eb749e9e7a4f83da30315`
**Candidate branch:** `Fix/ExternalPluginSourceSync`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:0dec2ddea4c02717b82d79bfece61b76a71c7f47f7c19cb3ecd0f5b246f662ca` `(10 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\review-fix-ext-83-final\review\de32f58dd7f801d5e4b50769c3d3f7977f11bf11ca2bb64861b1772078162c45`
**Candidate bundle identity:** `sha256:9a133855c0fb221e2f2e71bba476467284770b27724307d7b03da12551f1e92b`
**Work-order path:** `reviews/Fix-ExternalPluginSourceSync.md`
**Work-order mode:** `new`
**Pass judgment:** `approved`

Native layer: the host's built-in `code-review` skill, run three times over this branch as it converged
(twice on intermediate heads, once over the full frozen range `06480cfbdf37..f550b6a`). No security-path
or routed-skill trigger; security and repository-route layers did not apply.

### Findings

- [x] **F1 — MEDIUM — native** — `.agents/machine/scripts/claude_standards_sync.py:170`
  A plugin's own source entry could express the marketplace's own repository differently (scheme,
  trailing slash, `.git` suffix, host case) and compare unequal by plain string equality, wrongly
  splitting it into a needless external probe group. Fixed by adding `normalize_url()` and comparing
  normalized values.
- [x] **F2 — LOW — native** — `.agents/machine/scripts/claude_standards_sync.py:170`
  `external_groups()` carried a design-narration docstring restating its own logic, which the user's
  global instructions ban. Removed; the function name and body already say what it does.
- [x] **F3 — MEDIUM — native** — `.agents/machine/scripts/claude_standards_sync.py:170`
  The first `normalize_url()` lowercased the whole URL including the repository path, so two distinct
  repositories on a case-sensitive git host differing only by path case would wrongly merge into one
  external group and get probed/updated against only one of them. Fixed by folding case on the host
  segment only, preserving path case.
- [x] **F4 — LOW — native** — `.agents/machine/scripts/claude_standards_sync.py:170`
  `normalize_url()` had no SCP-style SSH handling, so `git@host:org/repo.git` and the equivalent
  `https://host/org/repo.git` for the same repository normalized to different strings, risking the same
  false split as F1/F3 for an SSH-configured remote. Fixed by folding SCP-style and `ssh://` forms to the
  same host/path form as HTTPS.

Not findings, assessed and dismissed:
- Whether `claude plugin update <identity>` actually honors a plugin's own `marketplace.json` source
  override rather than the marketplace's repository: not a defect in this diff. The plan's live cause
  investigation already verified this host behavior directly before this branch existed (`claude plugin
  update rust@tj-agents --scope user` moved the install to the plugin's own commit with the marketplace
  checkout unchanged), and this PR's own live `--check` acceptance against `cris-authz` confirms the
  detection side now agrees with that behavior.
- `current()`'s `install.version == remote[:12]` fallback does not match the `<12hex>-<8hex>`
  directory-naming suffix Claude Code uses for externally-sourced git-subdir installs. Pre-existing
  format quirk predating this branch; causes at most one harmless redundant update per already-current
  install on the first run after this lands, self-correcting once state is recorded under the new key.
  Out of this fix's scope.
