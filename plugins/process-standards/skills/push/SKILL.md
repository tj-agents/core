---
name: push
description: Push one stable substantive candidate and prove the remote actually carries it — verify the remote-tracking ref and any open PR head both equal the exact pushed head. Covers publishing known non-merge-ready GitHub review heads without CI, diagnosing a rejected, unconfigured, unauthorised or hook-blocked push instead of retrying blindly, never force-pushing unasked, and never manufacturing a ledger-only transport tail. Use whenever the user wants to push commits, git push, push this branch, publish a diff for human review, or recover a failed push.
domain: process
---

# Pushing a verified head

Push the current branch and prove the remote actually carries the work. The happy path is one command; the job
is to make the push land and to say plainly when it did not.

**A command returning success is not evidence.** What counts is a refreshed ref comparison: the
remote-tracking ref, and any open PR's head, equal to the exact commit you meant to publish.
[`committing`](../committing/SKILL.md) owns when to push at all: local commits are frequent, while pushes are
reserved for stable candidates, real handoffs, and meaningful published checkpoints.

## Step 1 — resolve the push state before mutating the remote

Record the current branch, its upstream, the remote tip, the commits to send, and any open PR and its head.
Resolve whether the work is plan-managed. If a material checkpoint is due, it must already be part of the
substantive candidate commit. Never manufacture a ledger-only tail in order to push.

## Publish a known non-merge-ready GitHub head without CI

When a push only exposes the diff for human review or preserves a remote checkpoint, skip CI only when a
later non-marker HEAD commit is already required independently of the review outcome: planned implementation
or a known fix remains, or the chosen base reconciliation will create a merge commit on this branch. The agent
may make this decision without being asked. A draft flag, outstanding review, or behind-base state alone is
not evidence; name the real gate and the later non-marker commit it requires.

Inspect the workflow triggers first. For GitHub Actions triggered by `push` or `pull_request`, put `[skip ci]`
in the pull request's HEAD commit message. It is not a `git push` flag; GitLab's `-o ci.skip` does not apply.

- Amend only an unpushed HEAD. Never rewrite a published commit merely to add or remove the marker without
  explicit force-push authorization.
- Required checks remain pending, so the review head must not be treated as mergeable.
- After the ref checks, poll `gh run list --commit "$work_head" --limit 100
  --json event,headSha,status,url,workflowName` for 30 seconds. Pass when no run from an inspected `push` or
  `pull_request` workflow appears by expiry; ignore documented non-suppressed events.
- The next substantive commit must omit the marker so CI validates the whole PR. When CI is the only remaining
  merge gate, or no later substantive push is expected, push normally; never manufacture an empty trigger commit.

The marker does not suppress events such as `pull_request_target`. GitHub documents its exact limitations in
[Skipping workflow runs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs).

## Step 2 — push the candidate once

After any review-head amendment, record `work_head=HEAD`, then push that exact head.

```
git push
git push -u origin <current-branch>   # first push on a branch with no upstream
```

## Step 3 — verify the work head landed

Fetch the branch, then require its remote-tracking ref to equal `work_head`. When an open PR exists, require
the PR's head to equal `work_head` as well. **Do not create a successful push checkpoint unless both
comparisons pass.**

## Step 4 — when the push or the verification fails

Read the error, fix the actual cause, then retry the same terminal push and verification.

- **Rejected because the remote has new commits** (`fetch first`, non-fast-forward): `git pull --rebase`,
  resolve conflicts, push. When a rebase is not safe or the conflicts are messy, stop and tell the user
  rather than force-pushing.
- **No upstream configured:** re-run with `git push -u origin <current-branch>`.
- **No remote at all:** say so. Do not invent one.
- **Auth or permission failure:** report it — the user fixes credentials. Do not retry in a loop.
- **A pre-push hook failed:** fix the underlying cause. Never `--no-verify` unless the user explicitly asks.
- **Never force-push** (`--force`, `--force-with-lease`) unless the user explicitly asks for it.

If the candidate push stays blocked or cannot be verified, **do not report success.** Record a genuine blocker
only when it changes the durable recovery state; never push merely to publish the failure observation.

## Report

- **Straight through:** one line, nothing more.
- **Something needed fixing:** what the problem was, what you did, and the final state — *"remote was two
  commits ahead, rebased and pushed"*.
- **Could not push:** what is blocking it and what the user must do next.

Keep it terminal: push, fix if needed, summarise, stop.
