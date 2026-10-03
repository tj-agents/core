# Critical-plan execution handoff

## Goalpost

For large critical plans, establish a distinct planning/readiness responsibility that produces a concrete execution handoff and actually transfers it to an accountable execution owner. The user should not have to rewrite prompts, restate the goal or keep telling executors to continue. The agent preparing the handoff must evaluate readiness and initiate the authorized transfer; producing a prompt alone is not completion. Preserve the useful existing single-owner/in-session path for small and medium work.

## Identity and ownership

- Repository: tj-agents/core; branch Feature/CriticalPlanExecutionHandoff.
- Checkout: C:\Users\TommySeery\source\repos\tj-agents\core.worktrees\Feature-CriticalPlanExecutionHandoff; fresh fetched origin/main base 6c7f365bbc1ec665f0901f92937543d3f890f8c7.
- Owner: current Codex session in the recorded checkout; pickup acknowledged 2 October 2026 after reading the goal and verifying branch/base identity. No second execution owner.
- PR: not opened.
- Related continuation owner: C:\Users\TommySeery\source\repos\tj-agents\core.worktrees\Feature-DefaultGoalContinuation\plans\default-goal-continuation\DEFAULT_GOAL_CONTINUATION.md.
- Primary scope: selected planning/readiness and execution-transfer contracts: plan-authoring, plan-execution, plans/checkpoint, handoff/handoff-format and the necessary base plan-artifacts fields. Associated tests belong to this owner.
- The other owner exclusively owns base continuation policy, persistent-delivery/persistent-workflow, scheduler/job lifecycle and host wake behavior. Use its existing completion/ownership contract through references. Do not create another scheduler or autonomous delivery engine. Machine launchers remain the existing transport; propose any necessary shared transport changes to its owner.

## Authority and boundaries

Tommy explicitly requested these two handoffs on2October2026, conditional on the predecessor agreeing; the predecessor agrees with the scoped reasoning. Implement the standards and their supported behavior, not just a proposal. Local source edits, validation, logical commits and draft publication are authorized. Merge, ordinary consumer/profile installation, enabling a scheduler on a live product checkout, and unrelated product changes remain outside this grant. Temporary isolated acceptance probes are allowed when supported and must clean up only their own resources. Preserve all other owners and never edit installed plugin caches. The B2B #42 successor continues independently; do not adopt or modify its source, plan, binding or jobs. No second agent owns either new checkout.

Core owns base behavior, engineering workflows and machine utilities. Read AGENTS.md, README.md, SOURCE_LAYOUT.md and PACKAGING.md. Canonical authored inputs are .agents/ plus genuine host adapters; plugins/* is generated. Use the supported catalog/generator/check pipeline and relevant tests. Source generation is not proof that users' installed hosts adopted the change. Distinguish implementation, publication, installation and actual host acceptance.

Launch lane: L1 for the bounded design decisions. Once decisions are documented, route specified implementation, tests, review and clerical work to the cheaper appropriate lanes while retaining one accountable owner. Never use a highest-tier session for all phases by default. A massive design phase can launch exactly one execution successor after readiness and a durable checkpoint; small/medium work should normally continue with in-session delegation. Do not launch sessions just to change model. Continue the authorized work to its completion condition without routine permission or keep-going questions; stop only at a real dependency, capability, budget or authority boundary and record its concrete resume condition.

## Evidence to inspect

Current engineering lanes already distinguish design from implementation, support in-session delegation for smaller plans, and recommend a fresh execution harness after a massive substantive design phase. Handoff already requires one actual launcher submission and preserves canonical pointers. The gap to investigate is whether critical-plan readiness, goalposts, ownership transfer, verified pickup and automatic execution are sufficiently defined and reached by the real host path, not whether another prompt template can be invented.

B2B exposed changing explanations, fragmented ownership, long repeated validation, stale plan state, and follow-up packets that were mistaken for active work. The latest B2B continuation owns that source; use recorded evidence read-only. An existing launcher receipt proves submission, not acknowledgement or progress. A separate prompt-preparing agent must add readiness evidence rather than acting as a permanent middleman for every trivial task.

Existing core plan and handoff ownership repairs and PRs #32/#58 may already cover part of this. Read current source/owner artifacts and keep the smallest compatible correction. Do not overwrite dirty main plans or active other checkouts.

## Completion expectation

A clear scalable critical-plan readiness/transfer convention, supported discovery/host path, meaningful acceptance tests, independent review and a verified draft delivery. A large authorized critical plan must move from accepted design to one accountable executor without a further user go-ahead; a planning-only request must still stop at its authorized planning outcome. Prompt-only requests remain prompt-only.

## Next Steps

Scope: whole plan through all remaining phases and terminal delivery within the explicit draft-only grant.
Current slice: review the implemented readiness/transfer correction and publish its verified draft.
Remaining scope: independent review, exact-head CI, verified draft publication and the gated authenticated launcher acceptance.
Done when: the assessed correction is reviewed, validated and published as a draft; merge and ordinary installation remain outside the grant.

1. Commit the focused-green candidate and complete independent immutable review, repairing concrete findings.
2. Publish this assessed slice as a draft and own its exact-head CI to a terminal result. Keep the continuation integration seam documented below; merge and normal-profile installation remain outside the grant.
3. Authenticated independent launcher acceptance requires explicit approval of its isolated credential/profile setup after automatic approval review rejected that exact action. Do not retry or substitute a normal-profile refresh. Existing actual in-session pickup evidence is separately recorded below.

## Current checkpoint

- Ownership and authorization reconciled against the supplied handoff and this checkout. Fetched origin/main remains 6c7f365bbc1ec665f0901f92937543d3f890f8c7; the branch is not behind.
- Measured candidate: 525 helper/test additions, 163 instruction/template changed lines, 8 catalog/manifest changed lines, the canonical goal, and 1,217 generated changed lines across 18 output files. The runtime and its invocation contract form one atomic correction; no separate concern or stack dependency is included.
- One focused delivery slice: readiness/transfer contracts, the smallest enforcing helper or host path needed, associated acceptance tests, harness declarations and generated output. Expected authored surface below 1,000 changed lines; reassess before expanding. Base is origin/main; no stack dependency is established.
- L1 resolved the bounded mechanism decision; an independent evidence reader mapped adoption and tests. L4 implemented the helper and subprocess cases; L5 executed the isolated pickup fixture. This session retains plan and acceptance ownership.
- Preserve this existing standalone goal as the progress owner; do not create a parallel roadmap or ledger solely because core ships the optional repository runtime.
- Authored contracts, helper, tests, harness manifests and generated payloads are implemented. Native independent launcher acceptance and normal installed adoption are not claimed.

## Verification and acceptance

- Transfer helper: 11 subprocess tests pass, including contention, competing claimants, early acknowledgement, stale goal/branch/head, interrupted launch, authority exclusions and equivalent Windows paths.
- Existing plan suites: 96 pass; workflow routing: 14 pass; source layout: 17 pass. Both PowerShell packaging and launcher regression suites pass. Instruction-file pairing, tier payload and diff whitespace checks pass.
- Harness manifest, catalog digest and generated distribution parity checks pass after final helper edits. The earlier parity failure was stale generated output and was repaired by generation.
- Actual in-session Codex pickup: attempt `91309582-0e4c-4548-b5be-a43c300d0221`; one fresh L5 agent read the canonical fixture, acknowledged as `final-pickup-agent`, produced RESULT.txt, and reached active. Parent status verified submission and progress digests on the final helper. Both isolated fixtures were cleaned up after their agents returned. Result SHA-256: `531d7076f037c7e80dc91b1332defcfbd26f03fde62b8e9fe253f093f811001a`; generated helper SHA-256: `2f9785d3b5a27c5e130d413cc743ce919f59efe9f1a110b394deb49f105a2256`.
- This demonstrates actual agent pickup using the generated helper, not independent Windows Terminal launch or installed hook adoption. Launcher regression tests use executable stubs; they are not authenticated-host evidence.
- Automatic approval review rejected a proposed isolated native profile because it would copy local Codex authentication and configure unattended execution without explicit approval of those exact side effects. That command did not run. No credentials, profile or normal installation were changed. Complete draft/review work first, then request the specific remaining approval.

## Reviews

Full immutable review completed at dded182; R1 ledger/checkpoint invocation and R2 harness declaration checks are repaired in this commit. Eleven focused tests and final generated-helper pickup pass. Fresh incremental review remains before draft publication. Owning artifact: reviews/Feature-CriticalPlanExecutionHandoff.md.

## Execution design

The distinct readiness responsibility lives in plan-authoring and uses the existing canonical goal.
Substantial design and the remaining execution context select a fresh executor by judgment; criticality,
plan length, a phase or a lane change alone does not. Small/medium work normally stays inline. Planning-only
and prompt-only authority cannot create an execution reservation.

Handoff gains a packaged skill-local Python helper. The goal contains readiness evidence and an exact
receipt pointer. The receipt is transport evidence, not a second plan or scheduler. It binds an attempt,
canonical goal digest, checkout, Git identity when available, predecessor, harness and optional existing
continuation-owner reference. Short OS-held locks serialize atomic receipt updates only.

Transitions are prepared → launching → submitted → acknowledged → active. A successor may acknowledge
while submission is still returning; late submission preserves that state. The predecessor stops
deliverable writes before begin and retains read-only pickup accountability. One distinct successor
acknowledges the exact checkpoint before writing and records first-action evidence afterward. A pre-launch
failure can be failed; an interrupted/ambiguous launch or expired pickup budget is uncertain, with no
automatic retry or reclaim. The helper does not prove design quality or enforce all host writes.

Acceptance covers actual subprocess transitions/races, authority boundaries, checkpoint and checkout
mismatches, interrupted launch and matching first-action evidence. Existing workflow cases cover continued
phases and human/dependency gates. One isolated generated-helper/native-launcher probe must distinguish
submission, acknowledgement and actual output. Package parity is a separate check from host acceptance.

## Integration with default goal continuation

The related owner’s 2 October design binds the canonical goal, checkout, branch, completion, authority and
finite limits, and owns foreground reservations plus the observer/supervisor lock. This change preserves
that identity through an opaque owner reference. Its receipt lock serializes receipt updates only and
never claims the foreground reservation. A managed transfer must use the other owner's supported
release/claim interface; if unavailable it is capability-gated. No API is invented and no machine launcher,
job, binding, persistent-workflow definition or other checkout is changed here.

The source slices are independent. Integrate any generated catalog/manifests by rerunning generation over
the combined authored tree. A later real managed transfer is accepted only after the continuation owner's
release/claim interface and this receipt are exercised together; standalone transfer acceptance does not
claim that integration or installed adoption.
