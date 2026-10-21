# Tracker-aware source coverage

## Current cutover — 21 October 2026

This matrix supersedes the historical audit below. Source inspection, package tests and installed host acceptance are distinct evidence.

| Owner and callers | Current disposition | Verification |
| --- | --- | --- |
| Core recording contract; session-guidance; bugfix/feature; address-bug/debt/mistake/review; self-repair; handoff; docs; skill-authoring; review-lifecycle | Selected profile owns recording/read/state and native content policy; Core supplies Engineering lifecycles. No Work Items dependency or Core writer aliases remain. | Selector15, provider8, source-layout24 and harness20 tests pass; examples and references resolve. |
| Core list-work/recents; roadmap; plans/plan-authoring/execution/checkpoint; merge/persistent-workflow | Selected profile owns backlog inventory/state; local plan helpers fail visibly for selected/invalid declarations. Plans retain design/recovery. | Existing50 list-work tests and packaging checks pass. |
| Core native session registry | Qualified external references bind to the existing SQLite execution/session store; reads create no execution. No cloud record schema or transport. | Schema4 writer validation and independent migration review pending; live activation held until installed readers support it. |
| Personal | GitHub-only helper and work-item/create-work-item/address-work-item replace typed wrappers and external runtime dependency. Explicit adoption remains required. | Writer finishing deterministic tests, packaged CLI and generated host checks. |
| Infonetica | Self-contained Azure helper, same three names, native New Products/CRIS policy; debt is Technical User Story. Retire create-devops-item and its callers. | Writer reports37 tests passing with one Core-discovery skip; final parent verification pending. |
| Work | Delete12 generic tracker wrappers and dependency; retain8 communication/review utilities. |21 tests, Template conformance and generation49 pass. |
| Marketplace and installed callers | Retire Work Items catalog/roster/bindings only after replacement sources and actual callers are verified. Separate consumer owner retains its migration. | Pending coordinated cutover; no compatibility aliases or installed-host completion claimed. |

## Historical audit (superseded architecture)

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
| handoff, admission | `workflow/handoff`; `.agents/workflows/admission.py` | Already resolves primary checkout and provider-backed current records. | Existing provider-admission regression coverage; source inspection. |
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
