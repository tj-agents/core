# Code review — Docs/CloseMergeWorktreeCleanup

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `a47cea8d9c7300e0ae7195146a253dfac3b9479c`  `(2026-09-25)`
**Judgment:** `changes-requested`

## Review pass — 2026-09-25 — full

**Candidate base:** `ce038fb871f736a02e381e0adb0caa66c2ed2a1e`
**Candidate head:** `a47cea8d9c7300e0ae7195146a253dfac3b9479c`
**Candidate branch:** `Docs/CloseMergeWorktreeCleanup`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:b54b962a3ab0afeb5199360f34dc09379232ba767b17e0e0b54c050eb8f791d5` `(35 paths)`
**Candidate bundle:** `C:\Users\tommy\source\repos\tj-agents\core\.git\agent-workflow\runs\merge-worktree-host-retarget-review-20260925\review\efaa3f98ee695d69a10adfccafe671da896e30d84ed327ed92b562eb787c149a`
**Candidate bundle identity:** `sha256:ab26e6fbdeef44fc9a6ba676dee9a825030cf34635519f6629972659ff207f46`
**Work-order path:** `reviews/Docs-CloseMergeWorktreeCleanup.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

### Findings

- [x] **MW4 — MEDIUM — workflow** — `.agents/engineering/workflow/merge/SKILL.md:212`
  The retarget/handoff block is unconditional, but the same Step 5 explicitly supports a branch developed
  directly in the primary checkout. In that path the host is already attached to the directory that remains,
  so a harness without native `/cd` would launch a needless successor and transfer cleanup ownership even
  though no linked active directory needs releasing. Gate retargeting on the recorded target being the active
  linked worktree and differing from the primary checkout; let the primary-developed branch continue locally.

  Resolved by comparing the delivery-bound target, primary checkout, and current host attachment before
  retargeting. Primary-checkout work continues locally; only an active linked target that differs from the
  primary enters `base:cd`. The process-contract regression suite covers both branches and passes all 17 tests.

The helper-selected `review-lens` contexts could not launch because their fixed model is unavailable on this
account. The owning session performed the documented parent fallback over the immutable bundle for both
native-general and workflow coverage. No changed path matched the merge gate's security inventory, so no
security marker is required.
