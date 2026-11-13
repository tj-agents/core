---
name: pr-preflight
description: Read-only go/no-go before opening or landing a PR - feature branch, upstream sync, committed code, the owning PR and the base currency GitHub requires. Use before open-pr or merge.

kind: operation
domain: process
---

# Is this branch clear to PR?

Owns one read-only pass that answers whether the current branch is clear to publish or land. It never
changes the working tree, index or branches; a fetch only refreshes remote-tracking refs.

```text
git fetch -q origin
python .agents/workflows/workflow_ops.py --workflow-run-id pf-1 delivery-preflight   # python3 on Linux/macOS
{"ownership": {"pr_url": null, "action": "create"}, "warnings": ["branch-name"], "blockers": [], "ready": true}
```

Pass `--pr-url <url>` when the work belongs to a known PR. No PR yet is green: `create` means
`engineering:open-pr` publishes the branch. `update` means push to the existing PR. A name outside
`<Type>/<Name>` only warns; `engineering:branching` owns naming.

| Blocker | Fix |
|---|---|
| `default-branch`, `detached-head` | Branch first per `engineering:branching` |
| `local-behind-upstream` | Pull through `engineering:pull` |
| `uncommitted-code` | Commit per `engineering:committing`; uncommitted Markdown rides along |
| `delivery-integrate` | Apply the corrections on the owning PR's branch |
| `delivery-reconcile-review` | The PR is closed or cross-repository; resolve which review owns the work |
| `base-update-required` | GitHub requires an up-to-date branch: merge the base, check, push |
| `merge-conflict` | Merge the base, resolve, check, push |

Confirm the focused local checks per `engineering:remote-validation` ran; never run a full build or
integration matrix here. Report one verdict: green with the next action, or one blocker per line, most
blocking first, each with its fix. Fix nothing here.
