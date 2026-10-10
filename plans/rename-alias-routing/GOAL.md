# Route a renamed skill through its alias

## Authorization and ownership

Bounded standards-defect side workstream under the standing authorization in
`engineering:session-guidance`, found by review of #173 on 2026-10-10. Authorized: implement, test, open
the PR and merge once this repository's gates pass. Installing into other scopes, publishing outside this
repository and destructive operations stay gated.

Worktree: `/home/tommy/projects/tj-agents/core/.worktrees/RenameAliasRouting` (yours alone)
Branch: `Fix/RenameAliasRouting`, from `origin/main` at `2dc7641`.
Originating session: `.worktrees/SplitDocsAndDebt` (PR #173). Read only; it keeps its own goal.
Lane: L4. The defect and fix location are known; the remaining choice is small and test-caught.

## Defect

`engineering:skill-authoring` ("Keep a published name working") says a one-to-one rename gets an alias in
`.agents/plugins/compatibility.json`. Every existing alias keeps the bare name (`base:x` →
`engineering:x`). An alias that changes the bare name deadlocks a route that names the old skill:

- `resolved_skill` follows the alias and finds the new skill file, so the skill is not reported missing;
- but `.agents/hooks/skill_router.py` then checks transcript proof against the old bare name
  (`outcomes.get(name.rpartition(":")[2] or name)`, around line 1490; Codex read-proof around 1480 and the
  pending-invocation map around 774), and `invocable_name` (around 656) tells the agent to invoke the old
  qualified name, which no longer exists. On Claude the invocation fails as an unknown skill; on Codex the
  proof looks for `skills/<old>/SKILL.md`. Every write on that route stays blocked.

#173 hit this renaming `techdebt` to `address-debt` and used a routing-only compatibility entry instead,
which the convention allows for "a rename an alias cannot express". Until this is fixed, every bare-name
rename needs such a stub.

## Completion expectation

1. Reproduce with a focused `test_skill_router.py` case: a route naming `engineering:old` whose alias
   targets `engineering:new` must resolve, tell the agent to invoke `engineering:new`, and accept proof of
   `new` on both hosts (Claude invocation and Codex read-proof).
2. Fix the router so an alias that changes the bare name carries the current name through invocation
   guidance and proof. Keep the one-hop rule and the unreadable-table fallback.
3. If the fix lands, nothing in `engineering:skill-authoring` needs to change; if a part cannot be fixed,
   correct that convention's alias bullet to say which renames need a compatibility entry instead.
4. Validate: both Python suites with `< /dev/null`, local `python -B scripts/update_catalog_digests.py` and
   `pwsh .agents/sync-generated.ps1` then `-Check`, catalog and harness `--check`. Leave `plugins/*` and
   catalog digests uncommitted (back up `.agents/catalog/catalog.json` before regenerating and restore it,
   so an authored edit is not discarded).
5. Review with `engineering:review`, open the PR against `main`, merge through `engineering:merge`, and
   finish Step 5 for this worktree.
6. Record the PR URL here and message the originating session (`.worktrees/SplitDocsAndDebt`) so #173 can
   replace its `techdebt` compatibility entry with an alias if it has not merged yet.

## Next Steps

Scope: whole goal through merge and cleanup.
Current slice: steps 1–2.
Done when: the fix is merged to `main` and this worktree is cleaned up.

Start at Completion expectation step 1.
