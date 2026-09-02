---
name: open-pr
description: Open or update the pull request for the current branch with the forge's own CLI once a stable substantive candidate needs remote validation. Covers the read-only readiness gate, continuing actionable work after opening instead of stopping by default, drafting the title and body from committed history, keeping required attribution, why end-to-end labels belong to merge, and that marking a draft ready is not merge authorization. Use when the user says open a PR, raise a PR, create the PR, or PR this. Landing it is the merge procedure's job.
domain: process
---

# Opening a pull request

Open or update the PR for the current branch. **During implementation, open a draft PR at the first stable
candidate that needs remote validation**; later stable candidates push to that same PR. This procedure does
**not** enqueue, choose the end-to-end tier, or wait for a merge — that is
[`merge`](../merge/SKILL.md).

**A draft is the remote validation environment, not a claim that delivery is ready.** Mark it ready only
once review and exact-head CI are green — and marking it ready is still not merge authorization.

## What is and is not this procedure's call

- **The end-to-end tier and its labels belong to [`merge`](../merge/SKILL.md)**, read fresh in the merge group. Do
  not set them at PR-create time; you would only have to reconcile them at merge.
- **Docs ride uncommitted; only code blocks a PR.** Uncommitted markdown, plans and scratch notes travel with
  the next commit and are not worth mentioning. Only uncommitted **code** means the PR would ship incomplete.
- **Keep whatever attribution the harness and the repository mandate** — a commit trailer, a PR-body footer,
  or both. Never strip one to tidy the body.
- **Use the forge's own CLI and nothing else.** Where a machine also carries an issue-tracker-linked PR
  procedure for a *different* organisation, that procedure is not this one and none of it — work-item links,
  board transitions, assignees — carries across. The user's own instructions say which repositories are
  which; this doc does not guess.

## Steps

### 1. Readiness gate

Run [`pr-preflight`](../pr-preflight/SKILL.md), or its checks inline, and stop on any blocker it names. Fix the blocker
with the procedure it names, then come back. **Do not open a PR over a blocker.**

### 2. Uncommitted work

```bash
git status --porcelain
```

Docs dirty → fine, they ride the next commit. Any completed **code** → run its targeted local checkpoint per
[`remote-validation`](../remote-validation/SKILL.md), then commit it per
[`committing`](../committing/SKILL.md). A PR contains only committed work.

### 3. Push the branch

```bash
git push -u origin HEAD
```

Only when there is no upstream, or the branch is ahead of its remote.

### 4. Draft the title and body from the branch itself

- **Title**: concise, under about seventy characters, stating the change — not "fix bug" but the actual fix.
- Read the branch to draft from, dropping merge commits:

  ```bash
  git log --oneline origin/main..HEAD
  git diff --stat origin/main...HEAD
  ```

- **Body** — factual, about the change and nothing else:

  ```text
  ## Summary
  <1–3 sentences: what this does and why>

  ## What changed
  - <area / behaviour bullets, drawn from the commits>

  ## Test coverage
  - <targeted checks completed locally, plus the exact-head gates delegated to PR CI>

  ## Notes
  - <a non-default end-to-end tier and why; a version-sync consequence if publishable source changed;
    anything a reviewer needs>
  ```

  Drop a section with nothing to say. Keep the mandated attribution footer.

### 5. Create the PR

```bash
gh pr create --draft --title "<title>" --body "$(cat <<'EOF'
<body>
EOF
)"
```

Add `--base <branch>` only when targeting something other than the default. Omit `--draft` only when the work
is already complete, reviewed, and exact-head-CI-ready.

### 6. Report and continue

Print the PR URL. Opening a draft is not a context boundary: continue implementing, reviewing, or observing
the candidate when the current authorization and context still cover that work. If landing is genuinely next,
[`merge`](../merge/SKILL.md) owns it. Update a plan only if PR creation is part of a material ownership handoff or
context-ending state; never merely because this procedure reported.
