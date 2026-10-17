# Rolling Plugin Sync

Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-AlwaysLatestPlugins
Branch: Fix/RollingDependencyActivation (follow-up); original reviewed head 17ca22dfeb69d38447172c11b8de4c8b298c2971.
PR: https://github.com/tj-agents/core/pull/286 (idle-startup correction; prior final head passed review and GitHub CI; reported Claude startup wiring regression being corrected). Previous handoff import/cleanup PR284 merged 17 October 2026 at 14:05:16 UTC as c978ef030e4dbed4c4b49b0be055c85212a3760e and published as 2bc7f61b2ebcd6b3b45615597093d3b3a9d8fa42. Activation #283 and original rolling #269 are already merged. The idle-startup correction continues in this same worktree.
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
each such change. Tommy explicitly authorized this session to merge on 16 October 2026. Do not delete user data or caches outside the plugin cache.

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

The original implementation is delivered; one writer now owns the idle-startup correction below. Current-main resolution, exact native cache replacement, startup
binding, selected permission and owned-agent convergence, release-pin removal, and documentation are
implemented. Preparation remains bounded to 300 seconds. The old Codex 20-second binding deadline is
being removed because SessionStart may wait for the first user turn; per-launch native roots will permit
releasing the preparation lock before an idle CLI receives that turn.

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

## 16 October 2026 conflict-resolution continuation

Tommy assigned this session to resolve #269 against main in its own worktree, validate the new head, and obtain fresh review. Merge still requires Tommy to say "merge". Consumer adoption, Concertable/agents migration and user-settings cleanup wait for that merge; harness-injection design is explicitly out of scope.

Current checkout: C:/Users/tommy/source/repos/tj-agents/core/.worktrees/Fix-RollingPluginSync, branch Fix/RollingPluginSync. Integrated main c58f71ff. Preserve current-main workflow and review-evidence changes; rolling selection replaces pin-based producer locks, retains producer identities and validates their source. Added migration regression and updated CI paths. No protected checkout or global settings changed.

Focused validation: plugin selection 6 passed; adoption 10 passed; repository config 38 passed; Codex sync 13 passed; rolling runtime 23 passed (one platform skip); CI selection 21 passed. Generation and generation check passed. Source-layout checks are running. Next: commit the merge candidate, freeze fresh review from the prior 38b148ab watermark (including security of the full PR), resolve findings, push once, and verify exact-head Windows/Linux CI and mergeability.

Main advanced during validation to 5bc4e2ea (company whole-skill routing). The initial ff816908 review was cancelled before synthesis; no completion is claimed. Integrating the new main required only catalog format/digest resolution. Its routed-skill behavior is retained. Validate the router and regenerate/check packages, then freeze and independently review the final head.

## Live conflict correction after merge approval

Tommy approved merge with "cool lets go? merge". Main subsequently advanced through OpenCli to 08a852e1, and the live PR became CONFLICTING/DIRTY. Reporting manual merge without first rechecking that live conflict was wrong. The existing merge contract already requires handling relevant base movement; no new harness-injection or unrelated standards repair is authorized by this correction. This same migration owner repairs the current conflict. The scoped merge approval remains recorded; any independent guarded-delivery stop must still be reevaluated after the candidate is repaired.

Merged current main while retaining OpenCli focus/reopen behavior and the published skill roster. Recovery continues through verified startup; the retired fail-open _sync_codex helper is not restored. Added a regression proving closed Codex reopen launches the startup coordinator before native resume. Focused recovery 25 tests and rolling-startup integration 4 tests pass; generation/check pass. Next: commit with main-owned generated digests/output, obtain incremental review at the new exact head, push and observe exact-head CI, then check live mergeability and guarded delivery state immediately before acting. Preserve protected checkouts and do not ask for the same merge approval again.


## Current merge ownership — 16 October 2026

Tommy explicitly authorized this session to complete and merge PR #269: “AS LONG AS U FULLY COMPLETED IT THEN YEAH FUCKING MERGE”. This supersedes earlier instructions reserving merge. Preserve the other-machine integrations now present at a8d395376120b4232658b1d6f6f7759c4c32dec0 and reconcile the latest main before final review. Do not hand off or divert into personal problem-management policy.

The canonical review ledger has been restored from the local saved evidence: completed review and security watermark 81dce32ea5f69deb1947ed6136824f33b45132da. Native incremental review artifact 9ea90e4de2020635-rolling-native-final-test-review.log was clean. Exact-head CI run 38824122187 passed both Windows and Linux source/runtime suites. Newer integration commits require fresh review and CI; previous passing evidence is retained rather than discarded.

Next: resolve current main, review 81dce32e through the final integration head, verify exact-head platform checks, merge PR #269, and follow main package regeneration to completion. Existing running CLI instructions are not claimed to hot-reload.

## Merged and published ? 16 October 2026

PR #269 merged at 2ed865e13f071a573d505dacd59c1a482eb5f2bb after completed native/security/workflow review and exact-head Windows/Linux CI 38939776660, including ci-required. Main publication run 38942340043 successfully regenerated, verified and committed packages at a341c197. The generated commit explicitly names this merge as its producer.

Local Codex activation is running through the reviewed rolling synchronizer. This active CLI and worktree are retained under Tommy's instruction to continue here without another handoff. The primary checkout contains other work and refused a safe fast-forward; no other owner's files were changed. Origin/main is current. The post-merge validation monitor remains attached while activation completes.

## Native activation follow-up - 16 October 2026

PR #269 and its main run 38942340043 both passed Windows/Linux checks; publication a341c197 is verified.
The same owner continues in this worktree on Fix/RollingDependencyActivation, based on a341c197.
A real Claude refresh exposed a verified transitive marketplace being rejected because it was not
previously registered locally. The follow-up supplies its verified directory catalog in command settings
and restricts the saved-registration check to explicit selections. Two regression tests reproduce the
original failure and pass with the fix; the rolling runtime suite passes 25 tests with one platform skip.
Real Claude activation is running before delivery.

Codex activation correctly rejected retired react-standards/dotnet-standards selections. Their current
react/dotnet packages were already enabled and publisher migration documentation confirms coverage;
only those two obsolete enabled fields in ~/.codex/config.toml were changed to false. Its next refresh
hit the startup deadline. Instrumentation isolated one 1049.764-second machine cache promotion; the
same current tree scans in 0.158 seconds, so no performance code change or timeout increase is justified
yet. A more detailed real activation trace is running. Saved Claude settings are unchanged.

Tommy confirmed the next sequence: complete and merge this activation repair, then remove remaining
versioning/pins across publisher repositories and consumers. The original main delivery is complete;
the whole migration is not complete until the follow-ups and real startup verification finish.


Follow-up candidate 2ba5da38bc5f577749221934e9606085adac1e0b is published in draft PR #283;
CI monitor 38948507536 is attached. The two-file delta has passed 25 rolling tests (one platform skip),
startup integration, Claude synchronizer tests, package generation/check and harness generation checks.
The canonical review is repository-private, resolved by workflow_ops review-path. Native Codex review
runs from the detached candidate. Both real-host timing probes are active; the first timed Codex retry
waited behind another refresh and then exhausted its deadline only at final verification. No persistent
Codex performance defect has yet been established. The real Claude retry passed dependency resolution
but exceeded its deadline, requiring per-stage evidence before further changes.


## Verified cache optimization - 16 October 2026

Current follow-up head is 31e5e359a92d721d4cb7cbc68490440bebb659ab, with the final cache optimization
under validation in this worktree. Its independent native and parent workflow/security review is
complete and recorded in the branch-private work order. CI 38949923827 passed Linux; Windows failed
only when the unchanged session-cleanup test could not read its transient result JSON. Earlier head
2ba5da38 passed both platforms. Final-head CI must pass; no gate has been waived.

Real Codex activation passed in 211.191 seconds (artifact 1a2472a4a3e58653-rolling-codex-uncontended-activation.log).
Real Claude activation now passes in 194.894 seconds (artifact aacb0ea8e06dcba4-rolling-claude-unchanged-tree-activation.log).
The measured fix preserves freshly fetched publisher main as authority, compares the complete file set,
bytes and supported executable modes, reuses matching owned native roots, and avoids rewriting unchanged
verified package/catalog trees. Native alias inventory, ownership/link protection, final publisher re-fetch,
explicit selection/disablement and the original 300-second deadline remain enforced.

The final working delta passed all 28 rolling runtime tests (one Windows platform skip), four rolling
startup integration tests and three Claude synchronizer tests. Package generation/check is running.
Next: commit the two-file optimization, freeze and independently review only that delta, complete
final-head Windows/Linux CI, merge PR #283 under Tommy's existing authorization, follow publication,
and verify installed startup. Then migrate Template first, followed by publisher and umbrella consumers.
Keep this live session/worktree; do not create a refresh skill or transfer ownership.


Final follow-up head 6ede0b9c7626ba4e457f6d2660c56421ac3eff62 is pushed to PR #283. Native review
f71176c712290ba4-rolling-native-verified-reuse-review.log and parent workflow/security review are clean;
the branch-private work order and review receipt cover this exact head. Generation/check and all three
harness manifests passed. Final Codex activation passed in 197.713 seconds, artifact
00a650ac3b8bf367-rolling-codex-final-timed-activation.log, including native inventory, final publisher
verification and hook trust. A preceding uninstrumented rerun timed out in a native command; the traced
same-head rerun completed without changing timeout or verification. Claude's 194.894-second success
covers the same runtime bytes. CI 38956716955 is monitored at the exact final head; merge awaits green.


## Activation follow-up merged - 16 October 2026

PR #283 merged as de168a43e844c29a1ed0b6bf15c7e16cfc0bf9e1 at 20:04:31 UTC. Exact-head CI
38956716955 passed Linux, Windows and ci-required. The final native/parent review receipt, clean delivery
preflight and fresh What/Why body check covered 6ede0b9c7626ba4e457f6d2660c56421ac3eff62. The causal
main publication run is 38959576845, currently monitored. Keep this session/worktree under Tommy's explicit
continue-here instruction; do not run session-close or worktree deletion.

Next publisher slice: Template Refactor/VersionlessPlugins, isolated worktree
C:/Users/TommySeery/source/repos/tj-agents/template/.worktrees/Refactor-VersionlessPlugins, based on current
main 4308bafa905c33d007665cabe7c3b585df131a81. A single bounded writer implements versionless host manifests,
versionless Template config, current-main CI callers, exact-content drift checks, and one-time updater
removal of old version fields; existing layout, schema versions, host CLI pins and validation remain.
Other owner's Template PR #10 is not a technical prerequisite and remains untouched. CPP main is verified
4a4c2cde9808f9e30d42f5bff3b95e57dbd2d0d1; its open PR #34 overlaps manifests and package-version ledger,
so its separate migration must preserve that owner's work through an isolated current-main branch.

## Published activation verified - 16 October 2026

Core PR #283 publication is 9b65ebf5bf55125caa6840483e9bede48cc9550c; the causal main run
38959576845 is successful on both platforms. The interrupted monitor was reconnected under its existing
identity and reconciled to that terminal result. Installed Codex activation passed in 171.182 seconds
using the published runtime. Both PowerShell profiles now contain the current Claude and Codex launcher
blocks, with unmanaged text preserved, syntax checked, and both bootstrap probes passing.

Published Claude activation hit a GitHub connection reset while fetching react; this did not invalidate
the earlier 194.894-second same-runtime acceptance. Connectivity recovered and a published-runtime retry
is running. Template remains the next delivery slice under its existing single writer lease.

Published Claude retry succeeded in 138.866 seconds: artifact
796cc79ddbe9ff7e-rolling-claude-published-activation-retry.log. Both real hosts now have successful
post-publication activation, and both terminal profiles use the published verified launchers. Core runtime
acceptance and its causal main CI are complete; the remaining work is the versionless publisher rollout.

## Remaining publisher delivery map

After Template lands, apply its updater in isolated current-main branches to dotnet, react, nvim, rust,
github-actions, azure, work-items and work. All eight have numeric Template config/CI pins and Codex
manifest versions; their Claude manifests already omit version. Preserve other owners' PRs. Dotnet also
has historical Core/Azure source refs in scaffold.yml; work-items has the remaining schema-3 selection
lock, whose base/engineering/machine/template selections must survive conversion to plugins.json.

Custom slices follow: CPP removes its 18 manifest versions, package-version ledger/recording code and
obsolete policy, retaining provenance, compatibility packages and ordinary validators. Its PR #34 overlaps,
so use isolated current main and reconcile any subsequent merge. Marketplace uses root catalog.json;
remove release/revision/commit entries and emit main for every git-subdir source, retaining identity,
dependency and selection rules. Unlike Core/Template it commits generated catalogs and has no publisher job.

Concertable/agents main ffbc41f53013dde62340824580b5a169ddce7b3d has an authored Codex manifest directly
under plugins/concertable, with custom PowerShell enforcement and no Template/ledger/pins. Its narrow
slice removes that version, changes generator host validation, and updates hook-manifest tests. Integrity
hashes and schema versions remain. Its separate currency hook can accept a six-hour cache after a fetch
failure; assess relevance to verified Core startup before expanding that slice. Existing PRs do not overlap
the narrow files. Infonetica is a distinct Claude-only legacy publisher with active packaging PRs #8/#6;
preserve their ownership and assess its manifest separately. CLI application releases are outside scope.

Core's remaining source pin is .github/workflows/ci.yml ref v2.0.0 for Template. Remove it in a separate
focused follow-up after Template publication; do not fold new code into the already merged #283 branch.

## Template candidate and independent catalog slice - 17 October 2026

Template PR #18 is open as draft at a0cb5be4dd3469a71c6fc202eafda8c74fa99966. Its 20 authored files
contain 104 insertions and 105 deletions; generated output is excluded for the existing publication job.
Exact-head CI 38966024095 passed Windows, Linux and native Claude/Codex acceptance. All eight real-consumer
snapshots passed migration, Template conformance and updater idempotence (artifact
core/.git/agent-workflow/runs/always-latest-template/artifacts/d682a8dc28ac0d05-consumer-migration-acceptance.log).
The frozen native review remains running; parent workflow/security synthesis found no actionable defect.
Descriptor lives in Template Git-private always-latest-template/review/34c89ab91bd9e71fe0f8dea43781f1e39286d3b5aaa5100be6e6a4971e919bf4.

While that immutable review is pending, execute the independently authorized umbrella catalog slice in
marketplace/.worktrees/Refactor-VersionlessCatalog, branch Refactor/VersionlessCatalog, fresh base
07c8b399e4c2e70a30340c7b0b11a8a7b1074e80. It has no Template dependency; its only serialized writer owns
catalog.json, generate.py, test_generate.py, README.md and the two generated catalogs. This bounded overlap
uses the review wait and preserves other owners' checkouts. Template remains eligible for immediate merge
when its required native review finishes; do not delay a ready parent for this independent slice.

Consumer rollout additionally updates all eight root AGENTS.md lines describing pinned vendored files.
Each consumer tracks generated output and has no post-merge generation job, so commit its generated
payloads with its source migration. Dotnet's active TECH_DEBT next action mentions the old Template pin;
update that operational wording while preserving dated historical evidence. Existing tests have no numeric
Template/plugin-version assertions. Application release/version tests remain unchanged.

Template PR #18 merged on 17 October 2026 at 11:12:31 UTC as
906e8747a5023bf4e350b3a9cb9e8db49e1a326a. Exact-head review receipt covers a0cb5be; native review's sole
proposed generated-output finding was dismissed against the existing generate-before-verify and post-merge
publisher contract, corroborated by all three successful CI jobs. Body check and delivery preflight passed.
The goal-authorized ordinary merge completed without auto-merge or admin; the standing automatic binder
classifies CI workflow changes as a stop and therefore was not used to arm unattended auto-merge.
Main run39027813831 is monitored for publication. Continue the eight consumer migrations under this same
goal; existing application/tool/SDK version pins remain outside scope.


## Versionless publisher rollout - 17 October 2026

Template #18 is fully published at df25a913b1493d985f55f1821117f87ae6baa9a3; main run
39027813831 passed, the primary main checkout was safely fast-forwarded, and this goal's Template
migration/review worktrees were removed. The published primary is the updater source for consumers.

Marketplace #14 merged as 9939a2ffa965bc7525ab78e421cdb37b5f3c9aee at 11:32:59 UTC.
Exact-head native/workflow review was clean; PR CI39028546633 and causal main CI39029126117 passed.
All 15 publisher identities/dependencies are preserved and every catalog source now follows main.
Its generated catalogs are committed by repository contract. Only this goal's completed worktrees were
removed; the other owner's Feature/WorkPlugin primary remains untouched.

Neovim #7 merged as e3e9aac1de261853096732c46fafc324325a38c3 at 11:37:37 UTC after clean
native/workflow/security review at e9b6ab0 and green PR CI39029153315. Main CI39029420259 passed.
React #19 merged as e4b82e6dc06669fdaed98859be4efdcbc92aaa71 at 11:39:12 UTC after clean
reviews at 509fcce and green PR CI39029204902. Main CI39029520384 passed. Both consumers retain
schema and application/tool versions while removing plugin/Template pins. Their cleanup remains.

Rust #6 at d905978 has clean native review and green CI39029482767; final delivery preflight is
running. GitHub Actions #12 at dd676c0 has a frozen independent review in progress. Azure 5d43903
and Work 68f403f are committed and their immutable review/draft-PR preparation is running. Azure's
two local ephemeral-ID failures were missing tr in Bash; both passed with existing Git Bash tools on
process PATH (artifact0f804cd5cbac34fd), without source or persistent environment changes.
The single mechanical writer now owns the Dotnet migration. Work-items' supported migration preview
changes only the selection file, existing two host settings and legacy lock; it preserves exactly
base/engineering/machine/template@tj-agents. Apply it in that isolated consumer branch alongside Template.

Continue all remaining consumer and custom publisher slices, including CPP/Infonetica/Concertable and
Core's CI Template ref. Keep this live Core session/worktree. Native review, current-head CI and ordinary
explicitly authorized merges remain required for each slice; no separate personal-policy work is adopted.

## Active continuation checkpoint - 17 October 2026

Core's rolling startup and real-host activation are verified. The umbrella publisher migration remains
owned by this session and is unfinished. Neovim and React cleanup is complete. Rust #6 merged as
1937227612c1445ebe8b5c4d6a6971d250dbfa63; main CI39029930076 passed. Azure #16 merged as
f70d45f64d6f5b9d317dca7ded9df1b2ba9ddbf2 and Work #8 as
461ff0409317d8b0cd41a3b4176b8b1ec35e3f78. Their main-run reconciliation and cleanup remain.

Dotnet #56 at 2811ead25c38141d65fe197de18965957dec84d3 has successful ci39030434791 and
Scaffold39030434591. Work-items #13 at f6bf439ceac975b6b6a6cd7981a0bea335bc9586 has
successful ci39030455894. Both exact-head results were recovered through the GitHub connector; native
reviews, receipt completion, delivery preflight and ordinary merges remain. The attempted native-review
launches failed before execution with Windows process-creation error26; no successful launch is claimed.

GitHub Actions #12 at dd676c00ed938b41c3d84eacd50999555fb81917 has clean native review and
ordinary CI, but Workflow Writer39029611984 failed on GitHub API anonymous rate limiting. Its bounded
repair is written and generated: API-only unredirected token headers, lint-step github.token wiring,
and focused no-network tests. Generator freshness passed. The writer lease is released; inspect the
actual partial diff, run focused tests and workflow verification, commit, then review and observe both
workflows on the repaired candidate. No merge is authorized before these existing checks pass.

Next publisher slices are CPP, personal tj-agents/infonetica, Concertable/agents, and Core's remaining
Template CI pin, followed by published refresh/audit. Preserve other owners' work and this active CLI.

Tommy called out this session ending without a concrete unblock action or continuation. This is an
active P1 shared-lifecycle self-repair under engineering:self-repair, which pauses unrelated work in this
session until its causal correction is verified or Tommy defers it. The original rollout remains owned;
this pause is not a global prohibition on Tommy's other work. The prior owner was reconciled and a
single B014 native successor was submitted at 12:56:53 UTC in Fix-VerifyStopEnforcement, using Codex
0.163.0-alpha.1 and the canonical plans/stop-enforcement-recovery/GOAL.md in that checkout. Submission
artifact: core/.git/agent-workflow/runs/self-repair-stop-enforcement/artifacts/99e2aa1cf6639d02-native-successor-launch.log.
That first submission failed before native launch. Its isolated import failure was reproduced and corrected; the subsequent native attempt is reconciled below. No successor remains active.

Dependency resolver: this originating owner, which retained B014 after the failed successor was verified terminated. Unblock condition: observed
causal correction with native acceptance, or Tommy's explicit deferral. Resume action: inspect and finish
GitHub Actions' partial CI repair, complete the Dotnet and Work-items native reviews and deliveries, then
finish the remaining custom publishers and the final published host audit. Current next action: observe
the missing native SessionStart acknowledgement and actual Stop invocation, verify the transport corrections, and retain this session's foreground ownership. The umbrella remains unfinished.

## B014 native transport correction - 17 October 2026

The first submitted repair did not start. Tommy confirmed the absent tab; direct execution of its exact
isolated Python wrapper reproduced a fatal sibling-import error before native launch. That failure is
now corrected in Fix-VerifyStopEnforcement at 9d9211f1e93eb3ecc0aaa2c8cb4f4e84528e7744. The source and
packaged isolated-import regression passes, as do startup binding (9), shared launcher (84, 17 skips)
and Codex launcher (39, 1 skip) suites. This transport correction stays with B014's repair; it does not
by itself prove the original Stop failure corrected.

One corrected native submission used the fixed wrapper; artifact:
core/.git/agent-workflow/runs/self-repair-stop-enforcement/artifacts/bef8929d78e12f08-native-successor-corrected-wrapper-launch.log.
The corrected wrapper started native session 01a149ff-3f79-7de1-969e-de66c35dfed6 at 13:13:50 UTC. It recorded no assistant/tool actions or SessionStart acknowledgement. The wrapper reported a startup failure and timed out terminating PID 34824. Parent verified its exact process creation identity and terminated that child through the same Windows handle; cleanup artifact 31a115c618ec7466-cleanup-failed-native-by-verified-handle.log reports wait_result 0 and identity_after null. This was failed startup, not a completed repair.

Tommy explicitly requested retaining the handoff correction in this worktree. The import fix is included here as a273592e826c7e52c08f639238b755358ce03460. Windows cleanup now falls back to the original child handle on taskkill failure and keeps its final wait bounded; the startup error survives cleanup failures. Startup binding (10 tests), rolling plugins (30 tests, one platform skip), shared launcher (84 tests, 17 skips), and Codex launcher (39 tests, one skip) pass. Actual native SessionStart/Stop acceptance remains open. The parent continues the causal investigation here; no repair child is live.

The originating session retained its
canonical continuation owner 447958748ecb7065aa11fcef and verified foreground native PID 28728. No
unattended scheduler is registered or claimed. Preserve this original goal and its exact remaining
next actions above; do not treat a submitted launch or this source checkpoint as completed rollout.

## Current handoff repair and native evidence - 17 October 2026

Parent owns this repair in Fix-AlwaysLatestPlugins on Fix/RollingDependencyActivation. PR284 merged
at c978ef030e4dbed4c4b49b0be055c85212a3760e on 17 October at14:05:16UTC, after exact-head native and
independent workflow reviews found no defects, current two-host coverage and delivery/body checks passed,
and CI39037681354 passed Windows/Linux generation and verification. Main publication39039256296
completed successfully, including both platforms and required checks, and published generated commit
2bc7f61b2ebcd6b3b45615597093d3b3a9d8fa42. Its shared monitor is terminal. The source fixes remain in
this requested worktree.

The original successor session01a149ff-3f79-7de1-969e-de66c35dfed6 performed no assistant/tool actions.
The parent terminated its exact native process after failed startup cleanup, not after completed work.
Its old repair goal is reconciled as historical evidence; no second repair writer owns B014.

Native acceptance evidence obtained without credentials or production settings:
- A normally trusted native0.163 SessionStart fixture confirms snake-case event delivery and all startup
  environment variables: Temp/tj-native-sessionstart-nowrite-tzh7_h3g/rpc-observation.jsonl.
- A normally trusted native Stop fixture called canonical continuation_stop.outcome with actual native
  payload. It refused an unfinished delivery with no owner: hook/completed status=blocked and exact
  reason Initialize persistent-workflow for the active delivery binding before ending this turn.
  Evidence: Temp/tj-native-core-stop-7k6zp3vs/rpc-observation.jsonl. One local mock completion was served;
  no remote model request or credential copy occurred. This proves the predicate through native Stop,
  not the original session's historical catalog or complete packaged-hook adoption.
- Runtime marketplace aliases preserve plugin-qualified skill names, normal per-hook trust/disablement
  and unchanged saved config, and execute original alias bytes after canonical cache overwrite before
  first turn: Temp/native-runtime-alias-fixture-h71e1ffm/observations.json. This is Windows probe evidence;
  Linux and full source integration remain to verify.

The idle defect is confirmed: SessionStart can run on first user turn, so the old20-second post-spawn
deadline can kill a healthy idle CLI. One bounded source writer implement_idle_binding owns the
specified correction here: unique per-launch native marketplace identities, retained private catalogs
and native roots under the normal CODEX_HOME, child-only selection/trust overrides, logical IDs for
convergence, validated router discovery context, and cleanup only after verified native child exit.
No release versions, private user profile transplant, fake ACK/prompt, security bypass or indefinite
global mutex is accepted. Verify changed/deleted files, concurrent idle/new launches, config and disabled
hook preservation, source/packaged helpers, Linux/Windows CI, native adoption, review and publication.

PR284's initial native reviewer stalled in an inaccessible Store PowerShell PreToolUse process and
returned incomplete. After verified owned-handle cleanup, the same frozen candidate reviewed clean in
153.510 seconds using launch-local PATH discovery of working Windows PowerShell, retaining all hooks,
trust and configuration. The original foreground CLI was not restarted or closed.

B014 remains in progress. Exact old0.162.0-alpha.17.2 source supports Stop and defaults hooks on; original
startup hook load/overrides are not recoverable from retained logs and must not be invented. Native
predicate acceptance does not alone close the historical host-adoption failure. Parent foreground
ownership remains447958748ecb7065aa11fcef, original nativePID28728. No unattended scheduler is claimed.
After causal startup/adoption repair is verified, resume the retained publisher actions above.

The packaged native acceptance probe verified all 345 published engineering package files and enabled
and trusted all ten actual hooks. Actual SessionStart exited 1 after 937 ms, before any model request;
Stop was consequently not reached. Evidence: Temp/tj-native-packaged-core-stop-nj4_deth/rpc-observation.jsonl.
The probe's own process is terminated. Investigation now checks the exact packaged command and normal
launcher snapshot prerequisites; this failure does not yet distinguish fixture setup from product behavior.

The integrated runtime-binding native acceptance passed all 32 checks on source fingerprint
ee077f39129799f6e8a8be04ffcf60c6b92a7b9d2c29f8679b5b62f111def26b. Two actual native generations
shared a disposable CODEX_HOME; generation one remained idle through replacement of the canonical cache
and catalog. Its roots, catalog, discovered skill and executed hook stayed at generation one, while the
second child used generation two. Both normally trusted SessionStart hooks stopped before model
generation; disabled hook commands never ran. Saved configuration and opaque plugin policy stayed
unchanged; exact runtime cleanup succeeded and all 14 owned process handles exited. Evidence:
Temp/native-integrated-runtime-uhizhy5c/observations.json. The first attempt stopped on an incorrect
typed-config assertion; the corrected assertion checks the preserved raw sessionFlags layer. This is
Windows stdio integration evidence, not full TUI/resume, Linux, remote-daemon or live agent-role coverage.
The already-loaded-instructions contract does not promise immutable future reads of shared agent-role files.

The current delivery slice replaces the Codex acknowledgement lifecycle atomically: runtime catalog and
cache isolation, child-only configuration/trust, router discovery receipt, startup caller and regression
tests must ship together. Splitting the alias helper from its startup or router consumers would either
leave the idle timeout in place or break verified plugin discovery. Claude retains its existing bounded
acknowledgement lifecycle. The writer is addressing bounded parent-review findings in this slice before
the candidate is committed and independently reviewed: structured identities, preparation-error
preservation, removal of a test-double-only fallback, and spawn/path-escape regressions. Required gates
are focused local checks, frozen native acceptance, independent/native review, Windows/Linux CI and
causal main publication. The remaining publisher rollout stays owned and resumes after B014's gate.

Parent-review cleanup is complete. Structured full plugin/marketplace tables preserve third-party
settings and dotted identities. The production fallback that existed only for old test doubles is gone;
preparation errors survive cleanup errors. Startup tests pass 13 cases and runtime binding tests pass
6, including native spawn cleanup once, unknown live-child preservation and valid-digest root escape.
The shared launcher suite passes 84 cases (17 skips); startup integration passes four cases, with its
updated convergence-failure case verified again after the test-double correction.

The changed argv implementation passed the full 32-check integrated native acceptance again on frozen
fingerprint 5fcdc2fea2b13d522fd42ab1931e1659bf8088b0e5607ad15cebf8f79e1f1d40. Evidence:
Temp/native-integrated-runtime-e1ojeeb5/observations.json. All 14 owned native handles exited and no
cleanup error occurred. Preserve this source identity through the candidate commit; next synchronize
the published base once, freeze review, obtain independent/native review and run current Windows/Linux CI.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/machine/scripts/startup_binding.py and rolling_plugins.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Refresh selected current-main packages before native launch and preserve active session roots",
      "source": ".agents/machine/scripts/rolling_plugins.py and startup_binding.py",
      "mapping": ".agents/machine/scripts/claude_cli.py through shared startup preparation",
      "verification": {
        "level": "planned",
        "result": "pending",
        "evidence": "Run shared startup and Claude launcher regression modules on the frozen idle-startup candidate; retain existing Claude acknowledgement behavior"
      }
    },
    {
      "host": "codex",
      "behavior": "Prepare isolated native plugin identities, release the global mutex, and allow an idle CLI to wait for its first user turn",
      "source": ".agents/machine/scripts/codex_runtime_binding.py, startup_binding.py, codex_marketplace_sync.py and .agents/hooks/skill_router.py",
      "mapping": "Codex launch preparation passes private catalog, selection, trust and authenticated discovery context to the native child",
      "verification": {
        "level": "planned",
        "result": "pending",
        "evidence": "Verify concurrent changed/deleted generations, idle survival, exact cleanup ownership, preserved policy and disabled hooks, receipt tamper rejection, packaged imports, native hook adoption and Windows/Linux CI on the frozen candidate"
      }
    }
  ]
}
```

## Idle-startup review correction — 17 October 2026

Frozen review of f4e47908 completed with three confirmed defects: canonical machine coordinator refresh,
session-scoped tier discovery, and enabled unmanaged-plugin discovery. One serial correction batch
refreshes only the durable canonical machine package, shares authenticated root validation between the
router and tier gate, and adds enabled unmanaged native roots to the receipt. Nine runtime regressions
and thirteen startup tests passed; full Windows/Linux validation belongs to PR286 GitHub Actions.
The native packaged adoption probe also passed unchanged published engineering hooks: SessionStart
completed, UserPromptSubmit completed, and Stop blocked unfinished delivery with the exact canonical
reason. Evidence: Temp/tj-native-packaged-core-stop-r7uckfnt/rpc-observation.jsonl and owned-cleanup-recovery.json.
The fixture was removed after its native child exited. This closes the disposable-directory ambiguity;
the historical old-session startup non-invocation remains unrecoverable and is not assigned an invented cause.
After this correction's incremental review and CI, merge and verify publication, then resume publisher rollout.


## Reported Claude launch blocker — 17 October 2026

The real launch from the tj-agents parent directory failed because the published startup coordinator
requires a SessionStart dispatcher acknowledgment while every shipped Claude SessionStart hook called
its script directly. This regression was introduced by the original always-latest implementation, not
by an old release pin. Each independently selectable Core package now wraps its existing first
SessionStart command through the shipped dispatcher, retaining its arguments and outer timeout.
Startup fixtures use the real machine manifest; a regression executes each real manifest command with
a disposable gate and verifies acknowledgment, forwarded event and arguments. All fourteen focused
startup tests pass. Full Windows/Linux suites remain GitHub-owned. Prior f42b21ce review and CI were
green but do not approve this correction. Review this delta, push through GitHub CI, merge and verify
generated publication and an actual Claude startup before reporting the blocker resolved.
