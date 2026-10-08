# Callout repair enforcement

## Authorization

Bounded side workstream under `engineering:session-guidance`'s standing standards-defect default:
implement, test, open the PR and merge once this repository's gates pass. Installing into any other
scope, publishing outside this repository, and destructive operations stay gated.

- Checkout: `C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-CalloutRepairEnforcement`
- Branch: `Fix/CalloutRepairEnforcement` (from `origin/main` 8fb3c34)
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

1. Read the canonical sources for `red_run_gate`, `hook_dispatch`, the Stop and PostToolUse
   registrations, and `engineering/policy/session-guidance`. Reproduce defect A with a fixture built
   from the incident output above.
2. Finish A and B with focused regression tests, then review and deliver the runtime slice. Deliver C
   as a separate guidance slice under the same goal. D is already owned by
   [PR #148](https://github.com/tj-agents/core/pull/148), which reserves L1 for critical or large
   designs and keeps bounded testable choices at L4; reconcile its delivery instead of duplicating it.
3. Validate, open the PR, merge when gates pass, and record the result here.

## Current evidence and delivery slices

- Runtime slice: A/B, `Fix/CalloutRepairEnforcement`, base `origin/main` at `8fb3c34`, no PR yet.
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
- The remote base moved after the initial fetch. Commit the focused-green authored candidate, then
  synchronize once before freezing its independent review; rerun affected checks after integration.
- D is delivered by PR #148, merged at `fa9f7400d939ba9cbf57048d2f94787aeaca864e`.
  The runtime refinement keeps ordinary arithmetic corrections outside the Stop trigger and caches
  a verified launch for the current prompt. Its 13 focused callout tests passed again.
- Lifecycle recording by `workflow_ops.py skills --lifecycle plan-execution` fails on the former
  `.agents/skills` layout. This is already owned by `docs/workflows/TECH_DEBT.md`; canonical execution
  and lane contracts were read directly. This goal remains the sole progress owner.
