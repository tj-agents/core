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
- Worktree: `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Refactor-WorkflowStatus`.
- Branch: `Refactor/WorkflowStatus`.
- Base/parent: `Refactor/MachineWorkflowBoundary` at `7c77e7d5b1dc6c419b5096431018079e7c530026` (PR #353).
- PR: not opened for S2b1. Parent [Core #353](https://github.com/tj-agents/core/pull/353) is reviewed, green and ready; [S1 #352](https://github.com/tj-agents/core/pull/352) is ready with review and Windows/Linux CI passed. Both retain `human-gate`.
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

Agent Store owns schema, migrations, transactions, identities/references and recorded state. Machine
owns observed native liveness, current-session attachment, launch, reopen and terminal operations.
Store metadata may capture repository identity and host/profile labels; it never starts a host or
claims that an unended row proves a live process. Its atomic claim keeps refusing an existing unended
owner without an explicit predecessor. This change does not add automatic stale-owner takeover.

One canonical runtime is authored at `.agents/agent-store/runtime/`. It is embedded unchanged at that
same package-relative path in each consuming payload. Each mapping has a single destination package;
Agent Store remains the source/API owner. Consumers load their own packaged bytes, never another
plugin cache. Package fingerprinting covers each embedded copy. This makes the existing resource-copy
mechanism explicit rather than adding a resolver service. Dependencies describe capability selection;
embedded code makes a selected package self-contained at runtime.

Workflow's public subjects are `plan`, `run`, `resume`, `status` and `handoff`. Its supporting plan and
continuation contracts have one owner beneath Workflow. Base supplies universal entry routing; Workflow
supplies the selected lifecycle. `run` works with or without a plan. It delegates discipline operations
when selected and keeps the whole goal's ownership. Engineering retains its code/design conventions,
review and guarded source delivery. Its existing remote-delivery continuation remains a delivery adapter,
not the generic task executor. Machine launcher guidance must accept a prepared authorized dispatch
without calling upward into Workflow to prepare it again.

No `workflow:review` is added: the examined readiness and completion gates already own the suggested
subjects. They remain explicit responsibilities of `plan`/`run`; `engineering:review` is the code review
operation whether invoked directly or by execution. Review-only authority still grants no repair.

Agent Store exposes `agent-store:inspect` for recorded execution/session/reference state. `inspect`
avoids a second bare `status` discovery entry and states what is being observed. Workflow status can
combine that recorded state with plans, selected tracker reads and explicit Machine observations.
A standalone Agent Store recovery skill is not justified by the current operations: there is no new
safe autonomous registry repair action. Workflow chooses the work/authorized transfer, Machine verifies
native recovery, and Agent Store applies its existing atomic updates. Do not add a facade that merely
calls the native recovery skill or a command that steals an owner based on age.

The intended capability graph, arrows meaning requires, is:

```text
Agent Store -> no lifecycle or host package
Base        -> no lifecycle package; route substantive work to selected Workflow
Machine     -> Base, Agent Store
Workflow    -> Base, Agent Store, Machine
Engineering -> Base, Workflow, Agent Store, Machine
```

Base alone can answer ordinary questions. Generic sustained work selects Workflow and its declared
closure. Engineering work selects Engineering and that closure. Base's entry routing must identify a
missing Workflow capability explicitly instead of pretending required tracking ran. Existing Engineering
selections acquire the closure through coordinated manifests and native selection; source generation
alone is not activation. Profiles keep their tracker policy and select the generic or engineering
operation their task actually needs. No ownership-based profile adoption occurs.

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

PR #353 at `8bcb82244a635b69f26b25b4f60e02f03e105459` is stacked on #352. The bounded L4 writer
moved lane-selection policy to Machine, corrected all active callers and resource anchors, and made
native launchers consume prepared dispatches with caller-owned authorization/checkpoint/pickup. Side-goal
ownership, explicit model selection and exit3 duplicate protection remain. Machine close preserves the
unresolved repair outcome; Engineering session retains discipline repair policy. Existing debt moved intact.
The 17-file source delta was 60 added/64 removed lines plus the current goal checkpoint. Focused lane,
launcher, startup, harness, tier, source-layout and transfer tests passed, as did generation/catalog checks.
Full and ordinary incremental private review passed at exact head `7c77e7d5b1dc6c419b5096431018079e7c530026`, including the six-line concrete lane example required by CI. Native review, parent synthesis of the workflow lens, full-pass security and frozen docs reachability passed. Windows/Linux CI and ci-required passed in run `39698190685`. PR #353 is ready with human-gate and merge authorization absent; completed bundles were removed after review-record. This status child has reconciled the exact parent by fast-forward.

A separate child checkout is actively needed because S2a is frozen for review while its merge remains
held. The dispatch requires completing authorized dependent preparation before the final approval request.
This status child is now the canonical goal owner; earlier checkout copies are frozen slice snapshots.
No other checkout writes this goal. Current owner was reconciled and re-claimed through Machine's supported
installed facade; this remains the same execution and native session, not a new goal or successor.

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

The isolated status slice is complete and locally verified against parent 7c77e7d5. It publishes the
hookless Workflow package, moves list-work to workflow:status, reads the owned Agent Store API directly,
preserves read-only selected tracker behavior, and moves the recording contract with all active links.
The source and regression tests own the detailed implementation. No old active list-work name/path or
Engineering recording-resource path remains in the bounded authored inventory.

The rename-aware source delta is 46 paths, 565 additions and 310 deletions. Twenty-two guidance edits
are mechanical href/caller updates; moved runtime and tests contain 221 changed lines. The remainder is
the minimum package/manifests/harness/tier/selection graph needed for a self-contained new package.
Atomicity assessment: this is one status/recording ownership cutover, below 1000 changed source lines;
its new namespace, resource embedding, permissions, manifests and callers must change together without
aliases. Generic lifecycle is already separated as S2b2. Existing catalog order and fingerprints were
preserved to avoid unrelated generation churn. The goal checkpoint is separate documentation.

Validation passed: 52 status cases, 25 source-layout cases, 21 focused harness/tier-source cases,
harness drift, generation/digest/tier payload checks, in-memory 610-file/83-skill build, and exact Template
examples for all 22 changed canonical guidance paths. The absent reader-class case now returns the
normal unavailable-store result rather than an AttributeError. Both retired runtime text and obsolete
Codex permission entries are removed. Generated distribution output is excluded. Full frozen review
and Windows/Linux CI follow the local commit; native activation remains S3.

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

Engineering plans becomes the software planning extension. Preserve roadmap/plan/ledger file graph and stable keys, technical implementation examples/standards, green consumption contracts, PR slicing/stacks, profile-specific conditional gates, compact ledger template/budget and validation, review watermark, substantive commit/push/remote evidence policy, software delivery/closeout and rename grep. Refer to common artifact owner for generic placement/authority/checkpoint timing/context transfer; do not duplicate whole-goal execution or readiness. Move software-specific checkpoint and recorded-repair transfer fields here. Retain every typed dependency gate/return path needed by software delivery.

Remove resume-plan and continue-roadmap entries from contract/v2/compatibility.json and their support-matrix rows/release-window prose; user clean replacement supersedes that compatibility window. Keep staged-review-all retained driver. Do not change contract version or its semantic stages. V2 workflow_id, persisted state IDs, roadmap item keys, continuation owner_id/nonce and historical review/dispatch identifiers remain byte-stable. They are not public skill discovery names.

New active delivery handoff next_stage values must use qualified current names (workflow:run when returning to generic execution; engineering:incremental-review for that actual software operation). Existing workflow_id bytes stay unchanged. Do not mutate persisted binding files in this source change or add an old-name resolver alias. S3 reconciles affected already-bound readers/owners before activation. Core worktree binding inventory on22Oct found only Feature/CrashRecovery carrying next_stage incremental-review (not a retired lifecycle name); no current old lifecycle next_stage binding was found. This is bounded inventory, not global native acceptance.

#### Tests, historical allowlist and scope

Update actual behavior fixtures, not only sentence assertions: plan_workflow_scenarios/harness, plan_authoring_harness and task_workflow scenarios for new public entry/owner values; remove compatibility scenario while preserving persisted workflow_id and stage IDs that are data contracts. Update authored_skill fixture to search Workflow, package coverage tests to use the owning package, host coverage source/mapping fixtures, CI transfer helper path, engine hook delivery tests and Base context tests. Remove obsolete route tests; add actual Source/Claude/Codex SessionStart payload and missing-contract behavior tests using deterministic subprocesses. Keep transfer receipt tests against moved exact helper, including dispatch-first no-ready-receipt path through guidance fixtures. Verify generic Workflow package has no Engineering dependency/runtime and both hosts resolve all new names.

Retired active names/paths must have zero hits after an explicit survivor allowlist: completed historical plans/observed acceptance records, this goal's migration mapping, and opaque stored v2 workflow/stage identifiers. .agents/plugins/runtime-assertion-ownership.json verified_acceptance is historical observed native behavior; do not rename it into a false observation. Do not edit the old completed routing/store migration goal. No automatic rewrite of every plan or every registry row.

Run focused lifecycle/transfer/continuation/context/host-coverage/package/selection tests, generation/digest/harness/tier checks, exact guidance-example validator and instruction-file pairing. Add concrete fenced examples to newly moved/changed guidance. Check catalog common generated fingerprints separately and exclude generated plugins output from commits. Windows/Linux exact-head CI and frozen native+targeted independent review follow. Installation is S3, never inferred from source tests.

Expected scope includes substantial deletion/consolidation of old guidance and ~950 obsolete unwired router/test lines. Separate mechanical caller/path updates from substantive policy/runtime lines. At >1000 substantive lines or40 substantive paths explicitly assess atomicity: public entry names, contextual routing, artifact owner, package resources and caller fixtures must switch together with no temporary aliases. The independently usable status package was already split out; do not grow S2b1. Parent must record measured assessment before review. No other unrelated cleanup.

Readiness: bounded independent reader /root/s1_readiness completed the exact source-contract check against 7c77e7d5. Its sole concrete correction, retaining future annotations in the receipt reader for Python 3.9, is included above. Parent verdict: ready for the specified implementation after the actual completed S2b1 parent is reconciled. No write lease is granted before that parent exists. Native activation remains S3.

### S3: coordinated selection and native acceptance

Core publishes both namespaces. Personal at `09ab438d644552831f9fb9f49162c02798a6a838`
and Infonetica at `59644f172c08e2f1afb49138db0db7d6907d1069` have no authored retired
lifecycle/lane calls; their selected GitHub/Azure record operations remain distinct. Personal's actual
producer requires Engineering and Machine; Infonetica requires Work, Base and Engineering. No lifecycle caller changes in either profile are needed by the demonstrated inventory. Their own source-project declarations still need coordinated required closure: exact fetched Personal origin/main selects Base, Engineering, GitHub Actions, Machine, Personal, Python and Template, so expansion adds Agent Store and Workflow; exact fetched Infonetica origin/main selects only Base and Machine, so expansion adds Agent Store only. Producer dependencies do not establish profile adoption. Prepare only these required additions through the candidate generator in separate isolated S3 source layers, with native review admission/activation explicitly gated.

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

A completed Marketplace source review records M1 (P2): its own explicit selection must acquire the new required closure. Candidate Machine adopt_plugins.py, with --root and --mode preview/write/check and no requested plugin/profile, preserves the existing selection and expands its required dependencies. Read-only previews passed for Core and Marketplace with exactly .agents/plugins.json, .claude/settings.json and .codex/config.toml changing; no installed payload or native installation is involved. Use the canonical candidate script because generated Machine output is intentionally stale until refreshed. Marketplace repairs these three files in #21; Core prepares its own same three declarations in a final S3 activation-declaration layer after the lifecycle source. This separates review of publishable source under the existing admitted selection from the later native-admission gate; it does not waive that gate. This preserves existing Personal adoption, not a new scope decision. The actual required closure is Agent Store, Base, Engineering, Machine, Personal and Workflow. Later launch refresh reads current enabled identities and does not expand the declaration, so this source correction cannot be replaced by a claim about eventual refresh. Native activation remains separate. Review of the newly declared packages must account explicitly for candidate-source contracts and currently absent installed namespaces before claiming scope resolved.

Marketplace native catalog CI passed on Windows and Linux. Separate policy jobs demand removal of the unchanged .github/workflows/check-personal-policy.yml. Establish exact baseline failure provenance; the dispatch excludes unrelated workflow deletion. Preserve that workflow unless its authorized owner or Tommy supplies the missing scope authority.

Publication order is Core source stack, successful generated-package publication, then the coordinated
marketplace roster. Hold breaking publication until the known callers and selection are ready together.
Use supported native installation/update paths only when authorized. Preserve running snapshots and
reconcile affected already-bound readers separately from fresh activation. Source generation and CI are
not installed acceptance. Windows native acceptance needs fresh selected Workflow/Engineering entry
points; Linux installed-host acceptance needs an actual supported Linux host. Resolve these named gates
after all independent implementation/review/PR preparation is complete.

## Execution readiness

Verdict: S2b1 implementation and targeted verification are complete; commit and frozen review are next. S2b2 passed the bounded source-contract readiness check and awaits the reconciled S2b1 parent. The isolated Marketplace catalog slice is ready for the specified edits above; source review, platform CI, merge and installation remain distinct gates.
Execution authorization: architecture and implementation through reviewed PR preparation.
Transfer: none; retain this owner under the explicit dispatch.
Unresolved: dependent S2b implementation/reviews, Marketplace review/CI, and S3 coordinated publication/native acceptance.
Resolver: current owner, bounded readers and independent reviewers. None blocks S2b1 implementation.

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

## Execution checkpoint

S1 runtime writer lease is released to the parent. Focused verification passed: 5 inspection tests,
21 registration tests, 48 recovery tests and 9 close-loader tests; the parent then observed 64 session
command tests, 59 store tests and 51 status-reader tests pass. The latter three suites ran in child
processes with inherited GIT_CONFIG_COUNT/KEY/VALUE overrides removed from their disposable fixture
environment. Windows environment restoration otherwise leaves an empty Git value missing from the
native environment. This is test setup isolation; no runtime Git configuration was changed.

Inspection now starts a read transaction so its envelope uses one SQLite snapshot. Its deterministic
WAL regression passes. The final runtime generation, generated drift check, catalog digest check and
four-package harness check passed. The duplicate test helper and import were removed. The 22 repository-provider tests and both final isolated-package
checks passed; the candidate is ready for its committed review checkpoint.

The S2 source assessment establishes existing engineering:feature and engineering:bugfix as the bounded
technical operations for Workflow run. Engineering plans remains the technical planning/design extension;
there is no demonstrated need for another engineering:design skill. Consolidate generic artifact and
checkpoint rules into one Workflow-owned plan-artifacts contract, with technical delivery fields in the
Engineering extension. The existing transfer helper permits non-Git directories but its prepared
receipt path requires critical implementation readiness; generic dispatch-first handoff must preserve
the separate path for unresolved architecture. Exact helper and activation edits still need S2 readiness.

The old marketplace Claude owner ad2a7ed0-622d-4a90-a640-2f9f3aee24b4 was found through supported recovery
inventory with status closed and activity 8 October 2026. The recorded parent Codex identity was absent
from the selected profile's recovery inventory. No owner was reopened, closed or repurposed. Preserve the
old checkout and goal; a new catalog slice still needs its current checkout/registry reconciliation.

S2a's bounded L4 writer returned its lease. The 17-file authored delta is 60 added/64 removed lines,
including a 96%-similarity policy move; the existing debt file moved intact. Lane tables (29), process
standards (22), Claude launcher (41, one skip), Codex launcher (37, one skip), startup (20), harness (6),
tier payload (13), tier predicates (14), source-layout and transfer fixtures passed. Generation/digest
checks and retired active namespace checks passed; generated output was restored and no output is staged.
The parent reconciled the actual diff against the approved source boundary. This commit is the S2a candidate.

S1 full and incremental private review receipts approve exact head `5e815d06`; no actionable findings.
Windows and Linux CI run `39695061838` passed; PR #352 is ready with human-gate. The small reviewer test wrote only a bytecode
cache in its disposable bundle; archive comparison proved all source bytes unchanged and that cache was
removed before the successful review-record. Review approval does not grant architecture merge authority.

S2b evidence found one production consumer of the unwired prompt router: `continuation_stop` reads its
control/receipt helpers. Retire the obsolete prompt router with the old lifecycle names while preserving
those readers, the existing temp receipt path/keys and unrelated continuation owner checks. Do not enable
any retired enforcement hook. New Base SessionStart context supplies the canonical routing guidance.
The status package is under its bounded implementation lease. The exact lifecycle specification above passed independent readiness, with Python 3.9 future annotations retained in the extracted receipt reader.

## Next Steps

Commit the verified S2b1 source and checkpoint, open the child draft with human-gate, and run its full
frozen review and exact-head CI. Start the independently ready S2b2 implementation from that exact
committed parent in its own child while S2b1 validation proceeds. Remediate Marketplace M1 through the
source-only generator; preserve the explicit native-admission gate. Establish policy failure provenance
against exact base without deleting the unrelated workflow.

Scope: whole plan through all remaining phases and terminal delivery within the dispatched authority.
Current slice: S2b1 commit/review; next S2b2 lifecycle implementation; Marketplace source correction.
Remaining scope: lifecycle implementation, caller migration, both-host source verification, review,
coherent PR preparation, required project declarations, and explicit publication/installation gates.
Done when: the requested namespace cutover satisfies acceptance, or only evidenced external gates
remain after every independent authorized action is complete.

```agent-host-coverage
{"schema_version":1,"shared_source":".agents/agent-store/runtime/","hosts":[{"host":"claude","behavior":"Use the canonical registry through package-local native adapters and expose read-only inspection without process-liveness claims.","source":".agents/plugins/manifests/claude/machine-hooks.json","mapping":"sources.json embeds the canonical store runtime in the consuming Machine and Engineering packages and publishes Agent Store inspection.","verification":{"level":"source","result":"passed","evidence":"Inspection 5, registration 21, recovery 48, close-loader 9, session commands 64, store 59, status-reader 51, repository provider 22; generated package checks and both isolated host inspector entry points pass. Installed activation remains an S3 gate."}},{"host":"codex","behavior":"Use the same registry and atomic ownership semantics through Codex lifecycle hooks, with separately labelled recorded-state inspection.","source":".agents/plugins/manifests/codex/machine-hooks.json","mapping":"The same canonical store bytes are embedded locally; Codex hooks retain package fingerprint and snapshot integrity.","verification":{"level":"source","result":"passed","evidence":"Inspection 5, registration 21, recovery 48, close-loader 9, session commands 64, store 59, status-reader 51, repository provider 22; generated package checks and both isolated host inspector entry points pass. Installed activation remains an S3 gate."}}]}
```
