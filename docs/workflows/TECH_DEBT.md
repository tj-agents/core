# Workflow runtime debt

## D001 — Configured routine design approval requires stack adoption

- **Kind:** debt.
- **Observed/reported:** 2026-10-12; a stack convention procedure reserved a routine decision despite the
  user's already-authorized scaffold work.
- **Impact and priority:** affected stack consumers can ask repeat approval questions; P2 because no merge,
  publication, permission, or active production harm is involved.
- **Source owner:** the affected stack source and its consuming repository; Core owns the shared setting and
  both-host context delivery.
- **State:** deferred.
- **Reason:** each convention owner must adopt the shared setting in its own contract.
- **blocked_by:** dependency.
- **Repair link:** [Core repair PR #219](https://github.com/tj-agents/core/pull/219),
  [repo-declared-config rollout owner](../../plans/repo-declared-config/REPO_DECLARED_CONFIG_PROGRESS.md), and
  [dotnet D001](https://github.com/tj-agents/dotnet/blob/main/docs/TECH_DEBT.md#d001-honor-configured-design-approval-across-agent-hosts).
- **Resolver:** each affected stack source and consuming repository owner.
- **Resume when:** a stack owner schedules adoption after selecting a Core release that understands the new
  key.
- **Next action:** update the affected convention contract and verify the selected installed Claude and Codex
  paths.
- **Resolution condition:** affected convention workflows honor the effective design value from
  `configuration.core.auto_approve` (`design` overrides `all`, with the flat alias supported only when
  the nested object is absent) for authorized routine choices, and both installed host paths are accepted.
- **Verification evidence:** Core source tests cover strict settings resolution and package-context delivery;
  installed-host acceptance remains pending.

## Recovery and delivery prevention gaps

The incidents and known causes are owned by [MISTAKES.md](../../MISTAKES.md), entries M001-M007.
Existing workflow standards did not prevent repeated ownership, authorization and evidence mistakes
in the 2026-10-11 sandbox recovery. Prevention work and a dedicated recording skill remain deferred.

Resolve when the shared workflows and applicable host adapters verify same-goal execution selection,
retained merge authority, supported continuation and reopening, accurate completion and recovery
claims, and state reconciliation after failed mutations. Record each incident's observed resolution
against its stable mistake ID. D002 records the later observed CI-waiter gap.

## D002 — Pending CI can be left with no launched background waiter

- **Kind:** debt.
- **Observed/reported:** 2026-10-12; after opening Core PR #230, the guard passed while Windows and Linux
  checks remained pending. The owner ended without launching a background CI waiter, a persistent-delivery
  continuation, or another background agent to own the exact PR head.
- **Impact and priority:** an authorized delivery can be stranded after local work completes; P1 because
  the user must rediscover the pending PR and resume its merge path.
- **Source owner:** Core engineering continuation and remote-delivery workflows.
- **State:** open.
- **Repair link:** [M003](../../MISTAKES.md#M003).
- **Next action:** make the delivery lifecycle launch and verify a background CI waiter when exact-head CI
  is pending, or persist a typed gate naming the resolver and observable resume condition.
- **Resolution condition:** both Core host-package paths prove that a nonterminal delivery is either
  actively foreground-owned, has a registered and verified background waiter or agent through the next
  delivery action, records a typed external gate with a resolver and observable resume condition, or is
  terminally closed. No Core consumer may leave a nonterminal delivery idle without one of those states.
- **Verification evidence:** PR #230 on `Fix/ContinuationStopBindingHead` was open at
  `2173ae76ab0fd1e042ae0f414c95dc1f67ff5fcb` with `verify-windows` and `verify-linux` pending; no
  background CI waiter, continuation, or background agent had been launched before the session returned.

## D003 — Incident records are routed through ordinary PR delivery

- **Kind:** debt.
- **Observed/reported:** 2026-10-12; this session put the mistake and debt records for its own workflow
  failure into PR #231 instead of committing them directly to `main`, adding an unnecessary review/CI wait
  before the shared record was available.
- **Impact and priority:** P2; a corrective record can remain unsynchronized while its source failure is
  already known, and it creates avoidable background delivery work.
- **Source owner:** Core problem-record and delivery conventions.
- **State:** open.
- **Repair link:** [M014](../../MISTAKES.md#M014).
- **Next action:** make `write-mistake`, `write-debt`, and the callout-repair path commit and push incident
  records directly to `main`, while keeping ordinary implementation changes on their normal delivery path.
- **Resolution condition:** a new incident record is committed directly to `main` without a PR, and both
  host-delivered conventions make that direct-main route explicit for mistake and debt records.
- **Verification evidence:** PR #231 was opened solely to carry D002 and M014 before Tommy corrected the
  delivery route.
- **Repeated 2026-10-13, now P1:** a Claude session made a worktree and PR #243 to carry D004, D005 and a
  machine incident, and Tommy corrected it again. The records moved straight to `main`, and #243 was closed.
  The primary checkout was dirty with another session's work, so a direct-to-main route also needs a way to
  land a record without touching that checkout.

## Slice retirement checks the broader goal's completion

The runtime's `checkpoint --state complete` calls the canonical goal's full completion check, even
when its bound slice PR is merged and a workflow handoff records a pending successor. This conflicts
with the documented foreground slice transition: the owner cannot complete while the broader goal
correctly retains unfinished acceptance. A foreground parent can retire the merged slice's scheduler
and binding, preserve its blocked owner receipts, and initialize the next slice against the same goal.

Resolve when slice retirement verifies its exact merged PR/head and handoff without declaring the
broader goal complete, and tests preserve pending successor acceptance across the foreground transition.

## PR preflight misclassifies an incremental review base

`delivery-preflight` passes its final incremental review descriptor to `review-reconcile` against `origin/main`. An incremental descriptor's base is the prior reviewed commit, so an unchanged `origin/main` can be reported as `base-changed-relevant-evidence` when the prior commit touched a path in the incremental pass. The core Windows hook PR reproduced this false blocker; preparing a cumulative base-to-head descriptor let preflight verify the already reviewed chain.

Resolve when preflight reads the canonical work order's continuous completed review passes, reconciles the original remote base against the full reviewed path and rule set, and tests an incremental pass with unchanged, disjointly moved, and relevantly moved remote bases.

## The strategic workflow stage is pinned below planning's lane

L1 now owns planning and design, but the workflow contract's `strategic` stage (architecture, major planning) is still derived from L3 in `.agents/workflows/hosts/*.json` and `STAGE_LANES`. Draft #39 repins the same stages for Codex, so the two changes would collide.

Resolve when `strategic` is derived from L1 on both hosts, `STAGE_LANES` and the host pins agree, and the workflow contract tests pass.

## Non-review workflows run helpers from the reviewed repository

The review family resolves `workflow_ops.py`, `tier_gate.py` and `docs_reachability.py` from the installed
engineering plugin root, so it runs in a repository with no `.agents/`. `plan-execution`, `feature`, `bugfix`,
`merge`, `merging`, `open-pr`, `pr-preflight`, `remote-validation` and `persistent-delivery` still name
`python .agents/workflows/workflow_ops.py`, which exists only inside core.

Resolve when each of those skills names `<engineering>/workflows/workflow_ops.py --root <repository-root>`
and the `test_review_native_layer.py` repository-helper check covers them.

## Workflow skill resolution still assumes the former flat layout

The `skills` operation defaults lifecycle names to `.agents/skills/<name>/SKILL.md`. Core now owns `feature` under `.agents/engineering/workflow/feature/`, so recording the lifecycle by name fails before producing its identity record. This predates the Sol 6.1 update and is independent of lane resolution.

Resolve when lifecycle discovery uses the canonical scope/kind layout and regression coverage proves `skills --lifecycle feature` records the shipped owner in both source and installed package layouts.

## Codex keeps a merge-cleanup obligation after a failed merge

`merge_cleanup_gate.py` records its obligation at PreToolUse, before `gh pr merge` runs. Claude reports a
failed merge through PostToolUseFailure and never blocks Stop on an unconfirmed obligation, but Codex has no
result event, so after a failed or rejected merge it nags once every 10 minutes until `--clear` or the
7-day reconcile drops the obligation.

**Resolution condition.** Codex publishes a tool-result or failure event that hooks can consume; wire the
gate's failure handler to it and delete the obligation when the merge reports no success.

## Review routing requires the write-time opt-in

`review-prepare` names the skills a review owes only through `.agents/skill-routes.json`, and carrying that
table also opts the repository into the write-time router and the red-run gate. The router blocks every
write while any routed skill is unresolved or plugin discovery fails. Core therefore carries no table, so a
review of a changed `SKILL.md` is not required to load `engineering:skill-authoring`; the description and
`AGENTS.md` are its only discovery.

Resolve when a route can apply at review time alone, without opting the repository into write-time routing
or the red-run gate, and core routes authored `SKILL.md` paths to `engineering:skill-authoring` through it,
with a test that `review-prepare` names the skill for such a path.

## D004 — The merge cleanup gate demands session exit after every merge, even mid-goal

- **Kind:** debt.
- **Observed/reported:** 2026-10-12 to 2026-10-13. A Claude coordinator session merged several PRs across
  azure, dotnet and core while the goal still had authorized work left.
- **Impact and priority:** the Stop hook re-blocked every 10 minutes for about a day. That covered azure #1,
  whose worktree had been removed on 2026-10-12, and later merges. The repetition buried real status in
  noise. P2: there's no harm to data, but it costs user attention on every turn.
- **Evidence:** `hooks/merge_cleanup_gate.py`.
  - `handle_stop` blocks while `session_exit_required` is set or the worktree exists.
  - `cli_clear` sets `checkout_retained` and `session_exit_required = True`, so `--clear` on a removed
    worktree never releases the block.
  - This contradicts `engineering:session-guidance`, under which only a terminal goal closes its own session.
- **Source owner:** core engineering hooks.
- **State:** open.
- **Next action:** stop blocking when the obligation's worktree is gone, or recorded as retained, and the
  session's canonical goal still has authorized remaining work. Keep session exit required only at the
  terminal merge.
- **Resolution condition:** a hook test where a coordinator merges two PRs from different worktrees, removes
  both, and keeps working. Stop doesn't block after removal, and still blocks at the goal's terminal merge.

## D005 — The continuation stop hook judges the launch checkout without checking its owner

- **Kind:** debt.
- **Observed/reported:** 2026-10-13. A Claude session launched from a directory where another session was the
  writer was judged on that checkout's state.
- **Impact and priority:** the Stop hook blocks on another owner's work. P3.
- **Source owner:** core engineering hooks (`continuation_stop.py`).
- **State:** open.
- **Related:** core PR #230 (binding `head` versus `remote_head_sha`).
- **Resolution condition:** `continuation_stop` evaluates only checkouts this session owns, as its registry or
  lease records them, with a test where a foreign-owned launch directory doesn't block Stop.

## D006 — A noticed problem can be parked outside its owning ledger

- **Kind:** debt.
- **Observed/reported:** 2026-10-13. A Claude coordinator noticed two hook defects (now D004 and D005) and
  wrote them only to a private host notes file. It cited the session limit as a reason to defer. The core
  ledger got them only after Tommy said "note it down". The `close.py` failure, the D003 repeat and a
  dotnet M003 were likewise recorded only after his callouts.
- **Impact and priority:** P1. Known problems stay invisible to other sessions and to the source owner, and
  Tommy has to prompt for every record.
- **Cause:** `engineering:session-guidance` ("Record noticed problems") says to record while the observation
  is available, but nothing enforces it. Recording was conflated with repair: being unable to launch a
  repair session was treated as a reason to postpone the record.
- **Source owner:** core engineering (session guidance, `write-debt`, `write-mistake` and the callout-repair
  gate).
- **State:** open.
- **Next action:**
  - state that a record lands in the owning repository's ledger, straight to `main` (D003), at the moment
    of noticing, whatever repair capacity there is;
  - add a gate that blocks a terminal report while the session has noticed a problem without recording it.
- **Resolution condition:** in a hook test, a session that observes a defect and then tries to finish
  without a matching ledger entry on `main` is blocked, and recording the entry releases it.

## D007 — An agent idles on a background test run instead of continuing the authorized work

- **Kind:** debt.
- **Observed/reported:** 2026-10-15. After focused tests passed on a slice, the agent started the full
  `.agents/hooks/tests` and `tests` suites in the background and ended its turn to wait for them, with
  further authorized slices unstarted. Tommy: "u can walk and chew gum right ... run those individual tests
  (definitely not all if its incremental) ... but then continue with the work? note that down as a fix".
- **Impact and priority:** P2. Wasted wall-clock time and repeated prompts; the full suites take over ten
  minutes and block nothing the next slice needs.
- **Cause:** `engineering:plan-execution` says a phase boundary is not a stopping condition but does not say
  that a pending background check is not one either, nor which tests an incremental change should run.
- **Source owner:** core engineering (`plan-execution`, `failing-tests`).
- **State:** open.
- **Next action:**
  - state in `plan-execution` that a slice runs only the focused tests for the paths it changed, in the
    background when slow, and the agent continues with the next authorized work while they run;
  - leave the full suites to CI and to a change that is broad enough to need them;
  - make the focused-test selection discoverable (a changed-path to test mapping) so the agent does not
    guess.
- **Resolution condition:** the `plan-execution` text carries the rule and a session that has a background
  check pending is not blocked from, or reminded to stop before, starting the next slice.
