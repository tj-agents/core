# Workflow and Agent Store

## Outcome and authority

Core publishes coherent `workflow:` and `agent-store:` namespaces with one implementation owner per
responsibility. Workflow owns authorized goals, planning, execution, resumption, status and deliberate
transfer. Agent Store owns the existing SQLite execution/session/ownership registry and deterministic
operations. Engineering owns software implementation, diagnosis, testing, code review and delivery.
Machine owns native identity, process observation, host launch and communication. Personal and Infonetica
retain their distinct GitHub and Azure item operations.

Tommy's 21 October 2026 dispatch explicitly assigns this session architecture decisions, the canonical
follow-up plan and execution of the coherent reviewed PR after readiness. It supersedes the older brief's
requirement for another launch. Its merge authority applies only to the separately owned narrow handoff
wording repair; this architecture work must preserve its own normal merge and installation gates.
No new independent successor is needed to decide this same architecture. Bounded evidence readers,
implementation workers and independent reviewers remain subordinate to this owner.

Source context: the dispatched `tj-workflow-architecture-dispatch-20261021.txt` and
`tj-workflow-agent-store-handoff-20261021.md` in Tommy's temporary directory. The prior routing/store
cutover's current completion checkpoints were read and accepted; its historical holds are superseded.
This is a new workstream, not a continuation of that completed migration.

Preserve the primary Core checkout, all unrelated dirty work, the originating CLI and
`work-items/.worktrees/Refactor-SharedWorkItemRuntime`. Do not modify the old migration goal, the separate
handoff repair or its branch. Its merged result was read before the namespace move: Core PR #344,
`ed6d56ffd060a64e7c9e14f5cf57bcddf7c3fc32`, merged 21 October 2026 at 21:49 UTC.
Preserve that dispatch-first behavior when moving its canonical skill.
No new repository, compatibility aliases, duplicate orchestration, remote issue creation, Azure writes,
bulk plan conversion, obsolete-PR closure, unrelated workflow deletion or account changes are authorized.
Agent Workboard is outside scope and is not a dependency.

## Ownership

- Native owner: `codex:01a16053-d03d-7753-8ad9-3174781fba89`.
- Execution: `github.com/tj-agents/core:workflow/agent-store-architecture`.
- Worktree: `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Refactor-WorkflowLifecycle`.
- Branch: `Refactor/WorkflowLifecycle`.
- Base/parent: `Refactor/WorkflowStatus` at `995f5e45caf269ca71ffd7235b4b1e520b9cc940` (S2b1; PR #354 reviewed and green).
- PR: [Core #355](https://github.com/tj-agents/core/pull/355), draft with human-gate. Parent [Core #354](https://github.com/tj-agents/core/pull/354), [Core #353](https://github.com/tj-agents/core/pull/353), and [Core #352](https://github.com/tj-agents/core/pull/352) have completed source review and Windows/Linux CI. All retain `human-gate`; architecture merge authority is absent.
- Pickup: exact native identity and first read-only action recorded in the dispatched pickup file.

Native history, the supported store status command, registered branches/worktrees, current plans and
open Core PRs were reconciled before checkout creation. No existing owner of this follow-up was found.
The supported atomic claim registered this owner after checkout identity was verified. No open red
generated-sync PR was present. Other open PRs retain their owners.

## Acceptance

1. Public skills have distinct subjects and current callers use their final qualified names. Removed
   names, aliases and forwarding wrappers are absent from authored active callers and native discovery.
2. Package selection and activation form an acyclic graph. Both generic and engineering work have an
   explicit minimum selection. Moving policy from Base does not silently remove required tracking.
3. There is one lifecycle owner. Continuation governs execution; a plan supplies steps when present.
   Planning-only and review-only requests grant no execution, repair or publication authority.
4. `engineering:review` remains the code reviewer. A new `workflow:review` exists only if source evidence
   establishes a distinct current subject not already owned by readiness and completion checks.
5. SQLite identities, ownership, references, requests and receipts survive unchanged. No database
   recreation or schema migration is justified by namespace changes. Live and ambiguous owners cannot
   be stolen; persisted state is distinguished from native process observation.
6. Canonical sources, both host adapters, package maps/manifests/catalogs, routes and tests agree.
   Generated distribution is refreshed for validation and stays outside source PR commits.
7. Focused Windows and Linux verification and independent exact-head review pass. Supported installed
   entry points and affected already-bound readers have explicit acceptance evidence, or a named resolver
   and observable remaining gate. Source tests never substitute for installed activation.

## Evidence and design assessment

The solution assessment is complete: extract Core's existing implementation. Namespace-only forwarding
would leave the mixed ownership unchanged; retaining the current split leaves its demonstrated coupling;
a new framework or registry service adds migration and scheduling machinery without a current need.
The primary checkout's stale source is not an implementation base. Reopen this assessment only for an
explicit user request; readiness checks below qualify individual implementation slices.

- `.agents/machine/scripts/session_store.py` owns schema 4 and atomic ownership writes. Its
  `live_owners` query means unended records, not observed process liveness.
- `.agents/machine/scripts/work_item_sessions.py` mixes store operations with native session discovery,
  worktree checks, process liveness and resume launch. Those responsibilities must be separated.
- `.agents/workflows/workflow_runtime.py` has an independent read-only store consumer. Preserve its
  read-only behavior while reconciling the schema owner.
- `.agents/plugins/sources.json` explicitly packages shared resources. `PACKAGING.md` requires
  self-contained installed packages and forbids runtime paths into a sibling plugin or author checkout.
  Current shared source embedding already includes hooks, lane data and repository identity helpers.
- `engineering:plans`, `plan-authoring` and completion validation already own design readiness and
  goal acceptance. No distinct current reason for another public review skill has been established.
- Existing `engineering:persistent-workflow` is specifically remote delivery continuation. Its name is
  broader than its current behavior; generic execution must not depend on forge delivery.

Retaining SQLite and the native adapters preserves identities and existing atomicity without adding
another scheduler, database or service. Public primary sources inspected: SQLite's
isolation documentation (`https://www.sqlite.org/isolation.html`), OpenAI plugin packaging
(`https://developers.openai.com/plugins/build/plugins`) and Claude plugin manifest reference
(`https://code.claude.com/docs/en/plugins-reference`). These document transactions and package-local
resources; they do not establish installed behavior on this workstation or override Core's contracts.

## Standards and execution setup

Read Core README, AGENTS, CODE_CONVENTIONS, SOURCE_LAYOUT and PACKAGING before source changes.
Applicable process contracts already read: engineering session, lanes, skill-authoring, plan-authoring,
plan-execution, plans, plan-checkpoint, git-branching, open-worktree, and Base plan-artifacts/continuation.
Machine recover-agents and its work-item command contract govern ownership reconciliation. Python code
uses Core's repository conventions; a separate Python standards package is not selected here.

The checkout's `.agents/settings.json` enables auto-merge but contains no routine design opt-in.
Architecture authority comes from this explicit dispatch, not that setting. The selected project
packages are Base, Engineering, Machine and the explicitly adopted Personal profile. Do not infer
Personal adoption for any other repository. No remote record creation is permitted by this dispatch.

L1 judgment is appropriate for interacting lifecycle, packaging, identity, activation and persistence
boundaries. This session retains that decision. Bounded readers gather evidence; specified code will use
L4 workers or a documented supported fallback, with serialized disjoint ownership. Tests use disposable
state and deterministic dummy processes, never model sessions as fixtures.

## Boundary decision

The standing cross-repository decision is owned by
[Docs: Workflow and Agent Store boundaries](https://github.com/tj-agents/docs/blob/Docs/WorkflowAgentStoreBoundaries/WORKFLOW_AGENT_STORE.md).
It records capability ownership, the acyclic graph, public subjects, distinct profiles and separate source,
declaration and activation gates. This Core plan owns the implementation and delivery evidence below.

Implement one canonical Agent Store runtime with unchanged schema/identity/atomicity; embed it locally in
consuming packages. Move the existing lifecycle into Workflow, wire Base entry context on both hosts,
and retain Engineering's bounded technical operations and Machine's native operations. There is no new
workflow:review, scheduler, store migration, compatibility alias or age-based ownership takeover.

## Delivery slices and consumption contracts

### S1: canonical store package and shared readers

PR #352 at `5e815d0658597f031c332e9d2a3e3bb35d886e8a` has completed full and incremental private
review and passing Windows/Linux CI (`39695061838`). It is ready with human-gate; merge authority is absent.
The canonical runtime, schema-4 unchanged writer/identity moves, read-only snapshot inspector, source/
packaged/staged loaders and package declarations are implemented. Their exact contract is in that PR's
source and tests. No old-path shim exists. Reader schema2/3 support remains its existing data contract.
Native installed acceptance remains S3. The frozen S1 checkout is preserved and no longer owns the goal.

The measured S1 atomic exception covered 763 runtime/test lines plus declarations and mechanical moves;
consumer paths and self-contained packages had to change together. No lifecycle work entered that slice.
Both reviews found no actionable defect. A two-line fixed tier inventory correction followed CI and passed
incremental review. Local process cleanup passed in candidate/base Temp exports and both CI platforms;
workspace-only timeouts were environment evidence, not a weakened runtime timeout. Disposable review
bundles were removed after successful private review receipts; proofs and logs remain in private state.

### S2a: Machine capability boundary

PR #353 at `7c77e7d5b1dc6c419b5096431018079e7c530026` is stacked on #352. Lane policy now belongs
to Machine; native launchers consume caller-prepared dispatches. Model selection, duplicate protection,
side-goal isolation and the unresolved repair outcome remain. Full and incremental review approved that
exact head; Windows/Linux/ci-required run `39698190685` passed. Its 17-file source delta is 60 added/64
removed lines plus the six-line concrete lane example. Review proof remains private, disposable bundles
were removed, and its checkout is a frozen snapshot. Merge authorization remains absent.

Dependent preparation uses recorded stack children because the dispatch requires concrete reviewed results
before the final merge/installation request. This Lifecycle checkout is the sole current goal owner under
the same supported Machine claim and native identity; earlier checkout copies remain frozen snapshots.

### S2b: Workflow owner and caller cutover

Depends on S1's supported store paths. Move and consolidate the generic lifecycle definitions, transfer
helper and entry routing, removing their superseded Base/Engineering names and wrappers. Preserve the
separately owned handoff repair by reading its actual merged result before moving that definition.
Retain discipline-specific Engineering review/delivery and Machine native adapters. Exact file mapping,
examples, external caller inventory and measured atomic scope must pass readiness before S2 writes.
If S1 cannot land because the user's merge gate remains, S2 must use a recorded parent/child stack;
the concrete reason is completion of authorized dependent implementation before requesting approval of
the whole reviewable result. Do not accumulate S2 in S1's diff.

S2 source evidence is now bounded. `plan-authoring` mixes generic readiness with Engineering design;
`plan-execution` mixes the whole-goal loop with software review/delivery. `resume-plan` and
`continue-roadmap` are published compatibility entries and must be retired into the appropriate new
operation. `list-work.py` currently imports the full Engineering workflow runtime for repository identity
and one read-only status call; its new Workflow owner must consume Agent Store directly instead.
`plans` and `plan-checkpoint` mix generic artifact/checkpoint fields with PR/review fields and need an
explicit extension boundary. `persistent-workflow` remains the Engineering remote-delivery adapter.

Base currently wires only tier-gate, agent-files and idea-initialization SessionStart delivery. Its
plan-artifacts and continuation context scripts are shipped but unwired, as are Engineering session
context and workflow_route. S2 must make entry routing real and correct the contradictory delivery prose;
it must not revive the retired procedural enforcement hooks. Machine's handoff skills and launch_claude
currently instruct callers to invoke Engineering handoff/plans/lanes; close also calls self-repair.
Replace preparation calls in native adapters with consumption of an already authorized prepared dispatch.

### S2b1: Workflow status and recording ownership

PR #354 at `995f5e45caf269ca71ffd7235b4b1e520b9cc940` is stacked on #353. It publishes the hookless
Workflow package, moves status and shared recording ownership, reads Agent Store directly and preserves
selected tracker read-only behavior. Its full review accepted one active dangling-link defect; the repair
also corrected four CI adoption expectations. Full plus incremental review and review-record completed;
Windows/Linux/ci-required run `39705151778` passed. The PR is ready with human-gate and an exact-head
binding, no native auto-merge and no merge authority. Lifecycle fast-forwarded to this exact parent.

The rename-aware source delta is 46 paths, 565 additions and 310 deletions. Twenty-two guidance edits
are mechanical href/caller changes; moved runtime and tests contain 221 changed lines. Its public identity,
resource embedding, permissions, manifests and callers form one coherent status cutover. It is separate
from the lifecycle consolidation below. The parent rejected the independent review's blanket-exception
proposal as unsupported hardening; raw evidence and synthesis remain in the private work order.

### S2b2: one generic lifecycle owner

This dependent slice follows the independent status package. The parent retains architecture and approval decisions; bounded implementation begins only after S2b1 returns its lease and is committed.

#### Public source mapping

- Engineering workflow/plan-authoring -> Workflow workflow/plan, name plan, kind workflow, domain process.
- Engineering workflow/plan-execution -> Workflow workflow/run, name run, kind workflow, domain process.
- Engineering workflow/resume-plan -> Workflow operation/resume, name resume, kind operation, domain process, a substantive reconstruction operation rather than compatibility wrapper.
- Engineering workflow/handoff (including transfer.py) -> Workflow workflow/handoff, same bare name/kind/process. Preserve dispatch-first repair #344. No second handoff-format skill.
- Base policy/plan-artifacts -> Workflow contract/plan-artifacts, kind contract/process, retaining templates/PLAN.md and scripts/host_coverage.py. Remove its unused session-context emitter. Consolidate generic checkpoint rules here.
- Retire Base goal-continuation and its unused emitter, Engineering continue-roadmap, plan-checkpoint and handoff-format folders and both host adapters. Fold their distinct responsibilities into the owners specified below; no forwarding instructions or aliases.
- Add Base policy/task-routing with thin adapters and one SessionStart context emitter. This is the universal dispatch guidance; Workflow remains hookless.
- Move host_coverage source mapping out of Base into Workflow's resources/plan-artifacts/host_coverage.py and keep Engineering workflows/host_coverage.py embedding the same new canonical source. In workflow_ops.host_coverage_module replace only source fallback path `.agents/base/policy/plan-artifacts/scripts/host_coverage.py` with `.agents/workflow/contract/plan-artifacts/scripts/host_coverage.py`; packaged runtime lookup stays unchanged.
- Update Workflow/Engineering/Base catalog memberships, sources/resources, harnesses, selection descriptions and both host adapters together. S2b1 already establishes package/dependencies. No new package, external profile edit or publisher rename here.

#### Canonical subjects and required content

Workflow plan selects substantive planning and implementation-ready design requests. It owns outcome, constraints, evidence, scope, acceptance, unresolved decisions/resolvers, reviewable dependency ordering and readiness. Read workflow:plan-artifacts, resolve exactly one existing owner before writing, and use the selected discipline's planning contract conditionally (engineering:plans for software). Do not require a roadmap/ledger/repository for standalone work. Planning-only work ends at its authorized artifact outcome, not execution; discipline-specific delivery authority still applies when selected. Preserve explicit publication/installation limits. A ready verdict permits the already-authorized next action; it supplies no authority itself. Consolidate the current authoring readiness fields, mechanism/code/example requirement under the discipline extension, bounded independent evidence reader and parent decision. A successor must not decide unresolved architecture that the current owner claims is implementation-ready. The separate explicit unresolved-architecture handoff remains valid and goes immediately through handoff without a readiness receipt.

Fold continue-roadmap's chooser into plan when the request asks what to plan next: selected profile list/read, reconcile live owners/dependencies, report existing work, present implementable choices with recommendation and obtain a missing product choice. Do not infer priority from list order or turn a status/planning request into implementation. engineering:update-roadmap retains software roadmap fact reconciliation. After selection, complete authorized planning rather than stopping at selection.

Workflow run selects substantive authorized sustained/multiphase work, with or without an existing plan. It owns the whole goal through actual acceptance and authorized delivery, reconciling user scope versus agent-authored slice limits. It reads one existing canonical goal, uses plan-artifacts for recovery, retains one next action, continues independent authorized work across local commits/PR boundaries, and stops only at an evidenced external/human/destructive/ownership gate after all independent work is exhausted. Read machine:lanes for bounded phase capability; parent retains design/acceptance/diagnosis/severity. Delegate specified implementation or independent evidence under exact disjoint leases; reconcile Git before reusing failed/cancelled leases. No model names in policy. Direct short requests remain their selected operation without a ceremonial plan.

For repository ownership, invoke machine:recover-agents and its published work-item-sessions.md command contract via native discovery. Reconcile stored execution/owner with actual native observation. Claim the same execution only after verifying the exact native identity and permitted predecessor; no age-based takeover. For standalone non-Git work, keep its existing task goal and do not invent a Git provider, SQLite identity or repository. Do not duplicate Machine path resolution or embed the Machine runtime in Workflow just to issue commands.

For software, load engineering:plans for technical delivery slicing and select engineering:feature or engineering:bugfix for a bounded technical operation. They own implementation, tests, code review and delivery inside the passed slice. Return evidence to the same whole-goal run owner and continue. Source review remains engineering:review; no workflow:review. Selected nonengineering domains use their own available operation. Missing discipline capability is a concrete dependency gate, while independent authorized work continues.

Move Base continuation's authority/completion/one-writer obligations into run. Select only an actually supported host continuation. Do not claim unattended execution before owner, foreground lease and wake are initialized and observed. Engineering:persistent-workflow is only the software remote-delivery adapter; do not require it for generic goals. Foreground execution remains valid when unattended capability is absent. Persist exact blocker/resolver/unblock/resume condition only after exhausting independent authorized work. No new unattended service or host-enforcement hook.

Workflow resume selects reconstruction of named work after interruption, relocation or loss of owner context. Resolve exact goal/ledger/worktree/native identity from the supplied pointer, Git/provider evidence and Machine recovery inventory. Read-only stored rows are not live-process proof. Refuse ambiguous or observed-live takeover and reuse the existing owner. Reconstruct missing recovery facts from evidence and preserve partial writes. A verified compact continuation with goal/absolute checkout/branch/state/next-action needs Git confirmation, not full corpus rereads; contradictions trigger targeted reconstruction. After reconstruction, preserve authority: planning-only -> workflow:plan; already-authorized execution -> workflow:run. Resolve a missing product choice rather than guessing among goals. Do not create a second executor or goal.

Workflow plan-artifacts owns one canonical Markdown artifact, absolute path response link, placement/promotion from host scratch, material progress, authority fields, one next action, host coverage, checkpoint timing and generic transfer criteria. Preserve the existing no-ceremonial-plan behavior. Consolidate only generic plan-checkpoint behavior: material milestones, changed blocker/owner, completed important review, terminal transition or unsafe context ending; repeated polls/ordinary commits are not checkpoints. Keep partial work, valid verification, open decisions, scope/current slice/remaining scope/done condition, and typed gate/transfer fields. Remove chronological detail that cannot change the next action. Detailed software ledger graph/template, 200line/16000byte ledger budget, PR/review watermark and commit/push mechanics belong only in engineering:plans. Artifacts supplies no duplicate execution loop and no SessionStart claim; task-routing owns actual context delivery. Preserve host_coverage.py semantics/data shape and template link.

Transfer criteria move from Engineering plans into the common artifact owner: explicit user request, actual owner/workstream change or independent context requirement, materially separate next work, substantial critical design with ready phased execution, or evidenced context degradation. Phase/commit/transcript age alone is not a transfer. Small/medium tasks continue in current parent; no new independent successor for this architecture. Engineering plans references the common criteria and retains only technical extensions.

Workflow handoff retains the existing source behavior, including immediate unresolved architecture dispatch after identity/authority/capability checks from a verified existing checkout; successor owns design/isolation before writes. Preserve bounded side-workstream original goal/writer, launch submission != pickup, no duplicate launch after ambiguity, explicit host/model choice, and critical prepared receipt ack/first-action observation. Move transfer.py byte-for-byte unless it contains a public old-name reference (none found in the bounded source scan); its receipt fields, identity hashes, locks and literal `Execution authorization: implementation` stay unchanged. Do not make prepared-critical receipt mandatory for unresolved architecture dispatch.

Fold handoff-format's pointer rules into this same handoff skill. Plan/ledger pointers use absolute owning paths, optional why line and opener; instructions stay in canonical goal. Non-plan dispatches include objective/context/constraints/authority/known questions and next responsibility. Existing selected-record repair instruction (address-bug/mistake/debt) moves to Engineering plans/addressing policy, which handoff consults only when that discipline is selected. Generic handoff must not require engineering:git-branching/open-worktree/review/merge; those apply conditionally to software transfers. Generic source references recorded selected profile through Workflow's recording document. Move the transferred cleanup-obligation subsection to engineering:merging and reference it conditionally from handoff, since its subject is that skill's owned finish obligation.

#### Base routing text and emitter

New policy front matter name task-routing, kind policy, domain behavior. Description: "Choose the selected task operation while preserving authority and the existing goal. Use when receiving a substantive planning, execution, status, recovery or transfer request."

Body must express this exact routing contract concisely:
1. Planning/design-only -> workflow:plan; no implementation authority.
2. Authorized sustained/multiphase work -> workflow:run, with or without a named plan; retain the goal across commits, phases and context changes.
3. Explicit reconstruction/resumption after interruption -> workflow:resume; ordinary ongoing execution stays with run.
4. Open-work/progress queries -> workflow:status; explicit handoff -> workflow:handoff. Prompt-only asks do not launch a process.
5. Quick answers and one-step tasks use the appropriate selected operation directly. Software implementation/diagnosis/review/delivery remains Engineering when selected; generic workflow review is not added.
6. Resolve and load the qualified advertised skill. If required Workflow is unavailable, report the concrete missing capability/selection and keep the existing goal; continue independent authorized work. Do not silently fall back to retired Engineering lifecycle names, invent installed capability, auto-install or claim that a package selection proves activation.
7. Context only, no enforcement/scheduler/authority. Include a concrete fenced example distinguishing "plan the migration" from "implement the migration through completion" without model names.

Create scripts/session-context.py from idea-initialization's existing emitter with IDENTITY='base:task-routing', matching diagnostic label, and the same file-relative SKILL.md validation, SHA256 marker, --instruction-fragment and SessionStart JSON. Do not add comments/docstrings merely to narrate the rename. Wire one additional --hook ${PLUGIN_ROOT}/.agents/base/policy/task-routing/scripts/session-context.py into both Base SessionStart manifests (both Codex platform commands; Claude's existing portable dispatcher form). Update Base harness source roots/required hook permissions as its actual schema requires. No PromptSubmit, PreToolUse or Stop enforcement wiring is added.

#### Retire obsolete routing, preserve receipts

The only production importer of workflow_route.py is continuation_stop.py, for direct_control/read_receipt. Both old route and stop are packaged but unwired. Keep unrelated Stop ownership/binding/scheduler/supervisor checks unchanged.

New `.agents/hooks/continuation_receipts.py` retains `from __future__ import annotations` for Python3.9 and the exact existing imports hashlib/json/Path/re/tempfile, RECEIPTS='agents-workflow-route', DIRECT_CONTROL regex, and only direct_control, receipt_path and read_receipt copied unchanged from workflow_route. This keeps existing stored receipt paths/keys and direct-control parsing. Change continuation_stop's import to this module. Replace the Engineering resource map workflow_route.py -> continuation_receipts.py. Remove workflow_route.py and its now-obsolete routing/recovery/receipt-writer tests. No production caller writes those receipts once the already-unwired router is retired; no new writer is invented. Active continuation ownership remains in its unchanged runtime, and existing receipts remain readable.

Keep meaningful continuation tests for read-only receipt parsing, malformed/missing JSON, direct pause/cancel/stop versus quoted text, exact-worktree isolation, execution_suspended, execution_obligation and freshness comparisons, and source/generated Stop loading. Replace old router-created test setup with direct literal receipt fixtures; do not test new fake classification/writer logic. Remove tests whose subject is retired intent routing or receipt-writing, rather than pretending fixture construction verifies them. Update torn-install import failure case in test_hook_dispatch to require continuation_receipts. Existing Stop owner tests remain intact.

#### Active callers, durable IDs and Engineering extension

Apply public-name mapping only to current callers/adapters/catalogs/examples/test expectations: engineering:plan-authoring -> workflow:plan; engineering:plan-execution -> workflow:run; engineering:resume-plan -> workflow:resume; engineering:continue-roadmap -> workflow:plan chooser; engineering:handoff -> workflow:handoff; engineering:handoff-format -> workflow:handoff pointer section; base:plan-artifacts / engineering:plan-checkpoint -> workflow:plan-artifacts (technical ledger-specific references -> engineering:plans); base:goal-continuation -> workflow:run.

Engineering feature/bugfix must explicitly accept a bounded technical slice from the Workflow owner, perform it and return evidence without redirecting back to run or claiming the whole goal. Their direct short-task behavior remains. Promotion of a larger direct task goes through workflow:plan under existing execution authority then workflow:run. Preserve their existing review/repair/delivery gates. Remove their mandatory whole-goal `skills --lifecycle` instruction for a delegated operation; resolve technical rules via selected native discovery. If a repository actually uses workflow_ops skills, specify its existing accepted repo-relative `name=path` interface; do not invent automatic namespace resolution, absolute installed paths, or a new compatibility wrapper. Generic Workflow never requires the full Engineering runtime.

Profile adapters may supply an existing address-bug, address-mistake or address-debt operation to run. Address-bug/mistake re-enter workflow:run for an existing goal only when not already executing under that goal owner; a delegated technical slice keeps that owner and selects its appropriate bugfix/failing-tests/feature operation, then returns verification and record evidence. Address-debt preserves an assigned slice/checkout instead of unconditionally starting another. Standalone addressing keeps its existing provider and software-delivery obligations. This prevents Run -> address-* -> Run recursion without introducing a second lifecycle or changing persisted kinds.

Engineering plans becomes the software planning extension. Preserve roadmap/plan/ledger file graph and stable keys, technical implementation examples/standards, green consumption contracts, PR slicing/stacks, profile-specific conditional gates, compact ledger template/budget and validation, review watermark, substantive commit/push/remote evidence policy, software delivery/closeout and rename grep. Refer to common artifact owner for generic placement/authority/checkpoint timing/context transfer; do not duplicate whole-goal execution or readiness. Move software-specific checkpoint and recorded-repair transfer fields here. Retain every typed dependency gate/return path needed by software delivery.

Remove resume-plan and continue-roadmap entries from contract/v2/compatibility.json and their support-matrix rows/release-window prose; user clean replacement supersedes that compatibility window. Keep staged-review-all retained driver. Do not change contract version or its semantic stages. V2 workflow_id, persisted state IDs, roadmap item keys, continuation owner_id/nonce and historical review/dispatch identifiers remain byte-stable. They are not public skill discovery names.

New active delivery handoff next_stage values must use qualified current names (workflow:run when returning to generic execution; engineering:incremental-review for that actual software operation). Existing workflow_id bytes stay unchanged. Do not mutate persisted binding files in this source change or add an old-name resolver alias. S3 reconciles affected already-bound readers/owners before activation. Core worktree binding inventory on22Oct found only Feature/CrashRecovery carrying next_stage incremental-review (not a retired lifecycle name); no current old lifecycle next_stage binding was found. This is bounded inventory, not global native acceptance.

#### Tests, historical allowlist and scope

Update actual behavior fixtures, not only sentence assertions: plan_workflow_scenarios/harness, plan_authoring_harness and task_workflow scenarios for new public entry/owner values; remove compatibility scenario while preserving persisted workflow_id and stage IDs that are data contracts. Update authored_skill fixture to search Workflow, package coverage tests to use the owning package, host coverage source/mapping fixtures, CI transfer helper path, engine hook delivery tests and Base context tests. Remove obsolete route tests; add actual Source/Claude/Codex SessionStart payload and missing-contract behavior tests using deterministic subprocesses. Keep transfer receipt tests against moved exact helper, including dispatch-first no-ready-receipt path through guidance fixtures. Verify generic Workflow package has no Engineering dependency/runtime and both hosts resolve all new names.

Retired active names/paths must have zero hits after an explicit survivor allowlist: completed historical plans/observed acceptance records, this goal's migration mapping, and opaque stored v2 workflow/stage identifiers. .agents/plugins/runtime-assertion-ownership.json verified_acceptance is historical observed native behavior; do not rename it into a false observation. Do not edit the old completed routing/store migration goal. No automatic rewrite of every plan or every registry row.

Run focused lifecycle/transfer/continuation/context/host-coverage/package/selection tests, generation/digest/harness/tier checks, exact guidance-example validator and instruction-file pairing. Add concrete fenced examples to newly moved/changed guidance. Check catalog common generated fingerprints separately and exclude generated plugins output from commits. Windows/Linux exact-head CI and frozen native+targeted independent review follow. Installation is S3, never inferred from source tests.

Expected scope includes substantial deletion/consolidation of old guidance and ~950 obsolete unwired router/test lines. Separate mechanical caller/path updates from substantive policy/runtime lines. At >1000 substantive lines or40 substantive paths explicitly assess atomicity: public entry names, contextual routing, artifact owner, package resources and caller fixtures must switch together with no temporary aliases. The independently usable status package was already split out; do not grow S2b1. Parent must record measured assessment before review. No other unrelated cleanup.

Readiness: bounded independent reader /root/s1_readiness completed the exact source-contract check against 7c77e7d5. Its sole concrete correction, retaining future annotations in the receipt reader for Python 3.9, is included above. Parent verdict: ready for the specified implementation after the actual completed S2b1 parent is reconciled. The child was created at c7bf94d8 and subsequently fast-forwarded to completed parent995f5e45 before candidate staging. Isolation permits dependent preparation while architecture merges are held; all older snapshots and unrelated checkouts remain untouched. Native activation remains S3.

### S3: coordinated selection and native acceptance

Core publishes both namespaces. Personal at `09ab438d644552831f9fb9f49162c02798a6a838`
and Infonetica at `59644f172c08e2f1afb49138db0db7d6907d1069` have no authored retired
lifecycle/lane calls; their selected GitHub/Azure record operations remain distinct. Personal's actual
producer requires Engineering and Machine; Infonetica requires Work, Base and Engineering. Retired-name inventory found no old public names in either profile, but a subsequent semantic read found stale whole-goal ownership in both address-work-item skills. A bounded S3 correction must enter workflow:run with the existing canonical item identity and mapped Engineering operation; Workflow owns the goal while Engineering returns software evidence. Preserve native kind mappings, provider read/update/closure helpers and company delivery gates. Personal README must name this boundary; deterministic tracker code stays unchanged. Their own source-project declarations still need coordinated required closure: exact fetched Personal origin/main selects Base, Engineering, GitHub Actions, Machine, Personal, Python and Template, so expansion adds Agent Store and Workflow; exact fetched Infonetica origin/main selects only Base and Machine, so expansion adds Agent Store only. Producer dependencies do not establish profile adoption. Prepare only these required additions through the candidate generator in separate isolated S3 source layers, with native review admission/activation explicitly gated.

Marketplace's exact source base is `063a604c86051388cc3889eefe8734a22f19010d`. Its old
CoreCatalogAdoption goal explicitly records delivery on 8 October 2026 (PR #4); supported native recovery
found its Claude owner closed and a current supported worktree find returned no matching owner. The old
checkout and goal remain untouched. The absent older parent identity is not itself liveness proof.
Open Marketplace #20 touches only record-selection files, not the catalog. The new branch/check-out names
below were absent and the primary checkout's unrelated untracked files are preserved.

The bounded catalog slice uses new branch `Feature/WorkflowAgentStoreCatalog` in
`C:/Users/TommySeery/source/repos/tj-agents/marketplace/.worktrees/Feature-WorkflowAgentStoreCatalog`.
This Core GOAL remains the only whole-goal owner; the catalog slice creates no competing lifecycle goal.
AGENTS and README were read. `catalog.json` is the only authored roster; unlike Core distribution output,
both generated native marketplace JSON files belong in this repository's source PR.

Exact changes: order Core entries Base, Agent Store, Machine, Workflow, Engineering. Agent Store has no
requirements; Machine requires Base and Agent Store; Workflow requires Base, Agent Store and Machine;
Engineering requires Base, Workflow, Agent Store and Machine. Keep repository `core` and current-main
producer references. Reconcile the demonstrated stale profile edges: Personal requires Engineering and
Machine; Infonetica requires Work, Base and Engineering. Keep all other entries unchanged. Update only
affected README roster/minimum-selection prose: generic sustained work selects Workflow and its closure,
software work selects Engineering and its closure, profile adoption remains explicit. Native discovery
still installs/selects nothing automatically. No aliases, account changes or profile adoption are added.

The catalog slice is committed and pushed as `4aeaa7d82cfa299aa9fad51ec1ec63727623ba8a`, [Marketplace #21](https://github.com/tj-agents/marketplace/pull/21), draft with human-gate. The five-file source delta is 75 added/22 removed lines. Generator/drift checks, all 14 existing tests and the native Claude validator passed. Full frozen review completed with M1 changes requested; native catalog CI passed on Windows and Linux. M1 remediation and its fresh review remain pending. The body check passed and binding records absent merge authority.

The workstation PowerShell claude function unexpectedly ran its prelaunch refresh before validation. Parent identified that helper, verified it had ended, and removed exactly its four new project-scoped registrations using native uninstall with keep-data. Other registration rows and all native user sessions were preserved; checkout settings were restored with exact semantic/hash guards. Direct native validation then passed without settings changes. Use the native executable for deterministic validation here; do not rerun the refresh wrapper. This event supplies no new-namespace activation evidence.

A completed Marketplace source review records M1 (P2): its own explicit selection must acquire the new required closure. Candidate Machine adopt_plugins.py, with --root and --mode preview/write/check and no requested plugin/profile, preserves the existing selection and expands its required dependencies. Read-only previews passed for Core and Marketplace with exactly .agents/plugins.json, .claude/settings.json and .codex/config.toml changing; no installed payload or native installation is involved. Use the canonical candidate script because generated Machine output is intentionally stale until refreshed. Marketplace repaired these three files in #21 at7cf51be5c4ee8850a31dca560cc2fa941c2391c5; source generator write/check passed and native catalog Windows/Linux CI39703431016 passed. The fresh pass is frozen but incomplete because actual native standards admission reports Agent Store and Workflow unavailable; Core prepares its own same three declarations in a final S3 activation-declaration layer after the lifecycle source. This separates review of publishable source under the existing admitted selection from the later native-admission gate; it does not waive that gate. This preserves existing Personal adoption, not a new scope decision. The actual required closure is Agent Store, Base, Engineering, Machine, Personal and Workflow. Later launch refresh reads current enabled identities and does not expand the declaration, so this source correction cannot be replaced by a claim about eventual refresh. Native activation remains separate. Review of the newly declared packages must account explicitly for candidate-source contracts and currently absent installed namespaces before claiming scope resolved.

Marketplace native catalog CI passed on Windows and Linux. Separate policy jobs demand removal of the unchanged .github/workflows/check-personal-policy.yml. Exact baseline proof is complete: immutable Personal 09ab438d helper and policy return exit 1 with the same remove-workflow message on Marketplace base 063a604c and candidate 4aeaa7d8. All four policy inputs were identical. Evidence is in Temp/tj-personal-policy-base-proof-20261022-yt5_33c9/evidence.json (sha256 521a74fec708078797cfb10217c6d07f441b336a450e285383a7b00936802746). This is independent existing policy drift; the dispatch excludes unrelated workflow deletion. Preserve that workflow unless its authorized owner or Tommy supplies the missing scope authority.

The two known profile source repositories also receive bounded declaration-only S3 layers. Fetched
Personal origin/main remains09ab438d; AGENTS/README identify explicit Personal scope. Its open#14
changes the adoption utility, not these project declarations. Use Fix/WorkflowSelectionClosure at
personal/.worktrees/Fix-WorkflowSelectionClosure. Fetched Infonetica origin/main remains59644f1; its
AGENTS/README explicitly prohibit Personal adoption. Its open#15 changes design-doc only. Use
Fix/AgentStoreSelectionClosure at infonetica.worktrees/Fix-AgentStoreSelectionClosure, outside its
unignored .worktrees folder. Both branch/path names were absent and primary dirty files are preserved.
The first bounded writer lease completed and released both declaration diffs. Parent committed Personal6c4962796a59a40c182e39e9694157ba17dadde2 (12 additions,2 removals) and Infonetica2d622c177d5ef4522e599e1cac1af42cf980a2d8 (5 additions). Generator write/check and pairing passed for both; Personal generated109 files with no drift, Infonetica48 tests passed (one skip) and payload shape passed. That lease owned only .agents/plugins.json,.claude/settings.json and
.codex/config.toml, generated from existing selection with no requested profile. A new separate specified writer lease now updates only each address-work-item guidance and Personal README,
plus the Personal generator projections required by that repository. No deterministic tracker code changes. They create no
independent goal, runtime claim or tracker operation. All native packages unavailable to the host remain
an explicit review-admission/activation gate. Hold each draft with human-gate and absent merge authority.

Publication order is Core source stack, successful generated-package publication, then the coordinated
marketplace roster. Hold breaking publication until the known callers and selection are ready together.
Use supported native installation/update paths only when authorized. Preserve running snapshots and
reconcile affected already-bound readers separately from fresh activation. Source generation and CI are
not installed acceptance. Windows native acceptance needs fresh selected Workflow/Engineering entry
points; Linux installed-host acceptance needs an actual supported Linux host. Resolve these named gates
after all independent implementation/review/PR preparation is complete.

## Execution readiness

Verdict: S1, S2a and S2b1 are source-reviewed and green. S2b2 implementation is complete; pre-freeze
preservation inspection restored the executable handoff/readiness/artifact contracts. The bounded test-only
correction restored checks for unchanged behavior; focused qualification passes and this commit is the frozen-review candidate.
Execution authorization: architecture and implementation through coherent reviewed PR preparation.
Transfer: none; retain this owner under the explicit dispatch.
Unresolved: Lifecycle review/CI, the shared standing decision, Core declaration closure, native admission,
coordinated publication and installation. The six-consumer publication rejection has its own explicit gate.
Resolver: current owner for independent preparation; Tommy for reserved merge, activation and rejected
consumer-publication approval after the concrete candidates are ready.

## Verification

Checkout is isolated and initially clean at the recorded base. Live store status found no prior item;
the subsequent supported claim succeeded for this exact session. S1 independent readiness passed. Source generation and its drift check, catalog digest and harness
checks, tier payload checks, instruction-file pairing, 16 adoption tests, 20 harness tests (3 native-tool
skips), 25 source-layout cases (the two initially failing cases passed on targeted rerun), and 12 Codex
snapshot tests (4 platform/native skips) have passed. PowerShell 7 is unavailable; the PowerShell wrapper
was replaced by its exact underlying Python generator command, while PowerShell-only checks remain CI
evidence. Runtime regression qualification passed; frozen-head review and exact-head CI remain pending. Installed acceptance
has not run and is not implied by these source checks.
The goal's host-coverage validation passes. Whole-repository plan validation reports six existing errors
in `plans/machine-events/MACHINE_EVENTS_PROGRESS.md` and
`plans/repo-declared-config/REPO_DECLARED_CONFIG_PROGRESS.md`; both files match the recorded base exactly.
Those separate owners resolve their headers/next-step fields. This goal adds no error to that baseline;
retain the known limitation rather than reporting the entire plan graph green.

## Reviews

Independent S1 readiness review by bounded reader `/root/s1_readiness` passed against base
`112df9f5f9714acf443c84fe911cc081f9772dc5` and this revised design. Findings on inspection semantics,
detached staging, sweep lookup and package closure were resolved before code work. Runtime tests,
independent frozen-head implementation review and installed activation remain separate gates.

## Lifecycle preservation checkpoint

The first candidate condensed moved guidance too far. Parent inspection and two read-only source audits
identified missing executable receipt steps, host-coverage schema, readiness fields and conditional
Engineering checkpoint/runtime/completion duties. Those are restored in their single new owners. The
transfer helper bytes and three extracted continuation receipt functions remain unchanged. The unresolved
architecture dispatch-first exception from #344 remains explicit, including non-repository task directories.

The first test rewrite also removed assertions for unchanged review/delivery behavior. The released
correction lease restored those cases and meaningful runtime assertions. A preserved test exposed the
missing transferred-cleanup contract; it now lives in Engineering merging, and Workflow handoff routes to
it. This retains release-marker, exact native identity, predecessor exclusion and residual-path rules.
The baseline's historical native acceptance document remains byte-identical; observed old names are not
rewritten into false new observations. Parent owns final source, catalog, goal and review.

Package generation/check (598 files,80 definitions), catalog digests, harnesses (5), tier payloads, source
layout (25), routing (4), host coverage (9), process standards (20), continuation (29), and guidance examples
(19 paths) pass. Both isolated Workflow host entry points execute transfer help and validate the shipped
coverage record; transfer helper hash remains2f9785d3b5a27c5e130d413cc743ce919f59efe9f1a110b394deb49f105a2256.
Handoff10 cases passed, and its sole Git rev-parse timeout case passed on a focused rerun without changing
runtime timeouts. Documentation reachability passes after correcting two moved source links. All18 final plan workflow cases pass. Frozen review and exact-head Windows/Linux CI follow. Generated output is restored
and excluded from the candidate.

### Measured Lifecycle scope and atomicity

The source delta contains105 paths before the goal checkpoint,1200 additions and3126 deletions. This
exceeds the review warning budget; the following counts retain deletion and test costs explicitly.

| Area | Paths | Changed lines |
| --- | ---: | ---: |
| authored behavior guidance | 28 | +544/-1120 |
| runtime and helper moves | 7 | +40/-48 |
| catalog manifests resources docs | 16 | +79/-76 |
| tests and fixtures | 24 | +437/-752 |
| retired router and test | 2 | +0/-952 |
| host adapters | 28 | +100/-178 |

The public lifecycle entries, bounded Engineering callers, universal routing, artifact owner, package
resources and both-host discovery must switch together without temporary aliases or a second executor.
Status was split into its independently usable preceding layer. Splitting routing first would advertise
unshipped operations; splitting the artifact/entry owners would require intermediate cross-owner callers
and another fixture transition. Pre-retiring the already-unwired router is technically possible but would
require a separate temporary rewrite of the same routing/recovery fixtures. Keep that pure retirement with
this owner/caller cutover; its952 deleted lines are shown separately, not hidden as mechanical renames.
Keep the remaining cutover atomic, freeze its scope, and require independent contract-preservation,
deleted-test/receipt-boundary review plus native review and Windows/Linux CI. No S3 declarations, profile
changes, publisher or unrelated cleanup enters this layer.

## Lifecycle CI correction - 22 October 2026

Core PR355 is a pushed draft at the initial candidate c1f0a8f5. CI39755570544 ran1232 source/package
cases on both platforms and found the same two startup-context expectation failures. The parent run
39705151778 actually executed and passed that step on Windows and Linux. The new routing emitter is
intentional; its missing expected hook entry is the regression. Restore that entry while retaining the
full command, context aggregation and timeout assertions. Both focused startup tests pass against regenerated packages in5.007 seconds. No timeout or runtime
behavior changes.
The generated-path guard also caught four catalog digests accidentally committed with authored catalog
changes. Restore only those digest values to the immediate parent; post-merge generation owns them.
The unstarted c1f0a8f5 review preparation is superseded without approval. Freeze the corrected full source
candidate after focused tests pass. Review, exact-head CI, merge and activation remain separate gates.

## Coordinated source preparation - 22 October 2026

Personal's isolated Fix/WorkflowSelectionClosure at0af44a12 contains only the dependency closure and
profile address guidance (10 paths,47 additions/32 removals including required generated mirrors and one expected-reference correction).
Infonetica's isolated Fix/AgentStoreSelectionClosure ate76d8d66 contains only its Agent Store dependency
and Azure address guidance (4 paths,10 additions/3 removals). These are assessed new delivery slices;
Personal PR17 and Infonetica PR18 are pushed drafts with human-gate, passing authoritative body checks and exact-head delivery bindings. Existing Personal3/4/14 and Infonetica15 retain their separate owners. Newly
observed Personal16 changes tracking policy and another README section; it does not own this caller cutover.
Both candidates are committed, declarations and focused local tests pass, and exact guidance examples pass.
Infonetica docs reachability passes. Personal's four reported adoption links are in byte-identical base
files, outside this delta. Native selected-standard admission explicitly fails for Agent Store/Workflow
(Personal) and Agent Store (Infonetica); frozen work orders remain pending and source host coverage passes.
Personal CI caught the static external-reference fixture missing workflow:run; the one-line correction passed all five packaging tests and generation/check. Windows/Linux/hosts CI39708517394 is green at0af44a12. Infonetica hosted CI remains manual and was not triggered. Do not substitute candidate discovery for installed admission.

The bounded prior-completion inventory identifies six actual consumers: tomjseery/cpp,
marketplace-car-hunter, onsite-sealants, Reunion, termboard and tj-agents/docs. Their current supported
selections contain Engineering and therefore require Agent Store and Workflow. Preserve Car Hunter's
python@python-agents identity. Work source also needs both additions without Personal. The retired
WorkItems primary's supported local checkpoint422ef8b needs closure too; preserve its historical source,
completed plan and originating checkout, and never start from stale remote WorkItems producer selection.
Onsite2 and Docs6 are old adoption PRs that would restore retired WorkItems selections; leave them untouched.
Prepare bounded declaration-only candidates against supported current sources, with separate human gates.
This is the recorded caller set, not a new repository scan or bulk plan conversion.

The following declaration-only branches are assessed new slices, each with exactly the three generated
project declaration files, a clean isolated checkout, and passing preview/write/check, semantic settings
preservation, pairing and whitespace checks. Existing old Onsite2/Docs6 do not own this new graph closure.
Native admission and final review remain held until the new packages are available. Automatic approval review rejected the combined six-repository publication action because it requires explicit user approval for those repositories; no pushes, PRs or labels were created. Preserve the local commits and request that publication approval only after unaffected preparation is complete. Each eventual PR must remain a draft with human-gate. No application stack source or tracker action is included.

| Repository | Branch / base | Candidate |
| --- | --- | --- |
| tomjseery/cpp | Fix/WorkflowSelectionClosure / b949bc15 | b5684fafdf19a912c101f6f49ebe4330fcacba36 |
| tomjseery/marketplace-car-hunter | Fix/WorkflowSelectionClosure / d2633357 | 8da517de889735f64d30fcf2989630f0553bde00 |
| tomjseery/onsite-sealants | Fix/WorkflowSelectionClosure / 9117f720 | b8668391d7f1f5130f6cd8a19f727766aa4c7081 |
| tomjseery/Reunion | Fix/WorkflowSelectionClosure / master e058dc8a | 6a48c286cf0e6aef59fe282ab7a0ff41e7a56681 |
| tomjseery/termboard | Fix/WorkflowSelectionClosure / 8a8914d0 | 647893b3b1b67655657519c0383884b5fe9a52c9 |
| tj-agents/work | Fix/WorkflowSelectionClosure / 3a92fc11 | 0e003fd73d5de00e3f2dfcc0ea9e83745a1ee50a |

Retired WorkItems has a local-only candidate1bb5debdea0522052e3d8740889041e295742036 at
work-items.worktrees/Fix-WorkflowSelectionClosure, based on the supported422ef8bb checkpoint. Its three
configuration paths, generation/check and semantic preservation pass; Kit and Template identities remain.
Do not push this retired producer: comparison with remote main contains unrelated historical source
changes. Its primary, old goal and protected originating checkout remain unchanged. Apply only its prepared
local configuration through the coordinated authorized activation step.

Docs has the standing shared decision in isolated Docs/WorkflowAgentStoreBoundaries from1b1bb3c9.
Only WORKFLOW_AGENT_STORE.md and its README pointer are authored. The parent corrected the S2a source
reference to7c77e7d5. Its publication records architecture, not shipped or installed behavior; Core keeps
this sole implementation goal. Pin lifecycle evidence and link the shared decision after the source commit.

## Next Steps

Finish the focused CI correction and freeze the corrected Lifecycle candidate for independent
review and exact-head CI. Then pin and publish the shared standing decision and prepare Core's three
project declarations. Preserve the six checked consumer commits without retrying their denied publication.
Complete every independent source/review action before presenting the concrete publication/activation gates.

Scope: whole plan through all remaining phases and terminal delivery within the dispatched authority.
Current slice: S2b2 lifecycle preservation, verification and review preparation.
Remaining scope: lifecycle review/CI, standing shared decision, Core and Docs project declarations,
held native-admission reviews, and explicit publication/installation gates.
Done when: the namespace cutover satisfies acceptance, or only evidenced external gates remain after
every independent authorized action is complete.

```agent-host-coverage
{"schema_version":1,"shared_source":".agents/agent-store/runtime/","hosts":[{"host":"claude","behavior":"Use the canonical registry through package-local native adapters and expose read-only inspection without process-liveness claims.","source":".agents/plugins/manifests/claude/machine-hooks.json","mapping":"sources.json embeds the canonical store runtime in the consuming Machine and Engineering packages and publishes Agent Store inspection.","verification":{"level":"source","result":"passed","evidence":"Inspection 5, registration 21, recovery 48, close-loader 9, session commands 64, store 59, status-reader 51, repository provider 22; generated package checks and both isolated host inspector entry points pass. Installed activation remains an S3 gate."}},{"host":"codex","behavior":"Use the same registry and atomic ownership semantics through Codex lifecycle hooks, with separately labelled recorded-state inspection.","source":".agents/plugins/manifests/codex/machine-hooks.json","mapping":"The same canonical store bytes are embedded locally; Codex hooks retain package fingerprint and snapshot integrity.","verification":{"level":"source","result":"passed","evidence":"Inspection 5, registration 21, recovery 48, close-loader 9, session commands 64, store 59, status-reader 51, repository provider 22; generated package checks and both isolated host inspector entry points pass. Installed activation remains an S3 gate."}}]}
```
