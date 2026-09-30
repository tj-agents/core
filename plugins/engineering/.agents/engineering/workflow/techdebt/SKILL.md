---
name: techdebt
description: Take one tech-debt item all the way to a focused PR in its selected checkout — survey every TECH_DEBT.md, pick one high-value item, fix it with the long-term scalable solution, verify, delete the resolved entry, and open the PR. Use when working through tech debt or handling one self-contained tech-debt item end to end.

kind: workflow
domain: process
lane: L4
---

# Working one tech-debt item — or a small bundle — to a PR

Take a tech-debt item all the way to a focused PR in its selected checkout, so nothing touches in-flight branches.
This is the *resolution* workflow; where a debt entry lives and when it is deleted is the `docs-and-debt`
standard. A single item is the default shape; bundling more than one into the same PR is the exception
below, not a second workflow.

## Steps

1. **Determine scope, then isolate.** First tell single-repo mode (the working directory, or an ancestor, is
   itself a git repository) from polyrepo-root mode (the working directory is *not* a git repository, but
   multiple of its immediate children are each their own git repository — e.g. a `Concertable/` folder
   holding `auth/`, `b2b/`, `customer/`, `payment/`, `search/`, `docs/`, `agents/` as separate
   checkouts, alongside whatever non-repo files or folders — a README, a shared script, IDE metadata — also
   happen to sit there; those are simply out of scope, not disqualifying). A directory with no ancestor repo
   and no such child repos beside it is neither mode — not a valid invocation; say so and stop.

   - **Single-repo mode:** survey the repository, then start the selected focused slice from the current
     remote default. Select or reuse an available checkout under `engineering:git-branching`; use
     `open-worktree` when concurrent work or necessary isolation requires another checkout. Each active
     writer has one owning branch and checkout.
   - **Polyrepo-root mode:** run Step 2's survey across every child repo's `TECH_DEBT.md` set as one
     combined list. Once the primary item is selected, its child repo owns this run. Select the branch
     and checkout there under the same `git-branching` and `open-worktree` rules as single-repo mode. A second item may join the bundle only if it also lives in that same child
     repo, on top of passing the Step 2 bundling test below — a PR belongs to one repo, so cross-repo
     bundling doesn't exist. Every other child repo stays untouched; picking from more than one of them is a
     future run, not this one.
2. **Pick the item(s) fast.** Skim titles and severity across every `TECH_DEBT.md` in one pass (in
   polyrepo-root mode, across every child repo's set, combined); do not read each entry in full or
   deep-dive candidates before choosing. Rule an item out only for a fact one command settles: already in
   flight (`git branch -a` or `git worktree list` naming that area, run within whichever repo the candidate
   belongs to), or needing a decision only the repository owner can make. Take the first remaining item
   that is genuinely high-value
   and self-contained as the primary, rather than continuing to rank candidates against each other; the
   bundling test below is applied after that pick, not as part of it. Say which you picked and why in a
   couple of lines before diving in. If the item as written is stale or wrong, say so.

   **Bundling.** Add a second (or third) item to the same PR only when *every* condition holds for it:
   - it is independently small — a narrow, mechanical, single-PR fix, not one already flagged as needing
     a split or a publish-first cut-over;
   - it touches files disjoint from every other item already picked for this PR, so there is no realistic
     merge conflict between them and each diff can be read on its own;
   - it does not depend on, and is not depended on by, another bundled item's change.

   A single non-trivial or multi-file item is still a PR of its own — bundling exists to stop trivial
   fixes each paying for a full isolate/PR/queue cycle, not to grow one PR's blast radius. State the
   whole bundle up front, the same couple of lines per item, before starting on any of them.

   **Opportunistic drive-bys.** A small, clearly-related improvement noticed in a file already open for
   the primary item — not a pre-tracked entry, just something spotted while you're there — may be fixed
   in the same PR, as its own commit, when it is genuinely small and safe: no new file beyond what the
   primary item already touches, no design decision a reviewer would want isolated, nothing that could
   plausibly need its own revert. State it in one line when you make the call, the same as a bundled
   item. Anything bigger than that, or outside the files the primary item already touches, is not a
   drive-by — it is either a new bundle candidate (apply the bundling test above) or its own tech-debt
   entry; never silently skip it.
3. **Investigate.** Read the surrounding code and understand the real root cause before touching anything,
   for each item in the bundle.
4. **Fix it properly.** Always the long-term, scalable solution, never the hacky shortcut — the shortcut
   rule and its one exception are the `docs-and-debt` standard. It can span multiple PRs; if it genuinely
   needs splitting, say so in one line, drop it from any bundle, and start with the first PR on its own
   branch.
5. **Verify.** Build the affected projects to zero errors and run the affected unit/integration tests. Do
   not run local E2E for PR-bound work; the merge queue owns that gate per the repository's plan floor.
6. **Close the loop.** Give each item its own commit — never squash a bundle into one — so the PR reads as
   N independent, individually-revertable changes. In the commit for a given item, delete that item's
   resolved entry from its `TECH_DEBT.md` — or, for a multi-PR cut-over, the final PR deletes it while
   earlier PRs record progress in the entry (the deletion rule is the `docs-and-debt` standard). Then push
   and open one PR covering the whole bundle following the `open-pr` standard, with a body section per
   item. Do not set an E2E label while opening the PR; the merge procedure's tier selection normalizes it
   mechanically at merge time.

Don't ask to confirm reversible steps — investigate, fix, build, commit, and push on the branch. Surface
the item(s) you picked before starting, and flag anything irreversible.

## Bounded dispatch, and the state that outlives a stage

The Step 2 survey and Step 3 investigation may use independent read-only Workflow v2 roles —
`evidence-explorer` over the `TECH_DEBT.md` set and the surrounding code, `test-impact-analyst` for the
affected projects and their commands — through the semantic envelopes in `.agents/workflows/contract/v2`, or
the packaged `../../workflows/contract/v2` bundle. Picking, bundling, the split call, and the fix stay with
the parent. A bundled item whose transformation is disjoint from every other may go to a `mechanical-worker`
under one exclusive writer lease; writes stay serialized and the parent reconciles the reported paths against
Git.

Each delivery slice keeps its branch, selected checkout, commits and PR through these stages. When the
work needs multiple PRs, resolve and validate Workflow v2 repository state, promote it through
`engineering:plans`, and checkpoint under `engineering:plan-checkpoint`. Deliver the remaining slices
under `engineering:git-branching`, resuming from the entry and ledger rather than this session.
