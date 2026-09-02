---
name: big-review
description: Select and drive the canonical isolated review workflow for a very large immutable branch diff in resumable, dependency-ordered area stages recorded in the branch's one canonical work order. Use for hundreds or thousands of changed files, a multi-service diff, or to resume one staged review area.
domain: process
---

# Staged review selector

This partitions one frozen candidate into resumable areas. `review` owns the executable native/lens pipeline
and parent synthesis; `review-lifecycle` owns the one artifact at `reviews/<branch-slug>.md`. A staged mode
never creates a `BIG-*` competitor.

## When to use

Use this for an explicit big/staged review, normally more than 300 changed files or several substantial
components. Use ordinary `review` for a one-sitting candidate and `incremental-review` when a completed
watermark already covers the original candidate.

One invocation reviews the next incomplete area unless the user names an area. `big-review-all` drives all
remaining areas through this same selector.

## First run — freeze and partition

Resolve the branch exactly as `review` Stage 1, then freeze its full merge-base, plan-anchor head, exact
sorted changed paths, path-set digest, canonical work-order path, and materialized candidate bundle. Record
the branch, `all` scope, and `new` mode. Every stage reviews `<merge-base>..<plan-anchor>`; never
substitute live `HEAD`.

Derive stages from the frozen diff rather than a remembered repository map:

- only changed paths receive a stage;
- every path belongs to exactly one stage;
- each stage fits one sitting, normally 50-150 files or about 10k diff lines;
- shared contracts and foundations precede consumers, adapters, tests, and UI; and
- unmatched files enter an explicit final `Everything else` stage.

Resolve routed skills and local guidance once from the frozen path set, then map them to the stages that
triggered them. Record route-table identity, applicable skills, local `AGENTS.md`, and security sensitivity
without copying the rules.

Have the parent create the canonical work order with top-level status/current judgment and the staged pass
judgment set to `in-progress`, `pending`, and `pending`, followed by the immutable pass descriptor and:

```markdown
## Coverage

- [ ] <Area> — <N files> — `<exact scope/glob>`

## Rules manifest

Route source: `<path and commit/hash>`

- <Area> — skills: `<qualified names>`; local guidance: `<paths or none>`; security: `<yes/no>`

## Cross-area notes

## Parent finalization

**Cross-area notes status:** `pending`
**Parent summary status:** `pending`
```

Coverage scopes must reproduce the frozen exact path union without overlap. The work order has no completed
watermark until every area and cross-area note is complete.

## Resume and drift

Read the canonical status, plan anchor, coverage, and live HEAD before selecting an area.

- Any `[~]` area was interrupted: discard its partial candidate conclusions, keep confirmed parent-written
  findings, and re-run that area from its frozen descriptor.
- Otherwise select the first `[ ]` area.
- All `[x]` while `Cross-area notes status` or `Parent summary status` is not `complete`, an active-pass
  or current judgment is pending, status is incomplete, the anchor watermark is missing, or a required
  security watermark does not equal the anchor is the `parent-finalization` resume state. Select
  finalization even though no coverage item is open.
- All `[x]` with complete notes and summary status, final judgments, complete status, the anchor watermark,
  and any required security watermark at the anchor means the staged pass is complete when HEAD equals the
  anchor.
- The same finalized state with HEAD beyond the anchor means the original pass is complete and the later
  delta belongs to `incremental-review`; do not create another staged file.
- An unusually large later delta may append a new staged wave to the same canonical work order after the
  parent freezes a new `<prior-watermark>..<head>` descriptor.

Post-anchor commits never enter an unfinished stage. They remain a later incremental pass even while stages
continue against the original anchor.

## Review one area

Set the selected coverage entry to `[~]` before dispatch. Read unresolved cross-area notes targeting it.
Invoke the canonical `review` pipeline over the stage's exact frozen paths and
`<merge-base>..<plan-anchor>`:

- native/general review receives that same scoped descriptor;
- only rules mapped to the stage are loaded;
- relevant fresh `review-lens` contexts receive no sibling conclusions;
- independent read-only lenses or disjoint subregions may overlap, while dependent stages stay serial;
- the parent validates, deduplicates, assigns severity, writes findings, and resolves cross-area notes.

A candidate whose other half lives in a later area becomes one parent-written cross-area note naming the
owning stage and check. Lenses do not edit coverage, notes, or findings and never dispatch another agent.

After synthesis, mark the area `[x]` with the date. When all areas are complete, resolve every cross-area
note, set `Cross-area notes status` to `complete`, write the parent summary, set
`Parent summary status` to `complete`, set the active-pass and top-level current judgments, set status to
`complete`, and stamp the single reviewed watermark at the immutable plan-anchor head. When security
review is required, resume or run it against the frozen stage and stamp its anchor marker only after its
evidence passes parent synthesis. If the live branch moved, route its delta to `incremental-review`. This
finalization is an idempotent parent-owned stage and is not terminal until every listed field is durable.

## Report

The canonical work order is the resume contract. Report the area reviewed, finding counts, remaining areas,
anchor watermark, and file. A plan checkpoints only when the whole staged review completes, a blocking
finding changes its next action, or review ownership transfers.
