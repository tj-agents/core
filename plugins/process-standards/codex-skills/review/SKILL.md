---
name: review
description: Run the canonical isolated code-review workflow over one frozen branch, PR, commit-range, or path candidate with native/general review, relevant fresh read-only lenses, validated evidence, and parent-only deduplication, severity, judgment, and work-order writing. Use for a first full code review when asked to review a branch or PR; use incremental-review for later commits, big-review for a very large diff, docs-review for a meta-only diff, and address-review for existing findings.
domain: process
---

# Canonical isolated code review

Review one immutable candidate through a mandatory native/general layer and relevant repository-aware lenses.
Subordinate contexts return evidence only. The strong parent validates every result, verifies citations,
deduplicates, assigns severity, makes the final judgment, and is the sole writer of the canonical work order
defined by `review-lifecycle`.

## Arguments and selection

```text
[low|medium|high|max] [<pr-number>|<branch>|<path>] [--comment] [--fix]
```

- Effort applies to the native layer and every lens. `low` and `medium` keep only high-confidence defects;
  `high` and `max` broaden coverage and may retain lower-confidence findings when their uncertainty and
  concrete fix are explicit. With no value, reuse the last review effort.
- No target means the current worktree's branch. A PR resolves its base, head branch, and head SHA through the
  forge. A branch resolves from its default-branch merge base. A path scopes the current branch candidate.
- `--comment` posts finalized findings to the target PR after the work order is complete.
- `--fix` explicitly authorizes the combined review -> `address-review` -> `incremental-review` lifecycle.
  The same transition is authorized when this review is a stage of an implementation workflow whose original
  request already authorized fixing its candidate. Otherwise review is read-only and ends after judgment.

Use `incremental-review` when the canonical work order already has a completed watermark and HEAD moved.
Use `big-review` when the frozen changed surface is too large for one pass, normally more than 300 files or
several substantial components. Use `docs-review` for a documentation/meta-only diff.

## Stage 1 — resolve and freeze the candidate

Resolve the target before reading or writing review state. With no explicit target, print the checkout and
branch and stop on the default branch or an empty range.

```bash
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git merge-base main HEAD
git log --oneline "<base>..<head>"
git diff "<base>..<head>" --stat
```

Freeze a candidate descriptor containing the full base SHA, full head SHA, target branch, scope as `all` or
an exact bounded value,
exact sorted changed-path set, SHA-256 of their UTF-8 bytes joined by one NUL byte with no trailing NUL, path
count, canonical work-order path, and new-or-append mode. Every later command and dispatch uses
`<base>..<head>`, never a live replacement
for `<head>`.

Materialize the candidate bundle defined by `review-lifecycle` in a disposable directory outside the
working tree. Validate its exported frozen-head tree, exact patch, NUL path manifest, identity manifest, and
bundle SHA-256 before dispatch. Add the bundle path and identity to every immutable-artifact set. A host
without safe read-only Git reads this bundle; no reviewer depends on the live checkout to reconstruct the
candidate.

If the branch moves while work is active, do not widen the pass. Cancel any dispatch whose baseline is no
longer trustworthy, finish or restart the frozen pass, and leave later commits to `incremental-review`.

## Stage 2 — open the canonical work order

Read `review-lifecycle`. Use only `reviews/<branch-slug>.md`; staged, documentation, and incremental modes
share it. Before expensive review work, have the parent create the immutable pass identity and set
the top-level `Review status`, current `Judgment`, and new `Pass judgment` to `in-progress`, `pending`, and
`pending`. A first pass has no completion watermark yet. An interrupted
incremental pass retains the earlier completed watermark but remains merge-blocking through its status.
Record every descriptor field, including branch, scope, bundle path and identity, canonical work-order path,
and `new` or `append` mode, before dispatch.

No lens writes the artifact. Append a confirmed finding only after the parent validates its result and
evidence. The parent may buffer independent lens results long enough to synthesize them together; recovery
identity and confirmed findings must remain durable.

## Stage 3 — native/general layer

Run the host's native general review first over the frozen descriptor, covering correctness, simplification,
reuse, efficiency, and error handling. If the host exposes no callable native review, dispatch the existing
`review-lens` capability with the bounded lens `native-general`. Do not invent or require a second
repository agent definition.

The invocation receives the frozen base, head, path digest, exact scoped paths, materialized bundle path and
identity, effort, rule-independent objective, read-only tools, and no prior lens conclusions. Validate the
result against Workflow v2 before using it. Agent/role/model unavailability falls back to the parent over
the same descriptor and bundle.

## Stage 4 — load applicable repository rules

Resolve rules mechanically from the frozen changed paths. Run the frozen tree's router with its working
directory set to `<candidate-bundle>/tree`, decode `<candidate-bundle>/paths.nul`, and pass every decoded
path as an exact literal argument:

```bash
python .agents/hooks/skill_router.py --skills-for "<exact-path-1>" "<exact-path-2>"
```

Read every routed skill, the root and nearest changed-path `AGENTS.md` files, and the architecture premise
from the exported frozen tree, never the live checkout. A `DENY PATTERN HIT` is evidence, not a hint.
Invoke additional standards only when the diff plainly touches their domain; a missing route is a
route-table defect rather than a list to duplicate here.

**Having invoked a skill earlier in the session — including while writing the diff now under review — is not
evidence its rules were applied.** Re-open each routed skill here and check every changed file against every
rule it states. A rule read at write time and never re-checked at review time is exactly how a stated,
unambiguous convention survives into a review that reports itself clean.

## Stage 5 — choose and dispatch fresh lenses

Choose only lenses supported by the frozen paths, rules, and risk:

- correctness: logic, concurrency, boundaries, exceptions, and observable failure paths;
- service isolation: runtime coupling that violates the repository's service-boundary owner;
- module boundaries: facade, visibility, and persistence ownership violations;
- seeding: writes production cannot make through the same path;
- language/framework conventions: only rules stated by the loaded standards; and
- changed-behaviour test impact: one concrete missing assertion for behavior this candidate adds or reroutes.

Each bounded dispatch uses `review-lens`, a unique dispatch/context identity, the same immutable candidate
artifacts including the materialized bundle path and identity, one exact lens or region, read-only
permissions, no subdispatch, and no sibling conclusions.
Independent read-only lenses or disjoint regions may be prepared concurrently. Any lens whose scope depends
on another result, and any overlapping region partition where independence is uncertain, runs in a later
wave. Writers never participate in review production.

Validate each result identity, status, citations, confidence, acceptance conditions, and decision boundary.
A malformed or correctable incomplete result gets at most one focused follow-up without widening scope.
Unsupported dispatch, timeout, cancellation, or a second invalid result closes that dispatch and returns the
same bounded check to the parent. Obsolete results from a different base, head, path digest, stage, or
dispatch ID contribute nothing.

## Stage 6 — conditional security layer

Classify the frozen paths through the merge gate's own generic and repository `security_paths` inventory.
When any path qualifies, run the host security review over the same descriptor. Security evidence joins
parent synthesis, while the `Security-reviewed up to commit:` marker is written only when the whole pass
completes. No qualifying path means no security marker.

## Stage 7 — parent synthesis and completion

The parent independently checks cited evidence and reads beyond the frozen diff only to confirm a candidate.
Drop pre-existing issues on unchanged lines, compiler/linter failures CI already owns, preferences no loaded
rule states, intentional changes, and anything below the effort-adjusted confidence bar.

Every retained finding is a defect the parent would fix and names one concrete fix. Do not keep hedged
observations. Deduplicate across native, security, concern, and region results by underlying defect and
evidence, preserving stable IDs. Lenses do not supply final severity or approval; the parent assigns
severity, writes one judgment, and records findings in the canonical shape from `review-lifecycle`.

On completion, set `Review status` to `complete`, set the current and active-pass judgments, stamp the single
`Reviewed up to commit:` marker at the frozen head, and stamp the security marker there when required. If
HEAD moved, this completed pass remains truthful at its frozen head and the later delta belongs to
`incremental-review`.

Remove the disposable candidate bundle after completion, cancellation, or terminal failure. An interrupted
pass may be resumed only after regenerating the bundle from its recorded descriptor and reproducing the
recorded bundle identity.

Apply `--comment` only after completion. Enter `address-review` only under the explicit combined
authorization described above; remediation remains a separate serial-write workflow and must return through
a fresh incremental watermark after any code change.

## Report

If a plan owns the work, completion of the whole pass is one material review transition; record only its
artifact and current gate. Report the frozen range, finding counts by severity or lens, canonical work-order
path, completed watermark, and whether an explicitly authorized remediation transition began. Do not replay
subordinate output or create a review-only commit.
