---
name: skill-routes
description: Building a repo's `.agents/skill-routes.json` — the layered floor-plus-route model where every matching row fires and the floors always apply, why a row keyed on a top-level directory cannot port to a carved repo while one keyed on architecture ports verbatim, the row fields (path, skills, content_requires, note, deny), and the registry that ships a carved service repo's table inside the plugin instead of committing one per repo. Use when adding or changing a route, building a new repo's route table, carving a service repo, or deciding how to key a row's path.
domain: process
---

# Building a repo's skill-route table

`.agents/skill-routes.json` maps a path to the skills that must be loaded before that path is written.
`skill_router.py` reads it at write time and at review time; that mechanism, and how it is delivered, is
the `agent-standards` README, not this doc. This doc owns the other half: **how a repo's table is built**,
and why every carved service repo derives its own rather than copying one.

The table is per-repo data — a service repo's paths are not the monorepo's. But the *convention* the rows
follow is platform-wide, and left unwritten it is eight repos hand-authoring eight tables from no stated
rule, which is the copy-and-drift failure the whole corpus exists to kill, at repo scale.

## Every matching row fires, and the floors come first

The table is layered on purpose. The area floors and the layer routes always apply; a more specific row
below **adds** to them rather than replacing them. Routing on a filename suffix alone only ever covers the
names someone thought to enumerate — a `Mappers.cs` rule silently misses every `XMapper.cs` — so a file
shape nobody wrote a rule for still loads its floor. Prefer a row keyed on the layer or area a file lives
in; reach for a name-shaped row only to refine.

## Key a row on architecture, not location, or it will not port

This is the rule the cut turns on. A row keyed on **architecture** — the layer a project declares
(`\.Application/…\.cs$`), a type's role (`Repository\.cs$`, `DbContext\.cs$`), a test tier
(`\.UnitTests/…`) — means the same thing whether that code sits under `api/` in a monorepo or at the root
of its own service repo. It ports verbatim. A row keyed on **location** — a top-level directory
(`^api/…`, `^app/…`) — names a folder a carved service repo does not have, so it cannot port.

Only the two **area floors** are location-keyed, and they change in exactly one way: the monorepo anchors
them under `api/` and `app/`; a carved single-stack repo anchors its floor at its own root. Everything
else — the layer routes, every name-shaped row, and the meta rows (`^plans/…`, `^reviews/…`, an
`AGENTS.md`, a `TECH_DEBT.md`) whose directories exist in every repo alike — carries no monorepo path and
ports unchanged.

## A carved repo is registered here; it carries no table

A service repo commits no `.agents/skill-routes.json`. `.agents/gen_skill_routes.py` holds the registry of
which repo gets which kind, emits the registry plus one table per kind into `.agents/routes/`, and
`sync-generated.ps1` ships that directory inside the plugin beside the router that reads it. Adding a
service repo is one `REGISTRY` row; the repo itself needs only the marketplace wiring in its
`.claude/settings.json`.

```
python .agents/gen_skill_routes.py --emit-registry .agents/routes           # after editing REGISTRY
python .agents/gen_skill_routes.py --emit-registry .agents/routes --check   # drift check
python .agents/gen_skill_routes.py --kind dotnet-service --into <repo>      # a repo that wants its own
```

The router resolves the repo from its `origin` remote as `owner/name`, so a worktree and a fresh clone
resolve alike. A repo that does carry its own table still wins — that stays the escape hatch for a repo
whose layout the kinds do not describe. An unregistered repo with no table is unrouted, exactly as before.

The generator carries the canonical rows once, re-anchors the area floor for the kind, and drops the other
stack's rows. Kinds:

- `dotnet-service` — a carved .NET service: the meta and dotnet rows, the `.cs` floor anchored at the root.
- `dotnet-service-with-app` — the same, plus the react rows, for a carved service that also carries an
  `app/` node. The react rows already name `app/` mid-pattern, so they port to such a repo verbatim; only
  the TypeScript floor re-anchors. This does not decide the frontend seam — it gates the frontend a service
  repo demonstrably already has.
- `monorepo` — every group, floors under `api/` and `app/`; this reproduces the platform's own table.
- `react-app` — **not yet.** Whether a carved frontend repo keeps an `app/` node is gated on
  `POLYREPO_ROADMAP §6/§4c`, and the react rows carry `app/` mid-pattern, so generating one now would name
  paths that repo does not have. Decide the frontend seam first.

## The row fields

- `path` — a regex matched against the repo-relative POSIX path.
- `skills` — invoked before writing the file. Use `plugin:skill` where a generic standard and this
  system's roster share a name (`dotnet-standards:persistence` and `dotnet:persistence`): both load and the
  plugin says which is which. A name with one home stays bare.
- `content_requires` — an optional regex over the content being written; the row fires only when it also
  matches (a `.csproj` routes to the testing skills only when it declares `<IsTestProject>true`).
- `note` — shown when the row fires. For why a row exists, never for restating the rule it points at.
- `deny` — a content regex whose hit is a hard block, not a nudge. Only mechanically-decidable violations.

## Prove coverage, do not assume it

A table is complete when every tracked path in the repo matches at least its floor, and no row names a path
outside the repo. The generator's test replays a simulated carved tree through the real matcher and asserts
exactly that; `--check` re-runs the derivation against a repo's committed table to catch drift. A row that
matches nothing, or a floor that still names `api/` in a carved repo, fails there rather than silently
leaving a file ungated.
