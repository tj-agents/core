# Routine review evidence and impact-selected CI

## Authorization and ownership

Tommy originally directed Core to stop committing ordinary Markdown review work orders and stop running the broad Windows/Linux matrix for every PR. On 16 October 2026, after the validation-efficiency investigation, Tommy said “okay lets go then?” to the concrete prioritized proposal. Implementation, focused validation, independent review and PR preparation are now authorized. Existing delivery/security stop classes still apply; CI workflow changes require their final delivery approval.

This is the existing goal promoted from `Fix-RoutineReviewAndImpactCi/plans/routine-review-evidence-and-impact-ci/GOAL.md` into its active delivery checkout. The session store reports no owner for that old checkout, and GitHub reports no PR for its branch. Its two unfinished source edits remain untouched as historical inputs, not an active implementation copy. This file owns current execution state; no competing goal is created.

- Owner: codex:01a1447f-62b8-70e0-a7a3-20a040f97690.
- Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Investigate-ValidationEfficiency.
- Branch: Fix/ImpactSelectedCi.
- Base: origin/main 07cda2b1963b724bd62e6cdbe7e13694ce661d35, integrated before implementation.
- PR: not opened.
- Investigation: `plans/validation-efficiency/FINDINGS.md`, local commit 58aab8b7.
- Routine design delegation: false by absent category in `.agents/settings.json`. The accepted proposal supplies the implementation direction; no new plugin, service or external dependency is selected.
- Standards loaded: AGENTS.md, README.md, CODE_CONVENTIONS.md, PACKAGING.md; plan-execution, lanes, git-branching, plans, plan-checkpoint, remote-validation, review/review-lifecycle and persistent-workflow contracts. The repository router declares no path-specific skills. C++ style/libraries were loaded as requested by session guidance; these changes use the repository's Python/CI conventions.

## Required outcome

1. PR CI selects the smallest established test closure for changed behavior, retaining full Windows/Linux coverage for broad or uncertain changes. Main keeps full coverage while PR selection is established.
2. A successful aggregate proves selection and every selected job succeeded. Failed/cancelled/missing classification or required execution must never become green through skipped jobs.
3. Ordinary review proof becomes private and consistently consumed without weakening reviewed-candidate, security, finding, authorization or recovery checks. Big/staged reviews keep durable Markdown.
4. Apply existing stable-push and factual-record batching; profile expensive fixtures during required CI and optimize demonstrated redundant setup without removing negative assertions.

Consumer adoption and PR #269 remain outside this goal. No hook disabling, global configuration changes, employer policies or generated package commits are authorized here.

## Assessment carried forward

The investigation established that #268's proportionality fix was active, and routine-docs mode is already delivered. Four relevant Core validation windows total 71m28s; the last Windows job spends about 94% in two serial suites. Reuse these findings rather than rerun the matrix to reproduce them.

For selection, use standard-library Python and native Actions job outputs/conditions. This repository has no dependency download bottleneck or existing selector to adopt. A third-party path-filter action would add a dependency without solving Core's behavioral test closure or aggregate semantics. GitHub's primary documentation confirms that conditional jobs can report success when skipped, and dependent required checks need `always()` plus explicit result validation. Default PR checkout tests the merge commit. The selector will inspect base-to-merge changes rather than silently treating head-only validation as equivalent. Research assessment complete; no library/plugin installation is needed.

## Delivery map

### 1. Impact-selected CI (current slice)

Own `scripts/ci_selection.py`, `tests/test_ci_selection.py`, `.github/workflows/ci.yml` and relevant CI documentation. Expected substantive size below 1,000 changed lines; reassess if the mapping exceeds that boundary. Preserve existing full jobs and main publication. No review-proof source changes belong to this slice.

Consumption contract: a classification step emits compact JSON with `mode`, `reason`, selected source/runtime test files and platform requirements through one Actions job output. Verification jobs consume this plan. A final `ci-required` aggregate runs even when dependencies fail or skip and explicitly checks classification, generated-path guard and selected job results. Existing job names remain where possible.

Classification fails conservatively to full for unresolved ranges, binary changes, excessive changed scope, unsupported events, unknown paths and changes to CI/selector/shared infrastructure. Rename/delete paths participate in the mapping. Inert prose gets the existing docs reachability check. Executable guidance never becomes inert merely because its suffix is Markdown. Known runtime families run their closed regression set on Windows and Linux plus generation/package invariants. Test changes join the selected set. No cached success is transferred between heads in this first slice, and no cancellation is introduced.

The deciding workflow relationship is:

```yaml
ci-required:
  if: always()
  needs: [select, guard, verify-windows, verify-linux]
```

The aggregate passes only when classification succeeded and every job selected by its exact plan succeeded. A skipped selected job is a failure. A prose-only plan expects both platform jobs to be skipped and still runs its docs check in classification. Tests exercise this result decision independently of Actions.

Verification: focused selector tests include actual disposable Git ranges, rename/deletion, unknown ranges/paths, binary/large changes, source-family unions, test additions, failed/missing/cancelled/skipped selected jobs and invalid plan data. Check workflow wiring and run the relevant existing guard tests. This CI-changing PR itself receives the full matrix remotely. Required-check server configuration is inspected and kept as a concrete delivery dependency if changes are needed; no server permission is silently changed.

### 2. Private ordinary-review proof

After slice 1 lands, reconcile `merge_review_gate.py`, `auto_merge.py`, `workflow_ops.py`, `delivery_runtime.py`, review contracts and host tests as one coherent cutover. Reuse the old goal's intended outcome, not its incomplete two-file patch. Preserve current-main foreign-repository and command-text fixes. Define proof identity and recovery before source changes; retain big/staged work orders. Record exact scope/size before beginning this slice.

### 3. Expensive fixture setup

Use timing from a required validation run to choose the smallest test-fixture optimization, beginning with workflow operations, continuation, cleanup and source-layout setup. Preserve real subprocess/Git/locking coverage and isolation. Do not introduce a cache or scheduler solely to measure. Record scope and acceptance before changes; split independently if needed.

## Current state

Ownership/baseline reconciled. The investigation remains complete; this follow-up supersedes its investigation-only execution restriction for the approved implementation. The selector, focused runner, fail-closed aggregate and workflow wiring are implemented. Mappings cover five bounded runtime families; shared helpers and every unknown surface retain full coverage. Test imports extend changed-test closure. Main remains full, selection never cancels prior runs, and Linux focused execution keeps stdin closed.

Focused selector/execution/wiring tests pass (21 cases, about 10 seconds), existing generated-path guard tests pass (4 cases, about 8 seconds), and the exact docs reachability command passes. An initial selector syntax error was fixed before these passes. The GitHub rulesets API returns an empty list and the prior branch-protection query returned 404: there is no observed server-side required-check configuration to migrate. The aggregate participates in the existing all-checks merge validator; README documents requiring `ci-required` if server enforcement is enabled. No server configuration is changed.

The earlier session-store claim could not verify a native registry attachment. Workflow inspection succeeds through host-side access to Git-private state. No verified native host PID is currently available for a foreground continuation claim; no unattended scheduler is registered or promised. Continue foreground work and retain this goal as the recovery owner.

## Reviews

No implementation review yet. Each delivery slice requires a frozen independent review with stale-head/security guarantees; reuse valid evidence and review only later changed deltas.

## Next Steps

Scope: whole plan through all remaining phases and terminal delivery, subject to existing delivery approval gates.
Current slice: impact-selected CI on Fix/ImpactSelectedCi.
Remaining scope: private ordinary-review proof and measured fixture optimization; batching applies throughout.
Done when: selected CI and consistent private review evidence are delivered with preserved safeguards, and demonstrated redundant fixture cost is addressed or explicitly dispositioned with evidence.

Implement and test the classifier, focused execution and required aggregate; validate locally through the compact workflow runner, then commit, review and prepare one stable PR. Complete all authorized preparation before requesting any final CI-delivery approval. Continue independent authorized work if one delivery action is gated.
