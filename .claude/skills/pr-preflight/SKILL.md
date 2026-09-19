---
name: pr-preflight
description: Read-only readiness gate answering whether the current branch is clear to open or enqueue a PR right now, run before you do. Checks it is a real capitalized Type/Name branch rather than the default one, that the local is not behind its own remote or tracking a deleted one, that it is current with base, that all code is committed while docs may ride uncommitted, whether a PR already exists, that no generated version-bump PR is explicitly red while healthy or pending automation remains out of scope, that no published-package cut-over is half-done, and that the targeted local checkpoint was run rather than a full solution build — then reports GREEN with the next command or every blocker with its exact fix. Changes no state beyond a fetch. Use when the user asks whether they can PR this, are clear to PR or merge, or wants a check before opening or landing one.

kind: operation
domain: process
model: claude-sonnet-5
effort: medium
---

# Is this branch clear to PR?

One read-only pass answering a single question: **is this branch clear to open, or enqueue, a PR right now?**
It runs the preconditions that — when missed — get a PR rejected, ejected, or built on stale state, and
reports a plain **GREEN (go)** or a list of blockers each with its exact fix.

## Read-only — this procedure never changes state

Inspection commands only. It does **not** edit a ledger, commit, push, checkout, pull, rebase or merge. The one
write it may perform is a `git fetch` to refresh remote-tracking refs; it never touches the working tree, the
index, or any branch.

## Why each check exists

- **Synchronize once immediately before final review.** Base movement before that point blocks. After an
  exact-head review, `review-reconcile` preserves disjoint base-only movement and the merge group validates
  the combined tree. Relevant evidence or a changed candidate head blocks. The local must also remain in
  sync with its own remote.
- **Only an explicitly red generated version-bump PR is a repository-wide merge gate.** A healthy or pending
  pre-existing sync is automation-owned and out of scope; do not wait for, review or mutate it. Red means the
  shared pin is known broken, so opening more work behind it only parks the new PR.
- **A published-package refactor is never left half-done.** A namespace or type move in a publishable package
  is an expand → republish → sync cut-over whose definition of done is **the old-identity grep returning
  zero** across the repo. A PR opened mid-cut-over is out of sync by construction
  ([`plans`](../plans/SKILL.md) owns the rule).
- **Docs ride uncommitted; only code blocks.** Uncommitted markdown, plans and scratch notes travel with the
  next commit and are not worth a word. Only uncommitted **code** means the PR would ship incomplete, or be
  reviewed against stale committed history.

## Checks

Run the deterministic local pass once:

```bash
python .agents/workflows/workflow_ops.py --workflow-run-id <id> delivery-preflight --descriptor <review-descriptor> --base origin/main
```

It returns branch and exact-head identity, upstream and base currency, code versus documentation dirtiness,
review reconciliation, and every local blocker. Do not reconstruct those fields with separate shell calls.

1. **On a real feature branch.**

   ```bash
   git rev-parse --abbrev-ref HEAD
   ```

   The default branch → **blocker** (nothing to PR; branch first). Not `<Type>/<Name>` with a capitalized
   prefix → warn; [`git-branching`](../git-branching/SKILL.md) owns the naming rule.

2. **Local in sync with its own remote.**

   ```bash
   git fetch -q origin
   git status -sb | head -1
   ```

   `[gone]` → **blocker**: the remote was deleted, so the branch already merged; return to a clean base
   rather than PR a dead branch. `[behind N]` → **blocker**: local is stale; pull first. `[ahead N]` → note
   the unpushed commits. Not a blocker for opening a PR (that pushes), but a blocker for landing one.

3. **Currency with base.** Before final review, any base commit missing from the branch blocks and must be
   synchronized. After review, reconcile movement against candidate paths and routed rule identities.
   Preserve an exact reviewed head when they are disjoint. Synchronize, validate, and review the changed
   head when they overlap.

4. **All code committed.**

   ```bash
   git status --porcelain
   ```

   Any uncommitted **code** path → **blocker**: commit first, because review runs on committed history. Only
   markdown, plans or scratch docs dirty → fine; say "docs ride along" and move on without fuss.

5. **Existing PR for this branch.**

   ```bash
   gh pr view --json number,state,url --jq '{number,state,url}'
   ```

   Already `OPEN` → do not open another; the next step is a push if ahead, then the merge procedure.
   `MERGED`/`CLOSED` → report it; most likely return to a clean base and start fresh.

6. **No explicitly red version-sync gate.**

   ```bash
   gh pr list --state open --search "head:chore/platform-sync" --json number,title,url
   ```

   If one exists, read its checks once. Red → surface it as blocking so it gets triaged. Pending or green →
   it is not a blocker; leave its automation alone and continue without polling it.

7. **No half-done published-package cut-over.** Skip entirely if the branch touched no publishable contract.
   Otherwise run the rename's definition-of-done grep for the **old** identity across the repo, excluding
   build output. Any hit outside a written allowlist → **blocker**: the cut-over is out of sync.

8. **The targeted local checkpoint is present.** Confirm the branch records the required generators and
   invariant checks, the smallest affected build, and focused unit tests. **Do not run a full solution build
   or integration matrix here** — exact-head PR CI owns those, per
   [`remote-validation`](../remote-validation/SKILL.md).

## Verdict

- **GREEN — clear to PR.** State it plainly and give the next command: push if ahead, then
  [`open-pr`](../open-pr/SKILL.md) for a new PR, or [`merge`](../merge/SKILL.md) if one is already open.
- **Not clear.** One blocker per line, most-blocking first, each with the exact procedure that fixes it. Fix
  nothing here — report and stop.

One short go/no-go, no preamble: inspect → verdict → stop.
