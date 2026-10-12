# Fix two engineering hook defects in delivery identity

Status: bounded side workstream, launched 2026-10-12 from the `tj-agents/github-actions` conventions session
under `engineering:session-guidance`'s standing standards-defect authorization. That authorization covers
implementing, testing, opening the PR and merging once this repository's gates pass. Installing into other
scopes, publishing outside this repository and destructive operations stay gated.

Checkout: `C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-HookDeliveryIdentity`, branch
`Fix/HookDeliveryIdentity` from `origin/main` 376df0c. PR: none yet. Single writer: the launched successor.

## Defect 1: `continuation_stop.py` always reports `binding-head-changed`

`.agents/hooks/continuation_stop.py` `binding_active()` converts the artifact through
`runtime.binding_from_artifact()`, then compares `binding.get(key)` for `head`. But
`.agents/workflows/delivery_runtime.py` `ARTIFACT_ALIASES` maps `("head", "remote_head_sha")`, so
`binding.get("head")` is `None`. Every Stop with an active, correct `.agents/persistent-workflow-binding.json`
returns "Reconcile the canonical continuation owner before ending this turn: binding-head-changed".
(`continuation_runtime.check_identity` reads the raw artifact's `head` and is correct.)

Evidence (installed 2026-10-12): a binding for tj-agents/github-actions PR 1 at head
465f84bf64c2de10d3dc5b0f4d7c7a270186cb0e. `runtime.identity()` returned the same head, and
`binding_from_artifact()` returned `head: None, remote_head_sha: 465f84b…`. A simulated
`continuation_stop.outcome({'hook_event_name':'Stop', cwd, session_id})` reproduced the message.

Expected: compare the converted binding's `remote_head_sha` (and `repository`) against `identity()`, or
compare the raw artifact keys consistently with `check_identity`. Add a regression test in
`.agents/hooks/tests/test_continuation_stop.py` using a real `delivery-bind`-shaped artifact whose head
matches; it must pass Stop. The current test fixture evidently uses a shape that hides the alias.

## Defect 2: the merge-cleanup gate attributes `gh pr merge --repo <other>` to the cwd's checkout

The session ran `gh pr merge 6 --repo tj-agents/marketplace --merge --match-head-commit 9bb8088…` with cwd in
`tj-agents/github-actions/.worktrees/Feature-Conventions`. `.agents/hooks/merge_cleanup_gate.py` then recorded
"`gh pr merge` for PR #6 (Feature/Conventions) ran from …github-actions\.worktrees\Feature-Conventions" and
demanded Step 5 cleanup of that unrelated worktree, whose own PR (github-actions #1) is open. The marketplace
PR's own worktree had already been cleaned.

Expected: when `--repo`/`-R` names a repository other than the cwd checkout's origin, the gate must not bind
cleanup to the cwd checkout. It should resolve the PR's own head branch and worktree, or record nothing. Add a
regression test in `.agents/hooks/tests/test_merge_cleanup_gate.py`.

## Part 3: the handoff failure path must record, not ask (M014)

When a bounded side-workstream launch is refused or fails, `engineering:handoff` says to preserve the task and
report it, but it does not name the recording step. A session asked Tommy what to do instead (M014). Amend the
failure path: record each discovered defect under `engineering:write-bug` / `write-mistake` in the owning
register and continue the original task; never offer the user a choice for this.

## Completion

Both regressions are tested and pass, part 3's wording is merged, and the repository's required checks and generators pass (generated
`plugins/engineering/hooks/*` copies regenerated). The PR is reviewed and merged under this repository's
delivery policy. Record the PR and merge SHA here.

## Next Steps

1. Acknowledge pickup under Progress. Read `AGENTS.md` and the engineering `bugfix` lifecycle; reproduce
   defect 1 with a failing test, then defect 2.
2. Fix both, regenerate, run the focused hook tests and the repository's required local checks.
3. Commit, open the PR, drive CI green, get review, merge, close this worktree.

## Progress

- 2026-10-12: goal written by the originating session. The Codex launch was refused twice by the auto-mode
  classifier, so there is no successor. B008, B009 and M014 are recorded in this branch's registers. Resume when
  a session picks this goal up.
