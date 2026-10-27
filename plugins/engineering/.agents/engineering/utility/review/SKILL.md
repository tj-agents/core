---
name: review
description: Review a branch, PR, commit range or selected paths with the host's native reviewer and the relevant standards injected into that repository. Use for a full code review or a targeted review; use incremental-review for a later sweep, staged-review for explicit resumable partitioning, and docs-review for documentation.

kind: utility
domain: process
---

# Review a candidate

Review is a bounded assessment that returns actionable findings. It can run directly or be called by a
workflow; it does not own implementation or delivery. Source review is read-only unless `--fix` or the
calling workflow's existing authorization includes remediation. `--fix` uses lifecycle-backed review
evidence before remediation, even when invoked directly.

## Arguments and selection

```text
[low|medium|high|max] [<pr-number>|<branch>|<path>|<base>..<head>] [--comment] [--fix]
```

Effort sets the confidence and coverage of every reviewer. Reuse the last explicit effort when available.
No target means the current branch. Resolve a PR's actual base and head; a stack child compares with its
immediate parent. An explicit path narrows that candidate. `--comment` authorizes posting the finalized
result to its PR; `--fix` authorizes `address-review` followed by `incremental-review`.

Use `incremental-review` for changes since a completed review, including a design sweep of a rebased
stack. Use `staged-review` only for explicit resumable area partitioning of a candidate too large for one
pass, normally hundreds of files. Words such as "big" or "thorough" alone do not select it. Use
`docs-review` for documentation or agent metadata; Markdown alone does not establish low semantic risk.

`<review-skill>` is the loaded host entry point's directory. `<engineering>` is its plugin root, two
directories above it. Helpers ship with that package and run against the reviewed repository.

## Stage 1 - resolve the candidate

Resolve full base/head SHAs and the exact paths before reviewing. Keep that candidate fixed; later changes
belong to a subsequent pass. Read the root and nearest path-specific repository instructions and relevant
architecture. For an existing frozen bundle, read its exported frozen tree, never the live checkout.

Before running a host reviewer that reads checkout `HEAD`, verify that its checkout is clean at the
resolved frozen head. Reuse a matching checkout; otherwise create a disposable detached worktree at that
exact commit and run the reviewer and standards resolver there. Never switch an occupied checkout or
substitute its current head. Remove the disposable checkout after preserving the result and any required
evidence. A host that accepts an explicit range may use that range directly.

A current-checkout assessment needs no plan, branch synchronization or review-state machinery. For `--fix`
or a calling workflow that requires delivery evidence, apply `review-lifecycle` for preparation, the
immutable bundle, canonical work order and completion proof before dispatch. Preserve a supplied
descriptor and its scope.

## Stage 2 - select the result destination

Return findings directly for a standalone assessment. `--fix`, staged, incremental and workflow-owned
reviews use `review-lifecycle`'s canonical artifact, resolved with
`<engineering>/workflows/workflow_ops.py review-path`. The parent alone writes it and retains earlier
findings and dispositions. Record the frozen candidate before dispatch and leave interrupted work incomplete.

## Stage 3 - native review

`review`'s host entry point names that reviewer and its invocation. Run it over the fixed candidate and
scope; reading the diff yourself is not this layer. If it is unavailable, use a fresh read-only
`review-lens` with `native-general`, or the parent fallback when that capability is unavailable. Record
which reviewer actually ran. Discard findings outside the requested range and paths.

## Stage 4 - injected standards

The reviewed repository's injected instructions and declared plugin selection define the standards scope.
Do not replace them with the reviewer's installed skill listing, another repository's selection, or a
scan of every cached standard. Confirm that the reviewed repository's selected packages are admitted and
loaded by the current host; an unavailable or conflicting injection is an unresolved scope, not a clean review.

The shipped resolver requires Python 3.10 or newer. Run it with `python` on Windows or `python3` on Linux/macOS:

```bash
python -B <review-skill>/scripts/review_rules.py --project <repository-root> --host <codex|claude>
```

Run against a checkout of the frozen head with no working changes affecting selection or applicability.
Compare the returned selection hash with `.agents/plugins.json` in the frozen candidate; a mismatch must
be resolved before dispatch. It reads `.agents/plugins.json`, limits applicability and whole-skill employer replacement to those exact
plugin identities and the named host's enabled inventory, and returns convention paths and hashes. Read the returned conventions whose subjects
the candidate touches, following their canonical references. Keep injected policies and path-specific
instructions in force. A route table may add relevant explicit skills and deny-pattern evidence; its
absence does not remove injected standards or create a route-table defect.

If no plugin selection exists, use the repository's actual injected native instructions and their explicit
skill references; do not infer a selection from installed caches. Report missing or ambiguous scope.
For workflow evidence, record the applied qualified names and body hashes beside the candidate. Reuse an earlier body read only when its recorded hash is unchanged. A changed or missing hash requires a
new body read. Plans also owe their implementation-path standards when assessing a design.

```text
Repository selects stack:style and company-stack:style; company replacement applies.
Changed API code -> review company-stack:style plus the injected API standard.
An unrelated installed frontend standard -> excluded.
```

## Stage 5 - focused independent checks

Add a fresh specialist lens only for a concrete concern supported by the paths and injected rules, such as
security, concurrency, API boundaries or a missing behavior assertion. Independent checks may run together;
each receives the same candidate, applicable rules, captured test evidence, read-only permissions and no
sibling conclusions. Reuse passed tests unless a concrete concern needs another check. Validate citations
and result identity before synthesis; an invalid result gets one bounded correction, then parent fallback.

## Stage 6 - security

Use the host security reviewer that `review`'s host entry point names when the candidate touches sensitive
behavior. For workflow evidence, `review-lifecycle` owns the required security range and marker. A host
without a matching native security reviewer uses the bounded `security` lens over that same range.

## Stage 7 - synthesize and report

The parent verifies evidence, deduplicates defects, assigns severity and makes the final judgment. Retain
concrete fixes with file/line evidence and an applicable rule or demonstrated behavior failure. Drop
pre-existing defects outside scope, unsupported preferences and issues the compiler or CI already reports.
Report findings first, then the reviewed scope, standards applied and material coverage limits. State when
there are no findings. A clean result does not claim checks or reviewers that did not run.

A calling workflow completes its work order, host coverage and security evidence through `review-lifecycle`
before advancing. Standalone assessment ends with its findings. `--fix` completes its canonical review before
`address-review` resolves those findings and `incremental-review` checks the repairs. Post only under
`--comment` or prior explicit authority; remediate only under the authorization above and review the resulting delta again.
