---
name: update-roadmap
description: Reconcile a decision, requirement, dependency, package release, or upstream API change across the default branch and active branch-owned roadmap, plans, and progress ledgers, updating only the owning level of each graph and never creating metadata-only synchronization pushes. Planning docs only; do not implement the change. Use when a change set must propagate through an epic.
domain: process
---

# Reconciling a change across a roadmap and its live plans

Update the complete live ROADMAP → PLAN → PROGRESS graph from one authoritative change set — a decision,
requirement, dependency, package release, or upstream API change. Planning docs only; do not implement
the change.

## Workflow

1. Resolve the target roadmap and the change set or source. Ask only when more than one roadmap plausibly
   owns it. Verify compatibility-sensitive claims against the named upstream source, release, package, or
   baseline when available.
2. Read the repository's root instructions, its plan floor (`plans/AGENTS.md`), the `plans` and `handoff`
   standards, and the roadmap. Read the repository's architecture doc — the one its root instructions
   name — for cross-service impact.
3. Inventory the default branch and every active worktree/PR that may own a plan under this roadmap. An
   active delivery branch owns its plan and ledger; the current default branch owns shared planning state
   that has already landed. Run `python .agents/hooks/plan_graph.py --root <absolute-owner-worktree>` for
   each target owner and reconcile declared branch/worktree/PR metadata with Git and GitHub. Include
   reserved, blocked, delivery-gated, and in-flight plans. Never substitute an older copy from another
   checkout for the active owner's copy.
4. Before editing, classify every change against every live plan as `roadmap`, `plan`, `ledger`, or
   `none`. Follow semantic dependency usage, not filename or keyword matches. Keep the reasons for
   every `none` classification for the final coverage report.
5. Preflight every owning tree before the first write. Preserve unrelated dirty planning files and never
   stage them accidentally. A dirty target roadmap, plan, or ledger owned by another active change is a
   collision, so stop before producing a partial reconciliation.
6. Update only the owning level:
   - roadmap: shared scope, ordering, status, invariants, and dependency map;
   - plan: design, phases, gates, verification, and definition of done;
   - ledger: current evidence, blockers, handoffs, verification validity, and one resolved next step.

   Replace stale assumptions instead of appending release-note history. Do not add roadmap citations
   to plans. Do not change product code, packages, generated baselines, tests, or runtime configuration.
7. Re-read each changed owner graph as a set, search for obsolete versions/API terms, and run
   `plan_graph.py` once per owner. A standalone shared planning change may use one path-scoped docs-only
   commit and the `docs-review`/`merge-docs` procedures. A material update to an active delivery ledger
   rides that branch's next substantive commit; do not push a metadata-only synchronization commit.
8. Report the source evidence, changed artifacts, justified `none` classifications, validation, and
   commits. Follow the `handoff` standard for each explicitly targeted actionable or blocked ledger.
