---
name: merge
description: Land the current branch's PR on its reviewed head with auto-merge, one background monitor and a worktree sweep. Use when the user says merge, merge it or land this PR.

kind: workflow
domain: process
---

# Merge a PR

Owns landing one PR and returning the checkout to a clean base. `engineering:merging` owns the rules; the
repository's GitHub rulesets are the merge gate. Never bypass a ruleset or a required check.

1. `gh pr view --json number,state,headRefOid,url` for the current branch. On the default branch or with no
   PR, stop; `engineering:open-pr` opens one. `MERGED` goes to step 5; `CLOSED` stops with a report.
2. Nothing uncommitted or unpushed. `engineering:review` covered the PR head, or a head with the same tree.
3. Validate the saved body once:
   `python <workflow-ops> --workflow-run-id pr-<n> pr-body-check --pr <n>` (`python3` on Linux/macOS).
   `<workflow-ops>` is `.agents/workflows/workflow_ops.py` in source or `workflows/workflow_ops.py` in the
   installed engineering package. Repair a failed body through `engineering:open-pr`.
4. Arm auto-merge on that exact head with the repository's merge method, then start one background
   `monitor --kind pr --id <n> --head <head>` through the host's notification primitive.
5. When it wakes, read GitHub once. A failed check goes to `engineering:failing-tests`; never retry or
   toggle a genuine failure. On merge, move the primary checkout to the fetched default when it holds the
   merged or default branch, then sweep:

```text
gh pr merge 42 --auto --squash --match-head-commit <reviewed-head-sha>
python -B <skill-directory>/scripts/worktree_sweep.py --repo <primary-checkout>    # Windows
python3 -B <skill-directory>/scripts/worktree_sweep.py --repo <primary-checkout>   # Linux/macOS
Result: each merged linked worktree is removed once cleanup_proof.py proves its PR merged at exactly
its head; a worktree with an active launch, a dependent open PR or a refused proof is kept and named.
```

Never force a removal the sweep refused. A branch developed in the primary checkout is deleted with
`git branch -d`, or `-D` once the proof covers a squash merge. Load `workflow:continue` and its delivery
reference only when the user asks for unattended progress.

Report the merge commit, that the base is current and what the sweep removed or kept. A merged PR is not
completion: name any requested outcome that remains.
