# Code review — Fix/MergeWorktreeCleanupFallback

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `4b0166d091550117b4e7c00e4882b44119255d95`  `(2026-09-25)`
**Judgment:** `approved`

## Review pass — 2026-09-25 — full

**Candidate base:** `b8566ebe57a3afe1ea2cda3788263c0f6a91804c`
**Candidate head:** `cbfec336ee70e6cc559ac0c2003b2bd64cc2b07e`
**Candidate branch:** `Fix/MergeWorktreeCleanupFallback`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:9a38503033dde932c380de0f36511cbd64057d213af3baab9dae9c6499d7b61e` `(19 paths)`
**Candidate bundle:** `C:\Users\tommy\source\repos\tj-agents\core\.git\agent-workflow\runs\worktree-cleanup-merge-workflow-20260925\review\6e2d49fbb22c935aa4cfc68afbf8af42390906946d7324ed9fb834dd02e8a194`
**Candidate bundle identity:** `sha256:6c07fe1a18c901213d1ba71c89cb097d708fad7cadf72b63135adbac6ea6f94f`
**Work-order path:** `reviews/Fix-MergeWorktreeCleanupFallback.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

**Lens coverage:** helper-selected `native-general` and `workflow`. Both read-only lens dispatches
were rejected because this account cannot launch their fixed model, so the owning session performed
the documented parent fallback over the immutable bundle.

### Findings

- [x] **MW1 — MEDIUM — workflow** — `.agents/engineering/workflow/merge/SKILL.md:212-221`
  The workflow resolves the primary checkout but still shows `./scripts/worktrees.ps1` for the preferred
  helper and describes helper absence only by its relative spelling. `git -C` does not change the shell's
  working directory, so a merge running from the linked worktree can probe or invoke the wrong checkout.
  This is material when the helper exists only on the fetched default branch: the workflow falls through
  incorrectly, or invokes a stale linked-worktree copy. Resolve the helper under `<primary-checkout>`, test
  that exact path, and invoke that exact path.

  **Resolved:** the workflow now constructs the helper with `Join-Path <primary-checkout>`, tests that exact
  file with `Test-Path -LiteralPath ... -PathType Leaf`, and invokes the resolved path. The focused process
  standards test protects all three clauses.

- [x] **MW2 — MEDIUM — workflow** — `.agents/engineering/workflow/merge/SKILL.md:229-232`
  The native fallback says to require a fresh open-PR query but supplies neither the query nor its accepted
  output. That leaves the most important preservation gate to agent interpretation immediately before
  worktree removal. Give the exact `gh pr list` command bound to the target branch and require its JSON
  result to be the empty array before continuing; protect that executable contract in the focused test.

  **Resolved:** the native fallback now runs `gh pr list` against the bound repository and target branch,
  requests only `number,url`, and continues only for the exact empty JSON array. The focused test protects
  the command and acceptance shape; 15 process-standard tests and both generation checks pass.

- [x] **MW3 — LOW — workflow** — `plans/merge-worktree-cleanup/MERGE_WORKTREE_CLEANUP_PLAN.md:45-54`
  Phase 2 ships a shared workflow capability, but the phase has no consumption contract. The selected plan
  standard requires every capability-producing phase to pin who consumes it and the exact output/call shape.
  Add the engineering merge workflow's consumers and the helper/native-Git branch plus final inventory shape.

  **Resolved:** Phase 2 now names the `engineering:merge` agent consumer, its synchronous inputs, the exact
  helper-versus-native selection, the inline final-inventory handoff to Step 6, and the blocking failure
  result. The plan-artifact tests pass.

### Verified and dismissed during synthesis

- The native path refuses a primary or detached target, checks tracked and untracked state, requires the
  target head to be merged into the fetched default, uses non-forced `worktree remove` and lowercase
  `branch -d`, and treats both command failure and a residual path as incomplete cleanup.
- The final inventory is an explicit blocking transition before publication/sync handling, so the audit gate
  cannot be mistaken for deferred cleanup.
- Canonical ownership and generated mirrors are correct; release metadata and catalog digests agree, and the
  bootstrap fixture repair derives its expected release instead of pinning the prior release.
- No security-sensitive behavior, secrets, tokens, or machine-identifying content were introduced.

## Review pass — 2026-09-25 — incremental

**Candidate base:** `cbfec336ee70e6cc559ac0c2003b2bd64cc2b07e`
**Candidate head:** `4b0166d091550117b4e7c00e4882b44119255d95`
**Candidate branch:** `Fix/MergeWorktreeCleanupFallback`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:3d68913da8b825f3adcd96fa7871cf01c6335000a1d49dde44aea218adc90010` `(8 paths)`
**Candidate bundle:** `C:\Users\tommy\source\repos\tj-agents\core\.git\agent-workflow\runs\worktree-cleanup-merge-workflow-20260925\review\2dea080e3aca85bca2fc227fc0dbd52f51615a6d730df83c787139481baa7518`
**Candidate bundle identity:** `sha256:3cc2cf39347238ccef604071e25633d098275506acf30b01004b207517bd3ac3`
**Work-order path:** `reviews/Fix-MergeWorktreeCleanupFallback.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

### Findings

No new findings. The delta contains only the three recorded remediations, their focused contract
assertions, generated mirror/catalog updates, and the review work order. The primary-checkout helper
resolution and repository-bound open-PR query now have executable shapes, the native safety gates remain
conservative, and the plan consumption contract agrees with the workflow's synchronous final inventory.
Canonical and generated workflow files match, catalog and generation checks pass, and the focused process
and plan-artifact suites are green.

Fresh `native-general` and `workflow` lens processes were unavailable because their fixed model is not
supported by this account; the owning session completed the documented parent fallback over the immutable
eight-path bundle.
