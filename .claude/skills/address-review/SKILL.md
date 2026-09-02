---
name: address-review
description: Serially resolve open findings in the canonical review work order without changing its frozen candidate, original finding text, severity, or completed pass judgment; verify and commit coherent fixes, then require a fresh incremental watermark. Use when the user explicitly asks to address findings or an implementation workflow already authorized review-and-fix.
domain: process
---

# Address a review serially

This is the separate write side of the review family. It may begin only when the user explicitly requests
fixes, passes `--fix` to `review`, or the original implementation workflow already authorizes repairing
its reviewed candidate. Review-only requests end after the judgment.

Read `review-lifecycle`, then derive the current branch's canonical `reviews/<branch-slug>.md`. If the user
names a file, normalize it to a repository-relative path and reject it unless it equals the derived path
exactly.

Before setting any finding to `[~]` or starting a writer, require the single top-level `Review status` to be
`complete`, the current `Judgment` and active `Pass judgment` to be non-pending final values, and staged
coverage to contain no `[ ]` or `[~]`. The single `Reviewed up to commit:` marker must exist and equal the
active pass's candidate head or staged anchor. When the active path set requires security review, its
`Security-reviewed up to commit:` marker must equal that same head. Otherwise resume review production or
parent finalization first. On a staged work order, the single `Cross-area notes status` and
`Parent summary status` fields must both be `complete`.

## Serial finding loop

Take one open finding or one tightly coupled group, set it to `[~]`, fix it under one exclusive writer, run
the smallest relevant validation, and return control to the parent before selecting the next. Never overlap
writers, even for disjoint files: one parent must observe and accept each resulting tree before another write.

The original candidate base/head/path digest, finding ID, text, severity, lens attribution, and completed
pass judgment are immutable. Remediation may only:

- move a finding from `[ ]` to `[~]` to `[x]`;
- append a concise disposition and fix evidence; or
- mark `[wontfix]` with a final reason and, when work is postponed, create the owning debt entry or issue
  with an objective resolution condition in the same stroke.

Do not reassess a high-confidence review finding as subjective and silently defer it. When part is fixable,
split the blocked remainder and land the fixable part now. A genuinely irreversible or product/architecture
decision stops with its owner and observable resume condition.

Commit each coherent finding or tightly related group locally with explicit pathspec staging. Batch completed
related commits into one stable push only when remote validation or handoff is due. No review result or
subordinate owns staging, commits, severity, or follow-on scope.

## Fresh review after writes

Keep the work order throughout remediation. After any code or durable guidance commit, run
`incremental-review` from its prior completed watermark to the new head. New findings re-enter this serial
loop. Completion requires:

- every original and incremental finding has a terminal disposition;
- the incremental pass is clean;
- `Review status` is `complete`; and
- the top-level watermark covers the fixing head.

Leave the clean artifact as the merge gate. Retire it only after merge according to `review-lifecycle`.

## Continue or report

If a plan uniquely owns the branch, checkpoint only when the whole addressing pass completes, a blocking
finding changes the next action, or ownership transfers. Otherwise run the repository's read-only PR
preflight and report its exact next action.

Report fixed findings, any final dispositions and their durable owner, fixing commits, validation, canonical
work order, and current watermark. Do not re-litigate a completed pass judgment.
