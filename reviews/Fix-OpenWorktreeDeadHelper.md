# Docs review — Fix/OpenWorktreeDeadHelper

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `8d28889`  `(2026-09-27)`
**Judgment:** `approved`

## Review pass — 2026-09-27 — full (docs)

**Candidate base:** `81b3340`
**Candidate head:** `8d288892a28d1fb764fee7e34211f4b635bfabff`
**Candidate branch:** `Fix/OpenWorktreeDeadHelper`
**Candidate scope:** `all` `(4 paths, meta-only)`
**Work-order path:** `reviews/Fix-OpenWorktreeDeadHelper.md`
**Work-order mode:** `new`
**Pass judgment:** `approved`

**Lens coverage:** accuracy, contradiction and followability, reviewed in the parent.

- `scripts/worktrees.ps1` is absent from this repository (deleted in `4021ceb`) and isn't shipped by
  the plugin.
- The new rows agree with `engineering:merge` Step 5, which already uses the helper when it's present
  and native Git otherwise.
- `retire` without the helper reports instead of deleting, which keeps the "never substitute a manual
  deletion" rule intact.
- No test pins the old wording.
- Docs reachability reports 0 errors. `sync-generated.ps1 -Check` and the digest checks pass.

### Findings

None.
