# Full model and effort lane map

## Outcome

Define one policy-owned four-lane map for Claude and Codex, route both handoff skills through it, and
mechanically reject literal model selections in skills, scripts, workflows, and launch commands.

## Constraints

- The machine policy in `~/.claude/routing/policy.json` remains the only model-to-lane mapping.
- Resolver output remains data-driven: every lane field flows through without resolver changes.
- The frontier lane requires explicit provenance and cannot be inferred from ordinary design inputs.
- Shared hook and CI logic has one owner in this repository and ships through generated plugin payloads.
- Authored files live under `.agents/`; generated mirrors are updated only by `sync-generated.ps1`.
- The PostgreSQL migration, standards reachability, and `Concertable/docs/plans/launch/` are untouched.

## Phase 1 — Policy and written map (complete)

Change the machine policy to expose Claude and Codex selections for four lanes, with a frontier lane
selected only by an explicit authorization parameter. Rewrite `ROUTING.md` so each lane has one clear
purpose and parameter provenance is unambiguous.

Verification gate: exercise representative resolver inputs for every lane and prove ordinary open design
inputs cannot select the frontier lane.

Consumption contract: callers receive the unchanged resolver object with lane metadata plus harness-specific
model and effort fields copied directly from policy data.

## Phase 2 — Routed handoffs and enforcement (complete)

Make both authored handoff skills declare task parameters, resolve immediately before launch, and pass the
relevant returned values to their dumb launchers. Add one shared PreToolUse/CI guard which rejects literal
model or effort assignments while allowing variable-backed resolved values and policy documentation.

Verification gate: focused unit tests cover both harness payloads, allowed resolved-variable forms, rejected
literal forms, and repository scanning; generated-file verification is clean.

Consumption contract: both harness manifests invoke the same hook mechanism for write and shell tools; CI
invokes that mechanism in repository-scan mode.

## Phase 3 — Review and delivery

Commit the coherent implementation, run the repository review workflow, address findings, complete all
required validation, push once, open a GitHub PR, wait for green CI, and merge it.

Verification gate: local full CI-equivalent checks and exact-head GitHub checks are green, and the PR is
merged.
