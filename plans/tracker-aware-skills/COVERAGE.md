# Tracker-aware source coverage

Core paths below are relative to `.agents/engineering/`; each skill path ends in `SKILL.md` unless a file is named. Authored Core and work-items skills were inspected for record creation, discovery, state, disposition and completion. Unrelated capability definitions retain their owners. Source inspection is not installed-host acceptance.

| Skills or callers | Source paths | Previous behavior and disposition | Verification |
| --- | --- | --- | --- |
| write-bug, write-mistake, write-debt | `convention/write-{bug,mistake,debt}` | Already provider first; retain conditional file defaults, deduplication and verified resolution. | Source inspection; native acceptance below. |
| write-issue | `convention/write-issue` | Missing; added thin five-kind classification and specific-writer delegation. | Both thin adapters generated; native acceptance below. |
| write-feature, write-task | `convention/write-{feature,task}` | Missing; added selected-provider recording preserving outcome, scope and acceptance. | Both thin adapters generated; native acceptance below. |
| address-bug, address-mistake | `workflow/address-{bug,mistake}` | Already selected list/read/update/close, repair-owner reconciliation and retention. | Source inspection; provider lifecycle tests cover the command path. |
| address-debt | `workflow/address-debt` | Body selected correctly; fixed unconditional file/deletion discovery description in both adapters. | Generation and packaging tests. |
| bugfix, feature | `workflow/{bugfix,feature}` | Added canonical writer reconciliation, acceptance and verified state updates. | Source/diff inspection. |
| automatic recording | `policy/session-guidance` | Problems already used writers; replaced plan-only debt destination and added feature/task/generic entry points. | Source/diff inspection. |
| self-repair | `workflow/self-repair` | Already delegates typed writers and reconciles existing repair owners. | Source inspection. |
| handoff; retired admission | `workflow/handoff`; prior `.agents/workflows/admission.py` | Provider-aware at first audit; synchronized main retired admission before delivery. Preserve main retirement and selected canonical writer identities. | Source inspection and synchronization conflict review; no retired runtime assertion. |
| handoff format | `convention/handoff-format` | Required file path; now permits canonical provider URI with stable identity. | Source/diff inspection. |
| address-review, deferred review findings | `workflow/address-review`; `convention/review-lifecycle` | Removed unconditional debt-file destination; selected writer owns postponed-work disposition. Ordinary findings remain in review work order. | Source/diff inspection. |
| review, docs-review, incremental-review, big-review, big-review-all | `workflow/{review,docs-review,incremental-review,big-review,big-review-all}` | Already share canonical review findings and corrected disposition owner; no issue per finding. | Source inspection. |
| docs, skill-authoring | `convention/{docs,skill-authoring}` | Removed unconditional TECH_DEBT file requirement; qualified writer selects destination. | Source/diff inspection. |
| list-work | `utility/list-work`; `utility/list-work/scripts/list-work.py` | Plan-only inventory; selected skill now lists tracker-only work. File helper refuses selected/invalid declarations and points to provider. | 49 tests pass, including selected/invalid failure without stale plan output. |
| recents | `utility/recents` | Adds selected recent/outstanding work; merged PR alone no longer implies item resolved. | Source/diff inspection. |
| continue-roadmap, update-roadmap | `workflow/{continue-roadmap,update-roadmap}` | Selected provider owns live candidates/state; curated roadmap retains design and graph keys. | Source/diff inspection. |
| plans, plan-authoring | `convention/plans`; `workflow/plan-authoring` | Preserve substantive design, keys and planning authority; link selected identity instead of duplicating live queue. | Source/diff inspection. |
| plan-execution, plan-checkpoint | `workflow/plan-execution`; `contract/plan-checkpoint` | Reconcile canonical identity/progress; verify state before retiring recovery artifacts. | Source/diff inspection. |
| merge, persistent-workflow | `workflow/{merge,persistent-workflow}` | Selected acceptance and state update precede completion/retirement; PR completion is not item acceptance. | Source/diff inspection. |
| standalone plans, continuation | `.agents/base/policy/{plan-artifacts,goal-continuation}` | Already preserve standalone ownership without mandatory tracker adoption. | Source inspection; unchanged. |
| git-branching, open-pr, commit-push | `policy/git-branching`; `operation/open-pr`; `utility/commit-push` | Existing optional docs handling and repository-specific employer/AB# policy remain applicable. | Source inspection; unchanged. |
| shared selection and recording | `resources/problem-records.md`; `.agents/hooks/problem_records.py` | Added one selected-writer reconciliation/readback procedure for five kinds and primary-worktree helper for listing. Strict three-kind admission reader preserved. | 7 selection tests pass, including root/feature/subdirectory and unselected cases. |
| discovery and packaging | `.codex/skills`, `.claude/skills`; `.agents/plugins/harness/engineering.json`; `.agents/catalog/catalog.json` | Added three thin adapters per host, corrected two descriptions, refreshed roster and shipped harness justification. | Source generation and skill-packaging checks pass. |
| operational docs | `README.md` | Documents optional five-kind selected tracker and conditional file defaults. | Source/diff inspection. |
| GitHub provider manage | work-items `.agents/work-items/utility/manage` | Existing five schemas, deterministic rendering, optimistic update, request receipts and retained closure already work. Fixed source selection/adoption to resolve primary checkout from root/subdirectory/feature. | 39 provider tests pass; five new regressions cover all kinds, dedup/update/note/link/closure/retention, primary selection and Azure isolation. |
| provider packaging/grants | work-items `.agents/plugins/manifests/harness/work-items.json` and generated host/packages | Existing grants retained; updated descriptions for primary-checkout behavior. | 53 generated files synchronized; generation check and diff check pass. |

## Acceptance evidence

Core workflow artifacts are Git-private under `core/.git/agent-workflow/runs/tracker-aware-skills/artifacts/`: `cdd9cdc1ed895120-core-routing-focused.log` (7 tests), `79a1f8ca721b1c1f-list-work-focused.log` (49 tests), `62634ff46616030d-packaging.log` (packaging).

Provider source slice: `C:/Users/TommySeery/source/repos/tj-agents/work-items/.worktrees/Fix-PrimaryTrackerSelection`, branch `Fix/PrimaryTrackerSelection`, base `bcf57f969a874181ca5327970dc59646ad820a6d`. No adoption checkout or migrated record was changed.

Native acceptance is in progress under temporary isolated Codex/Claude profiles at `C:/Users/TommySeery/AppData/Local/Temp/tracker-native-01a14f1d`. Generated skill and provider bytes are copied unchanged; fixture plugin manifests omit hooks to isolate skill discovery/execution. The provider's real CLI persists through a local GitHub API fixture, not live GitHub. Full trusted-hook activation and consumer rollout are outside this source test. Results, exact source candidates, persisted identities and limitations will be recorded after observation.


### Observed native results - 18 October 2026

Both native hosts passed actual packaged discovery and execution. Claude invoked `engineering:write-issue` five times and each of its five specific writers through the native Skill tool; its direct pass invoked all five writers and `engineering:list-work`. Codex loaded the installed packaged entry points and canonical skill files through its native file-based skill mechanism. Both executed the actual provider CLI.

Each independent persisted fixture has exactly five canonical identities, in bug/mistake/debt/feature/task order: `acceptance/tracker-codex#1` through `#5` and `acceptance/tracker-claude#1` through `#5`. Generic calls created five items; direct calls from a feature subdirectory added evidence to the same five, without duplicates. Tracker-only listing found all five without local plans. Parent inspection verified all managed body and kind hashes. Actual provider closure then retained all five bodies and ten evidence comments per host; closure explicitly means completion of the synthetic recording test, not a claim that a product defect was repaired.

Both hosts separately exercised selected-but-missing, malformed and offline providers. All preserved unsent facts, blocked action, resolver and resume condition in the existing fixture `GOAL.md`, with no BUGS/MISTAKES/TECH_DEBT fallback. An unselected fixture used the ordinary root `BUGS.md`. A synthetic employer-policy opt-out retained pending goal evidence and sent nothing to the personal backend. No actual employer repository was accessed. Adjacent cpp, dotnet and react authored skill sources were searched for unconditional problem-register or recording references; no additional affected caller was found.

The durable compact evidence index is Git-private `core/.git/agent-workflow/runs/tracker-aware-skills/artifacts/native-acceptance.json`, containing transcript/state paths and SHA-256 identities. Credentials are excluded. The native fixtures test skill discovery and execution with persisted simulated GitHub transport. They do not establish trusted-hook activation, live GitHub service behavior, or consumer rollout. Synchronization retired the obsolete admission paragraph; the exercised selected-writer procedure and three new canonical skill bodies remain unchanged.

Provider publication: work-items PR #18 merged at `dfb3fc4d59ff27a9761844e99e889f1f469095be`; exact-head CI run `39133891369` passed Windows, Linux and hosts, and the causally linked main CI run `39134901855` passed. Core PR298 is ready at23e842c62feb9203d73cb94c75e945c42b3e6ac8; merge and causal generated publication await its existing published-contract decision.

Core CI39135348347 exercised both Windows/Linux source suites and found the adapter-count assertion still expected85 after adding three recording skills. Commit23e842c6 changes that exact expectation to88, retaining both-host set equality and canonical-reference assertions. The focused failing invariant passed with CI's generated-digest setup (Git-private artifact d3c9a791f5463c67-layout-count-focused.log); its incremental review is complete and exact-head CI39136963491 passed both Windows and Linux plus guard/select/ci-required. The ready CLEAN PR is held only at the published-contract merge decision for plan-checkpoint.


## Personal entry-point ownership audit - 19 October 2026

Tommy requested direct known-kind recording and personal addressing. Read-only re-audit confirms that
Core's selected-provider workflow contracts are reusable across personal, employer and unselected repositories.
No personal Azure transport remains in the audited Core skills. Their current ownership is:

| Responsibility | Shared Core owner | Personal owner |
| --- | --- | --- |
| Classify an unknown recording request | `engineering:write-issue` | selected `personal:work-item` storage |
| Record a known kind with evidence and acceptance | `engineering:write-{bug,debt,mistake,feature,task}` | `personal:{bug,debt,mistake,feature,task}` direct entries and Azure commands |
| Reconcile/repair a recorded problem | `engineering:address-{bug,debt,mistake}`, existing plan or defect lifecycle | `personal:address-{bug,debt,mistake}` identity/scope entry points |
| Implement a feature/task | `engineering:feature`, existing declared workflow or `engineering:plan-execution` | `personal:address-{feature,task}` and generic `personal:address-work-item` |
| List and resume work | `engineering:list-work`, `engineering:recents` | selected provider's live list/read; personal queue state |
| Incident recording and deferred findings | session-guidance, self-repair, address-review, review-lifecycle | selected provider's canonical record/evidence |
| Plans, checkpoint, handoff, review and delivery | generic Core workflow/record contracts | selected item's facts, relationships and verified state |
| Azure REST, fields, retry journal, PAT and project MCP | none | `personal:work-item` runtime/configuration |

Source evidence: `convention/write-issue/SKILL.md:11`, `resources/problem-records.md:13`,
`workflow/address-bug/SKILL.md:15`, `workflow/address-mistake/SKILL.md:15`,
`workflow/address-debt/SKILL.md:16`, `workflow/bugfix/SKILL.md:43`, `workflow/feature/SKILL.md:44`,
`utility/list-work/SKILL.md:11`, `utility/recents/SKILL.md:21` and
`policy/session-guidance/SKILL.md:65` (all relative to `.agents/engineering/`).
GitHub PR inventory in recents remains a review/branch concern, not work-item storage.

The Personal source implementation is a separate child slice on Feature/PersonalWorkItemSkills,
parent personal PR3 at6ec6f50. Child head6d59214 is published as personal draft PR4 targeting PR3. Generated host delivery153 files,
Template layout, policy/tier checks and reference resolution against the reviewed Core candidate pass.
Independent routing review found no retained findings at exact child6d59214c199c6ecbd790b8beb185cfdfe591ec27 across the authored entries, shared routing, README and dependency manifests. CI39182325025 passes85 tests on each platform and both-host
marketplace validation; its only failures are the three missing public Core writers, which depend on CorePR298 publication.
Policy CI39182324808 passes both platforms. This audit establishes ownership; it does not claim
native execution of the new entry points, live Azure acceptance or a consumer cutover.


### Current host configuration evidence - 19 October 2026

Work-only MCP: authenticated ERM lookup succeeded; Claude reports Connected; Codex discovers azure-devops in all26 existing ignored employer-selected scope configurations, and an ephemeral native Codex startup discovered40 tools without a model turn. Config backups and scope receipts are in WORK-MCP-CONFIGS.json.

