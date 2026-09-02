---
name: big-review-all
description: Drive every remaining stage of one canonical staged big review to completion unattended, keeping dependency-ordered stages serial while the review pipeline may parallelize only independent read-only lenses or subregions inside the active stage. Use to do all stages, finish a big review, or run the entire staged pass.
domain: process
---

# Drive a staged review to completion

This is a thin unattended driver over `big-review`, not a second review lifecycle. The strong parent owns
the loop and the canonical `reviews/<branch-slug>.md` work order.

Derive the current branch's canonical work order. If the user names a file, normalize it to a
repository-relative path and reject it unless it equals the derived path exactly. The file must be in
staged mode with `[ ]` or `[~]` coverage, or in `parent-finalization` with every area `[x]` and incomplete
`Cross-area notes status`, `Parent summary status`, judgments, status, anchor watermark, or required
security watermark. A fully finalized file has nothing to drive; later commits route to `incremental-review`.

Run the next stage through `big-review`, inspect the parent-written coverage and cross-area notes, then run
the next remaining stage or parent finalization. Keep stages strictly serial because later stages consume
earlier notes and share one judgment. Do not spawn a subordinate that owns a stage or writes the work order,
and do not allow a lens to subdispatch. The canonical review pipeline may concurrently run only independent
read-only lenses or disjoint subregions within the active frozen stage.

Stop only when:

- every area is `[x]`, `Cross-area notes status` and `Parent summary status` are `complete`, parent
  synthesis set final judgments and status to `complete`, and the reviewed and any required security
  watermarks equal the staged anchor;
- a genuine human/external gate has an owner, action, and objective resume condition; or
- a dispatch or stage remains invalid after its one focused recovery and parent fallback.

Apply one plan checkpoint when the whole staged review completes, a blocking finding changes the next action,
or ownership transfers. Ordinary area completion does not rewrite a plan ledger.

Report the canonical work order, number of stages completed in this pass, finding counts, final watermark,
and whether the pass completed or the exact terminal gate.
