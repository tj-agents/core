# Tracker-aware skills and generic issue routing

## Authorization and outcome

On 18 October 2026 Tommy explicitly requested a separate source implementation handoff while the existing migration continues: ensure ALL affected skills send future bugs, mistakes, debt, features and tasks into the new selected work-item format. He requires `write-issue` to be a generic entry point that classifies the request and invokes the appropriate specific writer. This authorizes the source audit, necessary implementation, focused tests, independent review and source delivery through each repository's existing gates. This is execution, not another proposal-only investigation.

Success is verified future behavior across every affected skill and indirect caller, on both native hosts. A tracker utility, installation, consumer adoption, changed prose, or a grep result alone does not prove this. Preserve useful existing routing rather than rewriting it merely to produce a diff. Do not change unrelated skills.



## Ownership and separation from migration

- Source owners: tj-agents/core for generic engineering contracts, local session ownership and reusable recording/addressing workflows; tj-agents/work-items for the shared tracker runtime and existing GitHub provider; tj-agents/personal for personal scope/authentication and recording/addressing entry points; tj-agents/work for reusable employer-facing entry points; tj-agents/company for employer process and credential policy.
- Initial checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-TrackerAwareSkills
- Branch: Feature/TrackerAwareSkills
- Fetched baseline: 669d90ef0c6cba79051925b6076377ace96eda09
- Work item: work-items/record-writers
- Dispatching session: codex:01a1415f-6448-7123-8b17-c7fb67aee637
- Local source writer budget: one successor, with any bounded helpers governed by explicit disjoint ownership.
- Lane: L3; the coverage audit and generic router have bounded unresolved ownership/routing choices. Route specified implementation and review to the ordinary suitable lanes.
- Pickup: acknowledged on 18 October 2026 by codex:01a14f1d-abd0-74e0-9b75-b814a208ea87. Supported session-store `claim` succeeded for work-items/record-writers as owner at this exact checkout. No transfer receipt was supplied. Core fast-forwarded cleanly to fetched main 728ea8b2a605981625a12cc787701146630aca53 before implementation.

The separately running migration owner is codex:01a14ec8-5bdd-70a3-90c1-9d31a71289cf, work item problem-management/personal-policy, canonical docs plan C:/Users/TommySeery/source/repos/tj-agents/docs/plans/problem-management/PLAN.md. Its duties are existing-record migration and consumer adoption; yours are source skills/runtime behavior for future records. Tommy explicitly approved both continuing separately in his latest clarification. Do not pause, claim, close or duplicate that migration owner, or edit its docs plan, consumer settings, .work-items.json, .problem-records.json, plugin selections, tracker records or migration receipts.

The migration owner has configured docs and uses work-items Chore/AdoptWorkItemsTracker for consumer adoption. Do not edit that branch or any work-items primary checkout. If GitHub provider/source changes are necessary, read that repository's actual instructions and allocate your own isolated source branch/worktree from fresh main, with the same source goal linking its owner slice. Avoid overlapping adoption configuration files. Other active Core source goals, including launcher/session lifecycle changes and the earlier validation-efficiency investigation, retain their owners. Your worktree and source paths must stay distinct.

The earlier attempt to send the migration owner a pause instruction returned unavailable, explicitly no send attempted and no daemon started. That pause was not delivered and is superseded by Tommy's explicit latest direction to let migration proceed separately. Do not replay that old message or its receipt. Native coordination may be unavailable; record source publication/interface evidence in this source goal for the migration owner without claiming message delivery. Existing migrated record identities and schemas are compatibility inputs, not a new migration job.

## Established evidence and design decisions

Read the cross-repository docs plan for historical storage/package decisions and dated delivery evidence, but use this goal for current source implementation state. The personal Azure recommendation and its offline preparation below are historical: Tommy superseded that backend on 19 October 2026 with GitHub Projects, typed work items, parent/child hierarchy and independent-repository roadmaps. GitHub's generic issue record is not synonymous with Bug. Termboard may later consume the chosen remote backlog and the shared local session-storage interface; it does not become the only copy of the backlog. Source merge gates, existing record identities and coordinated cutover requirements remain in force.

Current fetched Core source ALREADY contains explicit provider-first prose in write-debt, write-bug and write-mistake. The shared .agents/engineering/resources/problem-records.md reads a primary-checkout .problem-records.json declaration, loads its qualified provider and blocks rather than creating a Markdown fallback if a selected provider is missing/invalid. Without a provider it retains the declared/file defaults. Existing provider admission and GitHub transport shipped in Core #272 and work-items #7. Do not claim these writers are wholly unintegrated or erase functioning selection. Verify the real command path and every caller, correct contradictions/gaps, and add missing routing. No write-issue, write-feature or write-task entry was found under current Core's engineering tree during dispatch; inspect both publishers and installed catalogs before choosing names/owners.

The earlier handoff mistakenly treated delivered tooling and read/admission integration as proof that all future writing workflows were complete. This source goal corrects that coverage gap explicitly. The migration's direct use of a tracker script does not establish that ordinary agents invoking recording skills follow it.

## Required behavior

1. `write-issue` classifies a request as bug, mistake, debt, feature, story or task, then delegates to the appropriate specific writer. Keep it a thin entry point: reuse shared classification/record semantics, deterministic templates, selection and transport; do not add a second backlog or duplicate creation logic. Direct specific-skill calls and generic calls must reach the same canonical item and format. Ask only when the available facts cannot resolve a materially different action. Recording must not silently invoke addressing/implementation.
2. Keep precise kinds: faulty software behavior is a bug; an observed agent/process error is a mistake; an intentional deferred compromise is debt; features/tasks retain their existing requirements and acceptance. One observation is not an instruction to create multiple records. Reconcile existing cause/owner and stable identity before creation; link genuinely distinct related problems without duplicating their repair owner.
3. In an explicitly adopted personal repository, future recording, discovery/listing, updates, resolution and verification use its selected provider and managed format. GitHub is the confirmed personal destination; preserve existing GitHub record identities while adding native types where supported, parent/child links, boards and roadmaps. Organization-scoped issue types must not be assumed to work on individually owned repositories; establish a verified supported representation for those repositories without requiring transfers. Preserve evidence, priority, state, source ownership, repair links, legacy IDs and request identity. Never create parallel BUGS.md/MISTAKES.md/TECH_DEBT.md records or append new live backlog to plans as a second canonical tracker. Retain substantial design plans and curated documentation in source.
5. Preserve both Codex and Claude discovery, qualified skill references, packaged helpers, host grants, harness manifests and generated catalogs through the owning publisher's normal source/generation process. Edit canonical source, not generated plugins. Preserve compatibility needed by already adopted declarations and migrated issues.

## ALL affected skills audit and acceptance

Create one compact source-owned coverage matrix listing each discovered affected skill/workflow/caller, source path, old behavior, changed or already-correct disposition, and actual verification. Audit every authored Core and work-items skill and their callers, then follow relevant references in other personal publisher packages when needed. Do not limit the search to the three write-* filenames. At minimum cover:

- write-bug, write-mistake, write-debt; address-bug, address-mistake, address-debt; bugfix and automatic problem recording.
- write-issue and concrete feature/task recording entry points; feature planning, work-item creation/listing, list-work/recents and roadmap routing wherever they read or write the live queue.
- session-guidance, self-repair, handoff/admission, review findings and deferred/blocked disposition paths.
- docs, plans/plan execution/checkpoint, completion and related delivery paths wherever they still create, resolve or require a file-backed record regardless of selected backend.
- shared record contracts, provider lookup, executable helper/API assumptions, schemas, permissions/manifests, both host adapters and current operational documentation.

Change every affected in-scope source owner or give concrete executable evidence that it already follows selection. Keep intentionally file-backed/unselected or employer contracts explicit rather than globally replacing strings. Use isolated source checkouts for any additional personal publisher edits; no consumer rollout or unrelated source changes.

Meaningful acceptance must exercise real writer dispatch and persisted results, not only assert prose. Verify generic and direct recording for all six current kinds, repeated-observation deduplication/update, correct selected-repository identity from a root and feature worktree, verified closure/retention, unavailable/invalid provider without fallback, unselected repository behavior, and work-policy isolation. Verify actual packaged skill discovery and execution on both Codex and Claude in isolated acceptance profiles/fixtures. Keep controlled verification records clearly identified and close only after observed evidence. Use focused regression tests, source generation and repository-required Windows/Linux coverage proportionate to the shared behavior. Do not rerun broad suites or recreate bookkeeping PRs for unchanged evidence.

Completion requires the audit matrix, source changes for remaining gaps, current independent review, all required passing checks, merged/published source where authorized by the source repository's gates, and honest installed-host acceptance. Report exact delivered interfaces and publication identities for the migration owner. Do not mark complete with an open coverage gap or claim a selected consumer was migrated by this source session.

## Active interruption: handoff reliability, 19 October 2026

Tommy explicitly requested causal repair of repeated black-screen Claude handoffs, comparison with working public implementations, then a fresh-context transfer of this original work-item goal. The broader hook and capability-scoping cleanup is deferred until later; it remains the distinct repository-capability-isolation goal. Do not describe faulty hooks as the proven black-screen cause.

Both attempted Claude launches failed with exit 1: native Claude did not acknowledge SessionStart before the startup deadline. Second receipt: C:/Users/TommySeery/AppData/Local/Temp/tj-agents-handoff-c5n2vojk/status.json. No successor pickup is established. The wrapper terminates its own child on this timeout. Do not retry blindly or create competing owners.

Repair source checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-HandoffStartupReliability, branch Fix/HandoffStartupReliability, base 281303c399046273be7b9d129daf8a9d4bde4d5b. The originating session retains diagnosis and repair ownership. A committed diagnostics correction reports startup phases, retains Claude native debug logs and prints both hosts' failed-attempt receipt paths; its focused Windows result is 220 tests with 24 skips. Native review found a missing Codex phase path, corrected with the same tests passing. The intermittent cause remains unresolved; this source correction is not a completed causal repair.

The successful init-only wrapper probe reached native launch after 182.16 seconds and acknowledged at 187.28 seconds; that proves preparation and this noninteractive probe only. Claude's official hooks documentation distinguishes interactive workspace trust from noninteractive execution. The exact Windows Terminal interactive path, its inherited handles/environment, trust state and hook entry require a bounded diagnostic before choosing a causal correction. Preserve diagnostic data, exact-child cleanup and visible failure; do not disable safety hooks or expand authentication to force startup.

Existing-component assessment is reopened at Tommy's explicit request. Public source inspected: smtg-ai/claude-squad session/tmux/tmux.go starts the native command in a PTY-backed tmux session, polls exact session existence, and captures pane output; raine/workmux supports prompt files and agent command injection. Neither source alone proves a fix for Windows Terminal. Official Claude CLI supports an interactive initial prompt; official hooks documentation states that interactive settings hooks wait for workspace trust. Compare these concrete mechanisms with the current launcher rather than adopting another framework wholesale. Sources: https://github.com/smtg-ai/claude-squad/blob/main/session/tmux/tmux.go, https://github.com/raine/workmux, https://code.claude.com/docs/en/cli-reference, https://code.claude.com/docs/en/hooks#workspace-trust.

The deadline-starvation repair now passes its real-child regression and focused tests. The originating session retains its isolated repair delivery while transferring this work-item goal to one fresh session. The broader repository-scoping goal remains queued for later, matching Tommy's deferral. Preserve all backend decisions, completed audits/design, frozen candidates, manual merge holds, credential-scope restrictions and the separate consumer-migration owner recorded here. Do not restart vendor research or the work-item design.

The completed storage audit, independently reviewed additive design and GitHub provider gap audit are preserved in [SESSION-STORAGE-DESIGN.md](SESSION-STORAGE-DESIGN.md). Carry them forward without repeating discovery. The normal-tools interactive diagnostic also acknowledged SessionStart: 102.98 seconds preparation, then 7.44 seconds to acknowledgement. Its exact native child was cleaned after the bounded observation window; no task owner was launched. This is additional acceptance evidence, not proof that the two original failures have been explained.

## Execution readiness

Verdict: ready
Execution authorization: implementation
Transfer: required
Receipt: C:/Users/TommySeery/AppData/Local/Temp/work-items-record-writers-transfer-20261019/receipt.json

The completed audit and independently reviewed storage design in SESSION-STORAGE-DESIGN.md establish the source implementation boundary. Live personal Projects provisioning remains credential-gated; source implementation is authorized and unblocked. The original source session stops writing this goal and its tracker source slices before launch. It retains only the isolated Fix/HandoffStartupReliability repair and its source delivery, with no overlap in tracker implementation paths. Its deadline-starvation regression failed before correction and the corrected focused suite passes 221 tests with 24 skips. Native normal-tools startup and response were independently observed; original historical failures lack phase timing. Repair publication and exact acceptance remain with that separate owner.

Target: Codex, L3, because narrowly scoped personal API access and cross-package rollout still have bounded unresolved alternatives; use the completed design for specified implementation. Effective design delegation is false by default because .agents/settings.json has configuration.core.auto_merge=true but no configuration.core.auto_approve; reread the actual checkout. Existing user-approved storage/backend decisions authorize their implementation; preserve explicitly reserved merge and credential gates. Pickup observation budget: five minutes after launcher completion. There is one successor for this tracker goal. Broad capability/hook cleanup B023 stays queued for later and is not part of this execution transfer.

## Next Steps

0. Before deliverable writes, read the receipt above and its attempt ID. From this exact checkout, run C:/Python313/python.exe -B C:/Users/TommySeery/.codex/plugins/cache/base-agents/engineering/local/codex-skills/handoff/scripts/transfer.py acknowledge --receipt C:/Users/TommySeery/AppData/Local/Temp/work-items-record-writers-transfer-20261019/receipt.json --attempt <receipt-attempt-id> --successor codex:<your-exact-native-session-id> --harness codex. Then claim the existing SQLite work item with C:/Python313/python.exe -B C:/Users/TommySeery/.codex/plugins/cache/base-agents/machine/local/resources/machine/scripts/work_item_sessions.py claim work-items/record-writers --host codex --predecessor codex:01a14f1d-abd0-74e0-9b75-b814a208ea87. If either operation refuses, stop deliverable writes and record the precise ownership gate; do not force or fabricate a new item. First action: verify the allocated Feature-NativeWorkItemSessions checkout still has its recorded branch/base and no conflicting code changes, and compare its current reader/schema entry points with the completed design. Save that concrete read-only verification to the transfer directory as first-action.txt, checkpoint its result in this goal, then run the same transfer helper's progress command with --receipt, --attempt, --successor, --harness codex and --evidence-file <absolute-first-action.txt>. Continue the implementation below in the same turn; an acknowledgement is not task completion.
2. Use the completed GitHub provider audit and GITHUB-REPOSITORIES.json to implement the remaining Personal slices: six precise work-item kinds including Story, verified native hierarchy, Projects membership, scheduling fields and board/roadmap views. Concertable and TjAgents have product boards; each independent personal repository has its own board and roadmap. Preserve existing selected-provider identities and retry receipts. Live provisioning is credential-gated: do not broaden the active employer account, switch its global login, run gh auth refresh -s project, or assume organization credentials can provision individually owned Projects. Source preparation remains authorized while narrowly scoped personal access is unresolved.
3. Reconcile the prepared shared-runtime PR20 and Personal PR3/4/5 with the changed backend and storage scope before any merge. Keep their exact reviewed heads and historical evidence; do not activate the personal Azure launcher or request an Azure subscription/PAT. Existing GitHub queues and the separate migration owner's records remain authoritative until coordinated acceptance.
4. CorePR298 retains its explicit manual published-contract hold. Its three missing published writer contracts still block Work/Personal source acceptance. On explicit approval, recheck its actual head and permitted manual path, own the causal publication, and resolve dependent reviews. Automatic approval review previously rejected inferred PR20 merge authority; no rejected action is retried indirectly.
6. Verify the complete personal GitHub workflow, every required independent roadmap and both native hosts, plus work/personal isolation and shared session lookup/resume. Report actual source delivery and live evidence separately. Preserve explicit merge holds and coordinate consumer declaration changes with the existing migration owner.

## Execution state

### Successor pickup — 19 October 2026

Codex successor `codex:01a154d1-300c-75b1-98cc-1145e2c2e724` acknowledged transfer attempt `16b1f828-899f-41c0-89e9-e9e525afaa48` and claimed the existing `work-items/record-writers` SQLite ownership from the recorded predecessor. The shared database claim required sandbox escalation and succeeded without changing its location or creating an item. First-action evidence is `C:/Users/TommySeery/AppData/Local/Temp/work-items-record-writers-transfer-20261019/first-action.txt`.

The allocated `Feature-NativeWorkItemSessions` checkout is clean on `Feature/NativeWorkItemSessions` at the recorded base `281303c399046273be7b9d129daf8a9d4bde4d5b`. Actual source matches the completed design: schema3 writer, non-null local labels, legacy CLI selectors, and Engineering read-only reader restricted to versions2/3. Next implementation action is the version4 reader compatibility slice before any writer activation. Effective design delegation remains false; approved backend/storage design is carried forward. Merge holds, narrow credential restrictions, frozen candidates and the separate migration owner remain unchanged.

### Session-storage delivery slices - 19 October 2026

The additive design is being implemented as two source slices under this same goal. Reader compatibility owns only Engineering's read-only schema4 admission, malformed-schema/null-label/opaque-key tests and its shipped harness declaration; its base is fresh main `281303c399046273be7b9d129daf8a9d4bde4d5b`, owning PR:316. Writer activation follows verified reader publication/adoption. The second slice owns Machine's transactional schema4/reference migration, native selectors and binding, the shipped `machine:recover-agents` facade, host grants and focused migration/ownership/recovery/packaging tests. Source candidates for that second slice are being prepared outside the source checkout until the reader candidate is frozen and delivered; no live-store upgrade is authorized by those fixtures alone. Existing PR298 publication hold is a separate review and is not expanded.

The lane is L4 for this specified implementation, with bounded non-overlapping helpers and parent-owned rollout, review synthesis and delivery. No design assessment is restarted. This split lets the reader be independently published before a writer can upgrade the shared database. Expected reader surface is three authored source/test/manifest files; writer scope is measured again before publication. Canonical goal ownership remains in this checkout; the allocated implementation checkout links this goal and does not create a competing plan.

Reader candidate is committed at `8f01ce3378684830f3df3b65b0f8685154c44ca9`: three authored files, +102/-4, independently reviewable against main `281303c399046273be7b9d129daf8a9d4bde4d5b`. Workflow contracts78 (2 skips), harness manifests19, catalog and generation pass. Native Codex review found no actionable defect and independently passed repository-provider22 tests. The configured specialist model was unavailable before dispatch execution; permitted parent fallback completed the frozen api-contract/workflow checks, both Workflow v2 results validated, and exact-head host coverage/private review-record pass. Canonical private work order is `C:/Users/TommySeery/source/repos/tj-agents/core/.git/agent-workflow/reviews/4cdaeb1d0aa95304e285541b7b6a759a584c087ded9b551048ed072e3adde0ca/work-order.md`. Generated validation output was restored after preserving evidence. Publication preflight has no code/base/review blocker; its remaining assess-scope is resolved here: the current tracker PR298 concerns recording/routing contracts, while this separate slice only expands the shared read-only database reader, so no existing PR owns it. Reader PR316 is open as a draft at the exact reviewed head, authoritative body validated, remote ref verified and delivery binding accepted under existing standing auto authorization. Its exact-head CI monitor is active: select/guard/guidance-examples passed, Windows is in progress and Linux queued at the latest authoritative read. No green remote result or reader adoption is claimed yet.

Writer source remains staged in `C:/Users/TOMMYS~1/AppData/Local/Temp/native-work-item-cli-20261019` and `C:/Users/TOMMYS~1/AppData/Local/Temp/native-work-item-sessions-candidate`; no live database upgrade. Initial cumulative CLI67 found one extra Git-context collection, repaired by reusing the claim snapshot. All new native behavior tests passed. Rerun67 passed that fix but one existing live-status test failed intermittently; isolated retry passed. Do not describe that full rerun as green. Source/Codex/Claude public-facade help smoke passes. The final cumulative candidate suite passes all133 tests in186.911seconds: full store, CLI67 and public facade3, including disposable source/Codex/Claude packaging and Unicode paths. Artifact: C:/Users/TommySeery/source/repos/tj-agents/core/.git/agent-workflow/runs/native-session-cumulative-candidate/artifacts/1319d5616b9435f7-store-cli-facade.log. Parent review found that rebuilding work_items would otherwise lose named indexes/triggers; the repaired migration captures and recreates them transactionally, with success and rollback behavior verified by the focused schema12 suite and this full cumulative pass. No live-store migration or reader adoption is claimed. The same133 tests also pass in network-disabled Linux containers on Python3.9.25 (11.131seconds) and3.12.15 (9.056seconds). Existing images only; read-only host fixture copied into disposable container-local storage. A later parent inspection reproduced a NULL-home-branch defect: a cross-repository owner handoff filled the execution branch from the foreign caller. The new regression failed before correction; native foreign-repository claims now suppress execution-branch updates while preserving actual successor session metadata and handoff links. Focused NativeReferenceTests7 pass. The revised cumulative134-test Windows/Linux3.9/Linux3.12 runs are in flight; earlier133 results remain exact prior-candidate evidence. Artifacts: native-session-linux-candidate/dd6d70abb99f42b7-py39.log and2a1b386f7db6eec1-local.log under the common Git workflow runs directory.


### GitHub source allocation - 19 October 2026

The completed GitHub audit is carried forward. The next independent source slice is six precise kinds including Story, preserving native type identity and readback plus honest capability handling for individually owned repositories. Hierarchy and Projects fields/views remain subsequent bounded slices; no live provisioning or adoption is implied. Work Items fresh main is `a69c5cd11e2f842631fdecdfa923d44fa9a494b1`; no open generated version-sync PR or matching branch exists, and free space is12.1GiB before allocation. New branch `Feature/GitHubNativeKinds`, checkout `C:/Users/TommySeery/source/repos/tj-agents/work-items/.worktrees/Feature-GitHubNativeKinds`, PR: not opened. PR20's frozen extraction is a different source concern; preserve its head and reconcile dependencies only after the new interface is frozen. Existing Work Items checkouts include migration/adoption owners and preserved review state, so this source slice requires its own isolated checkout. Canonical goal remains this file. The source owner will measure/split its authored diff before publication and retain all merge/authentication gates.

Parent accepted the bounded type-binding proposal: preserve the existing four-key selection shape, item-based request fingerprints, receipt format and old marker shapes; add optional per-issue native-type binding `{id,name}` in managed body metadata. New native creates resolve one exact ID, record it before POST, retain returned issue identity in the existing receipt before semantic verification, and verify fresh issue readback on every success/reconciliation path. Wrong/missing native types remain visible and prevent success/mutation; listing must not silently hide a managed binding discrepancy. Sparse mappings retain explicit body-kind representation with no native-type claim. New Debt/Mistake-to-Task writes refuse visibly before POST because those are distinct user-required kinds; existing records and reconciliation remain usable without automatic rebinding or config writes. This implements the approved precise kinds while preserving existing identities, rather than migrating consumers. Story requires substantive `user_story` and `acceptance`; persisted `debt` remains the Tech Debt contract key. The actual current GitHub OpenAPI confirms response `type` is a nullable object with an integer type ID; its frozen extraction is `C:/Users/TOMMYS~1/AppData/Local/Temp/github-native-type-contract-20261019.json` (official source SHA256 `dc477f0866b67a12f1f9f6adadf721a23ad87e2289980c46c5e6fa4dbc7c4492`). This is precise wire-contract verification, not a restarted provider assessment. CorePR298 remains frozen at its original five-kind routing source; the later Story routing extension requires its own source slice, preserving that hold.

The bounded native hierarchy design is complete and will follow the kinds slice serially on its source paths. Preserve existing comment-link behavior and journal format. Add explicit parent/children/add-child/remove-child operations using verified GitHub database IDs, fresh parent plus complete children readback, no implicit replacement, self/cycle checks, and existing request/reconcile-only semantics. First slice stays within the explicitly selected repository and all six kinds; no invented Feature-only matrix, cascading closure or Project side effect. Parent404 means no visible parent, not proved absence or unsupported capability. Pending receipts and later relationship drift never authorize replay. Unmanaged/foreign neighbours remain visible observations while mutations require selected managed endpoints. Exact REST payload/endpoints and semantic failure cases are recorded by the completed github_kinds_design helper; no live writes or new configuration occurred.

The approved Story router extension is allocated separately at C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-StoryRecordRouting, branch Feature/StoryRecordRouting, exact base23e842c62feb9203d73cb94c75e945c42b3e6ac8. Forge verification confirms PR298 still owns that unchanged head and targets main. This new source child extends its five-kind contracts to Story without modifying the held parent, using provider-neutral write-story plus the existing generic router/shared writer semantics and both-host adapters/harness coverage. PR: not opened; eventual base is Feature/TrackerAwareSkills until parent delivery is approved. Its implementation helper owns only that checkout; canonical goal and all publication/merge decisions remain here.


Current direction is the GitHub personal setup and shared session-storage clarification above. The Azure-specific Personal candidates described below are preserved preparation, not the approved current personal rollout. No personal Azure organization, credential, live item or queue switch was created. The SQLite implementation remains in Core Machine. Its completed reviewed evolution is in SESSION-STORAGE-DESIGN.md; the prepared Work Items PR20 adds shared remote record operations and is not delivery of this clarified storage outcome.

Core's tracker-neutral five-kind routing source is implemented and reviewed at 23e842c62feb9203d73cb94c75e945c42b3e6ac8 in PR298, with exact-head Windows/Linux and native simulated-provider acceptance recorded below. It remains subject to its published-contract merge gate. The GitHub provider source correction is merged as work-items PR18; old records retain their identities.

Personal PR3 contains the separately owned Azure provider, structured schemas, Core reader, secure OS credential launcher, Codex/Claude project configuration and narrowly scoped Claude suppression. Source implementation commit0454e04 was merged with current personal main11531d7 at354aeeb98e4a613f3e385bab1861b70f51691e1f. Subsequent review corrections verify Feature parents on both create-recovery branches, accept Azure's native open states in Core's reader, reject stale structured facts after human edits, and exclude Closed/Removed from the default queue. Current final delivery identities and verification results are recorded in the latest checkpoint below.

The frozen personal entry layer is Feature/PersonalWorkItemSkills at6d59214 (draft PR4, base Feature/AzureWorkItems/PR3). The current personal checkout is the new Refactor/SharedWorkItemRuntime child, extracting shared mechanics under the latest approved execution checkpoint. It supplies five recording-only kind entries, five typed addressing workflows and one generic addressing workflow, with an explicit Engineering dependency. Core retains provider-neutral lifecycle behavior; the ownership map is in COVERAGE.md. The parent provider branch remains frozen at6ec6f50.

Personal source publication, live Azure provisioning, installed Codex/Linux acceptance and migration are not yet complete. No live personal work item or personal queue selection has been created. Employer project settings and global MCP registrations are preserved.


## Historical execution evidence

These dated checkpoints preserve earlier observations. The current Next Steps and latest checkpoint supersede their pending actions.

### Implementation checkpoint ? 18 October 2026

Core now contains the thin generic issue router, concrete feature/task writers, shared selected-writer protocol, corrected indirect callers, matching host adapters and catalog/harness changes. Its file listing helper refuses selected/invalid provider declarations and directs callers to the qualified provider rather than showing a stale Markdown queue. Focused results: 7 primary-selection tests, 49 list-work tests and skill-packaging verification pass; source generation succeeds. The source-owned audit is [COVERAGE.md](COVERAGE.md).

The provider correction is isolated at C:/Users/TommySeery/source/repos/tj-agents/work-items/.worktrees/Fix-PrimaryTrackerSelection on Fix/PrimaryTrackerSelection from bcf57f969a874181ca5327970dc59646ad820a6d. All five kinds now share primary selection across feature and nested invocations. Its 39 tests and 53-file generation check pass. This is a separate provider PR because Core must not own GitHub transport. Both helpers have released their writer leases; this session owns remaining edits. No adoption setting, migration record or primary provider checkout was modified.

The Core slice is cohesive: one shared selection contract and all contradictory callers must ship together, plus three thin skills and the executable list guard. Provider transport remains a separate source slice. Generated Core plugins remain uncommitted. Independent review, required CI and publication are still outstanding.

```agent-host-coverage
{
  "schema_version": 1,
  "hosts": [
    {
      "host": "claude",
      "behavior": "Both scope profiles inject shared Work Items while retaining separate provider, credentials and process rules.",
      "source": "Canonical owner paths and frozen heads are listed in the final source checkpoint and PR delivery map.",
      "mapping": "claude generated skill adapters, shipped harnesses and Core rolling resolver projections",
      "verification": {
        "level": "source",
        "result": "limited",
        "evidence": "Shared9b2a2df Windows128 and Linux3.9/3.12 installed128 tests pass. Personalf8d00d7 actual Windows/Linux installed-wheel smoke, Windows58/Linux60 suites and CI60 on both pass. Employer53e3baf installed guard/help and30 suites pass Windows/Linux. Both host dependency/projection fixture passes at final payloads; no Personal employer graph leak. Native/workflow/security review and private exact-head receipts pass."
      },
      "exception": {
        "constraint_evidence": "Personal live organization remains unknown. CorePR298 manual contract hold blocks published writer references; employer CI was not started due to GitHub account billing. Automatic review rejected deriving PR20 merge approval from earlier wording; explicit approval is pending. Source/fixture/installed-library verification does not establish live native-host MCP activation.",
        "supported_other_host_outcome": "Both hosts map to the same canonical definitions, and each resolver/catalog projection passed. Existing work MCP verification remains intact; fresh personal native-host authentication requires the personal organization/secure credential setup and live pilot."
      }
    },
    {
      "host": "codex",
      "behavior": "Both scope profiles inject shared Work Items while retaining separate provider, credentials and process rules.",
      "source": "Canonical owner paths and frozen heads are listed in the final source checkpoint and PR delivery map.",
      "mapping": "codex generated skill adapters, shipped harnesses and Core rolling resolver projections",
      "verification": {
        "level": "source",
        "result": "limited",
        "evidence": "Shared9b2a2df Windows128 and Linux3.9/3.12 installed128 tests pass. Personalf8d00d7 actual Windows/Linux installed-wheel smoke, Windows58/Linux60 suites and CI60 on both pass. Employer53e3baf installed guard/help and30 suites pass Windows/Linux. Both host dependency/projection fixture passes at final payloads; no Personal employer graph leak. Native/workflow/security review and private exact-head receipts pass."
      },
      "exception": {
        "constraint_evidence": "Personal live organization remains unknown. CorePR298 manual contract hold blocks published writer references; employer CI was not started due to GitHub account billing. Automatic review rejected deriving PR20 merge approval from earlier wording; explicit approval is pending. Source/fixture/installed-library verification does not establish live native-host MCP activation.",
        "supported_other_host_outcome": "Both hosts map to the same canonical definitions, and each resolver/catalog projection passed. Existing work MCP verification remains intact; fresh personal native-host authentication requires the personal organization/secure credential setup and live pilot."
      }
    }
  ]
}
```


### Native acceptance and first publication checkpoint - 18 October 2026

Both native hosts passed generic/direct recording of all five kinds, semantic repeat reconciliation with dated evidence, tracker-only listing from feature subdirectories, retained synthetic closure, unavailable/invalid/offline no-fallback behavior, unselected defaults and synthetic employer opt-out. The coverage matrix records exact fixture identities and the Git-private hashed evidence index. These are installed skill tests with the real provider CLI and persisted simulated GitHub API; trusted hooks, live GitHub and adoption are explicitly unclaimed. All native processes exited successfully and both copied temporary authentication files were removed.

Provider source PR #18 is merged at dfb3fc4d59ff27a9761844e99e889f1f469095be. Source head 5ab611b5d79f1c89482cd7f97af1e79fbb740105 passed CI 39133891369 on Windows/Linux/hosts; main CI 39134901855 also passed. The source goal's observed execution/delivery authority was carried into its scoped binding under engineering:merging, without changing repository standing authorization. No consumer rollout was performed.

Core full review completed at a6e9858fd393a259678792825a9043a11dd5fa43 with no retained findings. Main moved through 86dbae8a9fa199e451017ef4c51bcbae6a5587a9; the only overlapping candidate change was its generated machine catalog digest. Reconciliation produced 4e4342a32a274ff384bacb2f63cb35d723eee881 with unchanged authored routing/runtime. Its required incremental review is being frozen. Core generation and packaging passed after the substantive earlier synchronization that retired admission. Remaining work: finish incremental evidence, publish Core PR, own Windows/Linux CI and merge/publication, then release completed source bindings and session ownership. The separate migration owner retains adoption and existing-record migration.

### Current review and CI recovery - 18 October 2026

Core source PR298 is draft at4e4342a32a274ff384bacb2f63cb35d723eee881. Full and synchronization-delta review are complete with no retained tracker findings. Both independent incremental lenses confirmed an independent upstream Codex startup timeout defect. Direct comparison to main86dbae8a proves identical startup_binding.py/agent_cli.py/launcher bytes; routing neither exposes nor worsens it. Dated evidence and repair conditions were appended to existing primary BUGS.md B018 under live owner codex:01a1415f-6448-7123-8b17-c7fb67aee637. This explicitly separate launcher owner retains the repair; no duplicate writer or consumer change was made.

CI39135348347 ran the full Windows/Linux suites and failed the source-layout test's old exact85-skill assertion after the three new canonical skills raised it to88. A fresh unit-debug context owns only tests/test_source_layout.py. This is a deterministic stale expectation, not a flaky test or platform failure. The repaired committed head needs focused source-layout verification, a small incremental review and one new CI run.

Delivery binder records published-contract stop at .agents/engineering/contract/plan-checkpoint/SKILL.md. The standing policy allows auth but does not exempt published-contract; persistent-delivery explicitly says scoped approval cannot bypass a stop. Blocked action: Core merge only. Resolver: Tommy. Observable resume condition: explicit decision for the contract-changing Core PR through the repository's permitted manual gate. Next action once all unblocked work is complete: present the fully reviewed green ready PR and this exact gate; retain the session for the answer.

The stale-count correction is committed as23e842c6. The actual failing invariant passed after refreshing generated catalog digests exactly as CI does; artifact .git/agent-workflow/runs/tracker-aware-skills/artifacts/d3c9a791f5463c67-layout-count-focused.log. Generated digests were restored to HEAD before committing; no distribution output entered the source PR. The helper's earlier direct attempt stopped at expected local generated-digest drift before reaching the assertion; no additional defect was inferred. Incremental review is freezing only4e4342a..23e842c6 (tests/test_source_layout.py).

### Final source candidate - 18 October 2026

Core PR298 now owns pushed head23e842c62feb9203d73cb94c75e945c42b3e6ac8. The one-file incremental review is complete, approved and privately recorded. Its native-general dispatch twice returned invalid Workflowv2 shape, so the parent closed it and completed the same bounded frozen objective under the defined fallback: exact patch hash,88 canonical definitions, equal both-host adapter sets and unchanged canonical-link invariants. No retained candidate findings or new security/host-surface delta. Full source and earlier synchronization review remain unchanged.

CI39136963491 is under the active supported readiness watch. Core remains draft until required checks pass; remaining merge decision is the recorded published-contract stop. The existing runtime binding is exact to23e842c6 and will be refreshed with the completed review evidence before transition. No further source edits or push is planned for metadata.

### Ready publication decision - 18 October 2026

CI39136963491 passed select, guard, verify-windows, verify-linux and ci-required at exact23e842c62feb9203d73cb94c75e945c42b3e6ac8; regenerate is correctly skipped for the PR event. Windows ran14:39:25-14:56:57UTC; Linux ran14:39:25-14:43:16UTC. The supported readiness watch terminated ready. Core PR298 was marked ready and an authoritative post-wake read confirms OPEN, draft=false, CLEAN and exact head23e842c6. Its final description and current review watermark were validated; the binding has no pending evidence and reviewed_sha equals the exact source head.

- State: blocked at human delivery decision, with all authorized preparation complete.
- Blocked action: merge Core PR298 and its causal generated source publication.
- Reason: .agents/delivery-authorization.json does not exempt published-contract; changed .agents/engineering/contract/plan-checkpoint/SKILL.md triggers that stop. The observed source-goal authorization does not bypass typed repository stops.
- Resolver: Tommy.
- Unblock action: decide whether to approve manual merge of the fully reviewed green Core PR298.
- Observable resume condition: explicit decision for that PR/contract change; current source remains23e842c6 with green checks and recorded review.
- Next action on approval: recheck exact PR/head, execute the permitted manual merge gate, own the landing and causal regenerate publication, then finish source-goal cleanup. Do not adopt consumers or change migration ownership.

The foreground delivery wait is terminal and its binding is released at this genuine authorization decision; no scheduled task or pending CI is left owned. The CLI and canonical goal stay available for the required answer. Core is not reported merged or the source goal complete.


### Earlier conditional interim assessment - superseded by long-term assessment below

Tommy's latest clarification allows considering GitHub only as a temporary workaround until Termboard, conditional on a better practical solution not being established. No unconditional backend approval or Core merge approval was given. This checkpoint supersedes the earlier ready-publication next action; preserve its CI and review as historical evidence.

Observed source evidence: the inspected work-items provider's github_tracker.py creates issues and optionally sets a configured native issue type. records.py renders generic links in the body. Its schemas and transport expose no native parent/sub-issue relationship operation. A body link is not verified native hierarchy. Existing fixture acceptance verified five-kind lifecycle routing, not feature/task grouping. The explanation should have distinguished those capabilities before presenting the original slice as ready for the user's intended workflow.

Official GitHub documentation confirms native parent/sub-issue relationships and Projects grouping/progress. Organizations have configurable issue types including Task, Bug and Feature; do not assume organization-only type support for personal-account repositories. GitHub's terminology therefore does permit work items beyond bugs, and the claim that grouping is impossible is incorrect. References: https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues ; https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/managing-issue-types-in-an-organization ; https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-parent-issue-and-sub-issue-progress-fields .

Bounded alternatives assessment: retaining the existing GitHub provider reuses delivered transport and repository access, but needs native hierarchy support to meet the clarified grouping requirement. Azure Boards provides typed hierarchical work items (https://learn.microsoft.com/en-us/azure/devops/boards/get-started/plan-track-work?view=azure-devops), but would introduce a different interim tracker/provider and setup before Termboard; employer-scoped skills cannot be reused in personal repositories. Keeping existing local file defaults avoids hosted adoption but does not establish the requested shared feature/task hierarchy. Building another custom tracker competes with Termboard. No evidence establishes that GitHub is the only solution or universally best.

Read-only Termboard primary README identifies the project as a skeleton. Its plans/ROADMAP.md places a local card store at milestone1 and Epic/Feature hierarchy in a later optional milestone6. This is source/document inspection, not a runtime readiness test; no Termboard file was changed. Termboard replacement/import support must be verified before any cutover is promised.

Proposed interim acceptance: explicitly temporary GitHub storage; native feature-parent/task-child relationships created and read back by the selected provider; Core remains backend-neutral; preserve stable identities, kind, state, evidence and relationships for an eventual export/import; verify migration to the actual Termboard interface before retiring any canonical GitHub records. Export/import is a requirement to design and test, not a delivered feature. Do not introduce another permanent hosted system solely for this bridge without a concrete advantage over these requirements.

Pending observation for the canonical mistake record: incomplete explanation of the storage model and of the gap between body links and native hierarchy led to a misleading readiness impression. Prevention is to state provider limitations and verify required relationships before claiming that workflow complete. Keep these facts here pending the backend decision rather than create a new GitHub issue while that destination is contested. Source diagnosis found no evidence that the generic Core selection contract requires a GitHub backend or forbids hierarchy; do not invent a broad standards change or blame a silent standard for an unsupported platform claim.

Remaining decision: Tommy resolves whether the explicit temporary GitHub proposal is acceptable given the practical alternatives and missing hierarchy work. Resume condition: that choice and the provider repair scope are clear. First dependent execution action: implement native relationship support with focused persisted read-back and retry/reconciliation checks in the provider's own isolated source slice, then refresh coverage and review. The existing published-contract gate still applies before Core merge. No consumer rollout, migration-owner message, replacement installation or remote tracker write was performed during this assessment.


### Long-term cloud tracker recommendation - 18 October 2026

Authorized scope: Tommy explicitly requested current solution and cost research, including Azure integration with Termboard. No account creation, subscription change, installation, replacement implementation or record migration was requested. The earlier assumed migration into Termboard's independent local store no longer meets the clarified requirement. Local storage remains useful as a cache, but cloud authority and multi-machine access must be explicit.

Assessment complete for recommendation, pending a real pilot before adoption. Recommend Azure DevOps Services/Azure Boards in a separate personal organization, with source code remaining on GitHub and Termboard providing terminal interaction, worktree/session launching and an optional reconstructible cache. Azure owns authoritative record identity, state and relationships. Do not build a second cloud tracker or commit a live SQLite database as a substitute for synchronization. Start with online reads/writes; offline writes require an explicit later conflict/retry design rather than an implied sync guarantee.

Current primary-source comparison checked on 18 October 2026:

| Option | Current advertised cost/limit | Fit and tradeoff |
| --- | --- | --- |
| Azure Boards | Basic license: first five users per organization free; additional Basic users USD6/user/month. Basic + Test Plans is separate and unnecessary for this proposal. Current new-organization instructions require an active Azure subscription. | Recommended for distinct Feature/Task/Bug types, native hierarchy, history, queries, configurable process and GitHub integration. More setup and process administration than GitHub. |
| GitHub Issues + Projects | Issues and Projects included in GitHub Free. Native sub-issues and organization issue types are supported. | Viable long-term alternative with existing source integration and least new account overhead. The current provider still lacks native hierarchy operations; changing terminology alone does not make it technically unsuitable. |
| YouTrack Cloud | Free full-featured edition for up to10 users,30GB; custom logo excluded. Paid plan charges all users after exceeding10. | Strong free alternative with typed fields, parent/subtask links and GitHub integration. Another service/provider; free-instance inactivity removal after3.5 months is relevant to dormant personal projects. |
| Linear | Free tier:2 teams,250 issues. Basic:USD10/user/month billed annually with unlimited issues. | Credible hosted option; free limit is a weaker fit for a growing backlog spanning many personal projects. |
| Independent local Termboard store | Custom development and ongoing operation; no cloud availability established by the skeleton. | Useful local learning/application milestone, but insufficient as the sole store for this user's current cloud requirement. Keep the terminal application; change the proposed persistence role. |

Azure pricing source: https://azure.microsoft.com/en-us/pricing/details/devops/azure-devops-services/ . Setup/billing: https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/create-organization?view=azure-devops and https://learn.microsoft.com/en-us/azure/devops/organizations/billing/billing-faq?view=azure-devops . The active subscription requirement does not mean a paid Boards seat is required for solo use; other purchased services remain separately billable. No claim is made that signup has been exercised on Tommy's personal account.

Alternative pricing: https://github.com/pricing ; https://www.jetbrains.com/youtrack/buy/ ; https://linear.app/pricing . YouTrack relationships/integration: https://www.jetbrains.com/help/youtrack/cloud/link-issues.html and https://www.jetbrains.com/help/youtrack/cloud/github-integration.html .

Azure process/license distinction: the free Basic access license does not require the Basic work-item process. Propose an inherited Agile process for Feature/Task/Bug and potential custom Mistake/Debt kinds. Its standard backlog hierarchy is Epic > Feature > User Story > Task; verify the user's desired feature/task navigation and board behavior rather than promising arbitrary skipped-level views. Custom type/backlog mapping needs pilot validation. References: https://learn.microsoft.com/en-us/azure/devops/boards/work-items/guidance/choose-process?view=azure-devops ; https://learn.microsoft.com/en-us/azure/devops/organizations/settings/work/inheritance-process-model?view=azure-devops .

Integration feasibility is documented, not implemented or exercised here: Azure Boards supports GitHub repository/commit/PR links; az boards, REST work-item operations and Microsoft's Azure DevOps MCP expose existing interfaces to reuse. Termboard can be a client without becoming a new synchronization service. Preserve Core's backend-neutral selection. References: https://learn.microsoft.com/en-us/azure/devops/boards/github/?view=azure-devops ; https://learn.microsoft.com/en-us/cli/azure/boards?view=azure-cli-latest ; https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/work-items/update?view=azure-devops-rest-7.1 ; https://github.com/microsoft/azure-devops-mcp/blob/main/docs/EXAMPLES.md .

Proposed pilot acceptance after selection: one isolated personal Azure project and process; create/read/update/list/close/reopen the required record kinds; native parent/child read-back and useful board navigation; two clients observe the same committed state; no silent fallback or duplicate creation after retry; GitHub PR linkage; retain source/legacy identities, evidence, history and relationships; demonstrate recoverable export before any existing canonical record is retired. Pushed Markdown files are in Git; hosted tracker records are separate service data and require their own backup/export. Do not imply that git clone includes issues.

Decision boundary: Tommy selects the long-term backend and authorizes its pilot; current recommendation is Azure Boards plus Termboard as a client. First execution step following that decision is checking the personal organization/subscription and preparing one isolated pilot, with provider ownership and employer separation explicit. Existing source/migration owners are preserved. No Termboard roadmap, employer resource, shared migration plan, cloud account, tracker record or consumer declaration was modified by this assessment. Core PR298 remains held and its prior source evidence retained.


### Authorized personal Azure implementation - 18 October 2026


Continue the same canonical goal; do not start a competing source plan. Intended slices: (1) masked configuration/source inventory and personal account/organization resolution; (2) personal provider namespace and Azure lifecycle transport with deterministic five-kind facts and native relationships, focused tests/review; (3) both-host repository-scoped MCP setup with explicit organization/auth context and tests preventing employer/personal crossover; (4) real personal free-tier pilot, packaged-host acceptance and authorized personal adoption/migration with preserved existing identities/history. Keep independently reviewable source ownership; Core remains backend-neutral. Do not pile all provider and machine changes into Core PR298.

Observed machine state: Azure CLI and GitHub CLI are installed; node/npx are absent from this process PATH (not proof of no installation). No callable Azure connector tools are exposed in this session. Browser inventory is empty and createBrowserTab(iab) returned unavailable, so no web setup was performed. The personal Microsoft account and existing personal organization URL were requested asynchronously; passwords/tokens must not be sent in chat. Current work authentication will not be reused silently for the personal organization.


Acceptance: personal requests resolve only the explicit personal Azure organization/project; employer-origin requests retain their existing employer routing and cannot invoke the personal provider. Both hosts discover the intended namespace and server in real isolated acceptance profiles. Verify reads/writes and native relationships against the personal pilot and distinguish fixture tests from live evidence. A selected backend's failure retains unsent facts and cannot redirect to GitHub, Markdown or the other organization. Personal data and employer data never share an implicit default. No stale source/CI evidence is represented as proof of the new backend.

### Personal source preparation and execution sequence - 18 October 2026

Source allocation is established: tj-agents/personal already exists, with another owner's personal-policy PR1. Its head was 959cb707d2c6c1f4083b51605889c5b5e5216870 when inspected. This session cloned that branch into C:/Users/TommySeery/source/repos/tj-agents/personal.worktrees/Feature-AzureWorkItems and created Feature/AzureWorkItems as a stacked child. Parent policy/adoption sources remain owned by PR1; child review must distinguish that base from its work-item changes. Core PR298 remains a separate generic routing slice and is not expanded with Azure transport. This goal remains the canonical source plan.

The source implementation is split into independently reviewable boundaries:

1. **Personal credential and repository boundary.** Validate the real primary checkout, canonical origin and explicit personal provider before reading any credential. The primary checkout owns .personal-work-items.json (schema version, organization slug, project, canonical repository and five kind mappings); .problem-records.json selects personal:work-item. Store the personal organization's PAT in Windows Credential Manager or Linux Secret Service, never source or project MCP JSON. Missing credentials fail without work-login fallback. Launch Microsoft's official local Azure DevOps MCP, pinned initially to 2.10.0, with a fixed personal organization, PAT authentication and core/work-items domains. Pass the PAT only in the child environment with the Basic encoding expected by the official server. This isolates organization credentials; the official MCP itself is organization-scoped, not project-locked.
2. **Managed Azure provider.** One personal:work-item entry owns recording, listing, read/update, state and native relationships for Feature, Task, Bug, Mistake and Debt. Reuse the established five-kind facts and request identities. Implement the Core-compatible scripts/read_problem_record.py adapter as well as the writer CLI; MCP availability alone does not provide that noninteractive adapter. Persist machine metadata in explicit Azure custom fields, with human-readable descriptions separately. Use revision tests for updates and reconcile ambiguous creates through a durable request journal; Azure request-ID fields are not a uniqueness constraint. Fail on duplicate identities rather than guessing. Read back both record facts and parent links before reporting success.
3. **Portable host configuration and packaging.** The personal plugin must ship its runtime and manifest requirements. Do not put machine-specific absolute paths in tracked consumer settings or copy helpers by hand. Claude plugin MCP can receive its project directory; current Codex plugin MCP does not reliably expose the consumer root. Resolve and fixture-test project-scoped MCP registration/installed runtime before choosing a generated layout. Both hosts must use the same repository/credential validation. Preserve unrelated host settings. Move the inherited global work Azure DevOps server only after its exact existing definition is preserved in every verified work scope; do not alter work authentication or cloud resources.
4. **Organization-dependent provisioning and pilot.** After Tommy supplies the actual personal organization URL, verify personal ownership and free access, then create/read back one private Personal project using an inherited Agile process. Add Mistake and Debt types, explicit metadata fields and appropriate backlog/state mappings. Verify the desired Feature/Task links in both API and useful Boards navigation: default Agile inserts User Story between Feature and Task, so direct links alone do not prove the desired UI. Exercise create/read/list/update/close/reopen, repeat request reconciliation, failure retention, two-client visibility, parent relationships and GitHub links. Export all pilot data and prove recoverability. No paid tier or employer scope is authorized.
5. **One coordinated cutover.** Reconcile the separately owned migration plan and existing adopted repositories before changing consumer declarations. Preserve existing GitHub identities, history, evidence and relationships; export, import and compare before retiring old live queues. Replace old provider registrations at the verified cutover rather than keeping two active backlogs. Update personal package discovery and both hosts, then repeat native acceptance from primary and feature worktrees. Termboard remains a later client of the authoritative Azure store; no Termboard implementation is included in this source slice.

Current bounded writer lease: personal_mcp_runtime owns only the work-item scripts credentials.py, context.py and mcp_server.py plus .agents/tests/test_personal_mcp.py in the isolated personal clone. The parent owns this goal, future CLI/skill/manifests and reconciliation. Read-only helpers investigate host portability and the Core adapter protocol. No source completion or live Azure acceptance is claimed until their actual results are reviewed.

Primary references for the implementation assessment: https://github.com/microsoft/azure-devops-mcp (local authentication and tools); https://developers.openai.com/codex/mcp (project MCP configuration); https://code.claude.com/docs/en/mcp (Claude MCP scopes); https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/work-items/create?view=azure-devops-rest-7.1 and https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/work-items/update?view=azure-devops-rest-7.1 (record fields, revisions and links); https://learn.microsoft.com/en-us/rest/api/azure/devops/processes/processes/create?view=azure-devops-rest-7.1 (inherited process). These are documentation/source evidence, not proof of a configured personal organization.

Immediate next action is finishing the first boundary's offline fixture tests and independent credential/isolation review, while selecting a verified portable host registration. Then implement the managed provider against the selected Core interface. The only current user dependency is the actual personal organization URL for live provisioning and acceptance. The source work above continues while it is pending.

### Source implementation recovery checkpoint - 19 October 2026

The personal clone now contains the credential/context/MCP scripts, five record schemas and validator, Azure REST provider and request journal, plus a nested installable runtime under .agents/personal/utility/work-item/runtime/src/personal_work_items. The deployable runtime provides portable console commands; both project MCP configurations can reference personal-work-item-mcp with the repository cwd and explicit release/source checks instead of an absolute plugin path. Root development tooling uses uv, Python 3.12, pytest, Ruff and mypy. Official uv 0.13.1 was installed without shell-profile changes; the clone's locked development environment and editable runtime installation succeeded. The existing plugin selection check passed under the real user account without adding the unpublished personal plugin to this source checkout.

Last fully observed bounded tests: MCP/context 23 passed and one Windows symlink-privilege skip; Azure provider 17 passed. These precede final cleanup and are not integration, packaging, native-host or live-Azure acceptance. Both source writers released their leases without committing. Their three runtime scripts and three provider scripts remain in scripts/ until the parent verifies and moves them into the single canonical runtime package; convert imports and tests to the installed package, move templates into package data, add the skill and manifest, then run the complete gate and wheel smoke tests. Parent-authored CLI, configuration, fingerprint, host-scope helper, Core reader wrapper and fixture files need reconciliation; the last integration command returned a running session without output, so inspect actual bytes before repeating it.

Automatic approval review rejected the proposed migration of both global Claude Azure servers into 33 work-project scopes, because the breadth and ownership of the general azure server were not established. That script was not executed. Do not replay it indirectly. The prepared safer alternative changes only disabledMcpServers in explicitly matched personal project scopes and preserves global and work definitions; its source and tests exist, but independent review and live application remain pending. No live Azure write, work-project configuration change, global MCP removal or credential-store write was performed by this setup slice.

Execution environment is currently unavailable: the parent and both writers observed shell commands stop returning, including a no-profile read-only probe. Pending parent observations are functions cells 62 and 63 and command session 93843; writer diagnostics may also remain pending. Do not infer successful mutation from empty output, repeat uncertain writes blindly, or start additional shell jobs until recovery. On recovery, settle these calls and inspect all personal-clone diffs; both writer leases are now held by the parent. Then complete package integration, focused configuration/host-scope fixtures, full formatting/lint/types/tests, independent review, generation and source delivery. Preserve PR1's parent ownership and Core PR298's separate published-contract gate. The actual personal organization URL and secure personal credential setup still gate provisioning/live acceptance; the user is creating the organization himself.

### Personal runtime integration checkpoint - 19 October 2026

The prepared personal branch now has a separately packaged Python 3.12 runtime under the canonical
`personal:work-item` skill, the Python 3.9-compatible Core reader shim, native Azure provider, five
structured schemas, OS credential storage, pinned official MCP launcher and project configuration
utility. The harness includes the new skill; generation/check initially passed for 105 outputs.
Generated files need refreshing again after the in-flight formatting/type corrections.

The first integrated suite reported 50 passed, two Windows symlink skips, one machine-PATH fixture
failure. That fixture is being corrected without weakening the credential-before-launch guard.
Configuration/isolation rerun after the employer-current-worktree fix passed 13 tests with one
symlink skip. Final aggregate tests/static checks/package/host acceptance remain pending.

Claude 2.1.282 native fixture: `mcp list` health-checks disabled registrations and is unsuitable for
proving session isolation. A fresh actual `claude -p` session with an isolated temporary profile
started the unrelated dummy control server and did not start either disabled Azure dummy server.
The model call stopped as not logged in with zero API usage; this establishes MCP startup suppression,
not model authentication or Azure readiness. Fixture directory:
`C:/Users/TommySeery/AppData/Local/Temp/personal-native-mcp-e2_6klpt`.

Applied the narrower project-only isolation to this Core feature worktree, its primary checkout and
the isolated personal implementation clone. The helper verifies explicit personal Git origin and
rejects employer current AND primary paths before profile reads. Compared the updated profile after
removing only those three explicit scopes: all remaining profile fields, global MCP registrations
and every unrelated/work project entry were unchanged. Private backups are outside source.
The rejected broad work-registration migration was never executed. No live Azure calls, personal
provider selection, token storage or employer settings changes occurred.

Personal organization URL remains an external dependency supplied by Tommy. Continue unblocked
source verification/delivery first; provision and pilot only after the confirmed URL and secure
interactive credential setup. Existing provider/migration ownership and Core PR merge gate remain.


Native host/package follow-up: personal policy PR #1 and its adoption-check successor PR #2
are now merged; fetched personal `origin/main` at `11531d7`. The implementation clone is still
based on `959cb70`; merge the current main after source checkpoint/gates and target the provider
PR at main, preserving the other owner's policy/Template updates.

Configuration now writes host entries to both the primary and current worktree, while the
authoritative provider identity stays only in primary. Verified the worktree regression and
repeat check. Running configure is required for another existing worktree. Explicitly disabled
Claude personal MCP settings are preserved by refusing configuration, and another provider cannot
be overwritten. Added Core reader admission/source-pin/retained-input tests (seven passing).
The runtime worker reports 23 passing MCP tests, one Windows symlink skip, and clean strict typing,
formatting and lint. Final aggregate checks/package install and provider worker completion remain.

Codex `mcp get` did not discover the fixture project entry, and the localhost-only `exec` diagnostic
timed out. Neither is evidence of successful Codex MCP adoption. Retain native Codex acceptance as
pending; no real organization/token was used. Do not claim both hosts/Azure are ready.


### Offline preparation verified - 19 October 2026

Personal PR3 remains draft at 6ec6f50a277406af3a50c7931f1cde91f27f9a31, pushed on Feature/AzureWorkItems. It is based on merged personal main11531d7 through merge354aeeb. Final incremental review of recovery-parent checks, current-facts/native-state behavior and cross-platform credential/journal typing returned no retained findings at this exact head. Earlier credential/scope review also passed; no writer leases remain active.

Verification: final local full suite83 passed,2 Windows symlink skips,3 subtests passed. Ruff lint/format, strict mypy for both linux and win32, generation/check109 files, the personal policy adoption check and git diff whitespace check passed. Exact-head source CI39179373799 passed85 tests on Windows and85 on Linux with no skips, plus both-host marketplace validation. Exact-head policy CI39179373615 passed both platforms. The earlier354aeeb CI failures were a missing concrete skill example and Linux Windows-API type checking; both are corrected and covered by the successful current runs.

The installed tj-personal-work-items0.1.0 wheel matches every packaged Python/JSON byte in the published Git commit, including all five schemas. Exact committed-source SHA256 is42826f565c3cd60002ccdffefc7ca8963d19adbd4f2a6c6a63109bb6e1644415. Wheel: C:/Users/TommySeery/AppData/Local/Temp/personal-work-item-git-exact-30diio5f/tj_personal_work_items-0.1.0-py3-none-any.whl. Installed five-kind schema commands with the correct release/source pins passed; a wrong source pin failed before output. Loading the actual Windows credential DLL and typed bindings succeeded without reading or storing any credential. This proves package/entry-point behavior, not authenticated Azure acceptance.

Native Codex0.163.0-alpha.1 app-server initialized and returned config/read for the isolated temporary personal fixture without a model request or Azure call. Its project layer was disabled with an explicit instruction to trust that fixture in the user config; both mixed-case and reported lowercase CLI trust overrides left it disabled. Only existing unrelated global server names were observed; no personal startup is claimed. Do not silently change global trust or report mcp list/version as proof. Resolve trust with the actual adopted repository's fresh native session and then verify the personal launcher/authentication. Earlier Claude2.1.282 fresh-session fixture proves personal suppression of inherited Azure registrations only, as detailed above. Linux installed/native Azure acceptance remains outstanding despite passing Linux source CI.

The concrete live setup sequence is saved in Next Steps. The immediate dependency is Tommy's confirmed personal organization URL, followed by interactive OS-store PAT setup, process/project provisioning and a live five-kind/hierarchy pilot. Keep the current GitHub queue authoritative and coordinate the final switch with the existing migration owner. No live Azure item, new selected consumer queue, personal credential-store write, employer project setting or global MCP registration change occurred in this preparation slice. Core PR298 retains its existing published-contract merge hold. Source readiness is complete for this offline slice; the overall Azure rollout remains active and externally gated by organization identity and native/live acceptance.

Final source delivery observation: PR3 body was refreshed with the exact validation/limitations; gh confirms OPEN/draft at6ec6f50. Personal git diff and staged diff are empty. No merge or live adoption was performed.


### Personal kind entry points and Core ownership - 19 October 2026

Tommy explicitly requested direct personal kind skills and asked whether addressing/other work-item skills must move out of Core. This authorizes the personal entry-point implementation and the ownership audit. The audit found all five Core writers, three problem address workflows, feature/bugfix, listing/recents and indirect plan/review callers already select a provider; they contain no personal Azure transport. Keep that reusable engineering behavior in Core. Personal owns the Azure implementation, personal scope checks and its recording/addressing entry points. Moving the shared workflows would also remove their work/unselected use and duplicate repair engines.

Public contract: personal:bug, personal:debt, personal:mistake, personal:feature and personal:task record the known kind only, using the corresponding engineering:write-* semantics and personal:work-item storage. They do not start repairs. Add personal:address-work-item plus the five personal:address-{bug,debt,mistake,feature,task} workflows for explicit repair/implementation requests. Addressing reads the current managed item, validates personal scope/kind and reconciles the existing owner before entering Core's repair/feature/plan lifecycle. Keep all Azure record operations in personal:work-item. No new storage, CLI, credential or implementation engine is introduced. Fully qualify shared names such as personal:feature and engineering:feature; both installed-host caches contain the latter.

Delivery slice: Feature/PersonalWorkItemSkills is a child of the frozen personal PR3 branch Feature/AzureWorkItems at6ec6f50a277406af3a50c7931f1cde91f27f9a31. Reuse its isolated checkout C:/Users/TommySeery/source/repos/tj-agents/personal.worktrees/Feature-AzureWorkItems; no other writer owns it. A separate child review keeps the new entry-point contract out of the already reviewed runtime PR. Parent live Azure/native acceptance is waiting on organization identity, while Tommy explicitly requests this independent source preparation now. Target the immediate parent branch, review only the child delta, and validate the cumulative package. Expected authored size: eleven thin skills, shared routing prose, dependency/harness/README updates, roughly400 lines. Generated output is reported separately. No new runtime tests are needed for rule-only skills; run generation, Template/reference/tier checks and existing source CI, plus independent routing review.

The child must ship its engineering dependency in payload and harness manifests and both generated hosts. It preserves current queue selection, organization/PAT gates, employer settings and the existing migration owner's cutover responsibility. The current source action is implementing these entry points; the broader organization-dependent sequence above remains pending. Published Core main does not yet contain write-issue, write-feature or write-task (verified via forge contents API); Core PR298 is still OPEN at23e842c6. Record that publication dependency explicitly rather than pretending the three new Core writers are already installed or bypassing corpus-reference checks. Local candidate-corpus validation may use the existing reviewed Core source; public-main reference acceptance waits for its normal merge/publication gate.


### Personal entry-point source checkpoint - 19 October 2026

Implemented and committed child6d59214c199c6ecbd790b8beb185cfdfe591ec27 on Feature/PersonalWorkItemSkills, published as personal draft PR4 targeting parent Feature/AzureWorkItems (PR3, frozen6ec6f50). The same isolated personal checkout now owns the child; parent branch remains unchanged. Added all five direct recording utilities, all five typed address workflows and personal:address-work-item. Shared personal:work-item checks selection, persisted kind/identity, current facts, existing ownership, closed history and verified closure. Tasks retain their declared workflow; scoped new/changed behavior uses the shared feature workflow. Record-only entry points cannot authorize implementation.

Measured child delta:17 authored files,376 additions/10 deletions;55 generated files,1041 additions/15 deletions. Runtime code and installed runtime source fingerprint are unchanged. Generation153 files, Template layout, personal policy, tier payload, Ruff, whitespace and candidate-corpus reference checks passed. Candidate corpus has105 shipped skills across Personal, Template and the reviewed Core branch after refreshing Core's derived package output/catalog digests locally; those Core generated values remain uncommitted and are not part of the child PR or a new Core source change. No new runtime tests were added for rule-only entry points.

Public CI has completed, and independent routing review found no retained findings at exact child6d59214c199c6ecbd790b8beb185cfdfe591ec27 across the authored entry points, shared routing, README and manifests. CorePR298 remains OPEN; its write-issue/write-feature/write-task references are a concrete publication dependency for public-main corpus validation. Do not classify an expected missing-publication reference failure as live readiness, hide it through an external-reference exemption or invent a second recording implementation. Personal PR3 live/native acceptance and migration retain the confirmed-organization and secure credential gates. No work settings, adopted provider selection or existing record was changed.


Child CI observation: run39182325025 completed at6d59214 with85 passed on each of Windows/Linux, successful Template layout and both-host native marketplace acceptance. Both source jobs fail only their public corpus reference step for engineering:write-feature, engineering:write-task and engineering:write-issue. Policy run39182324808 passed both platforms at the same head. The reference failures are retained as the observed CorePR298 publication gate, not hidden or reclassified as passed. Resume condition: CorePR298 merged through its existing published-contract approval and the causal main regeneration exposes all three writers, then rerun this exact child check and revalidate/retarget the child after PR3 lands. Source and staged child diffs are empty.


### MCP isolation and repository-board clarification - 19 October 2026

Tommy confirmed that the personal Azure organization has not been created. He requires a clear destination for every personal organization/repository and separate boards for independent projects. He clarified that Concertable can share one board across its repositories; the rejected grouping is a catch-all Personal board for unrelated apps. The corrected proposal uses one personal Azure organization as the account boundary, with product projects Concertable and TjAgents covering their related repositories, and separate projects/boards for standalone personal apps such as Termboard and C++. Personal is ownership scope only. No catch-all Personal project will be created. Further multi-repository groupings require established product identity or explicit direction. AZURE-REPOSITORIES.json inventories 66 observed repositories: tj-agents17, Concertable15 and tomjseery34, with four archived repositories retained in the map. The organization is null and no cloud resource has been provisioned. Standalone application destinations use namespace-prefixed project names to avoid collisions; Concertable and TjAgents use product names. Microsoft primary documentation confirms the project/default-team/board relationship: https://learn.microsoft.com/en-us/azure/devops/organizations/settings/about-teams-and-settings?view=azure-devops . Live pilot acceptance must verify the intended five-kind backlog/type visibility as well as persisted relationships; creating an empty project alone is insufficient.





### Approved layout and personal sign-in boundary - 19 October 2026

Tommy approved the product-based layout with “yep sure”: shared Concertable and TjAgents product boards, separate boards for independent personal applications, and no catch-all Personal board. AZURE-REPOSITORIES.json now records layout_approved_waiting_for_organization; its66 repositories map to36 distinct proposed project destinations, with archived identities retained without automatic activation. This approval is for the layout/setup; it does not waive the unrelated CorePR298 published-contract merge gate.

The browser surface inventory returned no apps or browsers. Opening the Azure DevOps organization portal through each supported attempted browser returned Browser is not available for both iab and chrome. No personal Microsoft sign-in, organization, billing change, project, credential or work item was created. The current session cannot complete that interactive account step. Existing work MCP verification,26 work configurations and50 personal isolation scopes retain their observed results.

Blocked action: authenticate against and provision the personal Azure organization/pilot. Resolver: Tommy supplies the organization URL after creating it with his personal Microsoft account, or connects an available browser for that sign-in/setup. Observable resume condition: confirmed personal organization identity/ownership and an available secure interactive credential-entry path; tokens must not be sent in chat. Next action: inspect the existing organization/process/projects read-only, provision the agreed pilot idempotently, store only the personal organization credential through the existing OS-store prompt, then verify both native hosts and the board/hierarchy before wider rollout. Do not repeat the completed backend/layout assessment, overwrite work credentials, or switch the existing queue prematurely.

### Shared Work interface and persistence investigation - 19 October 2026



Actual persistence responsibilities from source inspection:

| Concern | Current owner and format | Proposed ownership |
| --- | --- | --- |
| Agent sessions, local execution status and active ownership | Core .agents/machine/scripts/session_store.py; SQLite ~/.agents-state/sessions.db; shared by host hooks and Engineering workflows | Keep the existing shared Machine implementation and its native session/ownership semantics. Recording a backlog item alone must not claim execution ownership. |
| Personal Azure request reservation/reconciliation | personal_work_items/request_journal.py; private Git-common-directory JSON receipts and a writer lock | Extract reusable retry/journal mechanics into the shared tracker runtime. Preserve existing uncertain receipts and request identities. SQLite conversion is not necessary for this extraction. |
| Backlog contents, native state, hierarchy and history | Current queue remains authoritative until cutover; prepared Personal replacement uses Azure Boards | Retain the chosen remote provider as the canonical backlog. Local execution state and retry receipts do not replace cloud records or become a second queue. |
| Azure record operations, schema validation and provider adapters | Personal contains the new Azure implementation; existing work-items publisher contains GitHub transport, schemas and JSON request receipts | Recommended shared neutral runtime in the existing tj-agents/work-items repository, used through explicit scope adapters. |


Recommended package flow:

```text
personal:bug -> personal scope / policy -------+
                                             +-> work-items shared runtime -> selected remote provider

Core Machine session/ownership store remains a shared execution service.
Termboard can later consume the runtime and execution service through their supported interfaces.
```


Minimal extraction sequence if Tommy selects this design:

1. Use an isolated branch of current work-items main. Reconcile the neutral runtime boundary, supported interfaces, dependencies and shared design with its source owner before touching callers. Keep the current GitHub provider operational for the migration owner.
3. Make both profile adapters call the same installed, shipped runtime with explicit scope and provider identity. Scope journal/cache identities by provider, account/organization, project and repository. Preserve uncertain JSON receipts with a tested compatibility/migration path; receipt loss or a new machine must never authorize blind duplicate creation. Keep durable retry state distinct from a disposable read cache. Do not give consumers direct SQL access to Core's session schema.
4. Add Work recording entries and exact employer operation routing, then address entries supported by actual employer lifecycle/type mappings. Reconcile package manifests, Engineering/runtime dependencies, authored references and both generated hosts in each owner. Keep the current frozen Personal review/publication evidence intact until a separately reviewed successor supersedes it.
5. Verify direct and generic dispatch for both profiles, request collisions across scopes, uncertain writes, revision conflicts, parent preservation, missing credentials/context with no fallback, and Windows/Linux plus both-host packaging. Fixture acceptance must not create employer work items. Only a verified source delivery precedes any coordinated consumer cutover.

Assessment complete for this reopened shared-runtime idea: adopt existing Azure REST/MCP interfaces and SQLite for their existing purposes; selectively reuse/extract the current tracker implementations into the existing work-items publisher. Creating a fourth tracker repository adds an unnecessary owner; forking SQLite/Azure libraries does not address the actual duplicated policy/runtime boundary. Leaving all reusable Azure mechanics in Personal would make employer reuse depend on a personal profile. Keep Core's already shared session store in place and give future Termboard a stable runtime interface rather than building a temporary local-only backlog. A later SQLite receipt implementation remains optional and requires its own concrete reason and migration evidence.

Primary technical references consulted: Microsoft Work Items Update REST 7.1 documents revision-tested field/link operations (https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/work-items/update?view=azure-devops-rest-7.1); SQLite WAL documentation describes the local shared-memory and WAL-file requirements (https://www.sqlite.org/wal.html). These document platform behavior, not acceptance of the proposed extraction. Existing Core employer-tier tests cover employer selection and personal rejection; no new dispatch test or live integration was run for this proposal. Decision remaining: adopt the existing work-items publisher as the neutral runtime owner. First execution action after that decision: isolate its source branch and define the extraction interface while preserving current providers and receipts. The confirmed personal Azure organization and Core publication gate remain separate dependencies.

### Shared runtime execution authorization and slices - 19 October 2026


Current active source locations and review boundaries:

| Slice | Checkout / branch | Actual parent and dependency | Expected size / validation |
| --- | --- | --- | --- |
| Shared runtime | C:/Users/TommySeery/source/repos/tj-agents/work-items/.worktrees/Refactor-SharedWorkItemRuntime; Refactor/SharedWorkItemRuntime | Fresh origin/main a69c5cd, including another owner's merged PersonalAdoption PR19 | Extract existing tested modules/templates, then neutralize field/auth/journal policy; mechanical code/test relocation reported separately. Preserve current GitHub provider, Python3.9 contract and migration owner's receipts. Existing GitHub suite plus extracted Azure/journal tests and wheel smoke on Windows/Linux. |
| Personal integration | C:/Users/TommySeery/source/repos/tj-agents/personal.worktrees/Feature-AzureWorkItems; Refactor/SharedWorkItemRuntime | Stack directly on frozen PR4 Feature/PersonalWorkItemSkills at6d59214. PR3/PR4 wait on live organization/Core publication; explicit new user instruction requires independent source preparation now. | Remove Personal-owned shared modules/templates; adapter retains exact field mapping, admission, credentials and existing receipt namespace. Declare shipped dependency and verify installed shared source before credentials. Existing personal suite, packaging/native entry points, source digest mismatch rejection. |
| Work interface | C:/Users/TommySeery/source/repos/tj-agents/work/.worktrees/Feature-WorkItemSkills; Feature/WorkItemSkills | Fresh origin/main461ff04; depends on shared runtime/Core writers publication | Thin recording/address entries and exact selected employer routing; matching manifests and generation. Employer-free payload invariant, scope rejection and both-host references. |
| Employer adapter | C:/Users/TommySeery/source/repos/tj-agents/company/.worktrees/Refactor-WorkItemProvider; Refactor/WorkItemProvider | Stack directly on PR6 Feature/WorkCommunications9546906, which supplies exact employer context and Work dependency. Fresh maine21364d is its ancestor; fast-forward completed. | Rename company operation and callers; employer-only adapter consumes shared HTTP/journal/record primitives. Native types, fields, assignment/parent/branch decisions and commit/push gates preserved. Scope-before-credentials and native-record/uncertain-write fixtures. |



### Shared runtime integration progress - 19 October 2026

Work entry candidate is committed locally at7993d9dcee93c9328b62f749fedc7ef611f4023e against461ff0409317d8b0cd41a3b4176b8b1ec35e3f78. It has matching recording/address vocabulary for all five kinds, exact selected-context handler routing, explicit unsupported-kind refusal and shipped Work Items dependency. Authored20 files329additions22deletions; generated55 files1054additions12deletions. Generator85current and five packaging tests passed before commit. Required native and independent workflow review are active on that immutable candidate; no push yet. A worker's earlier reference to work-items main8ec0b6a was stale and is superseded by actual fetched maina69c5cd.

Personal now imports shared records, Azure client/tracker and journal directly. Removed its copies and schemas; the Azure engine suite has been rehomed in the shared owner. Personal passes its explicit three custom-field names and the existing personal-work-items receipt namespace. A new receipt compatibility fixture uses the original uncertain JSON format and verifies reservation remains blocked. Strict typing10sourcefiles and Ruff pass. Focused MCP/scope tests passed27 with one Windows symlink skip. Its shared source manifest is deliberately unfinalized until the library freezes, so full-suite and actual installed acceptance are still pending. The eventual dependency must be installable from the exact shared Git commit rather than an unpublished PyPI name or local absolute checkout path.


### Shared runtime review and repair checkpoint - 19 October 2026

Work candidate7993d9 passed its required native and independent workflow review except for the known missing public Core writer contracts. The canonical private review work order records changes-requested with that publication dependency open. No Work source repair or push occurred; CorePR298's explicit hold remains its resolver.

The first shared library candidate05d25da was superseded before review dispatch: parent inspection found old record/journal implementations retained beneath overriding imports, and new pytest tests lacked reproducible development dependencies. The shared owner is replacing those facades with explicit imports, adding locked development tooling consistent with Template CI, and checking the complete existing GitHub plus extracted Azure/journal suites. Both caller pins remain provisional until the corrected library freezes. Personal's full Windows suite passed58 tests with two symlink skips and three subtests against the initial shared source; its wheel builds. This evidence does not establish the final caller pin or Linux acceptance.

Employer candidate2d908eb completed actual native Codex review and independent workflow/security lenses. Parent accepted the corroborated findings: incorrect standalone helper import path; missing create reconciliation and update item arguments; an undefined state argument after a successful update; string/boolean PaidWork mismatch; display-name assignment readback mismatch; replay verification using a new sprint; missing parent target scope validation on create; and stale removed-operation guidance in the native-type reference. A serialized repair lease is active in the same isolated employer checkout, with required actual parser/subprocess and successful-write/readback fixtures. The old review identity and findings remain truthful at2d908eb; repaired source requires a new review identity.

Disposable Linux acceptance images are built for actual Python3.9 and3.12. They contain Git and pytest and will run with networking disabled, frozen source and installed wheel inputs only. No final installed Linux run has been observed yet. Remaining independent work: finish and review the shared library; update both exact source pins; resolve Personal's dependency lock, generation and review; repair/review the employer adapter; run cumulative resolver and installed Windows/Linux acceptance; then deliver eligible source PRs and present only genuine remaining Core/live-organization gates.


### Installed acceptance and shared review checkpoint - 19 October 2026

Corrected shared candidate add17d8176370bb6714ff69b70601cffba1bd7d0 has runtime digest f60a95b781ec6b22e894cf254ae4675be221dd87f8d71db1948e552e067bd8a7. The full frozen suite passed77 tests on actual Linux Python3.9.25 and3.12.15, with32 subtests also passing on3.12. The wheel was installed offline with networking disabled and source mounts read-only; its installed package origin and exact digest passed, and all five shipped CLI validation kinds passed. Windows canonical unittest39 passed; the one degraded-host pytest Git timeout passed on focused retry. Personal's regenerated121-file payload and current pin passed formatting14files, lint, strict typing13files and58 tests with two Windows symlink skips and three subtests. These caller pins will change again after shared review repairs.

Required native shared review completed at add17d8, plus independent workflow and bounded auth/journal lenses. Parent retained five concrete repairs: URL-encode native type names; make per-kind lifecycle policy explicit and profile-owned; reject silently truncated queues; verify visible title/description before acknowledging create/reconciliation/update; reject standard-field collisions in metadata mapping. A serialized shared implementation lease owns those files/tests and generated output. The lifecycle API is a required per-supported-kind mapping with open, closed and inactive values; Personal passes its existing New/Closed/Removed policy. No new personal policy defaults enter the library. The caller-stale update observation matches the prior Personal update implementation and documented coordinated-writer contract; no new caller uses that API concurrently, so that observation is not retained as an introduced defect or advertised as cross-machine serialization.

The employer source repairs are applied locally and nine new command-path tests bring its full offline suite to30 passing tests; the Core payload checker passes. They cover real parsed create/update operations, Boolean fields, display-name identities, parent scope, uncertain receipts and reconciliation-only behavior, old sprint reconciliation and actual subprocess import/help. Parent owns remaining employer source/pin/delivery; the test lease is complete. Current employer source remains uncommitted after2d908eb until the final shared pin is known. Its completed private review at2d908eb records changes-requested, host source coverage and a validated receipt; that old pass remains truthful.

Next action: finish the five shared repairs and incremental review, rebuild/freeze one final library pin, update both callers and Personal's dependency lock, review/verify the final cumulative source and installed fixtures, then deliver eligible source PRs. CorePR298's explicit manual published-contract hold and the missing personal Azure organization still remain separate gates; no Azure writes, live cutover or global configuration changes occurred.


### Final shared extraction source checkpoint - 19 October 2026

Shared Work Items is committed at 9b2a2df1d8ff2a6c4968b39624cbdc683e33da07 against main a69c5cd11e2f842631fdecdfa923d44fa9a494b1. All five review repairs are resolved, the incremental native/workflow pass is approved, and exact-head host-check/review-record pass. Final runtime digest is 80af64358ce4273a681b1456b533b96d5cbe613e63ca2e9539654ea8499f2c44. Windows128 pytest/Azure83/canonical unittest39, formatting/lint/mypy and89 generated outputs pass. Actual final installed wheel and all five commands pass on Linux3.9.25 and3.12.15 with128 tests each (3.12 adds32 subtests); installed Personal/shared wheel plus employer guard/help smoke passes Windows3.13.7. Initial bind-mounted Linux runs were stopped for filesystem latency; the same frozen source in container-local storage passes in under5seconds. No source failure was hidden.

Personal child is committed at f8d00d79be792df1ec076f3482d9ada65c8edbf1 against PR4 parent6d59214c199c6ecbd790b8beb185cfdfe591ec27. Its exact shared Git dependency is resolved in uv.lock through a process-local local-Git mirror; no global configuration was changed. Explicit personal fields and New/Closed/Removed lifecycle remain in Personal. Formatting/lint, mypy13,58 tests with2 Windows symlink skips and3 subtests, generation121 and wheel build pass. Native, workflow and cumulative security reviews are approved with validated exact-head private receipts. An optional native reviewer scratch cleanup was policy-refused; the ignored scratch remains, with no source/delivery blocker or bypass. No credentials or global Personal runtime installation were changed.



Publication scope assessment is resolved from this newly authorized extraction, branch history and current forge ownership: each of the following is a new coherent source slice, PR not opened, and no existing review owns it. The deterministic preflight returned only delivery-assess-scope; all actual base, dirty-code, exact-head review and host-coverage checks pass. This assessment resolves that ownership question inline under git-branching; source PRs must preserve these actual bases.

| Slice | Publication base / dependency | Measured final delta | Scope decision |
| --- | --- | --- | --- |
| Shared Work Items | main a69c5cd; independent of held CorePR298 |22 authored code/test files +2310/-151;2 docs +30/-14;71 generated +5778/-607;1 lock +531 | Atomic library extraction with compatibility facades and meaningful Azure regressions. Much source/test content is relocated from the already-reviewed Personal provider. Splitting definitions, five schemas, validation, journal or facades would leave an unusable or duplicated library. Freeze reviewed scope; no new concern. PR not opened. |
| Personal shared caller | Feature/PersonalWorkItemSkills6d59214 (PR4), itself above PR3; depends on exact Shared revision |19 authored code/test files +135/-2399;2 docs +15/-7;63 generated +279/-7782;1 lock +11 | One dependency/caller cutover removes copied implementations and relocated tests while retaining personal policy. Separating deletion from the import/lock cutover breaks installation; retain frozen reviewed scope. Parent cannot land before Core publication/live pilot gates; this source child permits independent cumulative validation. PR not opened. |
| Employer adapter | Feature/WorkCommunications9546906 (PR6); Work and Shared publication dependencies |8 authored code/test files +897/-13;7 policy/docs +132/-8 | One company operation boundary, route rename and parsed-command regressions; generic Work remains a separate owner. Below substantive size threshold. ParentPR6 remains unmerged, so child targets it and must never merge into its feature branch. PR not opened. |

Work remains committed/reviewed at7993d9dcee93c9328b62f749fedc7ef611f4023e. Its only retained review blocker is the unshipped Core writer entry points; no new Work PR is opened over that blocker. All eligible source PRs can proceed to remote CI, retaining the existing CorePR298 manual published-contract merge hold and personal organization/live-cutover gate. Next: publish reviewed eligible source slices, validate actual PR bodies/bindings and exact-head CI, then finish any CI repair and record the remaining concrete gates.


### Published source and genuine delivery gates - 19 October 2026

| Owner | PR / head | Observed result | Resolver / next action |
| --- | --- | --- | --- |
| Shared Work Items | https://github.com/tj-agents/work-items/pull/20 ;9b2a2df1d8ff2a6c4968b39624cbdc683e33da07 | Draft; all seven reported checks pass, including Windows/Linux verification and both-host checks. Native and independent workflow review approved; body validated. | Explicit PR20 merge approval requested. Automatic review rejected creation of an auto authorization from earlier goal wording, interpreting it as implementation/draft authority. No rejected action was retried indirectly. |
| Core | https://github.com/tj-agents/core/pull/298 ;23e842c62feb9203d73cb94c75e945c42b3e6ac8 | OPEN, ready, CLEAN, all required Windows/Linux checks green; existing exact review retained. | Tommy's manual published-contract decision requested; .agents/delivery-authorization.json exempts auth only. Remains held. |
| Personal | https://github.com/tj-agents/personal/pull/5 ;f8d00d79be792df1ec076f3482d9ada65c8edbf1 | Draft child of PR4/PR3. Exact60 tests, Ruff/mypy and Template conformance pass on both CI platforms; hosts/policy checks pass. Only reference checks fail for three writers absent from published Core. Body validated and binding captured. | Publish approved Core source, rerun failed reference check, reconcile/land parents bottom-up before child. |
| Employer | https://github.com/tj-agents/company/pull/12 ;53e3baf53de06ee8cb1d1b39e48045f132f29d5f | Draft child of PR6.30 local Windows and30 Linux tests plus installed guard/help pass. No-step CI failure annotation explicitly says account payments/spending limit prevented the job from starting. Body validated and binding captured. | Tommy resolves GitHub billing; resume existing exact run after that observable change, and publish dependencies before child delivery. |

Final Linux installed profile run completed: Personal60 tests plus3 subtests pass; employer30 tests pass. Source guards and all five Personal schema/validate entry points pass with actual installed wheels on Windows3.13.7 and Linux3.12.15. The final Core resolve/_projection fixture completed with both host catalogs and required-dependency refusal. No active native/cloud personal acceptance is claimed.

Only genuine dependency/human boundaries remain: explicit merge decisions, Core publication, employer account billing, parent delivery and the personal Azure organization/secure sign-in. There is no remaining uncommitted source implementation or owned running CI to repair. No scheduler is needed for terminally gated PRs; exact bindings may be released at this boundary and re-established after approval/dependency changes. The session remains available for required answers. The source goal is not complete.

```completion
{
  "acceptance": [
    {
      "id": "shared-runtime",
      "criterion": "One shipped shared runtime and schemas with explicit caller policy and compatible retry receipts.",
      "evidence": [
        {
          "source": "Shared9b2a2df; private review work order; installed wheel Windows/Linux3.9/3.12",
          "result": "128 tests pass, five kinds smoke pass, lifecycle/readback/overflow/collision fixes verified."
        }
      ],
      "owner": "Current source session",
      "next_action": "Reconcile this preserved cloud-operation extraction with the clarified session-storage scope before requesting or performing delivery."
    },
    {
      "id": "profile-composition",
      "criterion": "Personal and employer profiles share mechanics with isolated policy and both-host dependencies.",
      "evidence": [
        {
          "source": "Personalf8d00d7 / employer53e3baf / Work7993d9d and actual Core resolver fixture",
          "result": "Windows/Linux installed checks; Personal60 Linux and60 Windows CI tests, employer30 tests, both host projection and refusal checks pass."
        }
      ],
      "owner": "Current source session",
    },
    {
      "id": "live-personal-github",
      "criterion": "Personal GitHub typed work items, hierarchy, product projects and separate independent-repository boards/roadmaps pass live acceptance in both native hosts without employer credential interference.",
      "evidence": [],
      "owner": "Current source session, preserving the existing migration owner's consumer records",
      "next_action": "Verify GitHub account/project access, native organization types and personal-repository representation; implement and read back the approved setup without Azure signup."
    },
    {
      "id": "shared-session-storage",
      "criterion": "One SQLite session store resolves a qualified GitHub or Azure work-item/Feature identity to multiple retained native agent sessions/resume IDs, preserving ownership and existing retention policy.",
      "evidence": [],
      "owner": "Current source session",
      "next_action": "Audit existing Core Machine schema/lookup and affected consumers; qualify a compatible shared interface without duplicating session storage."
    }
  ],
  "deliveries": [
    {
      "repository": "tj-agents/core",
      "pr": 298,
      "head": "23e842c62feb9203d73cb94c75e945c42b3e6ac8"
    },
    {
      "repository": "tj-agents/work-items",
      "pr": 20,
      "head": "9b2a2df1d8ff2a6c4968b39624cbdc683e33da07"
    },
    {
      "repository": "tj-agents/personal",
      "pr": 3,
      "head": "6ec6f50a277406af3a50c7931f1cde91f27f9a31"
    },
    {
      "repository": "tj-agents/personal",
      "pr": 4,
      "head": "6d59214c199c6ecbd790b8beb185cfdfe591ec27"
    },
    {
      "repository": "tj-agents/personal",
      "pr": 5,
      "head": "f8d00d79be792df1ec076f3482d9ada65c8edbf1"
    },
    {
      "repository": "tj-agents/company",
      "pr": 12,
      "head": "53e3baf53de06ee8cb1d1b39e48045f132f29d5f"
    }
  ],
  "open_tasks": []
}
```


Final boundary audit: plan host-coverage validation passes. The read-only completion check confirms ready=false because live personal MCP evidence is absent and recorded source/parent PRs remain open; no complete receipt was written. The three new PR bindings were released with their exact dependency/approval reasons, and seven completed disposable review bundles were removed after retaining private descriptors/receipts. Actual source heads and canonical review work orders remain recoverable. Work7993d9d is committed locally and awaits Core publication before its PR; the other three new source slices are pushed. No background CI wait, scheduler, cloud write, payment change, consumer cutover or rejected-approval workaround remains active. Approval questions for PR20 and manual CorePR298 remain pending, so preserve this session and checkouts.

### Confirmed session-storage boundary and GitHub direction - 19 October 2026


Read-only Core audit at23e842c6 confirms existing schema v3 stores one work-item foreign key per session, permits many sessions per work item, and enforces one owner with a partial unique index. Existing recovery verifies native history, liveness and pickup. Preserve completed/closed-session deletion under PR295; one-to-many does not promise indefinite session history. Native remote-ID lookup is missing: CLI accepts only local feature/item labels and the read-only Engineering consumer accepts schemas2/3. Current Core origin/main was refreshed before implementation; newer root/registry fixes must be preserved.

Read-only Work Items audit at9b2a2df confirms its GitHub provider can create Feature/Task/Bug by type name but currently maps Debt/Mistake to Task. It has no Story schema, native sub-issue operations, Projects membership, scheduling fields or board/roadmap configuration. Its JSON request receipts are not session storage. Scope the GitHub additions to Personal; preserve existing GitHub provider declarations and receipts until coordinated migration. Current GraphQL documentation exposes project-view mutations, including roadmap layout, so do not assume UI-only provisioning.

Actual personal credential verification ran with a process-local token for tomjseery and restored the inherited environment; the active ThomasSeery login was not switched. The personal viewer is tomjseery (U_kgDOCvH4Hw). tj-agents is O_kgDOE9Sqkg and Concertable is O_kgDOEWN3zg. Both organizations currently expose exactly Task/Bug/Feature in the returned native type list. A separate read of Projects was refused with INSUFFICIENT_SCOPES: this credential has repo/read:org and other pre-existing scopes but lacks read:project/project. No token was printed, refreshed or broadened; no live project/type/item was created.

Credential gate: engineering:git-auth prohibits account-wide classic/OAuth scope expansion. Do not run gh auth refresh -s project. Establish owner-scoped Projects/Issue Types permissions for tj-agents and Concertable through supported fine-grained or app access. Individually owned projects have different API credential support; verify that separately instead of pretending an organization token covers tomjseery's independent repositories. Existing work credentials and MCP remain untouched. This gate blocks live project provisioning, not source preparation or session-storage design.


Candidate session design for independent review: add a unique provider/scope/native-ID reference to the existing execution record; legacy labels remain aliases to that record. Bind explicitly and transactionally; conflicting bindings fail without merging owners or creating another execution record. Native-only registration must not fabricate feature/item slugs; its schema evolution must preserve existing work-item keys and session foreign keys. Update native-ID claim/status/resume/status-update and the read-only workflow consumer together. Feature/type remains remote metadata, not a second identity for the same work item. Parent/child rollups belong to the cloud profile and may query the session service by the verified item identities.

Criticality assessment: the remaining boundary decision crosses live SQLite migration, native recovery/retention, plugin dependency direction and an existing selected provider's migration. A mistaken cutover could detach real resume IDs or redirect employer records. Use a bounded independent design check before selecting implementation; parent retains the canonical plan and final decision. Existing reviewed PR heads are preserved, and CorePR298's manual published-contract hold remains unchanged.

Assessment references: GitHub native types https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/managing-issue-types-in-an-organization ; organization type API https://docs.github.com/en/rest/orgs/issue-types ; Projects API and owner-specific credential support https://docs.github.com/en/rest/projects/projects ; project-view API https://docs.github.com/en/rest/projects/views . These document capabilities; only the dated account/type reads above are live observations.

### Repository capability isolation handoff - 19 October 2026

Tommy requested one Claude investigation and repair of all repository capability scoping, plus a shared Work rule that tj-agents-specific employer-checkout artifacts remain locally Git-excluded. The distinct side workstream is owned by C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-RepositoryCapabilityIsolation/plans/repository-capability-isolation/GOAL.md, branch Fix/RepositoryCapabilityIsolation, canonical bug B023. Parent retains this tracker goal and stops writes to the side-workstream paths before its single L3 launch. Source activation and native pickup are not yet verified. The original tracker work, source candidates and holds are preserved.

The independent Feature/NativeWorkItemSessions checkout was allocated at C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-NativeWorkItemSessions from origin/main281303c3 and remains without implementation edits. The bounded independent session-storage design report is complete: retain Core Machine storage, additive qualified native references, public Machine command facade and reader-before-writer schema compatibility; no live database was touched.

Claude side handoff launch result: the one supported L3 attempt exited1; C:/Users/TommySeery/AppData/Local/Temp/tj-agents-handoff-uzg732g8/status.json is failed with native Claude did not acknowledge SessionStart before the startup deadline. No goal pickup or transferred writer was verified, and no duplicate attempt was launched. The isolated repair goal records the Machine startup-binding resolver and observable resume condition. The tracker goal and its source candidates remain with this session.
