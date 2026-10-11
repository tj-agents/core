# Repository settings configuration owned by Core

Status: prepared for one Codex handoff; pickup not yet verified.
Date: 2026-10-11
Branch: Fix/RepositorySettingsContract
Worktree: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-RepositorySettingsContract
Base: origin/main at 73f1fbcc24efdda8ed1c0b0ccf07dc4064e7782c
Originating session: 01a12c10-0de6-7152-a9f2-9e5f374021f8
Lane: L3 for ownership reconciliation and the bounded settings contract; re-route specified implementation to L4 and delivery to its appropriate lane.

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

## Next Steps

Acknowledge this handoff in this goal with the exact native session identity. Load plan-execution, lanes and the relevant source conventions. Reconcile the existing Feature/RepositoryConfiguration owner and forward the user's correction before overlapping writes. Then update the same implementation contract or proceed after verified release, implement the settings interface and consumers, validate meaningful behavior on Windows/Linux and both shipped host payloads, independently review and deliver through the authorized merge/publication boundary. Keep this goal aligned with observed ownership and results; do not ask Tommy to repeat the already given correction or ordinary merge permission.
