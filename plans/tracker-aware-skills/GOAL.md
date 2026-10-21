# Tracker-aware skills and generic issue routing

## Current approved direction — 21 October 2026

Tommy explicitly rejected the separate Work Items repository/package boundary, approved profile-owned
recording, then authorized implementation with “yep lets go”. This direction supersedes historical shared
cloud-runtime, Work Items dependency and typed-entry naming decisions below. Preserve existing source
and remote data while migrating actual callers; retain no obsolete skill aliases or runtime wrappers.

The approved public surface is the same three names under each owning namespace:
`personal:work-item` / `infonetica:work-item` read/list/view through deterministic shipped scripts;
`personal:create-work-item` / `infonetica:create-work-item` create records without starting execution;
`personal:address-work-item` / `infonetica:address-work-item` reconcile an existing item and owner,
then use the applicable Core Engineering lifecycle. Personal owns GitHub behavior and conventions.
Infonetica owns Azure Boards behavior, native type/field mappings and employer authorization. Debt intent
creates an existing Technical User Story in Infonetica, not Technical Debt Item. Optional typed meta-entry
skills are unnecessary for the initial cutover. Work retains employer-neutral communications; remove its
superseded tracker dispatch/wrapper family. Core owns only the shared SQLite execution/session registry,
qualified external identity, ownership/status/resume links and reusable engineering workflows. Core does
not install or select a recording profile on behalf of a consumer. Reading an item creates no execution.

Same sole owner: `codex:01a15674-78c1-7703-8f6f-53e59ab10e57`. The distinct existing-record/consumer
migration owner remains `codex:01a14ec8-5bdd-70a3-90c1-9d31a71289cf`. Do not overlap its consumer edits;
record the changed provider interface and coordinated cutover dependency for that owner. No new handoff.

Delivery map (source preparation may run concurrently because existing source PRs are manually held or
externally gated; dependent publication/activation remains coordinated):

1. Personal PR5, existing checkout `personal.worktrees/Refactor-SharedWorkItemRuntime`, base main already
   included atb35d86d. Rehome existing GitHub runtime/schemas/receipts, add three current entry points,
   retire typed wrappers/dependency, test packaged CLI and same-record reconciliation. Existing code moves
   are reported separately; stop expansion for split assessment above1000 substantive changed lines.
2. Infonetica PR12, existing checkout `infonetica/.worktrees/Refactor-WorkItemProvider`, head94a04f4,
   fetched main23commits ahead before synchronization. Self-contained Azure helper, existing fixed auth/
   scope/revision/idempotency invariants, three current operations and debt Story mapping. Source tests and
   payload acceptance are independent of the existing employer billing/provenance gate. No live mutations.
3. Work PR10, checkout `work/.worktrees/Feature-WorkItemSkills`, head04fe9db, fetched main6commits ahead.
   Delete superseded tracker wrappers and requirements, preserve communication capabilities and later main
   fixes. Verify remaining discovery/dependency closure; no new tracker abstraction in Work.
4. Core PR298, checkout `core.worktrees/Feature-TrackerAwareSkills`, localbranch
   `Feature/TrackerAwareSkills-new` tracking the PR branch. Correction16c7cbf removes restored Markdown
   writing; latest synchronized head808d0b7d includes main01637cc6. Replace package-specific recording
   calls with selected-profile operations and remove Engineering's automatic Work Items dependency.
   Its interrupted review at808d0b7d is incomplete and superseded by this new candidate; preserve history.
5. Core native-session writer branch `Feature/NativeWorkItemSessionWriters`, baseline0a5b5b72, remains
   independently needed. Bounded writer owns its reconciled partial files/tests/docs. Core stores qualified
   remote references and execution metadata only; no cloud schema/transport copy. Preserve stored data and
   current real local execution identities. Windows/Linux/facade and migration tests precede review.
6. After replacement source and actual callers are verified, remove Work Items marketplace/roster/install
   bindings and retire its package. Source/runtime/consumer cutover is atomic in observable behavior;
   no compatibility aliases or fallback queues. Do not delete remote repository history as routine cleanup.

All source slices retain this one goal and owner, relevant independent review and exact-head checks.
Known code relocation is mechanical scope; schema/CLI/policy changes remain substantive and must be
measured per PR before final review. Never split into broken intermediate installed behavior merely to
reduce size. Preserve dirty historical worktrees and the distinct migration owner's tracker/config writes.

The Core298 manual merge hold, prior automatic-review refusals on35 workflow deletions and Personal3/4
closures, narrow personal Projects credentials, and employer billing/provenance restrictions remain.
The new architecture decision does not waive any of them. No live SQLite migration is allowed until all
installed reader entry points accept schema4; older Machine snapshots currently reject it. No new hooks,
gates, cloud account changes, broad credential scopes or model-session tests are authorized.

Previously verified Work Items20 source/install behavior remains historical migration input, not proof of
the replacement profiles' fresh-host acceptance. GitHub types/hierarchy/Projects/roadmaps stay distinct
incomplete obligations, with live provisioning requiring the recorded narrow permission resolver.

## Source checkpoint — 21 October 2026

Core routing is committed at70146c07; Work wrapper removal atcb2633e. Core source-layout24, harness20, provider8 and selector15 tests pass; examples and three-repository skill-reference closure pass. Work generation49, Template conformance and21 tests pass. Personal/Infonetica provider writers and Core schema4 writer remain in progress. No replacement source has been published or live schema activated.

Review scope uses each PR’s actual current main base, covering the complete remaining branch change rather than unrelated merged-main history. Core has55 paths including generated host deletions and plan artifacts, with ~1200 total changed lines; the existing single recording-boundary cutover remains atomic and removes aliases rather than splitting into inconsistent installed states. Independent review and exact-head checks remain required.

## Historical initial plan (superseded architecture)

## Authorization and outcome

On 18 October 2026 Tommy explicitly requested a separate source implementation handoff while the existing migration continues: ensure ALL affected skills send future bugs, mistakes, debt, features and tasks into the new selected work-item format. He requires `write-issue` to be a generic entry point that classifies the request and invokes the appropriate specific writer. This authorizes the source audit, necessary implementation, focused tests, independent review and source delivery through each repository's existing gates. This is execution, not another proposal-only investigation.

Success is verified future behavior across every affected skill and indirect caller, on both native hosts. A tracker utility, installation, consumer adoption, changed prose, or a grep result alone does not prove this. Preserve useful existing routing rather than rewriting it merely to produce a diff. Do not change unrelated skills.

## Ownership and separation from migration

- Source owner: tj-agents/core for generic engineering contracts and existing recording/addressing skills; tj-agents/work-items for GitHub-specific templates, transport and tracker behavior.
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

Read the cross-repository docs plan for approved storage/package decisions and dated delivery evidence, but use this goal for your source implementation state. The storage assessment is complete: per-project GitHub Issues, separate optional work-items plugin, deterministic five-kind templates, shared generic Core integration. No Firebase, replacement tracker, versioning repair or repeated market survey is needed.

Current fetched Core source ALREADY contains explicit provider-first prose in write-debt, write-bug and write-mistake. The shared .agents/engineering/resources/problem-records.md reads a primary-checkout .problem-records.json declaration, loads its qualified provider and blocks rather than creating a Markdown fallback if a selected provider is missing/invalid. Without a provider it retains the declared/file defaults. Existing provider admission and GitHub transport shipped in Core #272 and work-items #7. Do not claim these writers are wholly unintegrated or erase functioning selection. Verify the real command path and every caller, correct contradictions/gaps, and add missing routing. No write-issue, write-feature or write-task entry was found under current Core's engineering tree during dispatch; inspect both publishers and installed catalogs before choosing names/owners.

The earlier handoff mistakenly treated delivered tooling and read/admission integration as proof that all future writing workflows were complete. This source goal corrects that coverage gap explicitly. The migration's direct use of a tracker script does not establish that ordinary agents invoking recording skills follow it.

## Required behavior

1. `write-issue` classifies a request as bug, mistake, debt, feature or task, then delegates to the appropriate specific writer. Keep it a thin entry point: reuse shared classification/record semantics, deterministic templates, selection and transport; do not add a second backlog or duplicate creation logic. Direct specific-skill calls and generic calls must reach the same canonical item and format. Ask only when the available facts cannot resolve a materially different action. Recording must not silently invoke addressing/implementation.
2. Keep precise kinds: faulty software behavior is a bug; an observed agent/process error is a mistake; an intentional deferred compromise is debt; features/tasks retain their existing requirements and acceptance. One observation is not an instruction to create multiple records. Reconcile existing cause/owner and stable identity before creation; link genuinely distinct related problems without duplicating their repair owner.
3. In an explicitly adopted personal repository, future recording, discovery/listing, updates, resolution and verification use the selected GitHub tracker and its managed format. Preserve evidence, priority, state, source ownership, repair links, legacy IDs and request identity. Never create parallel BUGS.md/MISTAKES.md/TECH_DEBT.md records or append new live backlog to plans as a second canonical tracker. Retain substantial design plans and curated documentation in source.
4. Core remains backend-neutral and usable at work. Preserve repository selection, explicit opt-outs, existing unselected-repository contracts, and Infonetica/Azure DevOps ownership. Installing Core or work-items alone must not adopt a tracker or redirect employer evidence to GitHub. Do not modify employer repositories or copy their private content. A selected provider that is unavailable/offline must fail visibly and retain unsent facts under the existing contract without inventing synchronization or silently selecting a file fallback.
5. Preserve both Codex and Claude discovery, qualified skill references, packaged helpers, host grants, harness manifests and generated catalogs through the owning publisher's normal source/generation process. Edit canonical source, not generated plugins. Preserve compatibility needed by already adopted declarations and migrated issues.

## ALL affected skills audit and acceptance

Create one compact source-owned coverage matrix listing each discovered affected skill/workflow/caller, source path, old behavior, changed or already-correct disposition, and actual verification. Audit every authored Core and work-items skill and their callers, then follow relevant references in other personal publisher packages when needed. Do not limit the search to the three write-* filenames. At minimum cover:

- write-bug, write-mistake, write-debt; address-bug, address-mistake, address-debt; bugfix and automatic problem recording.
- write-issue and concrete feature/task recording entry points; feature planning, work-item creation/listing, list-work/recents and roadmap routing wherever they read or write the live queue.
- session-guidance, self-repair, handoff/admission, review findings and deferred/blocked disposition paths.
- docs, plans/plan execution/checkpoint, completion and related delivery paths wherever they still create, resolve or require a file-backed record regardless of selected backend.
- shared record contracts, provider lookup, executable helper/API assumptions, schemas, permissions/manifests, both host adapters and current operational documentation.

Change every affected in-scope source owner or give concrete executable evidence that it already follows selection. Keep intentionally file-backed/unselected or employer contracts explicit rather than globally replacing strings. Use isolated source checkouts for any additional personal publisher edits; no consumer rollout or unrelated source changes.

Meaningful acceptance must exercise real writer dispatch and persisted results, not only assert prose. Verify generic and direct recording for all five kinds, repeated-observation deduplication/update, correct selected-repository identity from a root and feature worktree, verified closure/retention, unavailable/invalid provider without fallback, unselected repository behavior, and work-policy isolation. Verify actual packaged skill discovery and execution on both Codex and Claude in isolated acceptance profiles/fixtures. Keep controlled verification records clearly identified and close only after observed evidence. Use focused regression tests, source generation and repository-required Windows/Linux coverage proportionate to the shared behavior. Do not rerun broad suites or recreate bookkeeping PRs for unchanged evidence.

Completion requires the audit matrix, source changes for remaining gaps, current independent review, all required passing checks, merged/published source where authorized by the source repository's gates, and honest installed-host acceptance. Report exact delivered interfaces and publication identities for the migration owner. Do not mark complete with an open coverage gap or claim a selected consumer was migrated by this source session.

## Next Steps

Complete isolated native Codex/Claude persisted writer acceptance and the [coverage matrix](COVERAGE.md). Checkpoint the two source slices, synchronize once before freezing independent review, repair validated findings, then publish through each repository's Windows/Linux and merge gates. Keep adoption and existing-record migration with the separate docs owner.

## Execution state

The first source inspection confirms provider-first routing already exists in the three problem writers and address workflows. Core's provider runtime currently implements strict current-record reads for handoff admission only; no generic or feature/task writer exists. `list-work` discovers Markdown plans, so tracker-only items are absent. `docs` and `skill-authoring` still require file debt destinations unconditionally. The work-items primary checkout is stale; fetched main bcf57f969a874181ca5327970dc59646ad820a6d contains the delivered five-kind tracker and must be inspected instead. No primary checkout or adoption setting was modified.

Current slice: one coherent Core routing change: thin issue/feature/task skills, shared selected-work contract, affected callers and executable selection/listing verification. Keep GitHub transport and templates in work-items. If its current interface needs correction, isolate a separate source slice; do not expand this Core PR with provider transport. PR: not opened. Expected Core size: below 1,000 substantive lines; reassess before exceeding it. Verification: focused provider/listing tests, generation, independent review, Windows/Linux CI, then isolated native-host acceptance. Design selection remains the user-approved five-kind router; repository routine design approval is false.


### Implementation checkpoint ? 18 October 2026

Core now contains the thin generic issue router, concrete feature/task writers, shared selected-writer protocol, corrected indirect callers, matching host adapters and catalog/harness changes. Its file listing helper refuses selected/invalid provider declarations and directs callers to the qualified provider rather than showing a stale Markdown queue. Focused results: 7 primary-selection tests, 49 list-work tests and skill-packaging verification pass; source generation succeeds. The source-owned audit is [COVERAGE.md](COVERAGE.md).

The provider correction is isolated at C:/Users/TommySeery/source/repos/tj-agents/work-items/.worktrees/Fix-PrimaryTrackerSelection on Fix/PrimaryTrackerSelection from bcf57f969a874181ca5327970dc59646ad820a6d. All five kinds now share primary selection across feature and nested invocations. Its 39 tests and 53-file generation check pass. This is a separate provider PR because Core must not own GitHub transport. Both helpers have released their writer leases; this session owns remaining edits. No adoption setting, migration record or primary provider checkout was modified.

The Core slice is cohesive: one shared selection contract and all contradictory callers must ship together, plus three thin skills and the executable list guard. Provider transport remains a separate source slice. Generated Core plugins remain uncommitted. Independent review, required CI and publication are still outstanding.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/engineering/resources/problem-records.md and canonical .agents/engineering recording/caller skills",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Classify and record five kinds through the selected provider, reconcile existing ownership and verify persisted state",
      "source": ".agents/engineering plus work-items/.agents/work-items/utility/manage",
      "mapping": ".claude/skills thin adapters and generated claude plugin skill payloads",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Matching thin adapters, successful source generation and packaging checks; native isolated persisted writer acceptance is running separately"
      }
    },
    {
      "host": "codex",
      "behavior": "Classify and record five kinds through the selected provider, reconcile existing ownership and verify persisted state",
      "source": ".agents/engineering plus work-items/.agents/work-items/utility/manage",
      "mapping": ".codex/skills thin adapters and generated codex plugin skill payloads",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Matching thin adapters, successful source generation and packaging checks; native isolated persisted writer acceptance is running separately"
      }
    }
  ]
}
```
