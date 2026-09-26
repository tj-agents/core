# Code review — Feature/PluginHarnessGrants

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `0cc3de6`  `(2026-09-26)`
**Judgment:** `approved`

## Review pass — 2026-09-26 — full

**Candidate base:** `1c9ba93`
**Candidate head:** `0cc3de61bc15d1a27b43329689806438b2cb5e41`
**Candidate branch:** `Feature/PluginHarnessGrants`
**Candidate scope:** `all` `(24 paths)`
**Work-order path:** `reviews/Feature-PluginHarnessGrants.md`
**Work-order mode:** `new`
**Pass judgment:** `approved`

**Rules routed:** root `AGENTS.md` (canonical `.agents/`, generated `plugins/*` via
`sync-generated.ps1`).

**Coverage:** read the full diff in the parent. The focus was on what a permission grant can approve.

- **`harness_grant.py`:** only a full-command `fullmatch` grants. Paths must be quoted, absolute, free of
  shell metacharacters, and without a trailing backslash. The origin must be on github.com and its owner
  on the shipped trust list. The default branch comes from `origin/HEAD`. Sync is refused on the default
  branch. Removal needs a registered linked worktree whose head is on `origin/<default>`. Git itself
  still refuses a dirty tree without `--force`, and `--force`/`-D` never match. Branch deletion needs an
  existing non-default branch already on `origin/<default>`.
- **`merge_review_gate.grant_if_trusted`:** runs only after every existing check passes, only for the
  canonical Claude envelope, and never for Codex. Sibling `deny` still wins by most-restrictive merge.
- **`denial_prompt.py`:** it can only emit `retry` or `ask`, never `allow`. A record is keyed on
  session, tool and exact input, used once, and expires after 15 minutes.
- **`hook_runtime`:** a missing or malformed trust list grants nothing. The base plugin's copy has no
  trust file beside it, so it grants nothing.

**Validation:** `test_harness_grant`, `test_denial_prompt` (7 tests, including pruning), `GrantTests`
and `test_process_standards` all pass. `sync-generated.ps1 -Check` and `update_catalog_digests.py
--check` pass at this head.

### Findings

- [x] **G1 — LOW — native-general** — `.agents/hooks/denial_prompt.py`
  A denied call that was never retried left its record in the temp directory forever. Fixed in
  `0cc3de6`: each new denial prunes records past the TTL, with a test.
- [x] **G2 — MEDIUM — native-general** — `.agents/hooks/merge_review_gate.py`
  `grant_if_trusted` was called but not defined after the worktree was recreated, so the gate would
  raise at the end of every clean review. Fixed in `283ab0b`; `GrantTests` covers it.
