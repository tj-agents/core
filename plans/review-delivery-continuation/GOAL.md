# Review-stamp delivery continuation

## Objective

Repair the shared review and persistent-delivery guidance so a completed review work-order commit has one explicit, recoverable delivery transition instead of leaving the PR owner stale or asking again for already-recorded same-PR merge authority.

## Authorization and isolation

This is the bounded standards-defect repair authorized by `engineering:session-guidance`. It owns only `Fix/ReviewDeliveryContinuation` at `C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-ReviewDeliveryContinuation`; PR #226 and its continuation runtime state remain outside scope.

## Diagnosis

`engineering:review` ends by prohibiting a review-only commit, but `workflow_ops.review_is_current` and the merge-review gate recognize that stamping the review watermark is itself a `reviews/`-only commit. `persistent-delivery` requires a rebind on every new head but does not make the review-stamp rebind and owner checkpoint a required transition. The contradictory guidance caused an independent review commit to advance the PR head while leaving its continuation owner stale.

The delivery runtime's treatment of a bound prior watermark after that rebind is a separate merge-control defect. It is recorded in `BUGS.md` and deliberately excluded here because the repository safety gate rejected a change that would relax that check without an explicit proof mechanism.

## Scope

1. Make the one review-stamp commit and immediate delivery/owner rebind sequence explicit, preserving same-PR authorization.
2. Add a focused standards regression and validate the changed source paths.

## Completion

Source guidance tells the owner to rebind its delivery artifact and continuation immediately after the single review-stamp commit, preserves same-PR authority, and the focused standards regression passes.

## Progress

On 2026-10-13, the review and persistent-delivery guidance was aligned and
`test_review_workflows.py` gained assertions for the one review-stamp commit, same-PR binder refresh,
owner rebind, and preserved authority. `B008` records the separate fail-closed delivery-runtime mismatch.
The generated-output refresh and focused test could not complete because `pwsh.exe` is denied by the host
and subsequent command helpers fail while loading managed Windows PowerShell; generated output remains
untouched and uncommitted.

## Progress

On 2026-10-13, the review and persistent-delivery guidance was aligned and
`test_review_workflows.py` gained assertions for the one review-stamp commit, same-PR binder refresh,
owner rebind, and preserved authority. `B008` records the separate fail-closed delivery-runtime mismatch.
The generated-output refresh and focused test could not complete because `pwsh.exe` is denied by the host
and subsequent command helpers fail while loading managed Windows PowerShell; generated output remains
untouched and uncommitted.

## Progress

On 2026-10-13, the review and persistent-delivery guidance was aligned and
`test_review_workflows.py` gained assertions for the one review-stamp commit, same-PR binder refresh,
owner rebind, and preserved authority. `B008` records the separate fail-closed delivery-runtime mismatch.
The generated-output refresh and focused test could not complete because `pwsh.exe` is denied by the host
and subsequent command helpers fail while loading managed Windows PowerShell; generated output remains
untouched and uncommitted.

## Next Steps

Restore a usable Windows PowerShell host, run `.agents/sync-generated.ps1`, run the focused
`test_review_workflows.py` regression and generation check, then review and deliver the guidance-only
repair. The separately recorded runtime merge-control defect requires an explicit proof-oriented design
before implementation.
