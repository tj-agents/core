# Configured routine design approval across agent hosts

Status: implemented 2026-10-12; focused checks passed; independent review next.

## Outcome

Diagnose the missing/ambiguous repository setting for delegated routine design/convention decisions.
Document the requested tech debt and deliver the minimal core-owned source correction so Claude and
Codex can honor an explicit repository opt-in across tj-agents scopes, without asking repeated approval
questions for work already authorized. Distinguish this from auto-merge and host permission bypass.

## Context and authority

Tommy, 2026-10-12 in the dotnet scripted scaffold session: "yep go?"; "again we shouldnt need approval
for this, i thought this was part of the configuration setting, maybe we need to add it to claude,
like auto-approve, write it down as tech debt in docs, as this should be applied to all tj-agents or
at least a fair few repos in the future, and contiunue".

The original scaffold handoff explicitly gated the single-service File structure decision.
The installed dotnet:learning convention procedure says Tommy decides before a convention is recorded.
The original owner followed that gate, then Tommy approved and requested the configuration debt.
This reveals a missing or conflicting shared routine-decision delegation mechanism rather than a
request to disable sandbox/security approval or treat auto-merge as authority for every action.

Standing engineering:session-guidance authorizes diagnosing and repairing consumed standards defects,
including implementation, tests, review, PR and merge under repository gates. This side workstream owns
only core source and its implementation goal; cross-repository design docs stay in tj-agents/docs.
Do not write the active dotnet scaffold checkout or change dotnet/other stack contract sources here.
Record linked adoption requirements instead. Do not install into consuming repos, refresh normal
host profiles, copy credentials, modify kit/Template or change machine-wide permissions.

Original task remains active and separately owned:
C:/Users/TommySeery/source/repos/tj-agents/dotnet/.worktrees/Feature-ScriptedScaffold/plans/scripted-scaffold/GOAL.md
Consumer debt:
C:/Users/TommySeery/source/repos/tj-agents/dotnet/.worktrees/Feature-ScriptedScaffold/docs/TECH_DEBT.md#d001-honor-configured-design-approval-across-agent-hosts

## Checkout and lane

Worktree: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-ConventionApprovalConfiguration
Branch: Fix/ConventionApprovalConfiguration
Base: fetched origin/main at d747cbed6add80e57c5d0cbbac716dbd4502bf78
PR: not opened
Owner: current Codex session acknowledged the bounded repair; parent retains the dotnet goal.
Lane: L4 implementation, because L3 diagnosis has specified one strict boolean and existing both-host
hook delivery. Canonical Codex lane agent owns the bounded implementation; this session owns orchestration.

## Acceptance

- Reconcile existing configuration owners, debt and active work before any deliverable edit.
- Identify whether an existing setting already controls routine design/convention approval, and why the
  handoff/learning contract did not honor it; do not invent a duplicate setting.
- Record the requested actionable documentation debt with an objective both-host resolution condition.
- If repair is authorized and no existing owner overlaps, minimally correct core shared configuration,
  composition/guidance and relevant tests, respecting false/default behavior and explicit user limits.
- Document affected stack contract adoption and rollout requirements with source-owner links; do not
  pretend source publication installs anything in consumers.
- Independent exact-head review, focused/full required checks and authorized PR delivery pass. Keep
  scope reviewable and report concrete delivery evidence in this same goal.

## Next Steps

Scope: whole plan through all remaining phases and terminal delivery.
Current slice: strict repository design-decision opt-in and shared both-host delivery.
Remaining scope: exact-head independent review, required Windows/Linux CI, PR and authorized merge.
Done when: core repair is reviewed and merged with Windows/Linux checks; dependent adoption is documented.

1. Reconcile the L4 worker's changes against the specification below, synchronize authored harness
   manifests, refresh generated packages locally, and run focused configuration/engineering hook tests.
2. Commit the focused-green source candidate; enter independent exact-head review and resolve findings.
3. Open the bounded PR, monitor exact-head Windows/Linux CI and merge once repository gates pass.
4. Report the source result and remaining rollout requirement through this goal's artifacts;
   keep its scaffold implementation independent. Do not claim original goal completion or close it.

## Progress

- 2026-10-12: L4 implementation completed; strict reader, relocated packaged hooks for both hosts,
  auto-merge, harness permission and manifest regressions passed. Manifest/catalog/package synchronization
  and generation checks passed; existing harness requirements cover the unchanged entry points and mappings.
  Full platform matrices remain with CI. Unrelated capability-bootstrap validation was stopped without
  a result; generated catalog CRLF whitespace is excluded from the authored candidate.
- Commit phase: L7 clerical staging of the nine authored repair paths plus this goal; generated output
  remains outside the PR. Review phase: L4 ordinary isolated review of the frozen candidate.

- 2026-10-12: fetched origin/main remains d747cbed6add80e57c5d0cbbac716dbd4502bf78; no overlapping
  routine-decision PR in the open inventory. RepositoryConfiguration released its writer and its old
  configuration.json design was superseded by settings.json. Repo-declared-config retains rollout ownership.
- L3 evidence: only core.auto_merge exists; session-guidance context is static; dotnet scaffold has no
  settings.json, and its learning/handoff gates were followed correctly. The new independent setting is
  core.auto_approve_design, strict boolean, false/absent by default, with no legacy design fallback.
- L4 slice: existing reader, session guidance and both-host context hook, handoff provenance, behavioral
  tests and documentation/debt. Keep the open namespace schema and this repository's opt-in unchanged.
  Routine choices apply only to authorized work; explicit user reservations and stricter repository rules
  retain precedence. Recheck settings on every prompt and after a handoff; never read plugin/profile settings.
- Atomic delivery assessment: one setting requires its reader and shared guidance/context together;
  separating the contract would advertise an unavailable mechanism. Expected below 500 substantive lines,
  one branch from current origin/main, no cross-repository implementation or generated output in PR.
- Continuation owner 9ad23200736b84defcafeb02 initialized and claimed to Codex PID 37748; supported
  Windows task registration succeeded. A verification wake returned working and preserved the foreground
  writer; no child execution or normal-profile refresh was performed.
  Workflow lifecycle-name resolution reproduced the existing flat-layout debt in docs/workflows/TECH_DEBT.md;
  use canonical source paths and native tools where that operation cannot resolve the owner.
- 2026-10-12: user asked whether the configuration foundation was finished before continuing.
  Verified the committed settings envelope/schema/reader and both generated package copies; commits
  531c793, 0a5fb18 and 36a08fc establish the shipped foundation. Only the new routine-decision option
  is unfinished. Answered the prerequisite question and resumed the authorized core repair.
- 2026-10-12: successor read the handoff and goal, verified checkout/branch and base SHA, and
  started L3 read-only configuration diagnosis through the canonical lane agent. This session owns
  only the core repair; the dotnet scaffold remains with its originating owner.
- 2026-10-12: parent inspected core worktree/branch inventory and existing configuration-related goals;
  no equivalent convention-approval owner was observed; this checkout was created and successor pickup
  is now verified.

## Agent host coverage

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/engineering/policy/session-guidance and .agents/workflows/repository_configuration.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Resolve repository routine design delegation for authorized work at startup and every prompt; preserve explicit user gates",
      "source": ".agents/engineering/policy/session-guidance/scripts/session-context.py",
      "mapping": ".agents/plugins/manifests/claude/engineering-hooks.json SessionStart and UserPromptSubmit",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Passed relocated packaged-hook tests in tests/test_engineering_hooks.py and strict reader regressions in .agents/hooks/tests/test_repository_configuration.py"
      }
    },
    {
      "host": "codex",
      "behavior": "Resolve repository routine design delegation for authorized work at startup and every prompt; preserve explicit user gates",
      "source": ".agents/engineering/policy/session-guidance/scripts/session-context.py",
      "mapping": ".agents/plugins/manifests/codex/engineering-hooks.json SessionStart and UserPromptSubmit",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Passed relocated packaged-hook tests in tests/test_engineering_hooks.py and strict reader regressions in .agents/hooks/tests/test_repository_configuration.py"
      }
    }
  ]
}
```
