---
name: incremental-review
description: Select and run the canonical isolated review workflow over only commits added after the canonical work order's completed watermark, appending one frozen pass and moving the marker only after parent synthesis. Use for new commits since a prior full or staged review, including remediation commits that require a fresh watermark.
domain: process
---

# Incremental review selector

This changes only candidate resolution. The executable review pipeline, lens isolation, result validation,
parent synthesis, work-order schema, and authorization boundary belong to `review` and `review-lifecycle`.

## Resolve the existing work order

Derive `reviews/<branch-slug>.md` from the current candidate branch. If the user names a file, normalize it
to a repository-relative path and reject it unless it equals that derived canonical path exactly. The file
must already represent this branch. If no work order exists, route to `review`. If its status is
`in-progress`, resume or restart that frozen pass rather than starting a competing incremental pass.

Read the single top-level `Reviewed up to commit:` marker. It is the only source of truth for the completed
watermark. Validate that its SHA resolves. A legacy work order with no marker and no recorded frozen pass
requires one human answer:

```bash
git log -20 --format='%h  %ci  %s'
```

Ask which commit the existing review covered; never infer it from dates or prose.

## Freeze the delta

Set the prior completed watermark as the full base SHA and the current target head as the full head SHA.
Freeze the exact sorted changed paths and their SHA-256 digest and materialize the candidate bundle exactly
as `review` Stage 1 requires. Record branch, exact scope, canonical work-order path, and `append` mode.

- Base equals head: report that nothing new exists and leave the artifact unchanged.
- Head is not a descendant of the watermark: stop; the work order does not describe this history.
- Non-empty valid delta: set the work-order status to `in-progress`, append one immutable pass descriptor,
  and invoke `review` Stages 3-7 over that descriptor.

Native/general review and every selected fresh lens consume `<watermark>..<frozen-head>`; IDs continue
without renumbering, prior findings and dispositions stay unchanged, and the parent appends only new
deduplicated findings. A later live `HEAD` never widens this pass.

On successful synthesis, set status back to `complete` and move the single top-level watermark to the
frozen head. When this pass follows `address-review`, verify the original finding text, severity, completed
pass judgment, and earlier candidate identity are unchanged apart from permitted status/disposition updates.
The new pass may move the top-level current judgment only when its own synthesis completes.

## Report

A non-empty completed pass is one material review transition for an owning plan. Report the exact range,
new finding counts, canonical work order, and new watermark. Empty or invalid ranges do not rewrite a ledger
or artifact.
