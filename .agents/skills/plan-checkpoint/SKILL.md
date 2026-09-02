---
name: plan-checkpoint
description: Keep plan-managed work resumable with a compact current-state ledger updated only at material implementation milestones, genuine blockers or ownership handoffs, completed full reviews or important findings, final delivery transitions, and otherwise unsafe context endings. Covers the single-substantive-push model, ledger size warnings and compaction, GitHub-owned remote evidence, and review-artifact ownership. Use when one of those material transitions occurs or when reconciling an oversized or stale ledger.
domain: process
---

# The plan-progress checkpoint

A progress ledger is a compact recovery snapshot, not a workflow transcript. Update it only when durable
state materially changes and a fresh context could otherwise take the wrong action.

## When a durable update is required

Update the ledger for exactly these transitions:

- a material implementation milestone completes;
- a genuine blocker appears or clears, or ownership is handed to another context or worktree;
- a full review completes, or a materially important finding changes the implementation or next action;
- delivery, merge, publication, or final closeout crosses a terminal boundary; or
- the current context is ending with partial state that Git, GitHub, the plan, and review artifacts cannot
  reconstruct safely.

A local commit, push, commentary update, review stage, read-only preflight, CI poll, queue observation, or
temporary stop is not a checkpoint by itself. Do not rewrite the ledger merely because a workflow reports.
Unchanged blockers and repeated observations never create another checkpoint.

## Resolve the plan

1. Prefer an explicit `plans/*.md` input.
2. Inspect the current branch, worktree, status, commits, review artifacts, and PR, then correlate them with
   candidate plans and `_PROGRESS.md` metadata in that checkout.
3. Continue only when the evidence identifies exactly one plan. If none or several remain, finish the
   workflow normally without choosing or inventing one.
4. Use the ledger declared for that logical workstream. A legacy plan without one gets a labelled
   reconstructed baseline containing only facts supported by repository evidence.

## Keep one current snapshot

Reconcile only the sections affected by the material transition:

- worktree, branch, PR, ownership, and dependency or package gates;
- current state, including partial or uncommitted work that must survive context loss;
- `## Next Steps`, containing one resolved action or the standard blocker/paused fields;
- compact completed milestones, normally one item per phase or delivery gate with a commit or PR link;
- only the latest verification still valid for the current candidate;
- under `## Reviews`, only the current review type, artifact, watermark, and open/blocking disposition;
- decisions, failed approaches, blockers, and deviations that still affect execution and cannot be recovered
  cheaply from code or named artifacts.

Do not copy the plan, review findings, git log, CI job list, PR timeline, queue observations, chat summary, or
historical verification into the ledger. Link the owning commit, PR, run, or review artifact instead. Git and
GitHub own chronology.

The budget is **200 lines and 16,000 UTF-8 bytes**. `plan_graph.py` warns when either limit is exceeded. The
warning does not block urgent recovery work, but the next material checkpoint must compact the ledger before
adding more state.

### Compact an oversized or chronological ledger safely

1. Preserve the ownership header, partial work, one next action, active blocker/handoff, current review gate,
   latest valid verification, and decisions or failed approaches whose loss could cause a wrong action.
2. Replace copied evidence with links or identifiers for commits, PRs, runs, packages, and review artifacts.
3. Collapse completed work to one concise milestone per still-relevant phase or delivery gate.
4. Delete event logs, recent-transition logs, superseded verification, resolved findings, repeated remote
   observations, and narrative already present in the plan or Git history.
5. Re-read the result as a fresh agent and run `plan_graph.py`. If removing a fact would not change the next
   action or cause a costly failed approach to recur, remove it.

Compaction is a rewrite of the current snapshot, not a historical migration. Git retains the deleted text.

## Commit and push without a bookkeeping leg

Before the substantive commit that carries a material transition, update the ledger with evidence already
known locally and stage it in that same commit. Record the commit as `this commit`; never add a follow-up just
to replace it with its SHA. Natural local commits that do not cross a material transition need no ledger edit.

A plan-managed push has one leg:

1. choose a stable substantive candidate;
2. record its local `HEAD`, upstream, remote tip, outgoing range, branch, and PR head;
3. push once;
4. fetch and require the remote-tracking ref and any PR `headRefOid` to equal the recorded local head.

The equality check proves transport; it does not create another ledger entry. Remote CI, PR, queue, merge,
publication, and sync observations stay on their providers. Record them only in the next substantive commit
or the final closeout when they materially change the recovery state. Never create or push an
observation-only, ledger-only, review-only, or checkpoint-transport commit.

If a push fails, diagnose the cause and retain the exact known heads. Update the ledger only when the failure
creates a genuine blocker or context-ending state; do not push the record of the failure.

## Review state has one owner

The review artifact is the source of truth for ranges, staged coverage, findings, dispositions, security
review, and the reviewed-up-to watermark. The ledger records only the current review gate and a link to that
artifact. A staged review does not update the ledger per area: checkpoint only when the whole staged review
completes, a blocking finding changes the next action, or review ownership is handed off.

## Report and hand off

Reporting does not make a checkpoint due. Report from current evidence, and update the ledger first only when
one of the material triggers above applies.

When a context transfer is genuinely selected, make the ledger safe to resume and follow `handoff`'s
pointer shape. An actionable checkpoint does not itself require a transfer. Blocked and paused plans report
their owner, unblock action, and objective resume condition without replaying the blocked plan.

## The progress-ledger template

~~~markdown
# <Plan title> progress

- Plan: `<repo-relative plans/<epic>/<NAME>_PLAN.md>`
- Roadmap: `<repo-relative plans/<epic>/<EPIC>_ROADMAP.md>`
- Roadmap item: `<stable epic/slug key>`
- Worktree: `<current delivery worktree, or none>`
- Branch: `<current delivery branch, or next proposed Type/<epic>_<name>>`
- PR: `<number and URL, or not opened>`
- Dependency/package gates: `<state, or none>`
- Last reconciled: `<date and material evidence source>`

## Current state

<Only current operational truth and partial work that cannot be reconstructed safely.>

## Next Steps

<One resolved, self-contained action. If blocked, begin with `Blocked:`, `Blocked by:`, `Unblock action:`,
and `Resume when:`. If only a human decision remains, use `Paused: <who> — <action and objective condition>`.
For a deliberate context transfer use `Transfer:`, `Transfer to:`, `Resume stage:`, and `Resume when:`
lines so the provider can reconstruct the typed transfer. Never name merge as next until review is recorded.>

## Completed work

<One concise item per still-relevant milestone, linked to commit or PR evidence.>

## Verification

<Only the latest checks valid for the current candidate.>

## Reviews

<Current review gate and artifact link only; detailed coverage and findings stay in the review artifact.>

## Decisions, discoveries, blockers, and deviations

<Only facts whose loss could change the next action or repeat a costly failed approach.>
~~~
