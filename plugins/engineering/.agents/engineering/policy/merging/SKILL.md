---
name: merging
description: Land a reviewed PR on its exact head with `gh pr merge --auto --match-head-commit`, one background monitor and a worktree sweep; never retry a genuine failure. Use when landing or watching a PR.

kind: policy
domain: process
---

# Merging

Owns the rules for landing a PR. `engineering:merge` runs the steps, `workflow:run` owns the user's authority
to merge, and the repository's GitHub rulesets are the merge gate.

1. Review the exact head once through `engineering:review`.
2. The PR body states Why and What; validate it once before the forge write.
3. Arm auto-merge bound to that head, so required CI must pass on exactly the reviewed commit.
4. Start one background monitor (`engineering:remote-validation`) and read GitHub once when it wakes.
5. After the merge, retire the checkout through `engineering:merge`'s worktree sweep and cleanup proof.

```bash
gh pr merge 42 --auto --squash --match-head-commit "$(git rev-parse HEAD)"
```

Replace `--squash` with the repository's merge method. Each wake resolves to one state:

- **Merged**: report the landing SHA and stop.
- **A check failed**: report the job and its run log and stop. Never retry or toggle a genuine failure.
- **Conflicted**: GitHub silently disables auto-merge on a `DIRTY` PR. Update the branch, review the delta and
  re-arm.
- **Query error**: surface the failed command and its stderr; never swallow it as "still waiting".

Load `workflow:continue` and its delivery reference only when the user asks for unattended progress.

## Transferred checkout cleanup

When an authorized `workflow:handoff` transfers cleanup, the successor removes the old checkout from a
verified surviving checkout only after the predecessor has stopped using it, then verifies the path is gone.
A command error or residual path is incomplete cleanup.
