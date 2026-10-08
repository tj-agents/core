# Callout repair enforcement

## Authorization

Bounded side workstream under `engineering:session-guidance`'s standing standards-defect default:
implement, test, open the PR and merge once this repository's gates pass. Installing into any other
scope, publishing outside this repository, and destructive operations stay gated.

- Checkout: `C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-CalloutRepairEnforcement`
- Branch: `Docs/CalloutAnswerOrdering` (runtime PR #152 is merged; guidance starts from remote base `54bbb94`)
- Originating session: cris-authz, answering "why won't PR #25 merge". It keeps its own goal; this
  workstream does not touch it.

## Incident (2026-10-08, Claude Code, engineering plugin 8fb3c340f65f)

1. The user asked why a PR would not merge. The agent ran a read-only diagnostic:
   `gh run view <id> --log | grep -iE "##\[error\]|error:|failed|Error " | head -30`.
   The output held only echoed workflow-script source (`echo "::error file=..."`,
   `echo "Error: The following required dependencies are missing..."`) and dotnet summaries
   `Passed!  - Failed:     0, Passed: 12`. No test runner was invoked and nothing was red.
   `red_run_gate.py` fired "RED RUN" as a PostToolUse block demanding `engineering:failing-tests`,
   then fired again as a Stop block.
2. Following session-guidance ("launch `engineering:handoff` ... in the same turn ... before the
   original task resumes"), the agent started the handoff before answering the user's direct
   question. The user rejected it.
3. The user then called out the mistake. The agent drafted a `SendFeedback` instead of launching the
   handoff, although session-guidance says verbatim: "An apology, a SendFeedback draft or local memory
   does not substitute for this source-owner repair." The rule was merged and loaded in context, and
   it still did not hold. The host's built-in SendFeedback tool description ("draft at frustration
   moments") won over the plugin guidance, and nothing enforced the plugin side.

## Defects to repair

A. `red_run_gate` treats any Bash output that matches failure words as a red run. It must fire only
   on an actual test-runner invocation that reports a nonzero failure count or a failing exit. A grep
   or read of CI logs, echoed script source, and `Failed: 0` summaries must never trip it, at either
   the PostToolUse or the Stop hook. Add regression coverage for this exact shape.

B. The callout rule is unenforced. Make "the user calls out a mistake → source-owner handoff, never a
   SendFeedback / apology / memory substitute" hold mechanically on both hosts where the host allows it
   (for example a PreToolUse gate on `SendFeedback` while a callout is unrepaired), not only as prose.

C. The rule's ordering preempts the user's question. "Before the original task resumes" made the agent
   launch a handoff ahead of answering what the user asked. Fix the wording and any enforcement so the
   user's direct question is answered first and the handoff launches in that same turn. Keep the edit
   minimal: this file loads every prompt.

D. `engineering:lanes` and the launcher tables define L1 as "plans and design decisions of any size".
   The originating agent launched this very workstream at L1 on that wording, for a set of bugfixes
   whose mechanism the goal already names. That is L4 by the table's own "bugfix" example. Tighten the
   L1 definition so that picking a mechanism inside a specified bugfix or feature cannot read as L1.

## Completion

All defects repaired or reconciled with their existing source owner, with regression tests,
the repository's validation green, PR opened and
merged once gates pass. Report the PR URL and merge state back in this file.

## Next Steps

Lane: L4. The user changed this same session to Sol and confirmed on 2026-10-08 that it should
continue. This session owns execution; its earlier bounded workers have released writing.

1. Validate and review C on `Docs/CalloutAnswerOrdering`: both ordering sites now put the answer before
   handoff, the process regression checks that order, and failing-tests' hook description matches A.
2. Open and merge the guidance slice with the same goal authority. PR #152's bound regeneration job
   passed in run `37809283406`. Its scheduler and binding are retired and receipts preserved in
   `%TEMP%/callout-repair-owner-pr152`; the same canonical goal now owns this guidance slice.
   D is already owned by
   [PR #148](https://github.com/tj-agents/core/pull/148), which reserves L1 for critical or large
   designs and keeps bounded testable choices at L4; reconcile its delivery instead of duplicating it.
3. Validate, open the PR, merge when gates pass, and record the result here.

## Current evidence and delivery slices

- Runtime slice: A/B, `Fix/CalloutRepairEnforcement`, [PR #152](https://github.com/tj-agents/core/pull/152),
  merged head `a0b7d8684a9c786e6e95da31e0276aa4aee0e0a0`, landing
  `759e26935b0cb66a8bdaf5395d1d501ac12c171c`.
  Target below 1,000 substantive lines; hook/parser tests, packaging and harness declarations, an
  independent committed-head review, and repository CI are its validation gates.
- Integrated remote main at `ab321492`; affected regressions, 29 lane-table checks, 41 Claude launcher
  checks (one skip), and harness validation passed. Native review could not read the candidate due
  to sandbox startup failure; automatic approval review rejected transmitting the patch directly.
  The fresh workflow role was unsupported on this account. The review contract's bounded parent
  fallback found and repaired R1: automatic feedback denial must not itself create a standards
  handoff obligation for an unrecognized complaint. Its 13 focused tests passed.
- Guidance slice: C, a subsequent `Docs/*` branch from the updated remote default, with the minimal
  wording correction and its process-standard regression tests.
- C's 22 process-standard checks and 12 red-run regressions passed on 2026-10-08. The runtime's
  documented slice-completion transition checks the broader goal and therefore cannot complete with
  C correctly pending. That limitation is now owned by `docs/workflows/TECH_DEBT.md`; the foreground
  parent preserved the blocked slice receipts, retired its scheduler and binding after merge, and
  initialized the same canonical goal for the guidance slice.
- The partial A patch was reviewed and corrected for quoted-command parsing, deleted E2E constants,
  mixed passing/failing suites, compound exit attribution, and old CI-read Stop state. Its 12 focused
  tests passed on 2026-10-08. Broader validation and review remain.
- B will block automatic feedback substitution and require observed launcher success, rather than a
  skill load or a promise. Direct answers remain allowed before repair. Host limits must be recorded
  accurately: Codex has no registered result/Stop event here, and neither host intercepts arbitrary
  final prose.
- The runtime slice includes the two launchers' additive `agent-handoff-submitted` receipt, binding
  the actual working directory and prompt path. That prevents variable-based commands from losing
  launch evidence and lets the gate inspect the prepared source-owner authorization.
- Focused validation is green: red-run regressions (12), callout regressions (13), Claude launcher
  tests (39, one platform skip), harness manifests (13), source-layout tests (19), and PowerShell
  launcher tests. The pre-integration shared runtime suite passed 964 tests with nine skips; it
  finished before the attempted cancellation and no process was stopped. Generated distribution and catalog
  changes are local test output and will not be staged.
- Remote base movement after the final-review synchronization is disjoint according to
  `review-reconcile`; preserve the exact reviewed head. The runtime monitor is bound to PR #152 and
  its head. Its continuation owner and Windows scheduler are registered, with a verified supported
  wake respecting this session's foreground lease. No headless writer has launched.
- D is delivered by PR #148, merged at `fa9f7400d939ba9cbf57048d2f94787aeaca864e`.
  The runtime refinement keeps ordinary arithmetic corrections outside the Stop trigger and caches
  a verified launch for the current prompt. Its 13 focused callout tests passed again.
- Lifecycle recording by `workflow_ops.py skills --lifecycle plan-execution` fails on the former
  `.agents/skills` layout. This is already owned by `docs/workflows/TECH_DEBT.md`; canonical execution
  and lane contracts were read directly. This goal remains the sole progress owner.
- CI run `37801891775` passed packaging, manifests, launcher and Windows compatibility checks.
  The source/package suite ran 697 tests with 12 skips and one failure: the expected Windows hook
  inventory did not include `callout_repair_gate.py`. Shared runtime CI was skipped because that
  earlier step failed. A fresh bounded mechanical worker owns only that inventory correction;
  no retry or merge bypass is authorized as a substitute for repairing the failure.

## Delivery acceptance

```completion
{
  "outcome": "Repair bounded callout enforcement and false red-run detection, answer questions before handoff, and reconcile lane pricing",
  "acceptance": [
    {"id": "A", "criterion": "CI log reads and passing summaries do not create red-run obligations", "evidence": [{"source": ".agents/hooks/tests/test_red_run_gate.py", "result": "12 focused tests passed after main integration"}], "owner": "", "next_action": ""},
    {"id": "B", "criterion": "Supported host events gate automatic feedback substitution and pair source-owner launcher proof", "evidence": [{"source": ".agents/hooks/tests/test_callout_repair_gate.py", "result": "13 focused tests passed; unsupported semantic and final-prose interception recorded in plugin debt"}], "owner": "", "next_action": ""},
    {"id": "C", "criterion": "Minimal session guidance requires answering the direct question before same-turn handoff", "evidence": [], "owner": "This source-owner session", "next_action": "Deliver the separate guidance slice after PR152 lands"},
    {"id": "D", "criterion": "Bounded testable choices do not select the critical-design lane", "evidence": [{"source": "https://github.com/tj-agents/core/pull/148", "result": "Merged at fa9f7400d939ba9cbf57048d2f94787aeaca864e"}], "owner": "", "next_action": ""}
  ],
  "deliveries": [{"repository": "tj-agents/core", "pr": 152, "head": "a0b7d8684a9c786e6e95da31e0276aa4aee0e0a0"}],
  "open_tasks": []
}
```
