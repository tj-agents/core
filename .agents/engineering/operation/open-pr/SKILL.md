---
name: open-pr
description: Create or edit a pull request with explicit nonempty Why and What sections, validating the proposed body before the forge write and the saved body afterward. Use before any PR creation or description edit through a CLI or connector, publishing a correction, showing the corrected review, or handing existing PRs over for approval.

kind: operation
domain: process
---

# Opening a pull request

## Validate the body before writing

Every new or edited PR description has explicit, nonempty **Why** and **What** sections. Explain the
problem or missing behavior under Why and the concrete resulting change under What. Use Markdown
headings, or `**Why:**` and `**What:**` paragraphs for a small change. Unlabelled prose does not satisfy
this contract, even when it discusses the reason and change.

Prepare the complete body in a UTF-8 file and run the packaged `workflows/pr_body.py` validator before
any CLI or connector mutation. Resolve the package root from this skill, not a guessed checkout path.
Use `python` on Windows and `python3` on Linux/macOS:

```text
python -B <engineering-package>/workflows/pr_body.py --body-file <proposed-body-file>
# {"valid": true, "errors": []} permits the write; a nonzero exit leaves it pending.
```

Read the authoritative saved body and run Step 6's `pr-body-check` after the write, before binding,
marking ready or reporting the PR. Preserve attribution and existing scope. A connector's successful
write response alone is not body validation. Reuse the same validator for both hosts and both write paths.

Resolve the work and its owning review under `engineering:branching`. **During implementation, open a draft PR at the first stable
candidate that needs remote validation**; later stable candidates within that slice push to the same
PR. A new substantive slice gets its own PR under `engineering:branching`, stacked when dependent.
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
- **Use the repository's forge connector or native CLI.** Apply the same body preflight and saved-body
  validation to both. Where a machine also carries an issue-tracker-linked PR
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

### 4. Draft the title and body from the delivery head

- **Title**: concise, under about seventy characters, stating the change — not "fix bug" but the actual fix.
- Read the resolved review branch, using its current head as `<delivery-head>`. For a new slice use
  the candidate head being published. Drop merge commits:

  ```bash
  git log --oneline <actual-base>..<delivery-head>
  git diff --stat <actual-base>...<delivery-head>
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

  A small change uses the labelled paragraphs defined above. Drop optional sections with nothing
  to say. State what was verified and what was not; never claim an unobserved result. A visible
  UI change attaches screenshots per `engineering:pr-screenshots`. Keep the mandated attribution footer.

### 5. Update the owning PR or create the assessed slice's review

For an existing review, use `gh pr edit <owning-url> --title <title> --body-file <body-file>` and
preserve its resolved base. For a slice whose scope assessment established a new review:

```bash
gh pr create --draft --head <delivery-branch> --title "<title>" --body-file <body-file>
```

Add `--base <branch>` only when targeting something other than the default. Omit `--draft` only when the work
is already complete, reviewed, and exact-head-CI-ready.

### 6. Check the published body and bind the delivery owner

After every create or body edit, fetch and validate the authoritative body before binding or reporting,
including when the head and existing binding are unchanged:

For the Python workflow helper examples below, use `python` on Windows or `python3` on Linux/macOS:

```bash
python <workflow-ops> --root <delivery-checkout> --workflow-run-id pr-body-<n> pr-body-check --pr <owning-url>
```

`<workflow-ops>` is `.agents/workflows/workflow_ops.py` in a source checkout or `workflows/workflow_ops.py`
under the installed engineering package. Use `--repo <owner/repo>` when naming a PR number in another
repository. If validation fails, repair the body, preserve its attribution and repeat the check.

For an existing review whose head is unchanged, retain its binding and continuation. A metadata update
from a correction checkout returns that review's URL with its owner still active. When binding a new
review or refreshing a pushed head, run from the review's delivery checkout with its explicit PR number.

A PR with nothing owning its wait is what turns every later transition into a question for the user.
For a stack child, record its parent dependency in the owning ledger. A binding may monitor its checks,
but `engineering:merge` must verify that its base is eligible before acting. After a parent lands,
reconcile the child and refresh this binding so the continuation does not rely on stale topology.

```bash
python <workflow-ops> --root <delivery-checkout> --workflow-run-id delivery-bind-pr-<n> delivery-bind --pr <n>
```

It resolves the repository's recorded standing merge authorization against this head and writes the binding
artifact; `engineering:persistent-delivery` owns what that means. Enter the
harness's `workflow:continue` skill to give that binding a continuation.

### 7. Report and continue

For pending CI, invoke `agent:listen` with the bound monitor before reporting the wait.
On its completion event, report readiness or the next required action through this reporting contract.

When the canonical goal has a fenced `completion` record, retain every unchecked PR task there with the
PR's repository, number, full head SHA, task text, owner, and next action. Keep those entries until a fresh
completion check observes the task resolved.

Include a clickable PR URL in the same user-facing message whenever reporting a created or updated PR
or requesting its review, approval or merge, even when the link appeared earlier or in tool output.
Use a Markdown link in rich chat and a plain URL in terminals, outside code formatting.

When handing PRs from explicitly adopted Personal projects over for Tommy's approval, select
`personal:bot-identity` and follow its approval handoff procedure for the PRs in that response.
This also applies to later readiness reports and approval requests for existing PRs.

```text
Ready for your approval: [PR #123](https://github.com/owner/repo/pull/123).
Personal project: select personal:bot-identity for the approval command accompanying that link.
```

Opening a draft is not a context boundary: continue implementing, reviewing, or observing
the candidate when the current authorization and context still cover that work. If landing is genuinely next,
`engineering:merge` owns it. Update a plan only if PR creation is part of a material ownership handoff or
context-ending state; never merely because this procedure reported.
