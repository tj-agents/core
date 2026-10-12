# Prevent inert closeout work from restarting delivery
Status: original repair checkpointed and independently reviewed on 2026-10-12; one cleanup-order finding is under bounded repair before final publication.
## Outcome
Diagnose and repair the core-owned workflow gap that allowed an agent to plan a bookkeeping-only push and another full CI/review cycle after the final executable scaffold candidate was green. Preserve meaningful code validation and security review.
## Authorization
Standing engineering:session-guidance standards-defect authorization, triggered by Tommy's direct callout that scripted scaffold work has taken six hours and asks whether core requirements are slowing it. This covers bounded core implementation, tests, PR and merge after core gates. No installation into dotnet or global settings, no kit edits, no weakening checks.
## Ownership
Worktree: C:/Users/TommySeery/source/repos/tj-agents/dotnet/.worktrees/Feature-ScriptedScaffold/.worktrees/Fix-InertCloseoutCadence
Branch: Fix/InertCloseoutCadence
Base: c91b60c955ad4a3f0f7a9383fc20f1c4a6b58510
This successor owns only this isolated core workstream. Parent retains dotnet scaffold goal and all its source/review/delivery; do not edit or close it. Other core writers are active: do not revert or edit their checkouts or overlap open PRs.
## Evidence
Scaffold parent has final head8f22d5d772e61d30b0d94dd97952bacfd0ec4f41 in tj-agents/dotnet PR47. It had wrongly planned a new documentation-only closeout commit/push (B003/B005/B007/M001 status updates), fresh native review and full seven-row Windows/Ubuntu CI after already obtaining source-bound passing proof. This extra loop has now been rejected before it happened. Real earlier delays included compilation failures, inaccurate subordinate success reports, and a genuine known-admin-password/default-interface fixture fix; do not misrepresent those repairs as pointless.
Installed core2.1.16 remote-validation Resource discipline and Metadata-only synchronization sections explicitly prohibit plan/ledger/observation-only pushes and describe executable-tree reuse. committing says commit every verified chunk including doc closeout but keep cadence separate and do not push ledger changes. The gap may be missing actionable final-record closeout choreography/enforcement under completion/problem-record/review constraints, rather than a requirement to remove exact-head checks. Inspect actual source before concluding. A standards source fix must improve the user's outcome, not add another ceremony.
## User testing decision
Parent supplied Tommy's 2026-10-12 correction in USER_TESTING_DECISION.md: interim checks target additions/changes; one full CI run validates the finished implementation. Batch implementation and commits before final publication. This bounded repair follows that cadence and does not change unrelated test selection. Parent reports scaffold PR47 merged at693618d89415731d3eec887fda460bb9046a6463 on2026-10-12T20:30:55Z; its CI adoption debt remains dotnet D003. The separate continuation-probe owner retains its paths; this repair changes only shared closeout guidance and its focused regressions.

## Lane
L3 for bounded uncertain diagnosis of the source/runtime gap; reroute specified testable implementation to L4. Do not raise lane for delivery.
## Diagnosis and delivery slice
Source diagnosis confirmed a policy collision: the blanket immediate-commit rule includes final doc closeout, but merge and guarded auto-merge require the same local and reviewed remote HEAD. Remote-validation already forbids bookkeeping pushes. Completion checks read the current local goal and fresh merged forge identity without requiring goal publication. The minimal repair is a late-record exception and terminal closeout choreography; exact-head gates remain intact. Recorded as BUGS.md B008.

One standalone core slice owns shared committing/problem-record/merge guidance and focused process/completion regressions. No parent dependency, no new skill, no runtime gate exemptions, no broad push parser. Open PR inspection found other writers on persistent-workflow and continuation hooks; those paths are excluded. Remote base was fetched and HEAD is current with origin/main at c91b60c955ad4a3f0f7a9383fc20f1c4a6b58510. L4 implementation was delegated to a bounded lane worker because the mechanism is now specified and testable; parent owns synthesis and delivery. Continuation owner65da76927960b85c595f99da is initialized and claimed by this foreground. Wake registration failed before task creation because Windows ScheduledTasks enumeration timed out after eight seconds; unattended continuation is not established. This owner continues in the foreground.
## Acceptance
One evidence-backed actionable core defect is fixed with focused regression coverage, reviewed and merged under core policy; or existing correct behavior is mechanically proven and this goal records the precise agent misapplication plus an objective enforcement repair owner. Source is host-neutral with both-host coverage as applicable. Do not undertake a broad performance audit or unrelated workflow redesign.
## Host coverage
```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/engineering/contract/committing/SKILL.md and shared engineering closeout contracts",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Keep late inert final records local while the frozen candidate remains under delivery gates.",
      "source": ".agents/engineering shared committing, problem-record, plan-checkpoint, plans and merge definitions",
      "mapping": ".claude/skills canonical pointers; .agents/plugins/sources.json engineering scope generation",
      "verification": {"level": "source", "result": "passed", "evidence": "Captured process/completion suites, harness validation and test_source_layout passed after regeneration; Claude adapters resolve the changed shared definitions and shared resources ship. Installed acceptance was not performed."}
    },
    {
      "host": "codex",
      "behavior": "Keep late inert final records local while the frozen candidate remains under delivery gates.",
      "source": ".agents/engineering shared committing, problem-record, plan-checkpoint, plans and merge definitions",
      "mapping": ".codex/skills canonical pointers; .agents/plugins/sources.json engineering scope generation",
      "verification": {"level": "source", "result": "passed", "evidence": "Captured process/completion suites, harness validation and test_source_layout passed after regeneration; Codex adapters resolve the changed shared definitions and shared resources ship. Installed acceptance was not performed."}
    }
  ]
}
```
## Next Steps
Pickup acknowledged in the named worktree on branch Fix/InertCloseoutCadence at the recorded base. Root AGENTS, README, CODE_CONVENTIONS, plan-execution, bugfix and lanes were read. Plan-execution owns this existing goal. Diagnosis is routed to a bounded L3 reader because the source cause is unresolved; the parent retains repair and delivery decisions.

Checkpoint the verified substantive candidate, synchronize once and freeze its review. Run independent native and required security review, resolve findings, publish one reviewed candidate and own exact-head CI through authorized merge and causal regeneration. Preserve this goal for the parent; do not install updated plugins.

Focused evidence: process standards24, completion12 and preserved auto-merge11 tests passed; harness declaration validation and manifest tests passed. The new completion regression accepts locally updated evidence only against the freshly fetched unchanged merged identity; changed heads and unmerged delivery still fail. A policy-test wrapping/encoding assertion was corrected and the suite reran green. Source-layout/package suite passed, including both-host shared-resource shipment and canonical adapter mapping; generated output remains excluded from the candidate. Canonical lifecycle identity was recorded using the helper's supported explicit name=source-path form because its legacy default .agents/skills path does not exist in this source layout.

Review checkpoint: frozen d42cae4caf1e8cd3dcfa7686362e8334777ef7b1 completed with one deduplicated HIGH finding (R1): terminal local records must survive linked-worktree cleanup without advancing its merged source head. Native declared specialist was unsupported by the account; declared L4 fallback completed, independently corroborating the workflow lens. Address-review owns the bounded guidance/cleanup regression repair, then incremental review and one final exact-head publication. No source candidate has been pushed.

R1 repair verification: completion12 passed; process choreography and goal-scoped merge authorization reruns2 passed; existing cleanup-proof set-aside/removal regression1 passed. Earlier local reruns hit host MemoryError and Git fork/spawn exhaustion; focused reruns recovered without source/test weakening. The repair keeps every continuation completion at its original goal path, preserves source HEAD through cleanup, and records retained pending retirement for the next substantive publication. Final repair checkpoint and incremental review next.
