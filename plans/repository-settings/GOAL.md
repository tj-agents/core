# Repository settings configuration owned by Core

Status: blocked on existing source ownership; contract and verification preparation complete.
Date: 2026-10-11
Branch: Fix/RepositorySettingsContract
Worktree: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-RepositorySettingsContract
Base: origin/main at 73f1fbcc24efdda8ed1c0b0ccf07dc4064e7782c
Originating session: 01a12c10-0de6-7152-a9f2-9e5f374021f8
Lane: L3 for ownership reconciliation and the bounded settings contract; re-route specified implementation to L4 and delivery to its appropriate lane.

## Pickup and current evidence

Picked up on 2026-10-11 by native Codex session `01a12ccb-c604-77f1-bb4c-cc8c5e21ead1`, recorded PID `18768`, in this exact worktree and branch. The handoff contains no transfer receipt. The first action was reading the existing implementation goal and inspecting its checkout read-only.

Ownership reconciliation is L3 because the existing writer's native identity and release state are unresolved. Its goal still specifies `.agents/configuration.json`, exact envelope keys and a Kit follow-up. Read-only Git status confirms substantial uncommitted reader, resolver, hook, schema, documentation, tests and packaging changes. There is no verified release and no runtime path has been edited in this checkout.

The implementation writer is native child `01a12ad1-ca57-78c1-ac1b-7900005a5db8`, task `/root/implement_repository_configuration`, whose session metadata identifies controller `01a122c4-e884-7402-a873-9fa7449e5c37` in `C:/Users/TommySeery/source/repos/tj-agents/rust/.worktrees/Fix-RustStandardDiscovery`. The registry and bounded recovery search report that controller closed. The child's recorded final response does not establish a release. Process closure is not durable source release.

One supported `machine:followup-codex` attempt to that exact controller returned `unavailable`: the existing app-server proxy is unavailable or disconnected. No send was attempted, no receipt was created, and no daemon, replacement session or second implementation writer was started. The private UTF-8 message is in the current Windows temporary directory as `core-settings-contract-01a12ccb-message.txt`; the reserved receipt pathname `core-settings-contract-01a12ccb-followup.json` does not exist.

The supported continuation owner was initialized at this checkout's `.agents/continuation/owner.json`, owner ID `2f1c1f446aebaa66d3a5a8ac`, and claimed by native PID `18768` with creation identity `134362265120029605`. Windows scheduler registration succeeded as `AgentStandards-Continuation-cedb7bc9e8d4a6c22d918d10a91a3f534c78f5d037bbc2cbeaddc01148acef03`; an explicit supported wake returned `working` while the foreground claim prevented a competing writer. These observations verify the scheduler path, not implementation or source release. The owner is checkpointed blocked and the scheduled wake removed at the ownership gate; do not claim unattended coordination with the closed controller.

No overlapping runtime, hook, schema or test paths were edited. The source and generated changes in the existing checkout remain preserved. Problem record: `MISTAKES.md#M008`.

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

## Ownership gate and next action

Blocked action: any overlapping source implementation, migration of the existing uncommitted patch, PR or delivery for that causal implementation.
`blocked_by`: conflict, with an unavailable coordination capability.
Existing owner: controller `01a122c4-e884-7402-a873-9fa7449e5c37` and child `/root/implement_repository_configuration` (`01a12ad1-ca57-78c1-ac1b-7900005a5db8`).
Owned paths: the source/test/packaging paths enumerated in `Feature-RepositoryConfiguration/plans/repository-configuration/GOAL.md`, including the configuration reader, delivery resolver/runtime, hooks, machine permission consumer, schema, docs and tests.
Resolver: that controller or Tommy's explicit ownership reassignment after preserving its uncommitted implementation.
Unblock action: the existing controller acknowledges this correction and checkpoints its updated causal implementation, or durably releases the listed paths and implementation for this goal. Restore its supported native endpoint only through an owner-supported recovery; do not create a replacement writer or silently infer release from a closed process.
Observable resume condition: an acknowledgment/corrected owner goal or explicit source-release/reassignment record naming that exact implementation checkout and owned paths.
Next execution action: reconcile the recorded release/result, apply this contract to the single existing causal implementation at L4, and run the arbitrary-repository scoped-approval case before the wider both-host Windows/Linux suite, review and authorized delivery.

## Next Steps

Blocked: Overlapping implementation and delivery of the preserved Feature/RepositoryConfiguration patch; this is a dependency/ownership gate, not missing merge permission.
Blocked by: Controller 01a122c4-e884-7402-a873-9fa7449e5c37 and child /root/implement_repository_configuration (01a12ad1-ca57-78c1-ac1b-7900005a5db8) own the reader, consumers, hooks, schema, packaging and tests in C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-RepositoryConfiguration. The controller is recorded closed without durable path release, and its supported native follow-up endpoint is unavailable with no send attempted.
Unblock action: The existing controller acknowledges and applies the corrected settings contract or durably releases its enumerated source paths; alternatively Tommy explicitly reassigns the preserved implementation. Preserve its uncommitted work in either case.
Resume when: An observable corrected owner checkpoint, explicit source release or Tommy's reassignment identifies that exact checkout and implementation. Then reconcile the single causal patch and implement/verify the settings.json contract at L4 through the already authorized review, merge and publication boundary.

1. Resolve the ownership gate above. The supported follow-up attempted no send. The fallback correction message was supplied in the session and retained privately; do not report it delivered or resend with a new receipt after an uncertain submission.
2. Read the reconciled existing implementation checkpoint. Continue its single causal correction or, after verified release/reassignment, integrate its preserved work under this goal. Do not overwrite, reset or copy uncommitted source before that condition.
3. Implement the prepared settings contract at L4, verify arbitrary consuming-repository behavior and both shipped hosts on Windows/Linux, independently review, open the owning PR, merge under the recorded authority and verify causal generated publication.
4. Keep this goal and M008 aligned with observed results. No Kit dependency, consumer installation or repository opt-in is part of this correction. Do not ask Tommy to repeat the contract or ordinary merge permission.
