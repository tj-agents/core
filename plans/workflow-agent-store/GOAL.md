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
- Worktree: `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Refactor-MachineWorkflowBoundary`.
- Branch: `Refactor/MachineWorkflowBoundary`.
- Base/parent: `Refactor/WorkflowAgentStore` at `5e815d0658597f031c332e9d2a3e3bb35d886e8a` (PR #352).
- PR: not opened for S2a. Parent: [Core #352](https://github.com/tj-agents/core/pull/352), S1 with `human-gate`; full and incremental source reviews complete, Windows CI pending.
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

Active branch/base are recorded above. This independently useful slice moves `session_store.py` and
`repository_identity.py` from Machine's authored scripts into `.agents/agent-store/runtime/`, publishes
the inspect capability, updates every current Machine/Engineering loader, and consolidates the existing
read-only schema reader. Native recovery behavior and all writer transaction semantics remain unchanged.
There is no old-path shim. The store remains `~/.agents-state/sessions.db` with its existing override and
schema version 4. Existing schema-2/3 read-only support remains an unchanged data-reader contract, not
a namespace alias or a newly introduced fallback.

S1's intermediate selection graph contains no Workflow package yet: Agent Store requires nothing,
Base requires nothing, Machine requires Base and Agent Store, and Engineering requires Base, Agent Store
and Machine. Declare those exact ordered prerequisites in sources/catalog and their transitive closure
in the plugin-selection roster. Agent Store's scope is `name/plugin: agent-store`, root
`.agents/agent-store`, kind layout, process domain. Its only skill is `utility/inspect`, kind utility,
domain process; its tier applies always when selected and its payload is `process`. Add both host adapters,
both package manifests (no hooks), both local marketplace entries, the catalog package and harness.
Add `agent-store@base-agents` to fresh selection after Base, preserving the other entries' order, and
match both local marketplace rosters. This existing publisher identifier is not being retired in S1;
the separate CanonicalSetup PR owns that work. Source declarations must not claim the external
`tj-agents` marketplace or native caches already contain the new package.

The harness declares Python/Python3 `-B` inspection commands for its canonical and generated skill paths
using the current precise `PLUGIN_ROOT` permission format on both hosts; it grants no writer, recovery
or launch command. Map the Agent Store tier file to `tier.json`, add its generated package root, and
update the existing Machine hook paths and harness inventory to the embedded canonical store path.
Core source package discovery and isolated generated invocation are S1 gates. Cross-repository selection
and real native activation remain explicitly owned by S3, with no source-only completion claim.

Consumer contract: Machine's host adapters invoke the same store functions using their captured native
identity; Engineering's repository provider uses the canonical read-only reader and translates its
errors to the existing provider error type. Inspection emits JSON to stdout, synchronously, with
recorded state clearly labelled and process liveness explicitly unobserved. It opens SQLite with
`mode=ro` and `query_only`; inspection must never create a database or run schema migration. Missing,
unsupported or invalid stores return actionable failures. No connection is held between commands.

Add these runtime mappings while retaining the existing .agents/machine/scripts directory mapping
for its remaining Machine utilities. Remove only the separate Engineering repository_identity.py
copy mapping; both moved source files leave Machine with no shim. Concrete new mapping:

```json
{"plugin":"machine","source":".agents/agent-store/runtime","destination":".agents/agent-store/runtime"}
```

The same source/destination mapping is declared for Agent Store and Engineering. A Machine shared-script
loader resolves identically from source `.agents/machine/scripts` and packaged `resources/machine/scripts`:

```python
HERE = Path(__file__).resolve().parent
store_path = HERE.parents[2] / ".agents" / "agent-store" / "runtime" / "session_store.py"
```

Skill adapters use explicit source/package layouts derived from their own location. They do not scan
the user's home, installed plugin inventories or the current directory for runtime code. Move the
existing `ReadOnlyWorkItemStore` implementation into `runtime/reader.py`, with a store-owned exception;
the Engineering provider catches that exception and raises `ContractViolation` with the same message.
Inspection and provider reads consume that one reader. Keep writer and reader opening separate:

```python
connection = sqlite3.connect(f"{database.resolve().as_uri()}?mode=ro", uri=True)
connection.row_factory = sqlite3.Row
connection.execute("PRAGMA query_only = ON")
```

The inspection CLI is `inspect.py [--database PATH] [--execution-key KEY | --repository REPO]`.
With no selector it lists the registry. Its stdout envelope has exactly `schema_version` (the observed
SQLite version), `state_kind: "recorded"`, `liveness: "not-observed"`, `work_items`, `sessions` and
`references`. Collections are sorted by key, handle and provider/scope/native-id respectively. Work items
and sessions expose the existing stored columns as JSON objects; no inferred liveness field is added to
individual rows. References expose provider, scope, native_id and work_item. An execution selector scopes
all three arrays to the same existing key; a repository selector scopes items by their repo and includes
sessions recorded in that repo or attached to those items. An absent execution, missing database,
unsupported schema or invalid store exits 1 with `{"error":"<concrete diagnostic>"}` on stderr and no
success stdout; invalid arguments exit 2. Older accepted reader schemas have an empty references array.
The operation never imports Machine, opens a writer, launches processes or consults native histories.

The detached close observer remains a supported self-contained staged payload. `start_detached`
copies the canonical store and repository-identity bytes next to its staged registration module;
`session_store_path` explicitly supports that staging layout alongside current source/package layouts.
This is delivery of the same implementation, not an old-path shim. `close_session.sweep_script` must
resolve Machine's `plugin_autoupdate.py` from its own source/package root, independently of the store
location; it must not derive a Machine utility path from `session_store_path().with_name(...)`.
Add a focused fixture that proves both sweep discovery and staged store use after the source move.

Expected scope: two mechanical source moves, roughly 200-400 substantive added/deleted lines plus
package declarations, loaders and existing-test path updates. Reassess at 1,000 substantive lines or
40 substantive files; measure moves and generated output separately. Verify transactional claims,
reader non-mutation during a writer transaction, native resume refusal rules, package isolation and
both host hook paths with deterministic fixtures. Run generation/harness checks and independent review
against the frozen candidate, then prepare its focused PR. Its merge remains within the dispatch gate.

S1 measured scope before review: 43 changed paths, 1,593 added/deleted lines. The two runtime
modules are byte-identical mechanical moves (931 existing lines); eight documentation/adapter/plan
files account for 490 diff lines. Runtime and tests account for 763 diff lines across 19 files, including
the extracted read-only reader; the remaining 340 lines across 14 files declare packages, permissions,
hook paths and dependency closure. Generated output and common generated catalog digests are excluded.

The approximately 1,000-line warning therefore triggers an explicit split assessment. Keep this bounded
slice atomic: the canonical runtime move, source/packaged/staged consumers and hook/resource declarations
must agree on the same path, while the selectable package and its read-only entry point must agree on
both host manifests, selection closure and harness permissions. A private extraction followed by a public
package would need two intermediate consumer/declaration/fixture configurations without an additional
behavior boundary; separating the declarations from their consumers would break shipped resolution.
The retained candidate has 763 runtime/test lines and no schema or writer algorithm change. Its review
covers source ownership, isolated packaging, detached staging, SQLite read isolation and exact-head CI.
No Workflow lifecycle changes may expand this frozen S1 scope.

### S2a: Machine capability boundary

S1 source review passed. The current parent includes its focused tier-fixture correction; independent
incremental review and exact-head CI remain with PR #352. The architecture merge hold prevents landing
that parent now, while the dispatch requires completing all authorized dependent preparation before a
final approval request. S2a therefore branches from its verified tip and must target that parent in its PR.
A second checkout is actively required because S1's frozen review and CI still own its existing checkout.
This child is now the canonical goal's current execution location; the parent plan is a frozen slice snapshot.
No other checkout may write this current goal.

A bounded independent source reader checked this prerequisite against `ce9b3966`. The parent resolved
its only remaining ownership decision: host capability/cost selection belongs to Machine, domain machine.
The slice is roughly 15 substantive paths and fewer than 300 substantive lines beyond a mechanical policy
move; it stays separate from the broader lifecycle replacement. No launch algorithm, model value, stored
identity or writer behavior changes. Personal, Infonetica and Marketplace fetched-main scans contain no
current `engineering:lanes` caller, so this slice needs no external profile mutation.


1. Move .agents/engineering/policy/lanes/ to .agents/machine/policy/lanes/ (including TECH_DEBT.md if present, preserving existing unfinished debt). Set domain: machine; kind remains policy. This is host capability/cost selection, so Machine is its logical owner. Keep bare name lanes, public namespace machine:lanes; no engineering alias. Remove the sentence directing large-plan execution transfer through engineering:plans; Engineering's plans already owns that policy. Existing lane data stays under .agents/lanes and its resource maps to both consuming packages stay unchanged.
2. Correct relative resource locators inside the moved canonical policy: from .agents/machine/policy/lanes, ../../../lanes still resolves shared .agents/lanes in source but Machine package uses resources/lanes. Use explicit source and generated paths consistent with PACKAGING; the host entry located <package>/skills/lanes uses ../../resources/lanes. Do not point into Engineering or author checkout. Give concrete commands only for paths that ship.
3. Update all current engineering:lanes calls to machine:lanes, both thin lane adapters' canonical path/domain, and catalog skill membership. New source scope is already declared for Machine. Update current source references to engineering/policy/lanes and package assertions. Preserve historical observed evidence rather than rewriting history; list any remaining matches and justification.
4. Machine handoff-codex and handoff-claude are transport adapters. Replace the paragraph beginning 'If the launcher printed its confirmation' with equivalent launch evidence and duplicate-attempt safeguards while making the already selected caller own full-goal/side-workstream checkpoint, release and pickup rules. Add the clear contract: accept an already authorized prepared dispatch; do not call a higher-level workflow to prepare it again. Preserve the originating goal for a side transfer and distinguish submission from pickup. A launcher-only request can finish at verified submission. Retain exact exit-code3 no-retry rule.
5. Remove the last four lines of the launch-lane paragraph that prescribe small/large plan transfers through engineering:plans. Keep the concrete lane-selection/launch behavior and references to machine:lanes. In Claude's effort paragraph, state directly that explicit user-selected model/effort/frontier is preserved; drop the upward engineering:handoff reference.
6. Change only launch_claude.py's error string at resolve_model for redirected L1: '--lane {args.lane} routes to Codex {route["lane"]}; use machine:handoff-codex, or omit --lane for an explicit user-named model.' Keep existing rejection and route behavior; no new comment.
7. Shared .agents/lanes/handoff-agent-body.md becomes a native routing proxy request without naming an upper-level workflow: 'You are a routing proxy. Return a required native handoff request to your parent for {host} {lane}. The parent owns authorization and context preparation. Do not inspect, execute, delegate, or otherwise advance the delegated task.' Keep placeholders and proxy behavior. Generated agent tests should assert the prepared-parent boundary rather than the removed Engineering invocation.
8. Machine close keeps a user-called-out mistake unresolved: answer the direct question and preserve the repair outcome until its current owner resolves it; a missed-close question does not instruct immediate closure. Remove calls to engineering:self-repair from this Machine skill. Engineering session keeps that selected-discipline instruction unchanged. Do not add another repair workflow or weaken close preconditions.


S2a verification: lane-table and process-standard checks; targeted handoff argument/model-resolution
fixtures; generation, catalog, harness and tier checks; source/packaged Machine lane resource resolution;
old active namespace/path grep; native routing proxy still returning only the parent request. Review the
child delta against its exact parent and validate the cumulative tree on Windows and Linux. Keep generated
output uncommitted. Bounded L4 implementation owns only this specified transformation; parent retains
architecture, acceptance, review synthesis and delivery. No native model session is a test fixture.

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

### S3: coordinated selection and native acceptance

Prepare only necessary caller/dependency changes in the actual owning repositories after reading their
instructions and reconciling their owners. External primary checkouts inspected during initial discovery
may be stale; their contents are leads, not current-main evidence. Publish namespaces from Core only.
Hold breaking publication until the known callers and marketplace selection are ready together.
Use supported native installation/update paths only when authorized. Preserve running snapshots;
validate fresh activation and affected bound readers with deterministic fixtures. Linux installed-host
acceptance needs a supported Linux host; CI source execution is separately labelled evidence.

Current-main consumer inventory was refreshed on 21 October 2026. Personal at `09ab438d` and
Infonetica at `59644f17` have no authored calls to the lifecycle names being retired. Their current
Engineering feature, addressing and PR operations remain valid. Personal explicitly depends on Engineering
and Machine; Infonetica explicitly depends on Work, Base and Engineering under the tj-agents marketplace.
Do not add Personal or change either profile's tracker semantics. Marketplace at `063a604c` still has its
older Base/Engineering/Machine dependency declarations in `catalog.json`; S3 needs the namespace entries
and correct closure there. Its old CoreCatalogAdoption goal/checkout is an ownership lead, not observed
liveness. Resolve that overlap through current native ownership and review evidence before its writes.

## Execution readiness

Verdict: S2a implementation and focused verification are complete; its immutable candidate is ready for independent review. S1 Windows CI and S2b/S3 readiness remain separate gates.
Execution authorization: architecture and implementation through reviewed PR preparation.
Transfer: none; retain this owner under the explicit dispatch.
Unresolved: S1 Windows exact-head CI; S2a independent review/CI; S2b exact source/route mapping and S3 coordinated publication/native acceptance. None blocks independent preparation.
Resolver: current owner and a bounded independent readiness reader. No new architecture successor.

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
Linux CI run `39695061838` passed; Windows remains running. The small reviewer test wrote only a bytecode
cache in its disposable bundle; archive comparison proved all source bytes unchanged and that cache was
removed before the successful review-record. Review approval does not grant architecture merge authority.

S2b evidence found one production consumer of the unwired prompt router: `continuation_stop` reads its
control/receipt helpers. Retire the obsolete prompt router with the old lifecycle names while preserving
those readers, the existing temp receipt path/keys and unrelated continuation owner checks. Do not enable
any retired enforcement hook. New Base SessionStart context supplies the canonical routing guidance.
The exact smaller status-package and subsequent lifecycle specifications remain under readiness assessment.

## Next Steps

Review this committed S2a candidate against `5e815d0658597f031c332e9d2a3e3bb35d886e8a`, then open
its draft against `Refactor/WorkflowAgentStore` with `human-gate` and obtain exact-head platform CI.
The parent continues S1 Windows CI in its preserved checkout. Continue S2b readiness under the same goal:
first publish Workflow status with direct Agent Store access, then perform the lifecycle/artifact/entry
routing cutover. This separates the independently usable read operation from authority/continuation policy.
The architecture merge hold and S3 native installation gate remain explicit.

Scope: whole plan through all remaining phases and terminal delivery within the dispatched authority.
Current slice: S2a review and platform verification, stacked on S1.
Remaining scope: implementation, caller migration, both-host verification, review, coherent PR delivery,
and explicit merge/installation gates when reached.
Done when: the requested namespace cutover satisfies acceptance, or only an evidenced external gate
remains after every independent authorized action is complete.

```agent-host-coverage
{"schema_version":1,"shared_source":".agents/agent-store/runtime/","hosts":[{"host":"claude","behavior":"Use the canonical registry through package-local native adapters and expose read-only inspection without process-liveness claims.","source":".agents/plugins/manifests/claude/machine-hooks.json","mapping":"sources.json embeds the canonical store runtime in the consuming Machine and Engineering packages and publishes Agent Store inspection.","verification":{"level":"source","result":"passed","evidence":"Inspection 5, registration 21, recovery 48, close-loader 9, session commands 64, store 59, status-reader 51, repository provider 22; generated package checks and both isolated host inspector entry points pass. Installed activation remains an S3 gate."}},{"host":"codex","behavior":"Use the same registry and atomic ownership semantics through Codex lifecycle hooks, with separately labelled recorded-state inspection.","source":".agents/plugins/manifests/codex/machine-hooks.json","mapping":"The same canonical store bytes are embedded locally; Codex hooks retain package fingerprint and snapshot integrity.","verification":{"level":"source","result":"passed","evidence":"Inspection 5, registration 21, recovery 48, close-loader 9, session commands 64, store 59, status-reader 51, repository provider 22; generated package checks and both isolated host inspector entry points pass. Installed activation remains an S3 gate."}}]}
```
