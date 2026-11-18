# Routine review evidence and impact-selected CI

## Authorization

Tommy directed Core to stop committing Markdown review work orders for ordinary reviews, retaining durable Markdown only for big or staged reviews, and to stop requiring both broad Windows and Linux verification jobs for every pull request. This goal owns the source repair, focused tests, review, PR, and merge under the repository's normal gates.

## Required outcome

1. Ordinary review evidence remains ephemeral or repository-private and still proves the exact reviewed candidate to the merge and delivery controls. Big and staged reviews retain a durable Markdown work order.
2. The review and merge contracts, runtime validation, host adapters, and tests agree on that distinction without weakening stale-head, security, finding, or authorization checks.
3. CI runs focused checks selected from the changed behavior. The full Windows-and-Linux repository matrix runs only for a massive or explicitly high-risk PR. E2E remains a selected merge-queue tier.

## Evidence

- PR #254 required `verify-windows` and `verify-linux` even though the workflow has no path selection. Both jobs run broad generated-source, packaging, hook, and runtime suites.
- The current review lifecycle requires `reviews/<branch>.md` for every review, and `merge_review_gate.py`, delivery runtime, and auto-merge read it as the merge proof.
- Existing `plans/review-delivery-continuation/GOAL.md` owns an earlier review-stamp continuity repair. This goal supersedes its assumption that the ordinary work order is committed, while preserving its exact-head delivery objective.

## Design boundary

Use engineering judgment over blanket platform coverage: a small shared-runtime fix still gets its focused regression and the smallest credible compatibility check; it does not automatically receive the entire repository matrix. Require the full Windows-and-Linux matrix only when the PR is massive, spans multiple execution surfaces, changes delivery/runtime infrastructure broadly, or is explicitly marked high risk. Do not replace safety gates with a label-only bypass. Use explicit, testable selection rules. Do not modify generated `plugins/` output in commits.

## First actions

1. Map review artifact consumers and define an ephemeral exact-head proof that each gate can verify.
2. Map the CI suites to source surfaces and add path selection plus tests for the selection matrix.
3. Split delivery into independently reviewable PRs if the review-proof and CI changes do not share a runtime contract.
