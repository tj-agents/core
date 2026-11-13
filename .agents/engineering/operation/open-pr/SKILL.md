---
name: open-pr
description: Create or edit a pull request whose body has nonempty Why and What sections, validated before the forge write and again after it. Use before any PR creation or description edit.

kind: operation
domain: process
---

# Open a pull request

Owns creating or updating a PR and its body. `engineering:branching` owns which PR the work belongs to and
the selected profile decides how many PRs deliver it; `engineering:merge` lands it.

1. Run `engineering:pr-preflight` and stop on any blocker it names.
2. Only committed work enters a PR. Commit completed code per `engineering:committing`; uncommitted
   Markdown rides the next commit. Push through `engineering:push` when the branch has no upstream or has
   unpublished commits.
3. Draft from the delivery head, grouped by behavior, never commit by commit:
   `git log --oneline <base>..<head>` and `git diff --stat <base>...<head>`. The title states the change in
   about seventy characters. The body has explicit, nonempty **Why** (the problem and what prompted it) and
   **What** (the resulting change) sections, as headings or `**Why:**`/`**What:**` paragraphs; add
   decisions, exclusions or a test plan only when they say something. State what was verified and never
   claim an unobserved result. Keep whatever attribution the harness and repository mandate.
4. Validate the body file before the write, then create or edit (`--base` only for a non-default base):

```text
python -B <engineering-package>/workflows/pr_body.py --body-file body.md    # python3 on Linux/macOS
{"valid": true, "errors": []}    -> gh pr create --head <branch> --title "<title>" --body-file body.md
{"valid": false, "errors": [...]} -> fix the body; no forge write
```

5. Read the saved body back with
   `python <workflow-ops> --workflow-run-id pr-body-<n> pr-body-check --pr <url>`, where `<workflow-ops>`
   is `.agents/workflows/workflow_ops.py` in source or `workflows/workflow_ops.py` in the installed engineering
   package. Repair and recheck on failure; a connector's success response is not validation. The same
   checks apply to the CLI and to a forge connector.
6. When the PR delivers a tracked item, move it to In Review through the selected profile's provider; a
   tracker error never blocks the PR.

Report with a clickable PR URL in the same message, a Markdown link in rich chat or a plain URL in a
terminal. When asking for approval of one or more PRs, lead with one plain sentence describing the overall
improvement once they merge. Opening a PR is not a stopping point: continue the authorized work, and wait
on CI through `engineering:remote-validation`'s monitor.
