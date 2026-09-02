---
name: merge-docs
description: Land a documentation or meta-only change as its own fast PR, bypassing the merge queue and its end-to-end gate through the sanctioned admin merge, because a diff with zero runtime blast radius has nothing for that gate to prove. Covers the in-scope path list that is a hard precondition rather than a hint, why a comment-only edit to a CI workflow still fails it, the docs review that is the only gate such a change gets and the pure-close-out exemption from it, the skip label that keeps a queue fallback cheap, and confirming no publish fired. Use when the user says merge docs, docs pr, or wants markdown, agent-instruction, plan or skill changes shipped without the full queue — and route anything touching runtime, package, schema, deployment or test-selection paths to the queue instead.
domain: process
---

# Landing a meta-only change

A documentation or meta change has **zero product-runtime blast radius**, so the merge queue's end-to-end
gate is pure waste on it — tens of minutes to prove nothing. Agent-process hooks still run their focused
tests. This lands such a change through a small
admin-merged PR: the queue bypass that [`merge`](../merge/SKILL.md) reserves for exactly this diff, made into its
own one-command flow.

**Meta-only is a hard precondition, not a hint.** If the diff touches anything with runtime, package,
schema, deployment or test-selection consequence, **stop and use [`merge`](../merge/SKILL.md)** — the queue must
gate it.

## The path list is the gate

- **In scope:** `**/*.md`, the agent-instruction trees (`.agents/**`, `.claude/**`, `.codex/**`), `plans/**`,
  `docs/**`, `AGENTS.md`, `CLAUDE.md`, `README*`.
- **Agent-standards source repositories only:** repository-owned process hooks, workflow helpers, tests and
  their generated plugin mirrors are meta-only when the repository's root instructions and generator name
  them as `workflow`-plugin assets and they cannot affect a product build or runtime. This exception includes a
  worktree-management script owned by the process standard; it does not make arbitrary `scripts/**` meta-only.
- **Out of scope → route to [`merge`](../merge/SKILL.md):** any runtime or product source, `package.json`,
  lockfiles, workspace config, project files, central package management, **CI workflow definitions** (they
  are test-selection logic, and a comment-only edit to one still fails this gate by path), migrations,
  deployment artifacts.
- **When unsure, it is not meta-only.**

The same list defines a docs review's scope in [`docs-review`](../docs-review/SKILL.md) and, where a repo
gates its CI matrix on it, the classification its workflow computes. Keep the three in agreement: a list
that drifts turns a cheap merge into an unreviewed one.

## Steps

### 0. Docs review first, unless the branch is a pure close-out

A meta PR still gates on a review — just [`docs-review`](../docs-review/SKILL.md), not a code review; it has
no runtime to code-review. A **pure close-out** — net diff deletions only — is exempt, as that doc's own
scope states, and merges straight through. Otherwise confirm a clean docs review of this branch before the
admin merge below; if none exists or findings are open, stop and hand off a docs-review prompt naming this
worktree and branch. **The bypass skips the queue, so this is the only gate the change gets.**

### 1. Branch off the fetched remote base, never a local one

An isolated capitalized `<Type>/<Name>` branch already cut from the remote base is fine as it stands — do
not create a second branch solely to change the type prefix to `Docs`. From the default branch or an
unrelated checkout, create a `Docs/<Name>` branch in its own worktree so a dirty main checkout is never
disturbed ([`git-branching`](../git-branching/SKILL.md) owns the naming):

```bash
git fetch origin --quiet
git worktree add <path> -b Docs/<Name> origin/main
```

### 2. Prove the diff is meta-only

```bash
git fetch origin --quiet
git diff --name-only origin/main...HEAD
```

Every path must match the in-scope list. **Any out-of-scope path → stop and hand off to
[`merge`](../merge/SKILL.md).**

### 3. Commit and push

Commit anything outstanding per [`committing`](../committing/SKILL.md), including whatever trailer the
repository mandates, then `git push -u origin HEAD`.

### 4. Open the PR

Plain `gh pr create --fill`, or a short explicit title and body ([`open-pr`](../open-pr/SKILL.md) owns the shape
when the body is worth drafting). Add the skip label so a fallback into the queue still skips the end-to-end
suites:

```bash
gh pr edit <n> --add-label skip-e2e
```

### 5. Admin-merge — bypass the queue

```bash
gh pr merge <n> --merge --admin      # no --delete-branch: the queue rejects that flag
gh pr view <n> --json state,mergeCommit
```

If `--admin` is refused — an unauthorized local token, most often — fall back to the queue **with the skip
label**: `gh pr merge <n> --merge --auto`, then poll for `MERGED` per [`merge`](../merge/SKILL.md)'s loop. **Never
force past a red check.**

### 6. Return to a clean base and clean up

```bash
git checkout main && git pull --ff-only origin main
```

```powershell
./scripts/worktrees.ps1 close -Worktree <path> -PullRequest <n>
```

### 7. Confirm no publish fired

A meta-only diff touches no publishable source, so nothing republishes and no version-sync PR opens. Confirm
it against the repo's own publish path filter rather than assuming, then stop.

## Report

One short report: PR number and merge commit, that it bypassed the end-to-end gate because the diff was
meta-only, and that the base is clean. If the diff turned out not to be meta-only, report that you stopped
and routed to [`merge`](../merge/SKILL.md).
