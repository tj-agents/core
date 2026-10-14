# Merge gate: decide jurisdiction before failing closed on git state

Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-MergeGateJurisdictionFirst
Branch: Fix/MergeGateJurisdictionFirst, off origin/main eded20b.
Owner: one side-workstream successor. The originating Claude session keeps its own task and does not edit this checkout.

## Scope

Source-owner repair raised by Tommy on 14 October 2026. Implement, test, commit and open one PR to
tj-agents/core. Merging is left to Tommy. No changes outside this checkout.

## Defect

`.agents/hooks/merge_review_gate.py` (mirrored to `plugins/engineering/hooks/merge_review_gate.py`) runs
`git rev-parse --show-toplevel` and blocks on failure ("MERGE GATE: cannot resolve git state ...") before it
decides whether the merge is its business. Two jurisdiction exits sit after that fail-closed point:

- `repo_flag(command)`: a `--repo/-R <owner>/<name>` naming another repository exits 0 for Claude, per the
  module docstring.
- `find_config(_GIT_CWD[0])`: a directory with no `.agents/merge-gate.json` at or above it claims no
  jurisdiction.

Observed: a Claude session attached to `C:/Users/TommySeery/source/repos/infonetica` (a plain folder, not a
git repo) ran `gh pr merge 13 --squash --delete-branch -R tomjseery/career` and was refused with
`MERGE GATE: cannot resolve git state (Command '['git', 'rev-parse', '--show-toplevel']' returned non-zero exit status 128.)`.
`tomjseery/career` has no merge-gate opt-in, so the gate had no jurisdiction.

## Completion expectation

- A merge run from a directory that is not inside a git repository, with no `.agents/merge-gate.json` at or
  above it, exits 0 instead of blocking.
- An opted-in repository whose git state cannot be read still fails closed.
- Codex canonical-target behaviour is unchanged.
- Regression tests in `.agents/hooks/tests/test_merge_review_gate.py` cover the non-git directory with and
  without `-R`, and the opted-in fail-closed case. The plugin mirror stays identical per the repo's
  mirroring convention.

## Next Steps

1. Read the repo's AGENTS.md, the merge gate module and its tests. Reorder so jurisdiction is decided before
   the fail-closed git-state resolution, without letting an opted-in repo with unreadable state through.
2. Add the regression tests, run the merge-gate test module, commit.
3. Open the PR and record its link here. Leave merging to Tommy.

## Progress

- 14 Oct 2026: goal written by the originating Claude session.
- 14 Oct 2026: L4 implementation moved opt-in jurisdiction ahead of Git-state resolution, added the three non-git regressions, and passed the focused hook and runtime suites plus generated-package synchronization.
