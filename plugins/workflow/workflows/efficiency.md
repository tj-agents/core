# Workflow efficiency contract

This workflow keeps plan, checkpoint, validation, review, publication, and delivery safeguards while moving
routine orchestration into deterministic operations. Detailed command evidence lives in Git-private
artifacts. A model receives compact state only when it must decide something.

## Incident evidence

A September 2026 delivery of a very small mapping change used 468 model turns, 217 shell commands, 222
wait-related calls, 28 skill loads, 14 review agents, and four source-review waves. Completion consumed about
55.0 million input tokens, including 54.3 million cached-context replay tokens, plus 92,000 output tokens. A
model-owned `gh run watch` stayed attached for 5,269 seconds and failed after the workflow had succeeded. The
root context resumed 5 hours 40 minutes later, and a later monitor introduced another 72-minute continuation
gap. Its ledger described only Phase 1 in `## Next Steps` while the task name implied an entire migration, so
the execution boundary remained hidden.

The causes were architectural: shell calls acted as the workflow engine, successful logs entered model
context, remote waiting depended on a live foreground tool call, review invalidation followed base movement
instead of evidence movement, lens contexts inherited excess history, skill bodies were repeatedly loaded,
and plan scope was implicit.

## Enforced operations

`.agents/workflows/workflow_ops.py` supplies the shared command boundary:

| Workflow activity | Incident-era expectation | Enforced expectation |
|---|---:|---:|
| Routine repository inspection | Several independent shell calls | One `inspect` result |
| One validation command | Full successful log in context | One `run` result; zero success-summary lines |
| Unchanged remote state | Repeated model turns and polls | Zero model wakes |
| One remote wait | Foreground watcher plus poll calls | One exact-identity monitor and one terminal or transition wake |
| Small candidate review | Up to four waves and 14 agents | One wave with native review and only relevant lenses |
| Skill resolution | Repeated full-body reads | One lifecycle identity plus directly routed technical identities, cached by content hash |
| Delivery readiness | Many model-orchestrated reads | One `delivery-preflight` result plus bounded forge state |

The monitor writes repository, worktree, branch, head, target kind and ID, workflow, and attempt before its
first query. It reconnects to that identity, classifies long wall-clock gaps as suspended or offline time,
allows one live owner per identity, and emits only a material transition, terminal result, query error, or
bounded timeout. Direct `gh run watch`, ad hoc sleeping forge loops, and repeated unchanged model polls are
hook-blocked.

The command wrapper records command identity, duration, exit state, failing items, a bounded failure summary,
and the artifact path. It never returns successful test, migration, build, generator, CI, or package logs in
full. Both harness hook registrations route those commands through the same shared implementation.

Review preparation synchronizes once immediately before final review and freezes an exact-head descriptor,
binary patch, path set, materialized Git tree, identity manifest, routed rule hashes, and selected lenses.
The helper verifies those identities before reconciliation. Base-only movement requires another source review
only when candidate paths or routed rules overlap the new evidence. A changed candidate head always requires
review; the merge-group run remains the authority for the combined tree.

Every `## Next Steps` block states `Scope`, `Current slice`, `Remaining scope`, and `Done when`. The scope must
say either `whole plan through all remaining phases and terminal delivery` or `current slice only; full plan
remains incomplete`. The graph validator rejects an ambiguous handoff.

## Telemetry and limits

`budgets.json` defines soft budgets for model turns, total tool calls, uncached input, cached replay, output,
active execution, remote waiting, and suspended/offline time, with hard guards for wait/poll and skill-load
calls. The hooks additionally enforce zero model-owned forge watchers, one live monitor per identity, bounded
failure output, empty success summaries, one small-candidate review wave, and one read per unchanged skill
hash.

Repository code cannot enforce live token limits when a host does not expose current usage before each model
turn. In that case `telemetry` parses the host transcript and deterministically reports the breach at the next
checkpoint; it cannot prevent tokens the host has already consumed. The hooks enforce the observable proxy
limits inside this repository, while live pre-turn token refusal remains a host capability.
