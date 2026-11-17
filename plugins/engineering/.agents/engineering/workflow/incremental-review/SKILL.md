---
name: incremental-review
description: Review only the commits added since a completed review, or the changed patches of a rebased branch or stack, through the review utility. Use after fixes or later commits on a reviewed branch.

kind: workflow
domain: process
---

# Incremental review

Owns selecting the delta since a completed review; `engineering:review` runs the review itself over that
delta. The reviewed head comes from the previous review's reported range.

- Head equals the reviewed head, or has the same tree: nothing new; report that and stop.
- Head descends from the reviewed head: review `<reviewed-head>..<head>` through the
  `review` Stage 3 native layer and any focused lens the delta needs. Earlier findings keep their text
  and severity.
- The branch was rebased or restacked: compare the patch series and review only added, changed or removed
  patches and conflict resolutions. Equivalent patches keep their earlier review.
- The earlier comparison cannot be recovered: say so and run a full `review`; never guess a baseline.

```bash
git range-diff <old-base>..<reviewed-head> <new-base>..<head>
# "=" lines keep their review; "!", "<" and ">" lines are the patches to review.
```

Report the exact range reviewed, new findings and the new reviewed head.
