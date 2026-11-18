---
name: incremental-review
description: Review changes since a completed review, using its recorded watermark for descendant commits and comparing old and new patch series for a design sweep of rebased work or a stack. Use for later commits, remediation checks or a relative design sweep; workflow evidence advances only after parent synthesis over a reconciled candidate.

kind: workflow
domain: process
---

# Incremental review selector

This changes only candidate resolution. The executable review pipeline, lens isolation, result validation,
parent synthesis, work-order schema, and authorization boundary belong to `review` and `review-lifecycle`.

## Resolve the existing work order

Resolve the current candidate branch's work order with `<engineering>/workflows/workflow_ops.py review-path`. If the user names a file,
resolve it and reject it unless it equals that derived canonical path exactly. The file
must already represent this branch. If no work order exists, route to `review`. If its status is
`in-progress`, resume or restart that frozen pass rather than starting a competing incremental pass.

Read the single top-level `Reviewed up to commit:` marker. It is the only source of truth for the completed
watermark. Validate that its SHA resolves. A work order without the marker has no completed watermark;
route to `review`.

## Freeze the delta

A design sweep of already reviewed work is a bounded call to the `review` utility over only the later
changes. For a rebased branch or stack, resolve each layer's old reviewed base/head and current parent/head
from its existing pass and stack map, then compare the patch series:

```bash
git range-diff <old-base>..<reviewed-head> <current-parent>..<current-head>
```

Review added, changed or removed patches and conflict resolutions; equivalent patches retain their earlier
review. Keep stack layers in dependency order and include changed cross-layer contracts in the sweep.
Do not substitute a merge-base-to-head full review because the watermark is no longer an ancestor.
If the old comparison cannot be recovered, report that missing baseline instead of guessing.
A sweep reports its exact comparison and coverage without claiming a new delivery watermark. A delivery
workflow reconciles the rewritten candidate and its preserved evidence before stamping completion; the
ordinary descendant-only preparation below cannot establish that reconciliation. For a requested design
sweep, call `review` with the resolved bounded changed-patch scopes, report its assessment and return here;
do not continue into descendant-only preparation or reselect the sweep from that supplied candidate.

Set the prior completed watermark as the full base SHA and the current target head as the full head SHA.
Freeze the exact sorted changed paths and their SHA-256 digest and materialize the candidate bundle exactly
as `review` Stage 1 requires. Record branch, exact scope, canonical work-order path, and `append` mode.

- Base equals head: report that nothing new exists and leave the artifact unchanged.
- Head is not a descendant of the watermark: stop; the work order does not describe this history.
- Non-empty valid delta: set the work-order status to `in-progress`, append one immutable pass descriptor,
  and invoke `review` Stages 3-7 over that descriptor.

The `review` Stage 3 native layer and every selected fresh lens consume `<watermark>..<frozen-head>`, the
native reviewer with the watermark as its frozen base; IDs continue
without renumbering, prior findings and dispositions stay unchanged, and the parent appends only new
deduplicated findings. A later live `HEAD` never widens this pass.

On successful synthesis, set status back to `complete` and move the single top-level watermark to the
frozen head. When this pass follows `address-review`, verify the original finding text, severity, completed
pass judgment, and earlier candidate identity are unchanged apart from permitted status/disposition updates.
The new pass may move the top-level current judgment only when its own synthesis completes. A routine docs
repair reviews only its affected delta, then reassesses the semantic risk; new consequential content returns
the pass to ordinary review.

## Report

A non-empty completed pass is one material review transition for an owning plan. Report the exact range,
new finding counts, canonical work order, and new watermark. Empty or invalid ranges do not rewrite a ledger
or artifact.
