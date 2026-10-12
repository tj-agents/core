# Repository settings configuration owned by Core

Status: active; PR208 owns committed candidate 531c793d285008f0bf8969eeed700b601b9326fe. Full independent review is complete with two reproduced settings-edge findings; classifier/parser repairs are pushed at178ba775bcddb68124d32a7e921b30902a62944b, with fresh incremental review and CI owned. B003 and required same-change harness alignment are implemented, parent-verified focused-green, and ready for one stable checkpoint followed by final incremental review/CI.
Date: 2026-10-11
Branch: Fix/RepositorySettingsContract
Worktree: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-RepositorySettingsContract
Base: origin/main at 73f1fbcc24efdda8ed1c0b0ccf07dc4064e7782c
Originating session: 01a12c10-0de6-7152-a9f2-9e5f374021f8
Lane: L4 implementation; contract and ownership decisions resolved, with meaningful tests catching the specified behavior. Independent security review selects L2; ordinary review selects L4; clerical delivery selects L7.

## Pickup and current evidence

Picked up on 2026-10-11 by native Codex session `01a12ccb-c604-77f1-bb4c-cc8c5e21ead1`, recorded PID `18768`, in this exact worktree and branch. The handoff contains no transfer receipt. The first action was reading the existing implementation goal and inspecting its checkout read-only.

The original L3 ownership investigation found substantial preserved uncommitted reader, resolver, hook, schema, documentation, tests and packaging changes under the superseded configuration.json contract. Ownership is now resolved by the exact controller's durable release below; the L4 writer will reconcile this single causal patch against the newer correction branch.

The original implementation writer is native child `01a12ad1-ca57-78c1-ac1b-7900005a5db8`, task `/root/implement_repository_configuration`, controlled by `01a122c4-e884-7402-a873-9fa7449e5c37`. Exact-session recovery resumed that controller, which contacted its existing child through native collaboration and recorded the child's explicit release to this successor.

One supported `machine:followup-codex` attempt to that exact controller returned `unavailable`: the existing app-server proxy is unavailable or disconnected. No send was attempted, no receipt was created, and no daemon, replacement session or second implementation writer was started. The private UTF-8 message is in the current Windows temporary directory as `core-settings-contract-01a12ccb-message.txt`; the reserved receipt pathname `core-settings-contract-01a12ccb-followup.json` does not exist.

The supported continuation owner at this checkout's `.agents/continuation/owner.json`, owner ID `2f1c1f446aebaa66d3a5a8ac`, is actively claimed by native PID `18768` with creation identity `134362265120029605`. Earlier scheduler registration and an explicit supported wake verified the foreground lease prevented a competing writer. The earlier blocked checkpoint was reconciled to WORKING during recovery. Register a supported wake for delayed delivery and rebind head through the supported checkpoint when committing.

At admission, no overlapping source path was edited before release. The original checkout remains preserved; the released causal patch is now being corrected by the single L4 writer here. Problem record: `MISTAKES.md#M008`.

## Outcome and authorization

Tommy explicitly requested a handoff to fix the configuration contract, then clarified that this and Kit/template are two independent handoffs. This goal owns the Core correction. Execute the authorized correction through implementation, meaningful Windows/Linux validation, independent review, PR, normal merge under applicable standing authority, and causal generated publication. Do not stop after a proposal or a source-only toggle.

A consuming repository has a settings.json containing a reusable configuration object. Users enable or disable options there. Core interprets the options centrally and ships the same behavior to Claude and Codex. It must work in an arbitrary consuming repository; it cannot require that repository to be tj-agents/core or a tj-agents plugin producer. Auto-merge is an initial option, not the entire configuration model. Do not invent unrelated settings just to demonstrate extensibility.

The user explicitly corrected the earlier assertion that Kit supplies this configuration template. Kit/template owns shared package structure; the configuration object and its interpretation belong entirely to Core. There is no Kit dependency for using these settings.

The exact settings path and envelope must respect the user's settings.json direction. Reconcile the repository's existing settings conventions and document one canonical path; do not silently keep a separate configuration.json as the final public interface or choose a host-private settings file. One illustrative shape is {"configuration":{"core":{"auto_merge":true}}}; namespace choice is a local contract decision, while simple enable/disable options and Core-owned semantics are required. Preserve unrelated settings and extension namespaces.

The consumer must not repeat Core's explanation, prose instruction, stop-class interpretation or repository-specific implementation at every opt-in. Core defines defaults, validation and behavior once. Distinguish the settings preference and the underlying authorized task in Core; preserve reviews, required checks, explicit holds and stricter work-repository instructions. Do not call a legacy delivery-authorization.json flag the completed generic configuration feature. Prove how an authorized task in an unrelated disposable repository uses the setting without manually copying boilerplate authorization explanations. This goal grants no unsolicited installation or settings changes in other consuming repositories.

## Problem evidence

The originating assistant presented the legacy delivery-authorization.json as the requested configuration and said the configuration was complete, despite observing a separate unfinished repository-configuration workstream. The user rejected that interpretation and clarified settings.json plus a configuration object with Core-owned meanings. Prevention condition: public docs, settings reader, both-host behavior and completion reports distinguish a generic settings interface from legacy authorization and prove the actual consuming-repository path. Preserve this evidence in the owning problem record during reconciliation; do not create another causal repair if the existing configuration workstream already records it.

## Existing owner and source boundaries

An existing Core checkout at C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-RepositoryConfiguration owns plans/repository-configuration/GOAL.md and has substantial uncommitted reader, consumer, schema, docs and test edits. Its old contract selects .agents/configuration.json and a separate Kit follow-up. That plan is governed by another Root controller. This handoff is the new user contract correction, not authority to overwrite, reset, cherry-pick uncommitted work or launch a second implementation writer over those files.

FIRST reconcile that exact owner, deliver this correction through supported native follow-up or coordinate a verified release. Reuse its causal implementation/goal wherever possible. This isolated checkout owns the correction/admission record until source ownership is reconciled. Do not edit overlapping runtime or hook paths while the existing writer owns them. If the existing owner receives the correction and completes it, track its actual outcome rather than build a duplicate repair. A real unresolved conflict needs the exact owner, paths, resolver and observable release condition; keep independent contract/verification preparation moving.

Read-only context:
- Existing implementation goal: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-RepositoryConfiguration/plans/repository-configuration/GOAL.md.
- Global rollout: C:/Users/TommySeery/source/repos/tj-agents/docs/plans/tj-agents-auto-merge/PLAN.md and PROGRESS.md. Do not edit that controller's checkout.
- Earlier configurable auto-merge PR #188 is merged. That fact does not deliver the generic settings interface.
- Independent Kit/template goal: C:/Users/TommySeery/source/repos/tj-agents/kit/.worktrees/Refactor-TemplateStructureContract/plans/template-structure/GOAL.md. Read only; no shared source writer.

## Acceptance

- One documented repository settings.json interface holds a configuration object and preserves unrelated options.
- Core owns option meanings, defaults and strict validation, with no repository identity allowlist.
- True, false, missing and invalid settings behave predictably; edits are re-read by real consumers and malformed present settings do not silently enable behavior.
- An unrelated disposable consuming repository can enable guarded auto-merge under its existing authorized task without copied interpretation or repeated boilerplate.
- Claude and Codex use the same shipped Core reader/resolver and maintain review, CI and explicit hold behavior.
- Existing configuration ownership is reconciled, and a single causal implementation is reviewed, merged and causally published.
- Completion reports the generic settings interface only after its actual behavior is verified. No Kit template or normal-profile installation is claimed.

## Recovery after the user called out abandonment

Tommy challenged the manual ownership blocker and instructed this session to resolve coordination without making him intervene. On 2026-10-11 this session invoked the shipped machine:open-codex helper for exact controller 01a122c4-e884-7402-a873-9fa7449e5c37 with a private prompt containing the correction and bounded source-release request. The helper returned success, and the native registry now identifies that same session alive under PID 1216. This verifies exact-session recovery; it is not delivery of the earlier follow-up or source release. Observe the existing Feature-RepositoryConfiguration goal for acknowledgment/release and continue the same settings outcome.

The consumed followup-codex manual-only fallback was a contributing standards defect. One disjoint engineering:handoff side workstream was launched through the supported native launcher at C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-FollowupRecoveryOwnership/plans/followup-recovery/GOAL.md, branch Fix/FollowupRecoveryOwnership, lane L3. The launcher confirmed Codex 0.163.0-alpha.1 submission; the native registry identifies successor 01a12d05-0e36-7cd2-afac-1936aa63404b, PID 9104. The side successor owns only the existing follow-up/recovery standards and directly needed behavior tests, with no settings-source or original-controller coordination ownership. This session retains the original foreground lease and task. A submitted side session does not complete either goal.

## Prepared contract and verification cases

The bounded contract preparation selects `<actual-checkout>/.agents/settings.json` as the host-neutral public interface. Neither `.claude/settings.json` nor `.codex/config.toml` owns this shared setting. The minimal document is `{"configuration":{"core":{"auto_merge":true}}}`. A root JSON object may contain unrelated settings; Core preserves them and reads only the configuration object. No mandatory new version field is imposed on unrelated settings. A missing configuration/core/auto_merge resolves false in a present settings file. Namespace objects remain extensible and opaque outside `core`; `core.auto_merge` is a strict boolean and unknown Core option names are rejected.

Reject malformed or unreadable present settings, duplicate keys at every depth, non-finite JSON values, invalid namespace shapes, directories and redirected/dangling paths. Read the actual absolute checkout root on each consumer invocation without ancestors, profile lookup or repository identity restrictions. A present settings file is authoritative; false or missing options cannot be overridden by legacy true. Preserve only the already published, fully validated legacy authorization preference when settings are wholly absent. The unmerged `.agents/configuration.json` draft is not a second public interface or a published compatibility commitment.

Route the actual engineering and machine consumers through one shipped reader/resolver. Treat preference separately from authority even when the legacy authorization file is absent. Inspection found `workflow_ops.standing_authorization` has an early absent-file return, `delivery_binding_gate.auto_merge_enabled` requires that legacy file, and `auto_merge.current_authorization` already composes an existing exact scoped approval. The old implementation must prove its corrected reader reaches the absent-standing-authority branch; simply renaming the input path does not prove arbitrary-consumer behavior. The guarded command continues to enforce valid scoped/standing task authority, current binding identity, all stop classes, explicit holds, current independent/security review and required checks.

Verification after ownership reconciliation must cover:

- An unrelated disposable repository with spaces and Unicode in its path, only the Core settings preference plus its existing exact scoped task approval, and no copied per-repository Core explanation or legacy standing declaration.
- True, false, absent file, present empty object, missing configuration/core/option, malformed JSON, nonboolean values, unknown Core option names and opaque unrelated settings/namespaces.
- Fresh file edits from true to false after binding, false/omitted authoritative values against legacy true, and denial/removal of stale conditional grants for invalid present settings.
- Explicit hold labels, each stop class and stricter work-repository instructions; settings changes classified as authorization-sensitive and security-reviewed work.
- Both generated Claude and Codex reader/resource mappings, real packaged machine consumer loading, focused/full Windows and Linux checks and causal post-merge publication. Local source tests alone establish no normal-profile activation or consumer adoption.

## Reconciled release and execution slice

The existing source goal records "Source ownership release and superseded contract" at `2026-10-11T22:16:13Z`, naming this exact successor UUID and correction checkout. It records the child's explicit acknowledgment, releases the enumerated authored paths and unused leases, and preserves a SHA-256 inventory of the dirty implementation at source head `316e77345dffcd497476879cc0acc653ea383626`. The original controller retains no implementation writer and will not adopt this checkout. The old configuration.json and Kit instructions are explicitly superseded. This is durable source-release evidence; no user relay is required.

One bounded L4 worker `/root/implement_settings` owns the released reader/resolver, consumers, schema, packaging, public docs and focused tests in this checkout. Parent retains this goal, problem records, review and delivery. The source checkout remains read-only and preserved. Apply tracked changes selectively against the current base, reuse new source files, and regenerate package output locally; never copy old generated output or commit `plugins/**`.

Delivery slice: one atomic settings reader and its real engineering/machine consumers, guarded scoped-authority tests, schema/public contract and necessary resource mapping. Measure substantive source/test changes before the 1,000-line trigger and reassess scope before expansion. Catalog synchronization and planning records are measured separately. Independent review is against the focused-green immutable source commit, followed by exact-head Windows/Linux CI, normal merge and causal publication.

## Current validation checkpoint

The L4 writer completed and released its authored paths without committing. Parent independently read the saved terminal unittest summaries: reader 11 tests (2 privilege skips), delivery runtime 36, guarded auto-merge 10, delivery-binding gate 38, merge-review gate 82 (1 skip), machine consumer 28, harness manifests 14 and source layout 21. All eight scopes passed: 240 tests, 3 skips. Catalog refresh, manifest consistency, local generation and the final generated check passed. The substantive candidate is 517 changed lines, including runtime 243, tests 225 and docs/schema 49; catalog digest and generated output are measured separately.

Initial test failures were confirmed in saved artifacts, repaired by adding the missing delivery_policy import and comparing the public ValueError boundary across dynamic module loads, then replaced by observed passing artifacts. The transient fake gh.cmd cleanup failure did not recur in the passing binding suite. M010 is reconciled. No candidate was committed from the misleading helper exit; full Windows/Linux verification remains owned by exact-head CI.

## Delivery map

- Runtime slice `Fix/RepositorySettingsContract`, base `73f1fbcc24efdda8ed1c0b0ccf07dc4064e7782c`; PR: 208 (draft). Includes settings contract, active engineering/machine consumers, strict validation, scoped-task guard tests and resource mapping. Focused local checks and exact-head full Windows/Linux CI precede delivery. Measured substantive code/test/docs-schema delta: 517 changed lines; catalog 4 lines, generated output excluded.
- Subsequent guidance slice `Docs/RepositorySettingsPreference`, from the then-current remote default after runtime publication; PR: not opened. Correct only the existing persistent-delivery skill's legacy-only preference explanation, which is a durable guidance change and must ship separately under git-branching. Expected substantive guidance delta below 100 lines plus required harness wording; catalog digests remain generated and uncommitted. Reuse the retained goal, validate both generated host adapters and applicable harness/skill packaging, review as a shipped skill change and observe exact causal publication. No implementation API or consumer installation belongs to this second slice.

## Next Steps

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/workflows/repository_configuration.py and shared engineering/machine preference consumers",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Read repository settings and enforce guarded auto-merge with independent task authority",
      "source": ".agents/workflows and .agents/machine/utility/bootstrap-capabilities/scripts/harness_permissions_sync.py",
      "mapping": ".agents/plugins/sources.json engineering workflows and machine sibling-reader resource for Claude payloads",
      "verification": {"level": "planned", "result": "pending", "evidence": "Focused arbitrary-repository scoped-task tests, packaged machine loading, generated Claude parity and exact-head Windows/Linux CI"}
    },
    {
      "host": "codex",
      "behavior": "Read repository settings and enforce guarded auto-merge with independent task authority",
      "source": ".agents/workflows and .agents/machine/utility/bootstrap-capabilities/scripts/harness_permissions_sync.py",
      "mapping": ".agents/plugins/sources.json engineering workflows and machine sibling-reader resource for Codex payloads",
      "verification": {"level": "planned", "result": "pending", "evidence": "Focused arbitrary-repository scoped-task tests, packaged machine loading, generated Codex parity and exact-head Windows/Linux CI"}
    }
  ]
}
```

1. Commit the verified settings-edge repairs, push the same PR208 branch, refresh its delivery binding, then rebind and reclaim the existing continuation owner at the full corrected head.
2. Freeze an incremental review from completed watermark 531c793d285008f0bf8969eeed700b601b9326fe without another full-review synchronization. Complete independent ordinary/workflow/security review and observe the replacement head's Windows/Linux CI through one owned monitor.
3. Reconcile the current base and review, ready PR208, perform the normal guarded merge under recorded authority, and verify the exact merge's causal generated publication.
4. Deliver the existing persistent-delivery preference explanation separately from the updated main branch, with its required harness/catalog changes, review, CI and causal publication. Keep this same goal and source boundaries.
5. Reconcile M008 and B001/B002 against observed delivery, complete closeout and the canonical continuation owner. No Kit dependency, consumer installation or repository opt-in belongs to this correction; no repeated user permission is needed.

## Independent review repair checkpoint

PR208 at head 531c793d285008f0bf8969eeed700b601b9326fe has a validated body, exact delivery binding and one reconnect-safe CI observer for run38183296901 attempt1. Native-general specialist capability was rejected by this host/account; the available bounded L4 parent fallback reviewed the same immutable candidate. Native-general and workflow reviews found no defects; independent L2 authorization/security review reproduced Windows casing classifier misses and deep-JSON stale conditional grants. Parent verified the defects and finalized reviews/Fix-RepositorySettingsContract.md as changes-requested at that frozen head. B001 and B002 record them under this same causal repair. One exclusive L4 writer addresses this tightly bounded settings-edge group, then parent commits/rebinds, incrementally reviews, and publishes one stable corrected head to the same PR. The observed first CI run does not establish replacement-head validation.

## Verified settings-edge repair

The exclusive L4 writer released all nine repaired source/test/catalog paths. Parent verified case-insensitive settings stop/security classification, the guarded-command uppercase settings regression, and normalization of decoder RecursionError to the public ValueError boundary. The strengthened machine regression first asserts active owned Claude and Codex wrapper grants, then applies deeply nested invalid present settings and asserts removal from both hosts. Saved focused terminal artifacts in repository-settings-review-fixes-001 report reader 12 (2 skips), runtime 36, guarded auto-merge 10, settings security patterns 10 and machine synchronization 28: 96 passing tests with 2 skips. The final generator check reports 527 files, 0 changed, 0 pruned. Earlier invalid unittest class selection and fixture seeding attempts failed and were replaced by these actual passing reruns; they are not counted as validation.

The bounded repair changes 63 source/test lines plus 4 catalog digest lines; it adds no unrelated API or installation scope. B001/B002 remain in progress until independent incremental review, exact-head Windows/Linux CI and normal causal delivery meet their objective conditions.

## CI generated-digest correction

The owned observer reached terminal failure for run38183296901 at the original 531c793d285008f0bf8969eeed700b601b9326fe head. Authoritative failed-step logs identify only the PR generated-output guard: engineering/machine catalog digest changes are generated publication output and cannot be committed in Core PRs. Restore those digest values to the actual merge-base baseline, keep all runtime fixes, and require scripts/check_generated_paths.py to pass on the corrected committed candidate. The post-merge job updates digests. This is a candidate preparation error, not a permission gate or a reason to weaken CI. Remaining jobs and the replacement head must be observed independently.

## No-legacy invalid-settings consumer repair

Fresh independent security review verified the classifier/parser repairs, then distinguished an existing initial-candidate error boundary outside that incremental delta. Parent reproduced it: workflow_ops.standing_authorization translates DeliveryContractViolation only when the legacy policy exists; the arbitrary repository path calls resolve outside that try. Invalid settings still deny merge, but the guarded command lacks its controlled diagnostic. B003 records this same authorized settings outcome; normalize the shared consumer boundary and prove malformed/deep invalid settings through actual guarded-command main with zero merge calls. This is an ordinary bounded repair, not an ownership or permission gate. Preserve completed review identities and review the new committed delta before final-head CI/merge.

## Completed first incremental review

Range531c793d285008f0bf8969eeed700b601b9326fe..178ba775bcddb68124d32a7e921b30902a62944b completed with zero new changed-line findings. Canonical reviews/Fix-RepositorySettingsContract.md now has watermark178ba and clean completed incremental judgment; original full-pass changes-requested judgment and R001/R002 identities remain intact. Fresh native-general, workflow and L2 security evidence was reconciled, including rejection/correction of a wrong review-base-versus-PR-base guard claim and unretained test claims. Parent verified the strengthened machine artifact; L2 independently ran 11 bounded frozen regressions. Current-base reconciliation is exact and unchanged. The same exclusive L4 writer now owns only workflow_ops.py and test_auto_merge.py for B003; no new PR, source owner, permission gate or normal-profile operation is introduced.

## Verified final consumer and harness repair

B003's real guarded-command main regression failed before the source change with exactly two absent-policy errors (malformed/deep settings), then passed after both resolve paths shared the existing WorkflowOperationError translation. Parent inspected the stronger diagnostic assertion and terminal artifacts in repository-settings-b003: auto-merge11, delivery-binding38, harness manifests14 (63 tests passed), plus manifest consistency checked3 declarations. The source writer released all five paths without committing. The measured repair is79 changed lines, including necessary authored catalog harness wording; no digest or generated package change is included.

The engineering harness now describes the validated repository settings preference, and the machine harness declares the two canonical shared reader/resolver dependencies already embedded by the source mappings. Catalog mirrors only the authored engineering justification and preserves merge-base generated digests. This satisfies required same-change shipped harness alignment; no permission command, installation or skill body is added here. Exact-head CI38184988930 at reviewed178ba775bcddb68124d32a7e921b30902a62944b completed successfully; that success is retained as its own evidence and does not validate the forthcoming final head.
