# Codex-first lanes: stop burning Claude usage

Status: PR #148 merged, generated packages installed, and post-merge CI passed. Fresh Sonnet routing acceptance failed by implementing locally. Successor `Fix/CodexFirstLanesRuntime` is local and unpublished; its L4 review repairs passed all 40 router tests. Further live Claude tests are blocked pending explicit approval and available usage. The goal remains open.

PR: https://github.com/tj-agents/core/pull/148

## Authority

Tommy, 2026-10-08: "we need to do a Codex handoff so we never use Claude Fable"; "just because it's a
design doesn't mean it always needs L1"; "I have a lot more Codex use, so if we have to use L1 then we
should use Codex more often than not"; "how to make sure this is all fixed". This is also standing
standards-defect authorization. Implement, test, PR, merge, and update the installed plugins on both
hosts.

Checkout: `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-CodexFirstLanes`, branch
`Fix/CodexFirstLanesRuntime` from origin/main `6e2e2db3d1ad48e095ca5c2a9889f1cdfb92c8f5`. Do not touch `.worktrees/Fix-CloseEveryFinishedSession`
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

1. Checkpoint and incrementally review the local R2/R3 fixes using in-session Codex workers. R1's standalone launcher repair is independently accepted at `9a9e2bfea3b819f160f67b5ea87c684133d69dad`. The later fixes route active-goal completion, remaining-phase execution and delegated architectural review to Codex, and honor the explicit human choice `I want Claude to build this utility.` All 40 router tests and the scoped diff check pass, and generated candidates are refreshed. No further Claude model calls are authorized by the latest response: Tommy raised scarce subscription usage and billing concerns rather than approving the pending probe. Automatic approval review also rejected sending the candidate plugins and synthetic workspace to Anthropic without explicit payload/destination authorization. Keep that test blocked and stop its continuation after independent local work is complete. Resume only after later explicit approval and available Claude usage; then require actual Codex launch and child results before publication.
2. Causally linked post-merge CI run `37795175405` passed, including regeneration job `113372642356` and verify job `113372641549`. The generated commit is a direct child of landing commit `fa9f7400d939ba9cbf57048d2f94787aeaca864e`; primary checkout fast-forwarded with pre-existing files preserved.
3. Record actual acceptance evidence, pass the completion check, release the completed delivery and scheduler, then close this session (`finish.ps1` after a removable `cleanup_proof.py`).

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

Historical PR #148 delivery evidence follows; the current next action is in Next Steps above.
Implementation: `fe34217`, reconciled at `a3c82ff`; review repairs: `f1c9077`.
The first independent pass found a routed-lane plus model override gap and a stale bootstrap dependency
assertion. Both are repaired; this commit clarifies the matching launcher wording.
Main was integrated conflict-free at `ccf475b`, with base `73fb99c`; the measured branch delta was
23 files, 254 added and 61 removed lines, below the recorded split triggers.
After repair, lane tests (29), launcher tests (41, one skipped), shared CLI tests (77, eleven skipped),
and bootstrap CatalogTests (6) passed. Package-layout tests (19), harness checks and source generation
passed on the implementation. The initial full bootstrap capture was inconclusive; only the six
CatalogTests are claimed locally, with full-suite coverage delegated to exact-head CI.
Generated distribution files remain excluded from commits. PR #148 is body-validated and bound to
the published head with goal-scoped merge authorization. Initial CI run: `37768193063`.
Both incremental lenses completed through `40647ff`; two wording inaccuracies were repaired: later
model-precedence prose must exclude routed L1, and the Claude frontier rationale must not call Codex
the same model family. No further runtime finding. After the monitor's GitHub TLS query error, one
authoritative read established that CI run `37768193063` failed in shared runtime tests. L3 diagnosis
found two stale assertions: planning prose still expected the old wording, and the core-selection test
removed machine, now triggering engineering's dependency guard before its intended core guard. Repair
the prose assertion and explicitly omit engineering from that fixture, preserving its original error
assertion. No production change or suite retry is needed; run both affected test files before the push.

Continuation owner: `.agents/continuation/owner.json`, owner `40f69016a71a88938ffa279b`.
Current foreground Codex PID: `5400` (resumed session). The original PID `40480` no longer owns the goal.
The continuation had blocked on its stale initial head; its checked receipt/rebind and claim functions
reconciled it to `40647fff` and the existing PR binding. The 20-minute scheduler remains registered.
Bounded current worker: `finish_test_repair_l4`, in-session Codex L4, owns only the two affected test files.
The parent retains the goal and does no substantive implementation. No independent handoff was launched.
Tommy clarified that lanes should execute cheaper work inside this session; the parent model label stays
unchanged and its coordination still uses that model. The L4 role explicitly selects its cheaper model.
The first repaired planning assertion exposed another old phrase, `parent may delegate bounded work`;
review all assertions in that one test against the canonical policy before rerunning both test files.
After the next commit/push, refresh the delivery binding and checkpoint the same continuation owner with
its exact old/new head rebind before claiming foreground ownership again; do not leave its saved head stale.

Focused repair verification: the L4 worker completed both full affected test files with exit 0 through
workflow runs `pr148-process-standards-repair` and `pr148-repo-config-repair`; diff checks passed.
The planning test now checks the canonical parent-ownership sentence, and the core-selection fixture
keeps its original guard assertion while explicitly removing engineering.

Verified repair candidate `2e6596e3` is committed and published; remote branch and PR head match.
Final incremental review covers six paths from `40647fff`. CI run: `37784159382`. The same continuation
owner was checkpointed with the exact old/new head rebind and reclaimed by PID `5400`.

Base reconciliation at reviewed head `2e6596e3` found relevant catalog/harness changes in main
`8fb3c340` (six commits after `73fb99c`), so the merge gate requires integration. The L4 worker
`finish_test_repair_l4` owns that integration and focused validation. The earlier six-path repair
review is approved with no actionable source findings. No independent session was launched.

Integration commit `7527935d` merged exact main `8fb3c340` without conflicts. Catalog generation
and five focused test files passed; local generated output was restored to merge HEAD. The remote
branch and PR match the published head. CI run `37786854612` owns its full verification.

Both independent integration lenses completed with no actionable findings; the canonical review
watermark is `7527935d`. The L6 monitor is `0a506cc61bac81c4caa9f22ae77566130197e1694db192f97acaf4817fb7526d`,
with CI verify still pending and no observed failures at its seventh query.

Reconciliation defect diagnosed: latest main remains `8fb3c340` and is already an ancestor of
reviewed head `7527935d` (Git ancestry exit 0). `workflow_ops.review_reconcile` compares current base
with the incremental descriptor starting watermark `2e6596e3`, falsely calling already-incorporated
changes new relevant movement. No additional base integration is needed. This blocks the current
delivery, so the existing L4 worker owns a minimal helper/regression repair here. Compare only base
changes absent from the frozen reviewed head; preserve genuinely new relevant/disjoint movement and
head-mismatch checks. No independent session or broader workflow redesign is authorized by this repair.

Gate repair verification: `review_reconcile` now compares current base against its common ancestor
with the frozen descriptor head. Regressions cover incorporated base changes and later relevant
changes; existing disjoint-base and head-mismatch checks remain. Captured runs
`pr148-review-reconcile-base` and `pr148-review-reconcile-head` both exited 0; diff checks passed.
Baseline CI run `37786854612` completed successfully at `7527935d` (guard and verify passed).

Final correction `eaf28ed2` is published and verified against both remote branch and PR head.
Review scope is three paths from `7527935d`; CI run `37791368941`, verify check `113359329709`.

Installed verification: only user base/engineering/machine updated on both hosts. All six package trees
have exact generated-file membership and match after normalizing text line endings; raw digest differences
are Windows CRLF checkout conversion, not missing, extra, or stale content. Generated Git exports match
the catalog's raw digests. Installed Codex agent preview/apply/verify completed with 12 profiles verified.
Digest evidence: `C:/Users/TOMMYS~1/AppData/Local/Temp/pr148-package-digest-6ulb1uq8/result.json`.

Fresh acceptance is not yet established. The first alpha/ALPHA probe was too small to distinguish the
tiny-inline allowance. The ordinary multiphase probe then ran locally, but its launcher omitted `--model`
and inherited user `model=opus` (actual `claude-opus-5-5`), invalidating the intended cheap-host test.
Preserve that observation; do not claim a route passed. One corrected run uses the identical task,
explicit `claude-sonnet-5`, low effort, a $0.75 cap and a bounded runtime. No further prompt reshaping.

The valid corrected probe used Python argv transport, confirmed `claude-sonnet-5` at init and preserved
the entire ordinary multiphase prompt. It completed in 29.029 API seconds with a CLI estimated cost of $0.2316332, writing
`task_summary.py` and `test_task_summary.py` locally and running seven passing tests. No handoff,
subagent, Codex lane receipt, or Codex child result occurred. This is an observed acceptance failure;
the requested outcome is not complete. Evidence directory:
`C:/Users/TommySeery/AppData/Local/Temp/pr148-claude-codex-first-corrected-python-10ea7aa3de974db282eeeb6134878fea`.
Preserve `argv.json`, `init-metadata.json`, `probe-summary.json` and `claude-stream.jsonl`.

Billing clarification, 2026-10-08: the read-only native `claude auth status` reports `claude.ai`
authentication and a Team subscription; the current process has no `ANTHROPIC_API_KEY`,
`ANTHROPIC_AUTH_TOKEN`, or `CLAUDE_CODE_OAUTH_TOKEN` override. No extra usage or API billing was enabled
by this work. CLI dollar figures are estimated token costs, not evidence of an invoice. The earlier
probes consumed Claude usage; the organisation's existing extra-usage setting was not verified.
No further Claude model call was made for this check.
