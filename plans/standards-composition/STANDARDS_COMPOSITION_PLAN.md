# Scoped standards composition

Design status: proposed composition contract, pending Tommy's decision. The inventory below distinguishes implemented behavior from the proposed mechanism. Publication approves the planning artifact only. Runtime implementation and consumer adoption remain gated; the owner slices identify additional content and host acceptance gates.

## Outcome

A project loads the standards it actually selects. Universal requirements stay compulsory within their stated scope. Employer/repository conventions, selected personal preferences, architecture and implementation technologies contribute separate, attributable requirements. Installing a package does not adopt every opinion in it.

The same resolved selection drives planning, first writes, review and generated host delivery. A successful implementation cannot be claimed from metadata, generated files or a tier announcement alone.

## Authorization and boundaries

Tommy requested work on the standards and their refactor on 2026-10-09, including repository plans that reach the personal repository's default branch even when implementation is unfinished. Planning publication is authorized. Implementation stays in the standards source repositories and proceeds only from resolved, reviewed design. This does not authorize application-code publication, changing live hook trust, enabling currently disabled hooks, or modifying another active writer's unfinished work. Infonetica retains its own commit/push/merge and private-tooling rules; personal plan publication must not be installed as work-repository authority. Tommy explicitly requested a fresh design handoff on 2026-10-09 for the direction of all tj-agents, beginning with .NET and React and updating kit templates if the design requires it. This supersedes the earlier same-session preference for this design work only. The current successor is authorized to investigate, propose and review the design and publish its personal-repository planning artifacts. Runtime implementation and live consumer adoption await Tommy's decision on the proposal. The originating session retains cris-authz and its unpublished local style correction.

## Evidence and existing ownership

- [.NET PR24](https://github.com/tj-agents/dotnet/pull/24) and [PR32](https://github.com/tj-agents/dotnet/pull/32) merged capability scopes and family-profile separation. `.agents/tests/test_source_layout.py` pins stack-free core hubs and keeps prerequisite-bearing members outside core. This is implemented and tested separation, but stack-free does not mean free of personal conventions.
- [Core PR140](https://github.com/tj-agents/core/pull/140) merged `.agents/machine/utility/bootstrap-capabilities/scripts/selection_profiles.py`: an optional read-only adapter for source-owned finite selection forms. It returns package IDs; discovery, installation and dependency closure are outside its contract. The inspected current source contains no production caller. [C++ PR37](https://github.com/tj-agents/cpp/pull/37) publishes one producer declaration and parity fixtures, but remains an open draft. Reuse this reader and producer work where their contracts fit; do not replace them under the claim that no separation existed.
- Core PR116 merged project/dependency facts and standards context, explicitly deferring source ownership and host activation. The current `Feature/StandardsSourceOwnership` worktree contains uncommitted `source_facts.py`, tier/context changes and tests. Preserve that owner; inspect its state before integrating its contribution.
- Dotnet PR35 merged the generator and registered cris-authz. Current C# routes select style/naming; the Domain row selects domain-design but not its DDD/value owners. Repository filename rules select EF-specific persistence without matching its prerequisite metadata.
- Core's installed tier gate announces .NET applicability. Review lists tier conventions but does not prove semantic prerequisites were selected. `workflow_ops.route_findings` requires a checkout-local table, whereas the router can cross a nested worktree boundary to the main checkout's private table.
- The .NET style skill mixes language and personal choices under `profile: core`; its no-underscore preference applies to all C# in its current wording. EF persistence and tenancy declare technology prerequisites but also contain selected library and house assumptions. Split those decisions rather than relabeling their whole bodies universal.
- Kit already generates `selection.json` with profiles, applicability, requires and provenance. Treat this as an existing inventory to consume, not proof of an enforced resolver. Core already owns scoped context facets for house, architecture and adopted suites. Reuse their capabilities after identifying missing consumer behavior.
- `Feature/ConfigurableAutoMerge` has committed implementation and reviewed evidence but no PR. Its existing goal authorizes delivery through a draft PR, defaults omitted/false to disabled, and makes merge conditional on separate delivery authority. Do not claim it shipped or silently take over its writer.
- [Infonetica PR1](https://github.com/tj-agents/infonetica/pull/1) already merged a dedicated employer package. Its `plugins/infonetica/skills/work-context/SKILL.md` says generic .NET/React standards supplement employer standards, but this does not select individual personal rules within mixed stack skills. Reuse the employer owner rather than inventing a replacement.
- Engineering plans already require planning artifacts to land; base planning alone does not select that lifecycle. This selection/publication gap and the personal-versus-work boundary need explicit repair.

## Selection decisions

| Category | Selection | Owner |
| --- | --- | --- |
| Universal behavior/safety | Always within its explicit scope; a profile cannot remove a higher-priority user requirement | Core or the framework contract owner |
| Language/framework correctness | Actual language/framework applies, with no personal conventions mixed into the rule | Stack owner |
| House/employer conventions | Explicitly adopted profile; employer/repository resolves its own conventions | Personal or employer owner |
| Architecture | Explicit project adoption, such as DDD, not inferred from a folder name | Architecture contract owner |
| Technology implementation | Actual project/source prerequisites and adopted abstraction, such as EF Core, Dapper, raw Npgsql, or a selected data-access library | Technology contract owner |

Tommy's provisional preference is shared technical requirements plus explicitly selected personal conventions. Before settling the detailed schema, trace and reuse the previously implemented separation; his latest request specifically prioritizes proving what already exists. The exact profile schema and migration remain unresolved. A logging example is not an instruction to disable logging. DDD's adoption in authz does not make every personal C# style opinion adopted there.

Select facts per project/source. EF Core in one service must not impose EF-specific tenancy on a Dapper or raw-Npgsql sibling. Tenant-isolation requirements may be shared outcomes where an actual owner requires them; filters, interceptors, SQL predicates and tenant context mechanics remain implementation-specific. Unknown/conflicting prerequisites are explicit diagnostics requiring resolution, not inferred technology adoption.

Employer and repository standards compose with selected shared standards. Resolve a conflicting house decision explicitly; emit its owner and selection evidence. Do not silently overwrite it with the generic package's convention. Broad skills mixing multiple selection classes must be separated so an employer can use shared technical guidance without adopting personal field naming or logging preferences.

## Delivery phases

### Phase 1: Resolve the taxonomy and publish the maintained design

Inventory core, kit, dotnet, react and employer contracts against actual source, distinguishing universal scope, technical prerequisites and house decisions. Begin with the merged .NET family/profile tests and core finite-profile reader, and distinguish package selection from individual requirement selection. Read the existing composition, conditional-route, source-ownership and auto-merge owners. Resolve overlap and the exact selection schema, diagnostics and migration examples before declaring runtime work ready.

Consumption: each source owner receives one path-to-contract inventory and its own concrete implementation plan; the cross-repository plan records only dependencies and shared acceptance. Existing owned plans remain their single progress owners.

Gate: reviewed personal planning artifacts are merged to main; scope/ownership and plan graph pass. Later implementation-ready designs include current/proposed code at the deciding boundaries and tests for the cases below. Publishing this requirements plan does not mark the refactor complete.

### Phase 2: One scoped selection result in core

Complete or integrate the existing scoped project/source facts safely. Editing, planning and frozen review consume the same selected requirement identities, source hashes, prerequisite evidence and diagnostics, anchored to the actual checkout. Installation is separate from adoption. A nested fresh worktree must not accidentally inherit another checkout's live table or omit the profile review used.

Consumption: both host adapters, routes and review preparation receive the same immutable requirement resolution. Produce explicit read/delivery evidence before a required write.

Gate: core resolver/route/review tests prove matching selections, conflicting house decisions, absent profiles, unresolved dependencies, nested worktrees and missing load proof. Source tests alone do not qualify live host acceptance.

### Phase 3: Separate .NET and React contracts by real applicability

Split universal/technical C# guidance from personal house conventions and explicitly adopted DDD/value behavior. Give EF Core, Dapper and raw-provider contracts separate technology identities and finer selected-abstraction prerequisites. Separate tenant mechanisms by implementation. Do not invent Dapper guidance from EF guidance. Keep one canonical owner per rule and explicitly migrate published names/profile membership.

Consumption: generated selection inventory and routes express selected contracts and technology prerequisites, including DDD behavior under API paths. No EF library or personal style rule is selected solely by a filename or .NET presence.

Gate: dotnet tests cover EF-only, Dapper-only, raw-Npgsql, mixed projects, employer underscore fields, selected DDD under API, and omitted personal logging conventions. Published producer identity is verified before adopting it in consumers.

React is the second initial stack owner, alongside .NET. Inspect its existing family/profile metadata and source routes before proposing changes. Separate React/TypeScript correctness and explicitly adopted domain guidance from personal styling, library, state-management and testing preferences wherever the actual source mixes them. Include employer-selected and mixed-stack examples. Do not infer that installing React adopts every selected-stack preference.

Kit owns producer/template mechanics. Propose template, schema or generator changes only when the .NET/React composition requirements expose a concrete gap in the current kit contract. If no kit change is needed, record the existing supported mechanism and evidence. Include regeneration/migration examples and producer tests for any required change; generated skill files are not the authored fix.

### Phase 4: Employer profiles and intentional personal adoption

The employer source repository owns employer profiles and its specific conventions. Compose selected shared technical/architecture contracts and any explicitly adopted personal conventions. Keep a future employer separate from Infonetica, rather than modifying the personal pack globally for each job.

Consumption: employer and project profiles resolve a visible composed selection with attribution and an explanation for each chosen contract. Work-repository private-tooling and publication rules remain intact.

Gate: profile tests preserve employer underscore style, select only requested personal standards, and prove omissions do not remove universal requirements. Validate generated private work-checkout adapters without putting personal tooling into application PRs.

### Phase 5: Qualify delivery on the actual hosts

The separate hook-repair owner resolves trust/activation. After that, run fresh isolated Claude/Codex probes using published selected packages. A required unread contract blocks a write; successful loading permits it; unrelated/nonselected opinions are not injected. Review sees the same requirement set. Keep disabled live hooks unchanged until the authorized repair/adoption step.

Gate: captured fresh-host receipts prove trust, correct selected bodies and read-before-write behavior. Preserve unresolved host limitations explicitly instead of marking adoption complete.

### Phase 6: Personal plans and configurable auto-merge completion

Repair the common-to-engineering plan-publication transition for personal repositories: a substantive unfinished plan is in its owning repository's plans convention and merged to the default branch as a planning deliverable. Active implementation checkpoints ride their substantive PRs. Explicit work-repository restrictions and user holds remain gates; an open PR is never reported as merged planning.

Reconcile the existing configurable-auto-merge owner and finish its authorized delivery rather than duplicate its implementation. Enable/disable changes mechanism behavior only; they do not grant delivery authority or bypass exact-head review, checks or holds. Record actual PR/configuration/authority state when a goal cannot merge. The refactor's planning publication is separate from permission to merge another unfinished feature.

Gate: focused tests distinguish personal planning, unfinished implementation, work-repository publication gates, explicit auto-merge true/false/omission and unavailable host capability. Complete the recorded existing feature through its legitimate publication/merge boundary before claiming the toggle shipped.

## Current design deliverable

The successor proposes one coherent standards-composition direction reusable across tj-agents, with .NET and React as the first concrete migrations. Keep unresolved decisions explicit. Preserve the recorded collaborator naming intent: the role suffix must remain correct, and a shorter subject is acceptable where the context makes it unambiguous. Compare reasonable alternatives, recommend one, and show current/proposed configuration and code at selection, precedence, generation, loading and review boundaries. Distinguish package installation, profile adoption, skill/rule selection and proof that the required body was read.

The design must trace producer and consumer identities end to end, preserve employer/repository authority, identify the smallest kit changes actually needed, and split migration into independently reviewable owner PRs with compatibility/rollback and acceptance evidence. Retain this plan and its ledger as the canonical cross-owner artifacts. Existing owner plans remain authoritative for their separate unfinished work.

Planning publication puts the proposed design on main; it does not adopt the proposal as runtime policy or authorize implementation. Return a concise proposal and the consequential decisions for Tommy before runtime changes.

## Inspected baseline and retained owners

Inventory taken on 2026-10-09. Repository-relative paths in this section belong to the named repository. Commit identities pin the inspected source, not a claim about the latest installed release. Generated payloads were inspected for delivery shape, never treated as authored fixes.

| Owner and inspected revision | Implemented producer or consumer | Missing behavior and disposition |
| --- | --- | --- |
| core, `3bd65f7` (this branch; code inherited from `71e76cc`) | `.agents/machine/utility/bootstrap-capabilities/scripts/selection_profiles.py:evaluate` validates a finite source-owned form and returns package IDs. `tests/test_selection_profiles.py`: 11 tests passed. PR140 is merged at `dcb8f5001dbcf3bfee74e404fec670c5f67db114`. | No production caller found in the inspected authored tree. Keep this optional package-selection adapter; do not turn it into requirement resolution. |
| core, same revision | `.agents/hooks/project_facts.py`, `standards_context.py`, and `tier_gate.py:evaluate_project` provide project dependencies, positive scoped context and diagnostic-bearing predicates. PR116 is merged at `9f12571bbc59a4f770e6fc888efb2573c43fed9a`. | Source ownership is a separate unfinished contribution. `Feature/StandardsSourceOwnership` at `73fb99c` has uncommitted source/context/tier changes and tests. Its owner supplies the source-to-project seam; this plan does not replace or copy that work. |
| core, same revision | `skill_router.py:find_repo_root`, `load_routes`, `transcript_skill_outcomes`; `workflow_ops.py:route_findings`, `review_prepare` | Root discovery searches for any ancestor table before a Git boundary; review exits early without a checkout-local table. Current Codex proof uses a body head/tail anchor and bare skill name, not the complete selected canonical body and release identity. These are concrete integration gaps. |
| core PR139, draft `ae107e162e94cde8f616b62a12efdde0e9e905db` | `Feature/ComposeCapabilityCatalog` composes catalog records from immutable source commits and package bytes. | Keep package provenance with this owner. Its checkout's root `GOAL.md` describes older hook-refresh work and does not establish a new composition-plan owner; PR139 is the current review identity. Do not claim this draft is published. |
| core PR54, draft `5f5af36d994025b8290f24afbb71c069638db014` | Required `skills` plus advisory `conditional` entries; its PR describes tests and host limits. | The trunk conditional-route ledger is stale relative to the open PR. Preserve its separate ownership and merge restriction. Advisory conditions cannot satisfy a required semantic prerequisite or load proof. This proposal does not require that draft to merge. |
| dotnet, `2d19e965ef2315e2fe1f258f65769b6beb0b11f6` | `.agents/tests/test_source_layout.py` pins stack-free core and prerequisite-bearing families; 3 tests passed. PR24/32/35 are merged. `.agents/sync_generated.py` emits profile inventory. | Stack-free core still includes personal naming/style. `.agents/dotnet/utility/skill-routes/scripts/gen_skill_routes.py` hardcodes style/naming for C#, domain-design for Domain paths and EF persistence for repository filenames; it does not consume selection metadata. |
| react, `5a23d4b3465cfe2c02c43d0a832eb28799afb907` | Generated `plugins/react/selection.json` separates core, selected-stack, testing, state, routing and other profiles. `.agents/tests/test_core_profile.py`: 5 tests passed. | No React-side selection reader or standards-route generator found. `style` and `structure` mix technical and house provenance; `testing` is a house authorization convention. `domain-design` has no agreed substantive rules. Do not manufacture a React DDD standard. |
| kit, `ac260634c671e5c5ff402f128be794079b9dcf50` | Canonical generator template `.agents/kit/utility/new-plugin/templates/repository/.agents/sync_generated.py.in` requires metadata and emits profiles, aliases, applicability, requires and provenance. Focused generator suite: 42 tests passed. | `applicability`, `requires`, and `provenance` are descriptive comma-split strings, not a validated predicate/precedence language. Add only the machine-readable composition extension described below; do not replace the generator or inventory. |
| infonetica, `9546906d5358317dd249db901a56e0c2ce9226fe` on `Feature/WorkCommunications` | Here `plugins/infonetica/` is authored source, by its own AGENTS.md. `tier.json` requires GitHub and `^infonetica/`; `work-context` delegates work standards to the employer, `service-standards` and repository docs. PR1 merged at `972f40571cd7eefaf0f93808c9923e4e0fe0ae35`. Employer suite: 14 tests passed. | Flat 20-skill inventory and employer detection do not select individual shared/personal requirements. Respect this source-layout exception and the existing communication-work owner. Underscore preservation is a requested repository-convention acceptance case, not a claim that this package currently publishes a C# field-naming rule. |

C++ PR37 remains an open draft at `3b42f8e8c568763d857d286224bcd7884a5e8bf6`; its finite-profile producer is reusable evidence, not an initial migration. Core `Feature/ConfigurableAutoMerge` remains at `a41bdac` with its own `plans/configurable-auto-merge/GOAL.md`, reviewed implementation and no open PR found. Its existing next step is delivery through a draft PR, with merge conditional on separate authority. Hook repair and host limitations remain owned by core's existing host work and `.agents/plugins/TECH_DEBT.md`. No inspected foreign working tree was changed.

Implementation-path standards resolved before writing the examples:

| Proposed destination | Standards read and route evidence |
| --- | --- |
| core `.agents/hooks/requirement_resolver.py`, `skill_router.py`, `standards_context.py`, `.agents/workflows/workflow_ops.py`, schemas and shared resources | Root AGENTS.md, README.md, CODE_CONVENTIONS.md, SOURCE_LAYOUT.md, PACKAGING.md, `engineering:skill-routes`, tier predicate contract, planning/checkpoint/review contracts. `skill_router.py --skills-for` over these intended paths reported no table; explicit repository owners still apply. Python uses standard libraries, explicit paths/UTF-8, argument-list processes and no explanatory code comments. |
| kit canonical generator/template and proposed `.agents/standards/` template files | Kit AGENTS.md, README.md, generator and tests, conformance/check contract. Generator changes originate in kit, are released there, then reach stacks through `kit:update`; vendored stack generators are not independent edit targets. |
| dotnet `.agents/dotnet/contract/` families, route utility and proposed `.agents/standards/dotnet.json` | Dotnet AGENTS.md/README.md, `style`, `naming`, `naming-collaborators`, `domain-ddd`, `domain-values`, `logging`, `persistence`, `multitenancy`, `skill-routes`, and core route convention. Its generated inventory does not constitute routed implementation standards. |
| react `.agents/react/contract/` families and proposed `.agents/standards/react.json` | React AGENTS.md/README.md, `style`, `structure`, `libraries`, `libraries-selected`, `testing`, `testing-frontend`, `domain-design`. No repository route table or standards-route generator exists; kit owns its generator. |
| infonetica `plugins/infonetica/standards.json` and contract skills | Employer AGENTS.md/README.md, `work-context`, tier and harness declarations. Personal authoring repo publication differs from private work-checkout tooling and employer application publication gates. |

## Recommended contract and alternatives

Recommend **homogeneous contract skills, owner-published profiles and one scoped resolver**. A contract skill is the smallest independently adopted body: it can contain several related rules, but all share one selection class and prerequisite set. Split a mixed body at that boundary. Do not parse paragraphs out of Markdown at runtime. Keep hubs as pointers; following a hub must not silently load every optional member.

| Alternative | Benefit | Reason for the recommendation |
| --- | --- | --- |
| Select existing whole packages/profiles only | Almost no schema work | Cannot retain C# technical guidance while omitting underscore or logging opinions inside the same body. |
| Homogeneous skills plus a structured manifest | Reuses skill delivery, family layout, profile inventories and package integrity | Recommended. Adds machine semantics where current string metadata cannot enforce selection. Skills stay readable without a custom paragraph renderer. |
| Stable rule IDs on every Markdown paragraph, overlay/filter the body | Maximum granularity | Creates a second document language, fragile fragment hashes and partial-context proof. Too much machinery for the observed splits. |

Four identities stay distinct: the capability lock selects installable packages; a scoped adoption selects profiles or contracts; resolution selects applicable requirement identities; delivery proof establishes which exact bodies reached the active session. None implies the next. A package update may add discoverable opinions without adopting them.

### Producer manifest

Keep existing `selection.json` and the finite-profile schema unchanged. Add an optional versioned `standards.json` per package. Kit authors it from `.agents/standards/<plugin>.json`; the legacy employer repo authors `plugins/infonetica/standards.json` directly. Core owns the JSON schema and resolver; kit vendors the released schema and fixture version through its existing update mechanism. Schema changes require core/kit parity tests, not a separately authored schema copy.

Proposed `standards.json` fields:

| Field | Exact meaning |
| --- | --- |
| `schema_version` | Integer `1`; unknown versions/keys reject the opted-in manifest. |
| `package` | Exact catalog ID `marketplace/plugin`, bound to verified release bytes; it cannot self-assert another owner. |
| `contracts` | Map from canonical, non-alias skill slug to the record below. Identity is `package#slug`. Every referenced skill must ship. |
| `profiles` | Map from local profile slug to a nonempty unique list of fully qualified contract IDs. No profile inheritance or ordering semantics in v1. Cross-package members require catalog dependency closure and locked producer manifests. |
| `fact_definitions` | Optional map of owner-qualified fact names to existing v3 predicates. Reject cycles and unknown references. The reserved source facts below cannot be redefined. |
| contract `category` | Exactly `universal`, `technical`, `house`, `architecture`, or `technology`. Mixed-class bodies fail producer review. |
| contract `activation` | `applicable` for universal/technical and actual-technology guidance; `adopted` for house/architecture and selected abstraction choices. House/architecture cannot declare `applicable`. |
| contract `paths` | Nonempty list of repository-relative POSIX-path regexes; OR within this list. A path only narrows relevance, never establishes technology or architecture. |
| contract `when` | One existing v3 positive predicate, evaluated for the owning project/source using the source-ownership seam. Unknown/invalid evidence stays diagnostic-bearing. No arbitrary expressions, commands or code. |
| contract `depends_on` | Unique fully qualified contract IDs, same target scope. Acyclic. Dependencies on `adopted` contracts must already be explicitly selected; dependency closure cannot adopt an opinion. |
| contract `decision` | Optional shared decision key, allowed only on `house` contracts. Different contracts with that key require an explicit choice; technical/universal obligations cannot be suppressed this way. |
| contract `body` | Generated package-relative canonical Markdown path. The generator derives it from skill discovery; it is not user-supplied arbitrary filesystem access. |
| contract `resources` | Optional unique list of mandatory package-relative resource paths, default empty. Must ship in the same verified package; reject links, traversal and external URLs. |

Representative proposed authored record, before the generator adds `body` (new names are proposals, not current published IDs):

```json
{
  "schema_version": 1,
  "package": "dotagents/dotnet",
  "contracts": {
    "style-language": {
      "category": "technical",
      "activation": "applicable",
      "paths": ["(?i:\\.cs$)"],
      "when": {"fact": "dotnet"},
      "depends_on": []
    },
    "naming-fields-personal": {
      "category": "house",
      "activation": "adopted",
      "paths": ["(?i:\\.cs$)"],
      "when": {"fact": "dotnet"},
      "depends_on": ["dotagents/dotnet#style-language"],
      "decision": "csharp.private-field-naming"
    },
    "domain-ddd": {
      "category": "architecture",
      "activation": "adopted",
      "paths": ["(?i:\\.cs$)"],
      "when": {"context": {"key": "architecture", "contains": "ddd"}},
      "depends_on": ["dotagents/dotnet#style-language"]
    },
    "persistence-ef": {
      "category": "technology",
      "activation": "applicable",
      "paths": ["(?i:\\.cs$)"],
      "when": {"all": [
        {"dependency": {"kind": "nuget", "id": "Microsoft.EntityFrameworkCore"}},
        {"context": {"key": "adopted_suites", "contains": "data-access:ef-core"}}
      ]},
      "depends_on": ["dotagents/dotnet#style-language"]
    }
  },
  "profiles": {
    "personal-fields": ["dotagents/dotnet#naming-fields-personal"],
    "ddd": ["dotagents/dotnet#domain-ddd"]
  }
}
```

The reserved `dotnet` fact is true only for a source owned by a discovered `Project.kind == "dotnet"`; source path patterns narrow it to C#. Reserved `typescript` is true for `.ts`/`.tsx` sources owned by a discovered npm project, with unresolved ownership retained as a diagnostic. Actual React guidance additionally requires its npm dependency predicate. The existing predicate language is reused, but aliases such as current free-text `entity-framework-core` do not magically become facts: the producer must publish their exact predicate definitions or use explicit dependencies as above. A new record's package ID is checked against the actual marketplace/catalog; `dotagents/dotnet` is the existing namespace, while every new contract/profile name requires producer publication before consumer adoption.

Implementation mechanisms need a positive source-scoped declaration as well as actual dependency evidence. Reuse `adopted_suites` identities `data-access:ef-core`, `data-access:dapper` and `data-access:raw-npgsql`; use the source-ownership owner's proposed `StandardsContext.for_path` seam for narrow roots. An EF+Dapper project declares separate source subtrees when the mechanisms differ. A project's Npgsql reference alone does not mean its source uses raw-provider access. Omitted mechanism facts select no mechanism body; when a requested persistence task needs one, planning reports `unresolved-implementation` until that declaration is supplied. Do not fill the gap by filename inference. Declaring multiple mechanisms on one shared source accumulates their compatible requirements and reports semantic conflicts for owner resolution.

### Adoption, authority and conflicts

Use one `.agents/standards-context.json` **version 2** for consumer intent, retaining existing `dependency_evidence` and positive facets. Do not add a competing per-project selection file. New scope keys are `providers`, `profiles`, `contracts`, and `choices`; `root`, `house`, `architecture`, and `adopted_suites` retain their roles. All four new arrays default empty when omitted. Provider IDs must be in the capability lock. They activate the provider's applicable baseline in that scope; installation alone does not do so. The common base behavior already selected by the host remains compulsory and cannot be disabled through this file.

Existing capability locks already contain `required_skills`, `path_scopes` and `exceptions`; `bootstrap_capabilities.py:validate_lock` validates their package/skill coverage. Preserve those installation-verification inputs unchanged. The v2 resolver does not reinterpret a historical `required_skills` list as adoption of every opinion in those skills, and exception URIs do not become waivers. Migration explicitly maps intended requirements into context v2 and verifies the resulting selected skills are present in the locked package. An unresolved mixed skill in that migration requires an explicit choice, not silent expansion.

Each profile is `package#profile`; each contract is `package#skill`. The distinct fields remove ambiguity. Overlapping scopes union positive selections. House-facet conflicts continue to be diagnostics as in v1. No negative profiles, implicit parent cancellation or last-wins ordering. A provider cannot use a baseline to import another provider: cross-owner baseline requirements need that provider's explicit adoption. Empty arrays are valid and mean no additional adoption, not a waiver of requirements already in scope.

Proposed mixed-stack repository example (illustrative project paths and future contract IDs):

```json
{
  "schema_version": 2,
  "scopes": [
    {
      "root": "services/authz",
      "providers": ["dotagents/dotnet", "infonetica/infonetica"],
      "profiles": ["infonetica/infonetica#engineering", "dotagents/dotnet#ddd"],
      "contracts": [],
      "house": {"employer": "infonetica"},
      "architecture": ["ddd"],
      "adopted_suites": [],
      "choices": []
    },
    {
      "root": "services/authz/Persistence/Ef",
      "adopted_suites": ["data-access:ef-core"]
    },
    {
      "root": "services/authz/Persistence/Queries",
      "adopted_suites": ["data-access:dapper"]
    },
    {
      "root": "app",
      "providers": ["react-agents/react", "infonetica/infonetica"],
      "profiles": ["infonetica/infonetica#frontend"],
      "contracts": [],
      "house": {"employer": "infonetica"},
      "architecture": [],
      "adopted_suites": [],
      "choices": []
    }
  ],
  "dependency_evidence": []
}
```

Employer scope also requires its verified tier detection; writing `house.employer` cannot counterfeit employer authority. Selected personal contracts must be named separately. Shared technical baselines remain required within the adopted provider and actual language/framework scope. Higher-priority user/repository instructions still govern: the resolver is an auditable selection mechanism, not an authority to waive them. Detectable mismatches are errors; semantic contradictions are review findings. No claim of automatic understanding of arbitrary prose is made.

For private work checkouts, the employer-owned published registry may supply this same scoped document as an input layer, keyed by exact host/repository identity. A clone-local excluded file can add reviewed project facts. The resolver records both inputs and reports overlap conflicts; it never reads another checkout's private file. Do not commit personal agent settings to application repositories. A frozen review explicitly captures the allowed private input snapshot as a Git-private artifact; its hash enters the descriptor while its private content stays out of PRs.

Conflicts are resolved by explicit choice, not package order or "generic wins". A `choices` element is `{ "decision": "csharp.private-field-naming", "use": "infonetica/infonetica#naming-fields", "reason": "Repository convention requires underscore fields", "evidence": ["AGENTS.md"] }`. Its winner must be among selected, applicable candidates with that decision key. Evidence paths are nonempty, contained, existing repository files whose bytes are included in input hashes. A choice cannot suppress universal, technical, architecture or technology contracts, select an unadopted contract, or override a stronger instruction. Conflicting choices on overlapping scopes error even if one root is deeper. Compatible contracts without a decision key accumulate; distinct naming decisions remain independent.

Proposed conflict boundary in core `.agents/hooks/requirement_resolver.py`; `candidates` is an ID-keyed map of validated records after scope/prerequisite checks, and `choices` is the validated decision-keyed map after rejecting overlap duplicates:

```python
def choose_house_contracts(candidates, choices):
    selected = set(candidates)
    groups = {}
    for identity, contract in candidates.items():
        decision = contract.get("decision")
        if decision is not None:
            if contract["category"] != "house":
                raise ValueError("non-house-decision: " + identity)
            groups.setdefault(decision, set()).add(identity)
    for decision, choice in choices.items():
        if decision not in groups or choice["use"] not in groups[decision]:
            raise ValueError("invalid-choice: " + decision)
    for decision, members in groups.items():
        if len(members) > 1 and decision not in choices:
            raise ValueError("conflicting-house: " + decision)
        if decision in choices:
            selected.difference_update(members - {choices[decision]["use"]})
    for identity in sorted(selected):
        missing = set(candidates[identity]["depends_on"]) - selected
        if missing:
            raise ValueError("unsatisfied-contract: " + identity)
    return sorted(selected)
```

The CLI catches these errors and emits a diagnostic with code, affected path/project, input locator, owner and repair action, returning exit status 2 and no usable selection. The function illustrates the conflict/closure decision only; package/schema/predicate validation occurs before it. One implementation must not swallow a diagnostic and continue with a partial winner set.

### Resolution and consumer calls

Resolution is synchronous, offline and read-only. Proposed entry point: `python -B <engineering>/hooks/requirement_resolver.py resolve --root <checkout> --request <request.json>`. Request schema v1 contains `operation` (`plan`, `write`, `review`), `targets` (path plus optional exact `intended_project` and optional `concerns` list of owner-defined task identities such as `persistence`) and, for a proposed write, the proposed UTF-8 content. A concern requests a completeness diagnostic; it never selects a technology. Snapshot preparation owns reading files and constructing the facts graph; resolution cannot fetch, install, update hooks or infer adoption from discovery caches. Source-usage analysis beyond declared scope is not promised: planning/review must detect missing task declarations semantically.

Algorithm, in order:

1. Anchor at the nearest Git checkout before looking for configuration. Validate contained target paths, symlinks and explicit project identities. For an exported review tree, accept only the verified descriptor's supplied root, repository identity and input snapshot; never walk upward looking for Git or installed tables.
2. Verify capability lock, selected package commits/digests, manifest schema/owner and context version. Load only declared providers and their closure. Unselected installed packages contribute nothing. Include the already-authoritative base obligations independently of optional profile omission.
3. Use the existing project graph and the source-ownership owner's adapter to associate each target with projects. For a proposed file with ambiguous ownership require `intended_project`; linked existing sources evaluate every owning project. Multiple owners cannot be reduced by picking the nearest filename. A source shared across differently styled owners needs compatible outcomes or an explicit owner-approved source split.
4. Expand named profile members and explicit contracts exactly. Cross-provider selection requires that provider in scope; missing IDs/releases fail. Add path-relevant `applicable` contracts from each adopted provider. Ignore nonselected `adopted` contracts without evaluating their prerequisites, so unrelated optional metadata cannot block work.
5. Evaluate every candidate's `when` for that same source/project. For automatic candidates, proven false means inapplicable; unknown evidence means a blocking diagnostic for that candidate. For explicitly adopted, path-relevant candidates, proven false reports `unmet-prerequisite`; do not silently downgrade the adoption. Evaluate all predicate branches and retain diagnostics even if an `any` branch matched.
6. Expand same-scope dependencies in stable ID order. Missing or cyclic IDs error; an adopted dependency not explicitly in the adoption set errors. Validate dependency prerequisites and relevance; a dependency body can be required outside its usual routing paths, but never outside its semantic `when`. Apply house choices, then recheck every dependency is still present. Emit no successful result when any targeted scope has a blocking diagnostic.
7. Emit sorted requirements, selected/suppressed reasons, full provenance and diagnostic arrays. Deduplicate by `(source, project, contract ID, package digest, body hash)`, not bare skill name. Targets in distinct projects retain their own evidence. Planning over a set of intended paths uses the same operation; unknown future technology must be resolved before dependent code is called ready.

Resolution output schema v1 contains `checkout_id` (canonical worktree path plus worktree Git-directory identity; private, never committed), `inputs_sha256`, `targets`, `requirements`, `suppressed`, `diagnostics`, and `resolution_sha256`. Each requirement has full contract/package/commit/digest, owning project, target path, canonical body and mandatory-resource hashes, prerequisite evidence paths/hashes, adoption locators and any decision. Hash canonical JSON using sorted keys, UTF-8, compact separators and no timestamps. Hash raw body bytes separately. Material file content, intended-project declarations, context, registry, lock, manifest, fact inputs and resolver contract version enter `inputs_sha256`.

Current write and review boundaries are independent. Representative current code being replaced:

```python
def find_repo_root(cwd):
    base = Path(cwd).resolve()
    for candidate in (base, *base.parents):
        if (candidate / ROUTES_FILE).is_file():
            return candidate
    for candidate in (base, *base.parents):
        if (candidate / ".git").exists():
            return candidate
    return None
```

```python
route_table = root / ".agents" / "skill-routes.json"
if not route_table.is_file() or not paths:
    return [], []
```

The first excerpt is from `skill_router.py`; the second is the opening of `workflow_ops.py:route_findings`. Proposed root replacement and caller wiring:

```python
def find_repo_root(cwd):
    base = Path(cwd).resolve()
    for candidate in (base, *base.parents):
        if (candidate / ".git").exists():
            return candidate
    return None
```

```python
resolution = resolve_requirements(snapshot, request)
if resolution["diagnostics"]:
    return deny_resolution(resolution)
missing = required_body_reads(resolution, transcript)
if missing:
    return deny_unread(missing, resolution["resolution_sha256"])
return allow_write(resolution["resolution_sha256"])
```

```python
resolution = resolve_requirements(frozen_snapshot, review_request)
if resolution["diagnostics"]:
    raise WorkflowOperationError(json.dumps(resolution["diagnostics"]))
descriptor["standards_resolution"] = resolution
descriptor["rules"] = resolution["requirements"]
```

These are proposed call-site replacements, not existing callable APIs. `snapshot` is the verified package/context/project input defined above; `resolve_requirements` implements the seven ordered steps. `required_body_reads` is defined by the proof contract below. Deny/allow adapters keep each host's existing structured decision protocol. `review_prepare` must export the selected bodies/resources and private input snapshot into its immutable bundle, include their hashes in bundle identity, and give lenses that bundle. It must not hash only `.agents/skills/<name>` or consult a live plugin cache after freezing. Existing route deny-pattern checks remain a separate accumulated result and cannot be lost in this replacement.

For v2-adopted providers, generated routes use `{ "path": "(?i:\\.cs$)", "contracts": ["dotagents/dotnet#style-language"] }` where a path refinement is needed. This is a proposed versioned route format, not a new meaning for legacy `skills`. The resolver loads all applicable baselines even without a route table; routes may narrow optional task relevance but cannot activate an unadopted house/architecture contract or waive a baseline. Both checkout and published registry routes enter the same snapshot. Mixed providers may retain legacy skill routes temporarily; a legacy mixed skill for a migrated provider causes `legacy-mixed-route` instead of loading its unselected opinions.

Writes, planning and reviews need equal selected identities for equal input snapshots, not identical hashes across different source revisions. A changed manifest, context, proposed content or dependency input invalidates the old resolution before the next write. Review resolves the frozen final tree and compares recorded write evidence where available; an intentional standards change requires new resolution/read proof. Cached selections cannot make a later candidate inherit an earlier approval.

### Loading and proof

Current `transcript_skill_outcomes` accepts a matching skill-path suffix plus a body head or tail in a successful Codex tool result; Claude uses successful Skill invocation. This proves less than the desired exact-body contract, especially when a generated adapter merely points at canonical content.

Proposed packaged loader: `python -B <engineering>/hooks/requirement_loader.py --resolution <private-snapshot> --contract <qualified-id> --offset <byte-offset>`. It verifies snapshot/package hashes and outputs one JSON chunk of at most 8 KiB on a UTF-8 boundary: contract ID, canonical resource path, full raw-byte SHA-256, total byte length, offset and `text`. It serves only snapshot-declared bodies/mandatory resources. Mandatory resources are an explicit producer list; external reference links are advisory unless the producer packages an owned required resource. No runtime HTTP download counts as a pinned body.

The host adapter pairs a successful call to this authenticated shipped loader with its complete model-visible JSON result. It reconstructs contiguous bytes for each resource, checks length/hash against the resolution and binds proof to host session, current context epoch and input identity. A digest printed without text, an alias adapter, truncated chunk, path mention, failed read, another package's same slug, an unpaired result or stale package bytes is insufficient. Claude Skill invocation remains a discovery route; it must also establish canonical-body delivery. A proof receipt is derived from host transcript evidence, never a model-authored `read: true` flag.

Proposed core proof reducer after host-specific transcript pairing (`reads` contains only validated loader results from the current context epoch):

```python
def complete_body(expected_hash, expected_size, reads):
    chunks = {}
    for read in reads:
        if read["sha256"] != expected_hash or read["total_bytes"] != expected_size:
            return False
        offset = read["offset"]
        data = read["text"].encode("utf-8")
        if offset in chunks and chunks[offset] != data:
            return False
        chunks[offset] = data
    position = 0
    body = bytearray()
    for offset, data in sorted(chunks.items()):
        if offset != position:
            return False
        body.extend(data)
        position += len(data)
    return position == expected_size and hashlib.sha256(body).hexdigest() == expected_hash
```

Imports for this proposed module are `hashlib` and the existing transcript adapters; no code is executed from a returned chunk. The caller first partitions by contract/resource/session/epoch and authenticates invocation provenance. Compaction/resume invalidates proof unless the host establishes retained full-body context; where that signal is unavailable, re-read in the current turn and require its paired result. Missing transcript/host signals yield `proof-unavailable`, never an automatic allow. This establishes observable delivery, not a claim about human-like comprehension.

Do not inject a body on denial and mark it read without observing delivery. Disabled/untrusted hooks, hook-launch failure and specialized tool bypasses remain real host limits. Core cannot promise universal fail-closed enforcement where the host does not supply it. Qualification reports the exact supported tools/events; a successful Python unit test cannot close this gate. This design session changes no hook setting or trust state.

## Stack migration and kit necessity

| Current source body | Proposed owner split and concrete behavior |
| --- | --- |
| dotnet `contract/style/SKILL.md`: private fields have no underscore; `.editorconfig` enforces that convention | `style-language` retains only reviewed language/framework requirements. `naming/fields-personal` owns the no-underscore preference. An employer/repository `_context` convention therefore survives without editing the shared technical body. Classifying a preference as `technical` merely because an analyzer can enforce it is invalid. |
| dotnet `contract/naming/collaborators/SKILL.md` | Keep role contracts separate from optional house spelling. Preserve correct role suffix and allow a shorter subject where namespace/type context makes it unambiguous, as Tommy requested. `PermissionResolver` can be sufficient inside a clearly named authorization context; do not strip `Resolver` or change same-concept sibling subject words inconsistently. Reconcile the unpublished `Docs/CSharpNamingClarity` owner rather than duplicate its change. |
| dotnet `contract/logging/SKILL.md`: every message uses `[LoggerMessage]` in one `Log.cs`, inline calls prohibited | Separate library-correctness guidance from personal source-generation/file-layout choices and employer event-volume policy. Omitting the personal profile does not disable logging, select a log level or remove employer requirements. |
| dotnet `contract/domain/ddd` and `domain/values` | DDD requires explicit architecture adoption. Value representation defaults are a separate adopted contract; DDD must not silently imply every personal record/struct preference. Selected DDD applies under API paths too. |
| dotnet `contract/persistence` and `multitenancy` | Split actual EF mechanisms from the `IReadDbContext`/`IWriteDbContext`/`IDbContext` abstraction family and its repository mapping. Selected abstraction guidance requires both EF evidence and explicit abstraction adoption. Split tenant-isolation outcome from EF filter/context mechanisms; Dapper and raw-Npgsql implementations have their own bodies and exact dependency predicates. |
| react `contract/style`: `interface` preference and camelCase JSON alongside TypeScript guidance | Separate actual TypeScript/React requirements from personal syntax choices. Wire field names follow the adopted API contract; do not force camelCase over employer snake_case contracts. |
| react `contract/libraries/selected` and library-specific state/routing/UI contracts | Selecting React does not adopt TanStack Query, Zustand, zod, TanStack Router, Tailwind/cva, dayjs, axios, Vitest or TanStack Table. Actual library evidence may activate correctness guidance; choosing a preferred stack is an explicit profile. Employer MUI and shared React guidance can coexist without Tailwind adoption. |
| react `contract/testing` and `testing/frontend` | House test-authorization policy is separate from an explicitly adopted suite's technical contracts. Neither profile omission nor installation overrides the user's test request or employer guidance. |
| react `contract/domain-design` | Keep the empty knowledge/learning entry discoverable; publish no required domain contract until the owner agrees substantive rules. An adopted backend DDD profile does not create frontend DDD requirements. |

Dapper/raw-provider content is not present in the inspected EF body. Its owner must review proposed library guidance against official dependency-version documentation when that slice is designed; copying EF filters/interceptors into SQL rules is forbidden. The provider identities and isolation acceptance cases are decided here, while those new bodies remain a content-design gate. Do not label that content slice implementation-ready merely because its manifest shape is ready.

Kit change is necessary, but bounded. Existing `selection.json` gives discovery metadata and remains useful. Its current deciding emission is:

```python
"applicability": split_tags(skill["metadata"]["applicability"]),
"requires": split_tags(skill["metadata"]["requires"]),
"provenance": split_tags(skill["metadata"]["provenance"]),
```

These are dictionary entries inside the existing generator, not a standalone program. Add a standards-manifest pass after canonical skill discovery and before package emission. Proposed generator seam in the canonical `.py.in` template:

```python
source = root / ".agents" / "standards" / (plugin + ".json")
if source.is_file():
    manifest = load(source)
    validate_standards(manifest, plugin, ordered, dependencies)
    canonical_paths = {skill["name"]: f"skills/{skill['name']}/SKILL.md" for skill in ordered}
    for name, contract in manifest["contracts"].items():
        contract["body"] = canonical_paths[name]
    emit(f"plugins/{plugin}/standards.json", dump(manifest))
```

The path expression above is the kit generator's inspected existing payload mapping: `plugins/<plugin>/skills/<name>/SKILL.md` contains the full canonical body; repository `.codex`/`.claude` entries point to authored source. Core's own generated package layout differs, so core supplies its canonical destination through `.agents/plugins/sources.json`, never by applying kit's path expression to core. `validate_standards` uses the pinned core schema, exact package identity from native manifests/catalog metadata, unique canonical skills, profile/dependency reference integrity, acyclic contract dependencies and required-resource containment. Foreign references are checked against explicit locked producer fixtures in integration tests; unresolved foreign owners block consumer resolution, not unrelated package discovery. The generator must reject a `body` supplied in authored input, then validate its generated output shape. No source body, package dependency or host permission is inferred from string tags.

Add opt-in manifest/schema fixtures and homogeneous-skill guidance to kit's stack templates and conformance checks; old repositories without a manifest continue generating identically. New scaffolds ask for or receive the intended profile instead of assuming `provenance: house` is universally adopted. Release kit, then `kit:update` dotnet/react; regenerate adapters, payloads and indexes from authored sources. The legacy employer package needs schema validation and payload checking, not a forced kit-layout conversion. Any added helper/resource/hook updates its owning harness manifest and packaging map in the same runtime PR.

## Compatibility and rollback

The composition capability is opt-in by context schema v2 plus pinned compatible core/producer versions. A v1 context retains its existing behavior. An installed producer's new manifest does not opt a consumer in. Old names remain dated compatibility discovery aliases for at least one minor release; v2 resolution selects canonical split bodies and rejects a mixed legacy body rather than treating its alias as an all-profiles bundle. Publish an owner-maintained old-name/profile-to-new-IDs migration map; migration previews exact selected/omitted/conflicting contracts and requires explicit personal choices.

Within a migrated scope, do not run legacy and v2 enforcement for the same provider and combine their opinions. Versioned route generation replaces that provider's legacy rows atomically with adoption. Unmigrated providers keep their legacy route semantics, identified in the report; universal host/user instructions still apply. Unknown v2 schema, missing producer, unsatisfied dependency or unsupported core version blocks that opted-in scope visibly. There is no silent v1 fallback after a v2 failure.

Rollback restores the prior committed/excluded-input snapshot and exact package lock together, then regenerates matching routes/settings and starts a fresh host context. Keep the prior artifact set until fresh-host acceptance passes. A review made under the rolled-back selection is invalidated and rerun. Reverting metadata alone while leaving changed skill bodies or cached proof active is not a rollback. Package publication follows each owner's compatibility/version policy; proposed IDs are never put in live consumer files before the producer artifact is verifiable.

## Owner delivery map

This is the cross-owner dependency map, not another progress owner. After Tommy approves the direction, each owner places its concrete slice plan in its own repository, or updates its existing active owner. They link this shared contract; they do not duplicate its requirements. No sibling checkout is pre-created. Proposed branches start from the then-current fetched owner `origin/main`; no slice depends on this docs branch being its Git parent. Existing draft/dirty owners retain their actual bases and authority.

| Slice / owner | Code and test boundary, approximate size | Local prerequisite / delivery prerequisite | Consumption and gate |
| --- | --- | --- | --- |
| C0 core contract | Schemas, resolver result/request types, pure validation and fixtures; 6–10 files, 400–700 changed lines | Approved direction / core release before kit consumption | One versioned standards/context contract, with old-input parity and invalid-identity/predicate/dependency tests. No live adoption. |
| K1 kit producer support | Canonical template, schema vendor pin, generation/conformance tests, release metadata; 8–12 files, 350–600 lines | Exact C0 artifact / published core contract and kit release | Emits standards manifests with canonical paths; old repositories byte-stable. Test aliases, missing resources, cross-package fixtures and package identity. |
| D1 dotnet language/house split | Style/naming/logging bodies and manifest plus tests; 10–18 files, 400–800 lines | K1 artifact and naming-owner reconciliation / released kit | Preserves `_context` employer fixture and explicit personal logging selection. Publish migration map and verify identities in generated payloads. |
| D2 dotnet domain/data split | DDD/value/EF/abstraction/tenancy bodies, manifest and tests; 10–18 files, 500–900 lines | D1 shape, existing source facts / published producers | DDD under API; EF only where present; abstractions only when adopted. Dapper/raw content is a separate bounded follow-up after source-owner content review, expected 4–8 files each. |
| R1 react split | TypeScript/React, house, library and suite bodies/manifest/tests; 10–18 files, 400–800 lines | K1 artifact / released kit | Employer UI/API choices and omitted personal libraries/tests; no invented domain standard. |
| E1 employer composition | Authored employer manifest/profile contract, private registry inputs and tests; 5–9 files, 200–450 lines | D1/R1 exact artifacts; work-communications owner reconciliation / published shared contracts | Employer-scoped selection with explicit repository convention evidence; no application tooling PR. |
| C1 core scoped resolution | Integrate source-ownership seam, resolve scopes/predicates/choices, snapshot provenance and tests; 10–15 files, 650–950 lines | C0, source-owner contribution and exact D/R fixtures / source-owner release and published fixtures | Deterministic same-source result, linked-source ambiguity, unknown imports, negative cross-project EF tests. Preserve source owner's code ownership. |
| C2 core consumers and proof | Router, loader, review bundling, host adapters and focused tests; 10–18 files, 650–950 lines | C1 plus package provenance seam / published C1 and selected producers | Atomic caller/result integration: plan/write/frozen review parity, registry-only and nested-checkout tests, full body delivery checks. Never split a guard from its required caller/tests. |
| A1 host adoption | Isolated profile fixtures and receipts in owning host work; size from that owner | C2, E1 and hook-repair readiness / published packages and separately authorized trust/adoption | Fresh Claude/Codex unsupported/supported-path matrix and actual read-before-write evidence. Disabled normal profiles remain unchanged. |
| P1 planning/auto-merge owners | Existing base-to-engineering planning transition and configurable-auto-merge work | Reconcile their current plans / their own review/authority | Personal plan publication and work-repo holds tested separately. Auto-merge mechanism never supplies merge authority. |

Deliver ready slices sequentially by default; independent source-owner preparation can use immutable local artifacts without claiming publication. Reassess the split before a slice exceeds roughly 1,000 substantive lines or 40 files. Generated output, mechanical moves and docs are measured separately. A contract/caller/test atomicity exception needs its own recorded rationale. Review each actual owner PR and revalidate against the published dependency before merging its consumer.

## Acceptance matrix and implementation readiness

| Case | Required observable result |
| --- | --- |
| Installed package, no provider/profile adoption | Discoverable skills only; no optional personal injection. Already-authoritative common/user requirements remain. |
| Employer underscores; personal profile omitted | Shared C# technical bodies plus employer/repository convention; `_context` unchanged and personal no-underscore body absent. |
| Both field conventions selected | `conflicting-house`; explicit owner-supported choice selects one and records the other as suppressed. Profile order reversal has no effect. |
| Personal logging omitted | Personal single-`Log.cs` convention absent; actual library/employer logging requirements retained. No inference that logging should be disabled. |
| DDD selected in authz API source | DDD body required despite `Api/` path; personal value representation only if separately adopted. No DDD selection from a `Domain` folder alone. |
| EF service beside Dapper/raw-Npgsql service; EF and Dapper within one project | Dependency evidence plus positive source scopes select only each implementation. `Repository.cs` or a shared Npgsql dependency alone selects no mechanism. Linked-source conflicting ownership is explicit. |
| EF with no selected abstraction | EF baseline only; `IReadDbContext`/repository family absent. Explicit incompatible abstraction selection yields `unmet-prerequisite`. |
| React employer MUI and snake_case API | React technical contracts and employer choices; no Tailwind/Zustand/TanStack or camelCase preference from installation. Actual selected-library guidance remains scope-specific. |
| React tests/domain | User/repository test instruction preserved; adopted suite guidance selected by evidence. Empty domain-design skill contributes no invented obligation. |
| Unknown dependency/import/context or missing selected producer | Targeted actionable diagnostic; no partial successful resolution. An unrelated nonselected optional contract does not block. |
| Fresh nested worktree and registry-only routes | Uses its own checkout/explicit registry snapshot. Main checkout private table never leaks; write and review see equal requirements for equal inputs. |
| Same slug in two packages, changed source hash, alias-only read, truncated body | Proof rejected. Complete authenticated chunk delivery for every required body/resource permits supported writes. |
| Frozen review after cache/profile mutation | Bundle retains pinned inputs and body bytes; no live lookup changes findings. Later source/context changes need a new resolution/review. |
| Host hook disabled/untrusted, launch failure or unsupported write tool | Receipt reports unsupported/unqualified enforcement; no claim of universal blocking. No normal-profile hook changes during tests. |
| Legacy consumer and rollback | No-manifest/v1 fixtures preserve old output; opted-in failure never silently falls back. Complete rollback restores selection and invalidates proof/review. |

Producer fixtures are necessary but insufficient: acceptance must trace authored body → generated package identity → catalog/lock → adopted profile → scoped requirement → delivered complete body → supported write → frozen review. Capture exact package commits/digests, host versions, trust state, project/source evidence, expected/actual selections and allow/deny results. Fresh-host probes use disposable files and isolated profiles; record unsupported host events separately.

The schema, selection, conflict and delivery direction are concrete proposals for approval. C0/K1 and the established-body splits can enter their owner implementation-design reviews after approval. Source ownership and catalog composition remain integration dependencies, Dapper/raw guidance needs its owner's content design, and universal host interception remains an upstream limitation. None is hidden by a declaration of whole-refactor readiness.

Consequential decisions for Tommy: approve homogeneous skills with a separate structured manifest; choose shared technical baselines plus explicitly adopted personal profiles; accept explicit conflict choices rather than automatic employer/house priority; and authorize the ordered owner slices. First execution action after approval is to reconcile source-ownership/catalog/naming owners and author the C0 contract slice against these examples. Approval of this planning publication alone authorizes none of those runtime changes.

## Completion

All required source changes and personal owner plans land through their actual repository gates. Published packages and declared consumers agree on selection and both hosts provide the acceptance evidence above, or the unresolved host gate is explicitly recorded. No uncommitted source work or branch-only plan is represented as shipped. Remove the completed plan only when the entire outcome is terminal.
