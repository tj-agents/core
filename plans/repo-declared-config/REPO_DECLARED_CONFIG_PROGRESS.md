# Repository-declared plugin configuration progress

Status: implementing the 2026-10-20 handoff; native acceptance and consumer migration remain open.
Owner: current Codex session.
Branch: Feature/RepoDeclaredPlugins
Worktree: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-RepoDeclaredPlugins
Base: origin/main at 993e3e22
PR: not opened
Merge authority: Tommy only.

Current slice: remove launch-time refresh and make refresh-cli use native host commands. Acknowledgement,
late-launch cancellation and recovery pickup remain. This slice is independent code but requires PR #320
for automatic background updates. Do not remove user declarations until repository-only discovery works
in that updater and the consumers pass acceptance.

Assessment complete: reuse existing project generator and native host operations. Current main already
emits Claude autoUpdate and both host selections. No new skill, hook or installer. Investigation lane L3
resolved from `.agents/lanes/codex.json`; no model switch is claimed. The large deletion of obsolete startup
preflight tests belongs with the removed behavior; separating it would leave a deliberately failing test
suite. The candidate has about 1,900 added/deleted lines, primarily deletions, across fewer than 25 authored
paths. Consumer migrations and background-update changes are separate delivery slices.

Focused Windows checks passed: startup acknowledgement/failure/timeout with real Python children;
refresh native command ordering and all three packaged skill entry points; existing agent-cli,
handoff-Claude, handoff-Codex, open-Claude and recovery suites; package generation and freshness;
harness manifest consistency. Full Windows/Linux CI and independent review are pending.

Native Codex 0.163.0-alpha.1: trusted project marketplace and plugin configuration is read. Declared,
uninstalled plugins are discoverable but absent from skills/list, including INSTALLED_BY_DEFAULT.
After native installation, a fresh app-server skills/list loads the plugin with no user marketplace
or plugin declarations. Exact project trust remains local. This does not establish automatic bootstrap.

Current-main inventory: Concertable's migrated consumers, Template, winwrap and sandbox-hwid already
use the unified marketplace. Their primary checkouts remain stale. Infonetica main has only a Claude
publisher; tj-agents/infonetica PR #8 owns Codex harness parity. Work consumer declarations cannot claim
Codex acceptance before that publisher is available. sandbox-dotnet still needs migration.

External conditions:
- PR #320: Tommy merges; background updates must discover repository-only declarations before cleanup.
- Infonetica PR #8: publisher owner/Tommy delivers a Codex marketplace; consumers then verify its source.
- Claude isolated authenticated acceptance: automatic approval review rejected reading an OAuth token
  into the child's environment without explicit credential-use authority. No token was read or copied.
  Resolver: Tommy authorizes that bounded acceptance run, or an already authenticated isolated profile
  becomes available. Continue noncredential work meanwhile.
- Linux native acceptance: requires an installed host on Linux and a fresh repository-only session;
  source CI is necessary but does not replace that check.

Next: finish verification coverage, commit authored sources, run independent review, open the draft PR
for exact-head Windows/Linux CI, then continue the independent consumer migration work.
