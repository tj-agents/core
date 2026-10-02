---
name: pr-preflight
description: Resolve the owning review and check publication readiness across the execution branch, actual base, upstream, committed code, review evidence and slice scope. Read-only apart from refreshing Git refs and runtime telemetry.

kind: operation
domain: process
---

# Is this branch clear to PR?

One read-only pass answering a single question: **is this branch clear to open, or enqueue, a PR right now?**
It runs the preconditions that — when missed — get a PR rejected, ejected, or built on stale state, and
reports a plain **GREEN (go)** or a list of blockers each with its exact fix.

## Read-only — this procedure never changes state

Inspect repository and forge state without editing the working tree, index or branches. A fetch may
refresh remote-tracking refs, and the runtime records its inspection telemetry in Git-private state.

## Why each check exists

- **Synchronize once immediately before final review.** Base movement before that point blocks. After an
  exact-head review, `review-reconcile` preserves disjoint base-only movement and the merge group validates
  the combined tree. Relevant evidence or a changed candidate head blocks. The local must also remain in
  sync with its own remote.
- **Only an explicitly red generated version-bump PR is a repository-wide merge gate.** A healthy or pending
  pre-existing sync is automation-owned and out of scope; do not wait for, review or mutate it. Red means the
  shared pin is known broken, so opening more work behind it only parks the new PR.
- **A published-package refactor is never left half-done.** A namespace or type move in a publishable package
  is an expand → republish → sync cut-over whose definition of done is **the old-identity grep returning
  zero** across the repo. A PR opened mid-cut-over is out of sync by construction
  (`engineering:plans` owns the rule).
- **Docs ride uncommitted; only code blocks.** Uncommitted markdown, plans and scratch notes travel with the
  next commit and are not worth a word. Only uncommitted **code** means the PR would ship incomplete, or be
  reviewed against stale committed history.

## Checks

Run the deterministic local pass once:

```bash
python .agents/workflows/workflow_ops.py --workflow-run-id <id> delivery-preflight --ledger <owning-progress-file> --descriptor <review-descriptor>
```

Omit `--descriptor` before review. For work without a ledger, use `--pr-url <owning-review-url>` when
known. The pass resolves the recorded review against GitHub before returning local readiness, using
its base by default; `--base` supplies the intended base for a slice without a review. It checks the
execution branch, upstream, base currency, dirtiness and review reconciliation in the same pass.

The `ownership.action` routes the next step: `update` uses that review, `integrate` returns corrections
to its branch, `create` continues an assessed slice recorded as `PR: not opened`, and `reconcile-review`
resolves a closed or fork review before publication. `assess-scope` means no recorded owner or branch
review was found: apply `engineering:git-branching` using the request, goal, handoff and history, then
record the resolved review or separate slice. Standalone work can perform these checks inline and
keep the assessment in its existing goal; a ledger is not required just to publish it.

This supported preflight returns nonzero for a blocked route. It does not infer semantic scope from
commit ancestry, nor intercept arbitrary forge commands. The slice assessment below remains required.

1. **On a real feature branch.**

   ```bash
   git rev-parse --abbrev-ref HEAD
   ```

   The default branch → **blocker** (nothing to PR; branch first). Not `<Type>/<Name>` with a capitalized
   prefix → warn; `engineering:git-branching` owns the naming rule.

2. **Local in sync with its own remote.**

   ```bash
   git fetch -q origin
   git status -sb | head -1
   ```

   `[gone]` → **blocker**: the remote was deleted, so the branch already merged; return to a clean base
   rather than PR a dead branch. `[behind N]` → **blocker**: local is stale; pull first. `[ahead N]` → note
   the unpushed commits. Not a blocker for opening a PR (that pushes), but a blocker for landing one.

3. **Currency with base.** Before final review, any base commit missing from the branch blocks and must be
   synchronized. After review, reconcile movement against candidate paths and routed rule identities.
   Preserve an exact reviewed head when they are disjoint. Synchronize, validate, and review the changed
   head when they overlap.

4. **All code committed.**

   ```bash
   git status --porcelain
   ```

   Any uncommitted **code** path → **blocker**: commit first, because review runs on committed history. Only
   markdown, plans or scratch docs dirty → fine; say "docs ride along" and move on without fuss.

5. **Owning review resolved.** Use the runtime's ownership result, or perform the same resolution inline
   under `engineering:git-branching`. Confirm the recorded review's repository, state, head and base.
   A correction branch's missing PR leaves that review unchanged. A closed review needs reconciliation
   with the requested scope before a new slice is selected.

6. **No explicitly red version-sync gate.**

   ```bash
   gh pr list --state open --search "head:chore/platform-sync" --json number,title,url
   ```

   If one exists, read its checks once. Red → surface it as blocking so it gets triaged. Pending or green →
   it is not a blocker; leave its automation alone and continue without polling it.

7. **No half-done published-package cut-over.** Skip entirely if the branch touched no publishable contract.
   Otherwise run the rename's definition-of-done grep for the **old** identity across the repo, excluding
   build output. Any hit outside a written allowlist → **blocker**: the cut-over is out of sync.

8. **The targeted local checkpoint is present.** Confirm the branch records the required generators and
   invariant checks, the smallest affected build, and focused unit tests. **Do not run a full solution build
   or integration matrix here** — exact-head PR CI owns those, per
   `engineering:remote-validation`.

9. **A reviewable delivery slice.** Apply `engineering:git-branching` to the measured diff against the
   actual PR base. An oversized or multi-concern candidate without a recorded split assessment and
   justified exception permitted by that contract (atomicity or frozen-scope recovery) is a blocker:
   decompose and validate it before adding scope or requesting
   final review. For a stack, verify parent/base/head identities, the layer's scope, and CI/protection
   coverage. A green top-of-stack build does not establish that lower layers can land independently.

## Verdict

- **GREEN — clear to publish the resolved slice.** Name the owning review or assessed new slice and its
  next action. Push missing corrections to that review; use `engineering:open-pr` for publication and
  `engineering:merge` when landing is authorized and next.
- **Not clear.** One blocker per line, most-blocking first, each with the exact procedure that fixes it. Fix
  nothing here — report and stop.

One short go/no-go, no preamble: inspect → verdict → stop.
