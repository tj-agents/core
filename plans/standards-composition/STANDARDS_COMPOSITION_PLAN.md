# Scoped standards composition

Design status: discovery and requirements plan. The classification and acceptance cases below are settled; the producer schema and package migration are not implementation-ready until Phase 1 resolves them against the existing owners.

## Outcome

A project loads the standards it actually selects. Universal requirements stay compulsory within their stated scope. Employer/repository conventions, selected personal preferences, architecture and implementation technologies contribute separate, attributable requirements. Installing a package does not adopt every opinion in it.

The same resolved selection drives planning, first writes, review and generated host delivery. A successful implementation cannot be claimed from metadata, generated files or a tier announcement alone.

## Authorization and boundaries

Tommy requested work on the standards and their refactor on 2026-10-09, including repository plans that reach the personal repository's default branch even when implementation is unfinished. Planning publication is authorized. Implementation stays in the standards source repositories and proceeds only from resolved, reviewed design. This does not authorize application-code publication, changing live hook trust, enabling currently disabled hooks, or modifying another active writer's unfinished work. Infonetica retains its own commit/push/merge and private-tooling rules; personal plan publication must not be installed as work-repository authority. Continue this work in the current session; no automatic successor/handoff.

## Evidence and existing ownership

- Core PR116 merged project/dependency facts and standards context, explicitly deferring source ownership and host activation. The current `Feature/StandardsSourceOwnership` worktree contains uncommitted `source_facts.py`, tier/context changes and tests. Preserve that owner; inspect its state before integrating its contribution.
- Dotnet PR35 merged the generator and registered cris-authz. Current C# routes select style/naming; the Domain row selects domain-design but not its DDD/value owners. Repository filename rules select EF-specific persistence without matching its prerequisite metadata.
- Core's installed tier gate announces .NET applicability. Review lists tier conventions but does not prove semantic prerequisites were selected. `workflow_ops.route_findings` requires a checkout-local table, whereas the router can cross a nested worktree boundary to the main checkout's private table.
- The .NET style skill mixes language and personal choices under `profile: core`; its no-underscore preference applies to all C# in its current wording. EF persistence and tenancy declare technology prerequisites but also contain selected library and house assumptions. Split those decisions rather than relabeling their whole bodies universal.
- Kit already generates `selection.json` with profiles, applicability, requires and provenance. Treat this as an existing inventory to consume, not proof of an enforced resolver. Core already owns scoped context facets for house, architecture and adopted suites. Reuse their capabilities after identifying missing consumer behavior.
- `Feature/ConfigurableAutoMerge` has committed implementation and reviewed evidence but no PR. Its existing goal authorizes delivery through a draft PR, defaults omitted/false to disabled, and makes merge conditional on separate delivery authority. Do not claim it shipped or silently take over its writer.
- Engineering plans already require planning artifacts to land; base planning alone does not select that lifecycle. This selection/publication gap and the personal-versus-work boundary need explicit repair.

## Selection decisions

| Category | Selection | Owner |
| --- | --- | --- |
| Universal behavior/safety | Always within its explicit scope; a profile cannot remove a higher-priority user requirement | Core or the framework contract owner |
| Language/framework correctness | Actual language/framework applies, with no personal conventions mixed into the rule | Stack owner |
| House/employer conventions | Explicitly adopted profile; employer/repository resolves its own conventions | Personal or employer owner |
| Architecture | Explicit project adoption, such as DDD, not inferred from a folder name | Architecture contract owner |
| Technology implementation | Actual project/source prerequisites and adopted abstraction, such as EF Core, Dapper, raw Npgsql, or a selected data-access library | Technology contract owner |

Work-profile default under discussion: shared technical requirements plus explicitly selected personal conventions, rather than wholesale personal adoption. Tommy's alternative include/exclude preference is being requested; this is an assumption, not a confirmed choice. A logging example is not an instruction to disable logging. DDD's adoption in authz does not make every personal C# style opinion adopted there.

Select facts per project/source. EF Core in one service must not impose EF-specific tenancy on a Dapper or raw-Npgsql sibling. Tenant-isolation requirements may be shared outcomes where an actual owner requires them; filters, interceptors, SQL predicates and tenant context mechanics remain implementation-specific. Unknown/conflicting prerequisites are explicit diagnostics requiring resolution, not inferred technology adoption.

Employer and repository standards compose with selected shared standards. Resolve a conflicting house decision explicitly; emit its owner and selection evidence. Do not silently overwrite it with the generic package's convention. Broad skills mixing multiple selection classes must be separated so an employer can use shared technical guidance without adopting personal field naming or logging preferences.

## Delivery phases

### Phase 1: Resolve the taxonomy and publish the maintained design

Inventory core, kit, dotnet and employer contracts against actual source, distinguishing universal scope, technical prerequisites and house decisions. Read the existing composition, conditional-route, source-ownership and auto-merge owners. Resolve overlap and the exact selection schema, diagnostics and migration examples before declaring runtime work ready.

Consumption: each source owner receives one path-to-contract inventory and its own concrete implementation plan; the cross-repository plan records only dependencies and shared acceptance. Existing owned plans remain their single progress owners.

Gate: reviewed personal planning artifacts are merged to main; scope/ownership and plan graph pass. Later implementation-ready designs include current/proposed code at the deciding boundaries and tests for the cases below. Publishing this requirements plan does not mark the refactor complete.

### Phase 2: One scoped selection result in core

Complete or integrate the existing scoped project/source facts safely. Editing, planning and frozen review consume the same selected requirement identities, source hashes, prerequisite evidence and diagnostics, anchored to the actual checkout. Installation is separate from adoption. A nested fresh worktree must not accidentally inherit another checkout's live table or omit the profile review used.

Consumption: both host adapters, routes and review preparation receive the same immutable requirement resolution. Produce explicit read/delivery evidence before a required write.

Gate: core resolver/route/review tests prove matching selections, conflicting house decisions, absent profiles, unresolved dependencies, nested worktrees and missing load proof. Source tests alone do not qualify live host acceptance.

### Phase 3: Separate .NET contracts by real applicability

Split universal/technical C# guidance from personal house conventions and explicitly adopted DDD/value behavior. Give EF Core, Dapper and raw-provider contracts separate technology identities and finer selected-abstraction prerequisites. Separate tenant mechanisms by implementation. Do not invent Dapper guidance from EF guidance. Keep one canonical owner per rule and explicitly migrate published names/profile membership.

Consumption: generated selection inventory and routes express selected contracts and technology prerequisites, including DDD behavior under API paths. No EF library or personal style rule is selected solely by a filename or .NET presence.

Gate: dotnet tests cover EF-only, Dapper-only, raw-Npgsql, mixed projects, employer underscore fields, selected DDD under API, and omitted personal logging conventions. Published producer identity is verified before adopting it in consumers.

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

## Completion

All required source changes and personal owner plans land through their actual repository gates. Published packages and declared consumers agree on selection and both hosts provide the acceptance evidence above, or the unresolved host gate is explicitly recorded. No uncommitted source work or branch-only plan is represented as shipped. Remove the completed plan only when the entire outcome is terminal.
