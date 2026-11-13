---
name: address-debt
description: Pick one high-value tech-debt item from the selected provider, fix it properly, verify it and deliver it under the selected profile. Use when working through tech debt or one debt item end to end.

kind: workflow
domain: process
---

# Address tech debt

Owns taking a debt item from the selected provider to a verified fix. Read
[the shared recording contract](../../../workflow/resources/problem-records.md) first; the selected profile's
provider lists, reads, updates and closes debt, and a provider failure blocks only that repository's record
operation. A parent Workflow run's goal, branch and checkout are reused, never duplicated.

1. **Scope.** Work in the current repository. From a directory that is not a repository but holds several
   child repositories, survey their debt as one list; the picked item's repository then owns the run.
2. **Pick fast.** List titles and severity in one pass. Rule an item out only for a fact one command
   settles: already in flight (`git branch -a`, `git worktree list`, open PRs), or needing a decision only
   the owner can make. Take the first genuinely high-value, self-contained item and say why in two lines;
   say so when an item is stale or wrong. A small related fix in a file the item already touches rides along
   as its own commit; anything bigger becomes its own debt record.
3. **Branch.** Start from the fetched default under `engineering:branching`; use
   `engineering:open-worktree` only when a concurrent writer needs isolation.
4. **Fix and verify.** Find the root cause and make the long-term fix. Build the affected projects and run
   their focused tests; local E2E is not a routine gate.
5. **Close the loop.** Commit each item separately, update it with the verification evidence and close it
   through the provider only once its resolution condition holds. Deliver through `engineering:open-pr`;
   the selected profile decides how many PRs.

Independent read-only surveys may go to host-native subagents (`evidence-explorer`,
`test-impact-analyst`); picking, the fix and every write stay with the parent.

```text
The provider lists debt WI-320, "remove the duplicate parser branch", as the first unblocked high-value
item in api/ with no branch or worktree in flight. Branch from origin/main, remove the duplicate branch,
run the parser unit tests, commit, record the passing tests on WI-320 and close it through the provider.
```
