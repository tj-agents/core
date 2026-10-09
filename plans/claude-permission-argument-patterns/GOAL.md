# Goal — require Claude permission wildcards for argument-bearing script grants

## Defect

The harness permission model renders `claude_allow` entries verbatim. Its existing tests prove exact entries for argument-free scripts but do not reject an argument-bearing script grant without `:*`. That allowed the work plugin's pending-review helper to be granted only as an exact command, which would still prompt when invoked with its required arguments.

## Authorization

Standing standards-defect authorization from `engineering:session-guidance` (2026-10-08).

## Scope

In this checkout only, add the smallest validation and regression coverage that distinguish argument-free script grants from argument-bearing ones. Do not edit the work-plugin PR or merge any PR.

## Next Steps

1. Read the manifest validator and its focused tests, then make the validator reject a `claude_allow` script invocation that accepts arguments but lacks `:*`.
2. Add focused regression coverage; run the relevant core tests and generation checks.
3. Commit, push, and open a core PR if the source-owner workflow requires it. Report the outcome to the originating pending-review grant task.

Lane: L4 — a small, testable validation repair.

## Progress

- 2026-10-08: isolated worktree created from `origin/main`; successor not yet launched.
- 2026-10-08: validator now rejects argument-bearing `.py` and `.ps1` Claude script grants without `:*`, with focused regression coverage for exact and wildcard forms.
- 2026-10-08: focused repository-config tests passed; catalog and generated-package refresh completed and remain uncommitted as required.
- 2026-10-08: recorded the independently observed Codex sandbox runtime-lock issue in `.agents/machine/TECH_DEBT.md`; review and delivery remain.
