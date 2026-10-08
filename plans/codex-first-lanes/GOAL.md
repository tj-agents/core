# Codex-first lanes: stop burning Claude usage

Status: implementation checkpoint `fe34217`; final policy reconciliation and focused validation precede review.

PR: not opened.

## Authority

Tommy, 2026-10-08: "we need to do a Codex handoff so we never use Claude Fable"; "just because it's a
design doesn't mean it always needs L1"; "I have a lot more Codex use, so if we have to use L1 then we
should use Codex more often than not"; "how to make sure this is all fixed". This is also standing
standards-defect authorization. Implement, test, PR, merge, and update the installed plugins on both
hosts.

Checkout: `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-CodexFirstLanes`, branch
`Fix/CodexFirstLanes` from origin/main e831904. Do not touch `.worktrees/Fix-CloseEveryFinishedSession`
(owned by the Codex tab "Core: close finished sessions"; its step 5 is superseded by this goal) or
`.worktrees/Fix-OutcomeVerifiedCompletion`.

## Defect (observed)

One Claude session on 2026-10-07/08 spent about 20% of Tommy's Claude usage on a bounded fix:
- It followed `engineering:lanes` and dispatched an in-session `engineering:lane-l1` design agent. On
  Claude, L1 resolves to `claude-fable-5/xhigh`; that agent used 166k tokens on a small design.
- An `engineering:lane-l4` implementer (245k) and a review lens (115k) followed, all on Claude.
- The contract says: "do not open an independent session solely to change model or cost". It also
  routes bounded work to in-session lane agents, which on a Claude host always spend Claude usage.
- Q1 "Design" sends any work that "decides how something should be built" to L1, so small mechanism
  choices land on the most expensive rung.

## Required outcome

1. **No Claude Fable by default.** No lane resolution, lane agent, workflow stage or handoff from a
   Claude session selects the Claude frontier/L1 model unless Tommy names it. L1 work from a Claude
   session goes to a Codex handoff (Codex L1).
2. **Codex-first for substantial work.** A Claude session routes multi-phase work, and any delegated
   design, implementation or review phase, to a Codex handoff by default rather than to in-session
   Claude lane agents. Claude keeps only tiny inline follow-ups and the conversation.
3. **Design is not automatically L1.** L1 is only for critical design decisions or big, complex plans.
   Require a concrete criticality or scale reason; architecture, data models, contracts and planning
   labels alone do not qualify. A small, bounded mechanism choice inside a fix runs at the fix's own lane.
4. Keep every-prompt policy text at minimum words (session-guidance, lanes summary).
5. Prefer a mechanical guard over prose: a test that no Claude lane agent or workflow pin resolves to the
   Fable model, and that the Claude L1 lane agent definition redirects to a Codex handoff.

## Next Steps

1. Finish the bounded L4 worker's policy reconciliation, package validation and checkpoint commit.
   L3 descriptions must allow bounded uncertain design; L4 must include small local design choices.
   Scope the no-handoff-for-cost rule to Codex, and keep the redirect body under canonical `.agents/`.
2. Freeze and independently review the candidate. Open its draft PR, own exact-head CI, repair any
   findings, and merge after the repository gates pass. Review and delivery use their selected lower lanes.
3. Update the installed plugins on both hosts and verify from a fresh Claude session that a design
   request routes to a Codex handoff without spawning a Claude Fable agent.
4. Close this session yourself when done (`finish.ps1` after a removable `cleanup_proof.py`).

## Selected design and execution checkpoint

The owner read the canonical lane, handoff, session guidance, packaging and generation contracts.
This checkout was fast-forwarded to origin/main `4ed911441448780d1fb8cea1560e213ee14c690b`
before implementation. Only this goal is owned here. No other worktree may be changed.

| Lane | Work worth that lane |
|---|---|
| L1 | Critical design decisions or big, complex plans with substantial interacting decisions; record the concrete criticality or scale reason. |
| L2 | High-stakes diagnosis or review involving production, security, migrations or stored data. |
| L3 | Open investigation or bounded design with unresolved alternatives requiring evidence and judgment. |
| L4 | Specified implementation and ordinary review, including small local mechanism choices within a testable fix. |
| L5 | Already-decided mechanical edits, configuration, docs and exact transformations. |
| L6 | Clerical loops or large input exceeding the floor's practical capacity. |
| L7 | Small clerical operations with no unresolved judgment. |

Tommy clarified during execution: L1 is for critical design decisions and big plans.
Design is L1 only when that concrete criticality or scale is established. Architecture, a data model,
a contract, a mechanism choice, or a plan document alone is not a reason to select L1.
Remove the unconditional L1 pin from plan-authoring and reconcile contrary examples.
Delivery operations never raise the lane.

Claude defaults to a full Codex ownership handoff for multi-phase work and before delegated design,
implementation or review, preserving the selected lane, canonical goal and one writer. It keeps
conversation and tiny inline follow-ups. An explicit user choice of Claude remains effective for
non-frontier work; Claude's frontier model requires an explicit user request naming that model/tier.
If Codex cannot launch, report the capability gate and preserve the checkpoint; do not silently
spend Claude usage on the substantial phase.

Claude L1 is a handoff dispatcher priced at the existing cheap full-context Claude routing setting,
with explicit Codex L1 handoff metadata and a generated redirect instruction. It never performs
L1 design locally. Keep the resolver's model/effort interface compatible; expose the handoff metadata
and make Claude lane-launch consumers reject that redirect with an actionable Codex route rather
than treating the local dispatcher model as a substantive L1 worker. The model tables remain the
single model-name owner. Existing Claude workflow pins already avoid the frontier model.

Mechanical guards cover every Claude lane model, generated lane agent, and workflow role/stage pin;
none may equal the Claude frontier model. Assert the generated Claude L1 agent returns a Codex
handoff to its parent and does no delegated implementation. Keep every-prompt routing text short.
Update the engineering harness manifest with the machine dependency now required by default routing.

Delivery slice: one atomic routing correction, its generated-agent logic, regression coverage and
shipped policy. These must ship together to prevent the policy and executable defaults disagreeing.
Reassess size at 1,000 substantive lines or 40 files. Generated distribution output stays uncommitted.

Implementation lane: L4, specified behavior with code-level judgment and regression tests.
Review lane: L4 (or the declared Codex review specialist). Delivery lane: L7 clerical operations;
use L6 for a sustained monitor. The L1 parent owns only design and synthesis, with bounded workers
applying implementation and review lanes.

Current next action: finish the L4 worker's reconciliation and validation, then freeze for review.
Implementation checkpoint `fe34217` passed 29 lane-table tests, 40 launcher tests (one skipped),
and 9 harness-manifest tests (one skipped). Source generation and declared dependency checks passed.
Shared CLI and source-layout checks are also required before the final review candidate is accepted.
Generated distribution files remain excluded from commits.

Continuation owner: `.agents/continuation/owner.json`, owner `40f69016a71a88938ffa279b`.
Foreground Codex PID: `40480`. Initialization, foreground claim and 20-minute scheduler registration
succeeded. Bounded implementation worker: `implement_lanes`, Codex L4. The parent retains this goal.
