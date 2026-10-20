# Repository-declared plugin configuration progress

Status: implementing the 2026-10-20 handoff; native acceptance and consumer migration remain open.
Owner: current Codex session.
Branch: Feature/RepoDeclaredPlugins
Worktree: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-RepoDeclaredPlugins
Base: origin/main at 85e3a0d3 (includes merged #320)
PR: https://github.com/tj-agents/core/pull/321 (draft)
Merge authority: Tommy only.

Current slice: native launch without refresh, explicit native refresh, and project-aware scheduled Codex
installation/update. Acknowledgement, late-launch cancellation and recovery pickup remain. PR #320 merged;
this branch extends its updater to use native inventories for exactly trusted projects, bootstrap absent
marketplace snapshots and track external publisher revisions. User cleanup still requires migrated actual
consumers and fresh-host acceptance.

Assessment complete: reuse existing project generator and native host operations. Current main already
emits Claude autoUpdate and both host selections. No new skill, hook or installer. Investigation lane L3
resolved from `.agents/lanes/codex.json`; no model switch is claimed. The large deletion of obsolete startup
preflight tests belongs with the removed behavior; separating it would leave a deliberately failing test
suite. Consumer declarations remain an independent delivery slice.

Focused Windows checks passed: startup acknowledgement/failure/timeout with real Python children;
refresh native command ordering and all three packaged skill entry points; existing agent-cli,
handoff-Claude, handoff-Codex, open-Claude and recovery suites; package generation and freshness;
harness manifest consistency. Windows/Linux CI is running. Independent review found three issues (Git URL normalization, external
publisher verification, POSIX group termination); fixes and regression tests are committed. The updater
extension and final candidate require independent follow-up review.

Native Codex 0.163.0-alpha.1: trusted project marketplace and plugin configuration is read. Declared,
uninstalled plugins are discoverable but absent from skills/list, including INSTALLED_BY_DEFAULT.
After native installation, a fresh app-server skills/list loads the plugin with no user marketplace
or plugin declarations. The final Windows probe used the real published unified marketplace and a fresh
profile containing exact project trust only. The scheduled updater bootstrapped its marketplace and
installed base@tj-agents. Removing the resulting user enabled entry still allowed a fresh app-server to
load all five base skills; the next updater run reported current. Real refresh-cli --verify-only passed
native inventory, marketplace revision and external publisher package-byte checks. Exact project trust
remains a native admission prerequisite; native installation writes user enabled entries automatically.

Current-main inventory: Concertable's migrated consumers, Template, winwrap and sandbox-hwid already
use the unified marketplace. Their primary checkouts remain stale. Infonetica main has only a Claude
publisher; tj-agents/infonetica PR #8 owns Codex harness parity. Work consumer declarations cannot claim
Codex acceptance before that publisher is available. sandbox-dotnet declarations are generated and checked in an isolated migration worktree; its PR is pending.

External conditions:
- PR #320 merged; final project-aware updater review and CI remain required before adoption.
- Infonetica PR #8: publisher owner/Tommy delivers a Codex marketplace; consumers then verify its source.
- Claude isolated authenticated acceptance: automatic approval review rejected reading an OAuth token
  into the child's environment without explicit credential-use authority. No token was read or copied.
  Resolver: Tommy authorizes that bounded acceptance run, or an already authenticated isolated profile
  becomes available. Continue noncredential work meanwhile.
- Linux native acceptance: requires an installed host on Linux and a fresh repository-only session;
  source CI is necessary but does not replace that check.

Next: final independent review and exact-head CI; publish the sandbox migration; reconcile remaining
Infonetica consumers and legacy local callers before user-profile cleanup. Nothing has been merged by
this session.
