# Goal — report pull-request readiness honestly

## Outcome

Provide a small core-owned command for private GitHub repositories that checks one PR and returns a clear terminal or waiting state:

- pending checks: show the observed state and a bounded recheck interval;
- checks green: say the PR is ready for the next delivery gate;
- genuine failed checks: name the failed job and its URL;
- runner/account/provider blocks, including GitHub's failed-payment or spending-limit message: say that no ETA is available, name the external resolver, and give the exact resume condition.

It may offer a watch mode for pending checks. It must not spin forever on a terminal external block or invent an ETA. Use `gh` so authenticated private repositories work.

## Authorization

Tommy requested this handoff on 2026-10-08. Implementation, tests, commit, push, and opening a core GitHub PR are authorized. Do not merge.

## Scope

First locate existing core monitoring and persistent-delivery utilities. Extend the single appropriate source owner rather than duplicating a polling implementation. Add focused tests for pending, green, ordinary failure, and the billing/spending-limit failure signature.

## Next Steps

1. Run the remaining repository-required validation and review for the PR-readiness change.
2. Commit, push, and open a draft PR; do not merge.

Lane: L4 — specified implementation with small code-level choices and test coverage.

## Progress

- 2026-10-08: isolated worktree created from `origin/main`; successor not yet launched.
- 2026-10-08: added `workflow_ops.py pr-readiness` and focused coverage for waiting, ready, ordinary failure, and external billing blocks. The focused tests and syntax check pass.
