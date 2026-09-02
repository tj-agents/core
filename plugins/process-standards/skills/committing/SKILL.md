---
name: committing
description: Commit completed reversible work at natural local boundaries, and push separately only when a stable candidate needs remote validation, a real handoff, or a meaningful published checkpoint. Covers safe staging, tests before commit, batching related review fixes into one verified push, exact-head remote verification, and why finished work must not remain loose. Use whenever a chunk of work goes green, when deciding whether a local commit needs publishing, or when finished work belongs in a different PR than the current branch.
domain: process
---

# Committing and pushing

**The default is to commit, not to "leave it for review."** The moment a discrete chunk of work is complete
and its targeted local checks pass, **commit it, without asking.**

This is not scoped to phase boundaries or handoffs. It applies to *every* finished, verified chunk: a phase,
a bug fix, a refactor, an investigation's output, a doc close-out. Reading the rule as conditional on
handing off is exactly the misread that produces the failure below.

## "I've left it uncommitted so you can look first" is the anti-pattern, not the courtesy

- **Review runs off commits.** A review diffs the branch against its base; work sitting in the working tree
  is invisible to it. Leaving it uncommitted is precisely what stops the reviewer seeing it.
- **Uncommitted is the fragile state.** It survives no `git checkout`, no stray `git restore`, no context
  clear. A commit is the cheapest insurance that exists.
- **It silently wrecks PR scoping.** Finished work left loose gets swept into an unrelated PR by a later
  `git add -A`, or stranded when the branch moves on — and a reviewer opening the PR finds the feature the
  branch is *named after* missing from it.

If finished work belongs in a **different PR** than the branch you are on, that is a reason to branch and
commit it *there* — never a reason to leave it in the working tree.

**Mechanical trigger:** the targeted checkpoint went green → commit. If your next sentence would be *"should
I commit this?"* or *"I've left it uncommitted for your review"*, **that sentence is the trigger** — don't
send it, commit.

## Commit cadence and push cadence are different

Commit completed reversible work locally at every natural boundary. Push only a **stable executable
candidate** that genuinely needs remote validation, a real ownership handoff, or a meaningful published
checkpoint. Several related slices or review fixes may therefore become several local commits and one
verified push.

Do not push because a ledger, review file, check result, queue observation, or commentary changed. Fold a
material ledger update known before the candidate commit into that substantive commit; keep review artifacts
local; leave remote evidence on GitHub. A metadata-only push must never cancel useful exact-head CI or launch
the matrix merely to transport bookkeeping.

**Enqueueing, merging, and deploying remain separate operations.** Marking a PR ready for review is a
review-state change, not merge authorization.

## The commit message is where the reasoning lives

The diff shows *what* changed; the message carries the *why* — the incident, the root cause, the alternatives
considered. That is what keeps it out of the code as running commentary.

## Use the fewest safe merges

Complete a piece of work in the fewest PRs its real dependencies allow. Numbered steps, commits, and phases
do not each need their own PR; keep coherent work together. Split only where a merge, a package publication,
a generated sync, or a runtime deployment must finish before the next work can build or run — and group all
the work possible on each side of that gate.
