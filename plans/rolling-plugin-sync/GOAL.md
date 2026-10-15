# Rolling Plugin Sync

Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-AlwaysLatestPlugins
Branch: Fix/RollingPluginSync, originally off baa8f13a; integrated f2dd95ca; merging newer main 6be8c45a.
PR: https://github.com/tj-agents/core/pull/269 (draft; Tommy owns merge)
Owner: Codex session `01a13fa0-a1c6-7051-b3ce-a63fb26916da`;
work item `always-latest-plugins/implementation` (stable in-flight identifier).

## Requirement (Tommy, 15 October 2026)

Tommy is the only user of tj-agents. Every Claude and Codex session must synchronize the selected
tj-agents plugins to current published `main` content before launch. A session must never run an older
snapshot or version. Fix it permanently for all tj-agents plugins, not one plugin or one symptom.

`main` is the only truth. When a skill, hook, agent or file is deleted, renamed or changed on `main`,
every future session sees exactly that: a deleted skill is gone, a renamed one exists only under its new
name, and nothing old stays loadable or cached. Backwards compatibility with old versions is explicitly
not wanted. A large migration is acceptable, including a one-time manual refresh of every existing repo
and breaking old skills, aliases or snapshots.

## Scope

Investigate, design, implement, test, commit and open a PR to tj-agents/core. Changes to this machine's
Claude Code and Codex plugin or marketplace configuration are in scope where the fix needs them; report
each such change. Leave merging the PR to Tommy. Do not delete user data or caches outside the plugin cache.

## Confirmed direction (15 October 2026)

Tommy approved one rolling version on `main`, with no release pins or maintained compatibility paths.
Every new CLI session must refresh and verify the complete selected set before launch; a refresh failure
blocks launch. Existing running sessions retain their already-loaded instructions.

Selection and freshness are separate: effective repository/user settings choose the enabled packages and
their required dependencies; startup follows those packages' publisher `main` branches. Registering a
marketplace does not select every package in it. Repository-injection work can subsequently remove user
selections without changing the freshness contract. Do not auto-enable an entire publisher to infer a rename.
An explicitly selected package removed from the current roster must fail clearly until its selection is
corrected; deleted files and renamed skills inside a surviving package must disappear automatically.

Related work: the repository-only refresh change Tommy made on 14 October is not identified in the
published PRs. Stop searching for it at his explicit request; do not change that other workstream.
Core PR #131 (merged 7 October) adds clone-local configuration output and is NOT evidence identifying
that later refresh change. The prior chat inference conflated related work and is corrected here.
Core PR #100 declares harness ownership; dotnet PR #53 declares repository plugins with the old pin.
Do not modify those other owners' PRs. Keep source selection an input to freshness.

## Investigation evidence

Old umbrella refs, same-version native cache reuse, incomplete selection handling and fail-open launchers
caused stale sessions. See the native artifacts below and the original incident for observed evidence.
Fetched main f2dd95ca was integrated in merge commit af100167 after authored checkpoint 2452dbb4.

## Execution state

The original session `codex:01a13fa0-a1c6-7051-b3ce-a63fb26916da` owns this implementation again.
Tommy interrupted the replacement session and explicitly directed the original session to continue here.
Actual native PID/start-time identity was verified before reattachment; the supported work-item claim
atomically removed the replacement owner. Preserve its branch rename and removal of the redundant
`refresh-cli` skill. Do not transfer this task again.

Implementation writers are finished. Current-main resolution, exact native cache replacement, startup
binding, selected permission and owned-agent convergence, release-pin removal, and documentation are
implemented. Codex hook trust occurs under the startup lock; preparation is bounded to 300 seconds and
native binding to 20 seconds. Same-generation aliases deduplicate; differing generations fail.

Both actual native adapters passed two generations with unchanged manifests: changed payloads were
replaced, deleted files disappeared, and real saved settings stayed byte-identical. Evidence:
`4d722d0af34b3626-native-adapter-acceptance-resumed.log`; terminal telemetry records success at
2026-10-15T21:03:19Z. This supersedes the earlier timed-out probe. Source generation check, source-layout
suite and harness closure also passed (`6d7715d227921ff5`, `c9ec2fc20a53a71b`, `92b3a9342c330be2`).
Focused evidence: runtime 45 tests (one POSIX-only skip), convergence/integration 18 passed, startup binding
7 passed, terminal launchers 24 passed (five platform skips). Independent review and exact-head Windows/Linux CI remain delivery gates.
The duplicate local full suites were stopped; they do not count as passing validation. Their observed
snapshot and continuation errors passed isolated reproduction (`68f0e0f2621c95ef`, `e291bec80de63fce`).
Tests of the retired release-version validator were removed. Post-merge generation and its check passed.
The catalog guard passes six checks, including legacy-base/new-format digest preservation.

PR #268's proportionality changes preserve authorization, autonomous ownership and correctness gates while
reducing repeated reads, bookkeeping, checks and handoffs. Its bounded assessment retained no blocking
finding; no measured speedup is claimed. The installed six optimized bodies match published `f2dd95ca`
after CRLF normalization (`2f87f01c17e28323-refreshed-optimization-content.log`).

The authorized published Codex refresh trusted 10 hooks
(`df7f25c240301c32-refresh-current-published-codex.log`). It changed installed cache files, Codex hook trust
in config and `~/.codex/rules/base-agents.rules`. Captured Claude settings/registries and both PowerShell
profiles stayed unchanged. No selection change was intended. Baseline is Core Git-private
`agent-workflow/runs/always-latest-plugins/machine-before.json`. An earlier help query also accidentally
ran the old wrapper's refresh; subsequent probes use native executable paths and profile-free shells.
This original CLI has not restarted; freshly loaded startup hooks are not claimed. The replacement started
fresh and was then interrupted. No persistent continuation scheduler was initialized.

The implementation and main integration are committed and draft PR #269 is open at 1be576a4.
The first full review is complete with four findings: Claude selection merge, cache path safety, packaged
permission-helper resolution, and expired-deadline child cleanup. Independent native review completed;
its snapshot-helper allegation was disproved against the packaged layout. CI run 38810619930 failed;
all four runtime findings are now fixed in 3dac61f7, 5f5888c8, e4992106 and 0906c406.
Claude selection cases (4), cache boundary cases (4), deadline cases (2), and startup binding cases (8)
passed. CI fixture repairs passed: Claude launch/open 68 cases (2 skips), Codex launch/profile 62 cases
(1 skip), terminal wiring 14 cases (3 skips), and startup integration 4 cases with an empty global Git
config. Post-fix generation and its check passed. Incremental review and exact-head Windows/Linux CI
remain delivery gates. Tommy owns merge. Deferred self-repair followups and
the separate personal-policy design resume after this delivery; they must not divert this implementation.

## Main overlap discovered during delivery (16 October 2026)

PR #270 merged after the earlier synchronization and advanced main to 6be8c45a. GitHub blocked CI for
38b148ab because its multi-marketplace lock touched files this cutover retires. This is new integration
work required to unblock the original PR, not another search for the unidentified other-machine work.
The prior incremental review completed clean at 38b148ab, including native review and host coverage.

Preserve PR #270's qualified identities, per-marketplace source map, canonical owner/source validation,
duplicate-source rejection and unrelated host settings. Remove revision pins and explicitly migrate
schema 2 and 3 locks. Keep this branch's approved selective-package behavior: only requested packages and
dependencies are selected; an empty initial adoption defaults to base, engineering and machine. Do not
restore a mandatory all-Core roster or the old project-only refusal. Extend verified rolling refresh and
permission convergence to explicitly selected Concertable publishers already allowed by PR #270.

## Implementation decision and delivery boundary

Use a shared Python rolling synchronizer with host adapters. Git main objects are authoritative; native
hosts materialize and load the selected packages. Never use a cached success receipt to skip the network
check. Existing per-repository selection behavior remains an input, including selected-but-uninstalled
identities and explicit disables. Required dependencies come from current package harness declarations.

1. Resolve effective launch directory, settings and selected identities. Authenticate selected catalogs
   and external publishers as GitHub tj-agents sources; handle only explicitly known old URL migrations.
2. Fetch selected catalogs and publisher main commits once per publisher, resolve current package paths
   recursively, and reject missing selections, cycles, unsafe paths and disabled required dependencies.
3. Produce cache-only native catalog projections preserving plugin identities. Extract exact Git trees,
   rejecting symbolic links/reparse points. Install with disposable maintenance settings so native install
   does not leak enabled plugins into the user's global profile.
4. Verify the complete installed file set and bytes, not versions. Serialize publication and startup;
   stop on every failed fetch, install, trust or verification operation. Delete stale inactive package
   candidates only inside validated plugin caches. Keep existing running-session hook isolation.
5. Launch every supported terminal/handoff/recovery entry through the same preflight immediately before
   the native process. Raw binaries or external integrations that bypass it cannot receive its guarantee.

Native evidence: Claude 2.1.282 consumes the verified local catalog through a directory source in a
disposable maintenance registry under its temporary plugin cache. Both config and cache are disposable;
the real authenticated Git marketplace stays unchanged. Both native adapter generations passed in the resumed acceptance artifact above.
Codex 0.163.0-alpha.1 accepts per-command local marketplace overrides, but native add writes a global
enable. Install in disposable CODEX_HOME then promote verified package roots; its cache has no separate
install registry. Final inventory/trust/launch must share the exact catalog overrides. Native plugin/list
reports marketplace/name/version but no installed path; derive and validate its conventional cache path.
Both hosts accepted disposable plugins whose manifests/catalogs omit a version; Codex uses its native
`local` cache slot. Native config/read includes selected-but-missing Codex packages and explicit disables.
Claude repeated versionless install reported success but retained the old payload in its `unknown` cache
slot. Materialize Claude in both disposable config and cache, then promote verified bytes into a Git-SHA
cache directory and repoint applicable real registry records. Preserve active session roots and unrelated
project registry entries. The native experiment is captured in the Git-private workflow artifact
`952bc814239d7eec-native-claude-versionless-reinstall.log`.
Codex named profiles use NAME.config.toml and are not accepted directly by app-server; selection must
honor that format or refuse the option clearly. No live host acceptance of the integrated updater is
claimed yet. Current main `f2dd95ca` is integrated; preserve that single pre-review synchronization.

Release removal: replace release/pin catalog metadata and manual manifest versions with current package
metadata and automatic host-required identity only. Retire the version-bump command and turn adoption
into package selection on main. Structural schema versions still identify formats. Any old lock input
is supported only by an explicit one-time migration that discards its release pin.

Rejected: autoUpdate alone; refreshing every registered marketplace; accepting native version equality;
enabling whole publisher rosters; guessing renamed selections; stale fallback; rewriting user/repo
selection preferences merely to refresh their packages.

This is one atomic PR cutover: splitting the freshness verifier, its host launch wiring, and selection
generation would leave an exposed stale or incompatible intermediate state. Separate local commits and
bounded reviews organize the source, host integration and metadata changes. Expected scope exceeds the
1,000-line review warning; measure the actual candidate before independent final review. Generated
plugins/* remain uncommitted. The final full review must cover cache deletion, trust and concurrency.

Acceptance checks cover both hosts, selected subsets, missing/removed/renamed content, same-version file
changes, offline/install failures, explicit disables and dependencies, concurrent starts, safe pruning,
alternate profiles/settings and --cd, no global selection leakage, and native disposable-profile probes.
Source generation, harness closure and the required Windows/Linux matrix remain delivery gates.

## Original incident

The originating Claude session loaded old core lane tables and session guidance, while an old dotnet
package omitted skills required by the current router and blocked repository tools. Global Claude's
umbrella marketplace pinned old publisher releases. More than a hundred stale cache directories remained.
Native versionless Claude reinstall was proven to report success while retaining old bytes; the actual
Codex adapter passed same-manifest changed/deleted-file replacement with saved settings unchanged.

## Current user steering

Tommy requested a fresh session with current published hooks/instructions and asked whether the just-merged
workflow optimizations preserve autonomy and reduce unnecessary overhead. The successor was launched through
the existing same-host handoff path. Tommy then corrected the proposed `refresh-cli` surface: it is redundant
with that existing workflow and must not ship as a skill.
The relevant optimization is core PR #268 (`ef73606c`, published by `f2dd95ca`), fetched on 15 October.
Its bounded review is complete with no retained blocking finding; this is separate from repo-settings WIP.
Refresh uses the existing published same-host handoff launcher, one successor and verified ownership,
not unpublished checkout launch code: current main does not yet contain this branch's publication marker.
No merge or branch installation is authorized by refresh. Preserve this worktree and its dirty work.
## Completion expectation

- Root cause identified with evidence: why installed copies lag the source on each harness.
- One mechanism, documented in the owning source, that guarantees each new Claude and Codex session loads
  the latest tj-agents for every tj-agents plugin, and that fails loudly rather than silently running an
  older copy when it cannot.
- Version mismatches between tj-agents plugins can no longer happen (e.g. `base` newer than `dotnet`).
- Stale cache versions are cleaned up as part of the mechanism.
- Tests for the mechanism; the global instruction text updated to match.
- A PR open with a summary Tommy can read in two minutes.

## Next Steps

Scope: whole authorized goal through implementation, verification, review, commit and open PR.
Current slice: repairs reviewed clean at 38b148ab; integrate newly merged PR #270, then validate the integration head.
Remaining scope: independent review, exact-head CI and ready PR; Tommy owns merge.
Done when: verified implementation and any machine changes are reported with an open reviewed PR.

1. Original session codex:01a13fa0-a1c6-7051-b3ce-a63fb26916da has retaken ownership on Tommy's explicit
   correction. The replacement's last turn was interrupted after its commands completed; supported direct
   follow-up was unavailable with no send attempted. This original live native identity was reattached
   with PID/start-time verification, then the work-item claim atomically removed the replacement owner.
   Preserve the rename and removal already made; do not create refresh-cli or transfer this original task again.
2. Native acceptance, focused regressions and post-merge generation passed. Main was synchronized once.
   Review the committed candidate independently,
   and open the reviewed PR with exact-head Windows/Linux CI. Tommy owns merge. Generated output stays
   out of authored commits; preserve current test evidence instead of repeating passed suites blindly.
3. Separate planning-only research in C:/Users/TommySeery/source/repos/tj-agents/docs/plans/problem-management/PLAN.md
   owns personal problem-record/docs policy. It must not become a universal Core requirement or take over
   this implementation. Core primary BUGS.md B013 records the failed skill/goal reads, uncommitted for batching.
4. Activation of rolling startup still waits for Tommy's merge and main regeneration. Report actual machine
   changes and unverified native behavior honestly.
