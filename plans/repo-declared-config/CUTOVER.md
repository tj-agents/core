# Repository-declared plugin cutover

Authority: Tommy's 2026-10-20 request to execute
`~/.claude/plans/core/handoff-repo-declared-plugins.md`. Commit, push and open PRs;
Tommy merges. This checkpoint supersedes the older plan's startup refresh and self-heal design.

Owner: current Codex session, branch `Feature/RepoDeclaredPlugins`, worktree
`core/.worktrees/Feature-RepoDeclaredPlugins`, base `993e3e22` (`origin/main`).

Outcome: committed repository plugin selection and native host settings provide the plugins;
launchers do no refresh, generation, installation or configuration convergence. Updates run
in the background through Claude's native updater and core PR #320's Codex updater.

Assessment: existing `plugin-selection` already emits both host declarations and Claude
`autoUpdate: true`. Reuse that generator and native hosts. No new hook, gate or skill.
PR #320 remains open and green; avoid duplicating its installer and background updater.

Investigation lane: L3, because native project installation and update behavior need observation.
Resolved against `.agents/lanes/codex.json`; no model switch is claimed.

Work remaining:

1. Probe the real installed hosts with empty user marketplace/plugin declarations and record
   trust, discovery, installation and fresh-session results separately.
2. Remove rolling preflight from handoff, open and recovery launchers while preserving handoff
   acknowledgement and late-launch cancellation. Give refresh-cli a fast native default and
   an explicit slow verification mode.
3. Reconcile Template's new-repository path and migrate known consumers' declarations.
4. Remove superseded user declarations and legacy marketplaces only after the consumers
   pass acceptance. Preserve unrelated user settings and installations.
5. Focused tests, independent review, Windows/Linux CI, pushed PRs ready for Tommy to merge.

Windows inventory: legacy declarations remain in Concertable and sandbox-dotnet; Infonetica
projects also contain machine-local Codex marketplace paths. No user wiring has been removed.
The main core checkout is dirty and preserved; it is 640 commits behind origin/main.

Linux acceptance: pending. Acceptance requires native project discovery and fresh-session
loading with empty user plugin declarations, plus real handoff/open/recovery entry points.
