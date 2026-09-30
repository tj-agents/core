---
name: open-pr
description: Open or update the review that owns the resolved delivery slice, integrating corrections from other branches before publication. Use when opening a PR, publishing a correction, or showing the corrected review.

kind: operation
domain: process
lane: L4
---

# Opening a pull request

Resolve the work and its owning review under `engineering:git-branching`. **During implementation, open a draft PR at the first stable
candidate that needs remote validation**; later stable candidates within that slice push to the same
PR. A new substantive slice gets its own PR under `engineering:git-branching`, stacked when dependent.
An existing draft is not permission to keep expanding its scope. This procedure does
**not** enqueue, choose the end-to-end tier, or wait for a merge — that is
`engineering:merge`.

**A draft is the remote validation environment, not a claim that delivery is ready.** Mark it ready only
once review and exact-head CI are green — and marking it ready is still not merge authorization.

## What is and is not this procedure's call

- **The end-to-end tier and its labels belong to `engineering:merge`**, read fresh in the merge group. Do
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

Run `engineering:pr-preflight`, or its checks inline, and stop on any blocker it names. Fix the blocker
with the procedure it names, then come back. **Do not open a PR over a blocker.**

### 2. Uncommitted work

```bash
git status --porcelain
```

Docs dirty → fine, they ride the next commit. Any completed **code** → run its targeted local checkpoint per
`engineering:remote-validation`, then commit it per
`engineering:committing`. A PR contains only committed work.

### 3. Publish to the owning review

Follow preflight's ownership action. Integrate corrections into the owning review's branch when needed,
then use `engineering:push` for the stable candidate. If the review already contains the correction,
continue with its title and body. An assessed new slice publishes its selected branch.

Push only when the delivery branch has no upstream or has unpublished commits.

### 4. Draft the title and body from the branch itself

- **Title**: concise, under about seventy characters, stating the change — not "fix bug" but the actual fix.
- Read the branch to draft from, dropping merge commits:

  ```bash
  git log --oneline <actual-base>..HEAD
  git diff --stat <actual-base>...HEAD
  ```

- For a stack, use the immediate parent's branch as `<actual-base>` and `--base`; link the parent,
  owning delivery map and next layer when present. Show this layer's delta and its cumulative checks.

- **Body** — written for a reviewer who has never seen the branch: why it exists, then what it does. Draw
  it from the diff and commits, grouped by behaviour, never commit by commit:

  ```text
  ## Why
  <the problem or gap this closes, what prompted it, and what was true before; link the PR or issue it
  follows>

  ## What
  - **<area or behaviour>** — <what changed, with its reason wherever the diff alone would not say>

  ### Decisions worth the reviewer's attention
  <each non-obvious choice, the alternative it rejected, and why>

  ## Not in this PR
  - <deliberately excluded scope, known follow-ups, pre-existing failures a reviewer will hit>

  ## Test plan
  - [x] <checks run locally and passed>
  - [ ] <what a reviewer or the exact-head PR CI still has to confirm>

  ## Notes
  - <a non-default end-to-end tier and why; a version-sync consequence if publishable source changed>
  ```

  A small change collapses to two paragraphs, `**What:**` then `**Why:**`, with no headings. Drop a section
  with nothing to say. State what was verified and what was not; never claim an unobserved result. A visible
  UI change attaches screenshots per `engineering:pr-screenshots`. Keep the mandated attribution footer.

### 5. Update the owning PR or create the assessed slice's review

For an existing review, use `gh pr edit <owning-url> --title <title> --body-file <body-file>` and
preserve its resolved base. For a slice whose scope assessment established a new review:

```bash
gh pr create --draft --head <delivery-branch> --title "<title>" --body-file <body-file>
```

Add `--base <branch>` only when targeting something other than the default. Omit `--draft` only when the work
is already complete, reviewed, and exact-head-CI-ready.

### 6. Bind the delivery owner

A PR with nothing owning its wait is what turns every later transition into a question for the user.
For a stack child, record its parent dependency in the owning ledger. A binding may monitor its checks,
but `engineering:merge` must verify that its base is eligible before acting. After a parent lands,
reconcile the child and refresh this binding so the continuation does not rely on stale topology.

```bash
python .agents/workflows/workflow_ops.py --workflow-run-id delivery-bind-pr-<n> delivery-bind
```

It resolves the repository's recorded standing merge authorization against this head and writes the binding
artifact; `engineering:persistent-delivery` owns what that means. On Claude the
delivery-binding gate has already run it for you — then it is bound, not to be bound again. Enter the
harness's `persistent-workflow` skill to give that binding a continuation.

### 7. Report and continue

Print the PR URL. Opening a draft is not a context boundary: continue implementing, reviewing, or observing
the candidate when the current authorization and context still cover that work. If landing is genuinely next,
`engineering:merge` owns it. Update a plan only if PR creation is part of a material ownership handoff or
context-ending state; never merely because this procedure reported.
