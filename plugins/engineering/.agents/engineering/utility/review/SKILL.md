---
name: review
description: Review a branch, PR, commit range or paths with the host's native reviewer plus the standards the repository selects, and return findings. Use for code review; docs-review covers documentation.

kind: utility
domain: process
---

# Review a candidate

Owns one bounded review of a fixed candidate and its findings. `engineering:review-lifecycle` owns what a
review covers, how findings are resolved and the severity vocabulary. Review is read-only: `--comment`
authorizes posting the result on its PR, and `--fix` authorizes `engineering:address-review` afterwards.

```text
[low|medium|high|max] [<pr-number>|<branch>|<path>|<base>..<head>] [--comment] [--fix]
```

Effort sets every reviewer's confidence bar; reuse the last explicit effort. `<review-skill>` is the loaded
host entry point's directory. Use `engineering:incremental-review` for commits after a completed review and
`engineering:docs-review` for documentation or agent metadata.

## Stage 1 - resolve the candidate

Resolve full base and head SHAs and the changed paths. No target means the current branch against its PR
base, or the fetched default when it has no PR; a stack child compares with its immediate parent; a path
narrows the scope. Keep that candidate fixed: later commits belong to a later pass. A head whose tree equals
an already-reviewed head's tree counts as reviewed.

A host reviewer that reads `HEAD` runs in a checkout clean at the candidate head. Reuse a matching checkout,
otherwise create a disposable detached worktree at that commit and remove it afterwards. Never switch an
occupied checkout.

## Stage 2 - result destination

Return findings in the reply. A calling workflow or the selected profile may record them elsewhere.

## Stage 3 - native review

`review`'s host entry point names that reviewer and its invocation. Run it over the fixed candidate and
scope; reading the diff yourself is not this layer. If it is unavailable, use a fresh read-only
`review-lens` subagent with `native-general`, or review in the parent when no subagent is available. Record
which reviewer ran and discard findings outside the candidate.

## Stage 4 - selected standards

The reviewed repository's injected instructions and `.agents/plugins.json` selection define the standards;
never substitute the reviewer's own installed skills or a scan of every cached standard. Resolve them from a
checkout of the candidate head (`python` on Windows, `python3` on Linux/macOS; Python 3.10+):

```bash
python -B <review-skill>/scripts/review_rules.py --project <repository-root> --host <codex|claude>
```

It limits applicability and employer replacement to the selected plugin identities in the host's enabled
inventory. Read the returned conventions whose subjects the candidate touches. A missing or conflicting
selection is an unresolved scope, not a clean review; without a selection, use the repository's injected
instructions and their explicit skill references.

```text
Repository selects stack:style and company-stack:style; company replacement applies.
Changed API code -> review company-stack:style plus the injected API standard.
An unrelated installed frontend standard -> excluded.
```

## Stage 5 - focused checks

Add a fresh read-only `review-lens` subagent only for a concrete concern the diff and selected rules
support, such as security, concurrency, an API boundary or a missing behavior assertion. Each receives the
base and head SHAs, its one concern, the applicable rules and captured test results, and no sibling
conclusions. Independent lenses may run together. Reuse passed tests unless a concern needs another check.

## Stage 6 - security

When the candidate touches sensitive behavior, run the host security reviewer that `review`'s host entry
point names, or a `security` lens over the same range when it has none.

## Stage 7 - synthesize and report

The parent verifies evidence, deduplicates, assigns severity and makes the judgment. Keep concrete fixes
with file and line evidence and an applicable rule or demonstrated failure; drop pre-existing defects
outside the candidate, preferences and issues CI already reports. Report findings first, then the reviewed
range, the standards applied and any coverage limit. A clean result never claims a reviewer that did not run.
