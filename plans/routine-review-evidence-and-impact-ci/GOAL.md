# Routine review evidence and impact-selected CI

## Authorization and ownership

Tommy originally directed Core to stop committing ordinary Markdown review work orders and stop running the broad Windows/Linux matrix for every PR. On 16 October 2026, after the validation-efficiency investigation, Tommy said “okay lets go then?” to the concrete prioritized proposal. Implementation, focused validation, independent review and PR preparation are now authorized. Existing delivery/security stop classes still apply. Tommy explicitly approved merging the reviewed CI change in PR #274 once its full Windows/Linux CI passes; the approval is scoped to this candidate and resolves its CI-workflow human gate.

This is the existing goal promoted from `Fix-RoutineReviewAndImpactCi/plans/routine-review-evidence-and-impact-ci/GOAL.md` into its active delivery checkout. The session store reports no owner for that old checkout, and GitHub reports no PR for its branch. Its two unfinished source edits remain untouched as historical inputs, not an active implementation copy. This file owns current execution state; no competing goal is created.

- Owner: codex:01a1447f-62b8-70e0-a7a3-20a040f97690.
- Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Investigate-ValidationEfficiency.
- Branch: Fix/PrivateReviewEvidence (successor to merged Fix/ImpactSelectedCi).
- Base: origin/main 621c7a21ec2684fe7d252b1944ece5689f94f398 for the private-proof slice.
- Delivered CI: PR #274, head 5b42318ef0369ef59dcbbdde40505dd21a857ad8, merged at 621c7a21. Private-proof PR #275, initial head ff3504864217cf0b048a78c997a2d354d15117a2; review/CI repair in progress.
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

### 1. Impact-selected CI (delivered)

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

### 2. Private ordinary-review proof (current slice)

After slice 1 lands, reconcile `merge_review_gate.py`, `auto_merge.py`, `workflow_ops.py`, `delivery_runtime.py`, review contracts and host tests as one coherent cutover. Reuse the old goal's intended outcome, not its incomplete two-file patch. Preserve current-main foreign-repository and command-text fixes. Define proof identity and recovery before source changes; retain big/staged work orders. Record exact scope/size before beginning this slice.

Prepared dependency map: ordinary completion currently exists only in the Markdown body. `merge_review_gate.main` and `auto_merge.current_review` prefer the committed body and then fall back locally; `workflow_ops.review_binding` reads the local body; `delivery_runtime` validates the derived watermark. Incremental/docs/staged contracts share that representation. Existing Git-private descriptors authenticate frozen candidates and restore bundles, but contain no completed judgment or finding state. The cutover must centralize proof resolution and identity across these readers before removing ordinary Markdown transport. Relevant regressions are `test_merge_review_gate`, `test_auto_merge`, `test_workflow_ops`, `test_delivery_runtime` and `test_review_workflows`. Preserve big/staged coverage and parent-finalization recovery; do not use a two-reader-only patch. Implementation starts on Fix/PrivateReviewEvidence after PR #274 landed. Use one Git-private directory per checkout/branch, with the existing editable review body and an atomic completion receipt binding repository, checkout, branch, exact head, frozen descriptor identity and body hash. A single shipped resolver serves merge, auto-merge, binding, host coverage and inspection. Missing, edited, stale, redirected or mismatched private evidence fails closed; never fall back to legacy evidence when private evidence exists but is invalid. Existing durable staged work orders and legacy reviews remain readable during migration. Ordinary full/incremental/docs/address workflows resolve the private path and finalize through the receipt command. Recovery preserves the existing body and immutable descriptor; it does not infer approval. Include the work-item finding reader and successor rebinding so private evidence is not lost at a lifecycle boundary. Expected source/contracts/tests delta below 1,000 substantive lines; keep this cutover atomic and reassess before exceeding that scope.

### 3. Expensive fixture setup

Use timing from a required validation run to choose the smallest test-fixture optimization, beginning with workflow operations, continuation, cleanup and source-layout setup. Preserve real subprocess/Git/locking coverage and isolation. The first required implementation run already supplies source-suite completion gaps: Windows work-item sessions 59.0s, Claude standards sync 43.3s and source layout 41.7s. These include setup/teardown and logging and are not isolated fixture timings. Completed required run 38902959829 supplies both suites without an extra measurement run: Windows source 305.693s and runtime 680.557s. Completion-gap estimates put 40 frozen-review cases at 102.161s, source-layout at 44.271s, and nine PR-readiness cases at only 4.677s. Prefer a reusable immutable base repository copied into isolated writable fixtures across the workflow tests over optimizing only those nine cases, subject to focused before/after measurement and preserved Git behavior. Evidence: plans/validation-efficiency/completed-implementation-ci-timing.json. Do not introduce a cache or scheduler solely to measure. Record scope and acceptance before changes; split independently if needed.

## Current state

Ownership/baseline reconciled. The investigation remains complete; this follow-up supersedes its investigation-only execution restriction for the approved implementation. The selector, focused runner, fail-closed aggregate and workflow wiring are delivered. Causal main run 38905321932 also passed, including regenerate, both platforms and ci-required. The successor private-proof cutover is published as PR #275; independent review and full CI identified repairs now being verified. Mappings cover five bounded runtime families; shared helpers and every unknown surface retain full coverage. Test imports extend changed-test closure. Main remains full, selection never cancels prior runs, and Linux focused execution keeps stdin closed.

Focused selector/execution/wiring tests pass (21 cases, about 10 seconds), existing generated-path guard tests pass (4 cases, about 8 seconds), and the exact docs reachability command passes. An initial selector syntax error was fixed before these passes. The GitHub rulesets API returns an empty list and the prior branch-protection query returned 404: there is no observed server-side required-check configuration to migrate. The aggregate participates in the existing all-checks merge validator; README documents requiring `ci-required` if server enforcement is enabled. No server configuration is changed.

The earlier session-store claim could not verify a native registry attachment. Workflow inspection succeeds through host-side access to Git-private state. No verified native host PID is currently available for a foreground continuation claim; no unattended scheduler is registered or promised. Continue foreground work and retain this goal as the recovery owner.

Private-proof focused validation: all 14 new identity/reader/completion regressions pass across the focused runs (one symlink case skips on this Windows host). The linked-worktree case completes a real frozen descriptor and publishes/reads private proof. Existing auto-merge tests pass; the 96 workflow-operations cases pass after correcting their one noncanonical watermark fixture, and existing merge/delivery/review regressions pass after the successor-path repair and generated-source refresh. Harness-manifest and docs-reachability checks pass. No full local matrix was run. The source delta remains below 1,000 substantive lines. The active installed hook still has the legacy reader, so this delivery keeps its existing untracked durable review work order for source-migration compatibility; private acceptance is tested directly, and no installed-host upgrade is claimed.

## Reviews

CI slice reviewed at a4a187ddc891706dcdf880202feb0b3253a319a4 against 07cda2b1963b724bd62e6cdbe7e13694ce661d35. Native read-only Codex review completed with no findings; specialist security/workflow role dispatches were unsupported by this account, so their bounded checks returned to the parent as the review contract requires. The local work order `reviews/Fix-ImpactSelectedCi.md` is complete and approved with a current security marker. It remains uncommitted. The first full remote run completed with a deterministic permission-contract failure on both platforms: the Windows verify job now contains 18 commands, while its regression expected 16 and its project Claude allowlist omitted the two new focused-run commands. The failure reproduced in the three-test permissions module. The repair adds only those exact commands for Bash and PowerShell and updates the roster count; all three permission tests now pass. No runtime test assertion is removed. The repair is committed at 5b42318e, published and has completed a clean native incremental review. Its fresh exact-head full run 38902959829 passed all selected jobs and ci-required; Windows took 17m28s and Linux 3m17s.

PR #274 was reviewed, body-validated, marked ready and merged at 621c7a21ec2684fe7d252b1944ece5689f94f398 on 16 October 2026. Its delivery binding was released; this active checkout is retained for the same goal. Causal main run 38905321932 is monitored separately. CI run 38901210387 attempt 1 failed the permission contract; the repaired stable candidate 5b42318ef0369ef59dcbbdde40505dd21a857ad8 is published and bound to full CI run 38902959829 attempt 1 through the supported monitor. Repository delivery binding reports the existing `ci-workflow` stop class. Tommy supplied the concrete final CI-workflow approval on 16 October 2026, conditional on green full Windows/Linux CI; no policy table or stop class is changed. The generic preflight cannot treat this maintained goal as a legacy ledger; its remaining no-ledger `assess-scope` result is resolved by this goal's delivery map and the published slice, not by inventing another ledger.

Private-proof review at ff350486: native Codex and the workflow lens found no defects. The integrity lens required one elevated-read follow-up, then returned two confirmed defects: committed legacy evidence hid newer local findings, and private finalization inherited legacy tolerance for missing completion fields. Repairs prefer the existing live durable body and require explicit unique completion/judgment fields for private publication and every consuming gate. Sixteen private-proof tests pass, including both regressions; existing merge-gate and auto-merge regressions pass. Full CI run 38909183928 failed both platforms on five unqualified installed-helper references in the new contracts; those references now use the engineering resource path. The source-suite assertions remain intact. The local packaging check first saw stale generated copies; regeneration repaired that fixture state before focused recheck. These repairs will share one stable push and a fresh incremental review.

The isolated twelve-sample workflow fixture measurement completed with a 1.8319s median and 21.5683s total for setup, cleanup and two baseline verification Git calls. It creates independent writable repositories each sample. Raw compact evidence is in the Git-private validation-efficiency-fixture run; retain that baseline for slice 3.

## Next Steps

Scope: whole plan through all remaining phases and terminal delivery, subject to existing delivery approval gates.
Current slice: private ordinary-review proof on Fix/PrivateReviewEvidence.
Remaining scope: private ordinary-review proof and measured fixture optimization; batching applies throughout.
Done when: selected CI and consistent private review evidence are delivered with preserved safeguards, and demonstrated redundant fixture cost is addressed or explicitly dispositioned with evidence.

Finish the confirmed private-proof review/CI repairs, checkpoint and publish one stable candidate, then incremental-review and deliver PR #275. Causal main run 38905321932 is already green. After private-proof delivery, implement the measured immutable baseline fixture with isolated writable copies, verify before/after timing and behavior, then deliver that final slice.

## Host coverage

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": "The shipped review_evidence resolver supplies the same private identity and completion checks to review workflows, merge gates and delivery binding.",
  "hosts": [
    {
      "host": "claude",
      "behavior": "The Bash and PowerShell merge hooks resolve the canonical private receipt and retain the existing security and foreign-repository boundaries.",
      "source": ".agents/hooks/merge_review_gate.py",
      "mapping": "Canonical hook calls workflows/review_evidence.py, shipped to both hosts by the engineering resource mapping.",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "14 focused private-evidence regressions and the existing merge-gate regressions, including private acceptance and tamper rejection; installed-host adoption is outside this source change."
      }
    },
    {
      "host": "codex",
      "behavior": "The canonical pushd merge envelope resolves the same checkout and consumes the shared private receipt.",
      "source": ".agents/hooks/merge_review_gate.py",
      "mapping": "Canonical hook calls workflows/review_evidence.py, shipped to both hosts by the engineering resource mapping.",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Existing canonical-envelope/foreign-repository regressions and focused private merge-hook integration; independent native review remains required before delivery."
      }
    }
  ]
}
```
