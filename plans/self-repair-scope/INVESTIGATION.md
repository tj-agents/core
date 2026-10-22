# Self-repair investigation

## Accepted implementation

Tommy accepted the internal tooling boundary and requested the update. Core's self-repair source now
limits automatic repairs to demonstrated reusable defects in authorized `tj-agents` tooling, with
explicit personal scope for both the originating task and source. Employer tooling remains outside
automatic scope, and other standards owners require explicit source-repair authority. Personal product
maintenance retains the existing engineering lifecycles. An adequate rule permits no source change.

Core's session, handoff, close and problem-record callers now follow that decision and permit retaining
facts while a profile's recording decision is pending or declined. Both self-repair host adapters carry
the same discovery description. The source-policy checks have been updated to the accepted contract.

The Infonetica source update is isolated on `Fix/AzureCreationConsent` in
`C:/Users/TommySeery/source/repos/tj-agents/infonetica.worktrees/Fix-AzureCreationConsent`, based on its
current `origin/main`. `create-work-item` owns the creation decision; work-context, ship, implement and
open-pr route to it. Existing intended items are reused. No new tracker item, host hook, runtime consent
flag or second repair workflow is introduced. This is instruction-level policy, not proof that a model
will comply or an API caller has conversational permission.

Source review and local validation are recorded below when complete. Generated Core package output is
refreshed only for validation and excluded from the source commit. Installation and fresh-session
acceptance remain separate; this source change does not update already-loaded instructions. The live
session-store writer was not activated: its shipped rollout notice requires compatible installed
readers before schema-4 writes. Native-history recovery identified this session as the live owner of
the self-repair investigation and found no separate live owner of the Azure-creation topic.

The following sections retain the investigation and earlier source snapshot as evidence; the accepted
implementation supersedes their proposed or pending policy decisions.

## User decision and investigation direction — 22 October 2026

Tommy clarified that autonomous Azure Boards creation is unwanted. When Tommy explicitly requests an item, that request authorizes creation within its stated scope. When the AI proposes an item, it must first ask whether Tommy wants it created and wait for an affirmative answer. Discovering a problem, selecting an Infonetica provider, or having permission to implement code does not supply that answer. An item should represent work Tommy intends to address at some point; an observation alone is insufficient. This employer policy belongs in `tj-agents/infonetica`. Personal-project autonomy should remain available.

The remaining question is the useful scope of self-repair. This investigation recommends separating three decisions: correcting the active task, repairing a reusable agent standard, and creating a tracker item. Permission for one does not imply permission for the others. No Azure Boards or GitHub item was created for this investigation, and no runtime policy was changed.

## Concrete use cases

| Situation | Useful response | Self-repair value |
| --- | --- | --- |
| A handoff workflow drops the active task or transfers to a second writer | Reproduce the workflow failure and repair the shared handoff implementation or governing rule | Strong: future sessions share the same defect |
| An agent reports unattended delivery although its continuation scheduler never registered | Distinguish misleading workflow guidance from a runtime failure; repair the causal owner and test the unavailable-scheduler path | Strong when a reusable source defect is established; historical M003 supplies an observed incident |
| An agent ignores a clear instruction to inspect state after a failed patch | Inspect the actual state, correct its report and complete the task | No automatic standards edit: historical M007 shows the mistake, but a mistake alone does not establish an inadequate rule |
| A Concertable skill points at an unavailable standard or omits a required composition-validation root | Verify the broken route or missing requirement against the owning standard; repair `Concertable/agents` if the reusable source is defective | Strong, conditional on an established standards defect and source authority; this is a hypothetical example, not a diagnosed Concertable failure |
| One Concertable application has an incorrect DI registration while its standard is adequate | Correct that application under its existing task and test it | Ordinary product repair; no additional self-repair or work item follows automatically |
| A work session proposes an Azure item merely because a reusable agent rule misbehaved | Keep employer details private; correct the active task and propose a source repair when useful | Reusable source repair may help, but this is not employer product backlog; personal agent tooling already has a no-ADO rule |
| A work session notices a separate product bug outside the requested change | Explain the finding; ask whether Tommy intends to address it and wants an item | A product backlog decision, not self-repair |
| A preference changes, such as adopting a different library or design | Discuss the desired behavior and its scope | A design decision, not evidence that the previous standard was defective |

Self-repair earns its cost when a concrete reusable instruction or runtime defect explains the observed mistake and a bounded correction can prevent recurrence. Repeated mistakes justify diagnosis; they do not prove another rule, hook or tracker item is needed. An adequate-rule/no-source-change outcome must be a normal result.

## Recommended scope and policy ownership

Keep the reusable repair mechanism in Engineering and limit its subject to agent standards, skills, routing, hooks and lifecycle tooling. Fix application behavior through its existing lifecycle. Diagnose which source owns the cause before changing it; the current self-repair skill names Core, while the session policy also refers to consumed standards packages more generally. Supporting Concertable's own standards requires an explicit source-owner boundary rather than treating all standards as Core-owned.

Keep high autonomy for explicitly adopted personal projects, including a personally adopted Concertable standards repository. In an employer task, recommend and scope a separate standards repair before diverting that task into a cross-repository repair or source publication. The originating employer task's permissions still apply even when the proposed destination is a personal tooling repository. Stop an actually unsafe affected operation when necessary; a generic P1 source classification should not by itself take over unrelated employer work.

Infonetica owns consent for Azure Boards creation, the requirement that items represent intended future work, and employer-specific metadata. Core's recording contract should defer to that policy and recognize 'awaiting a recording decision' without demanding a replacement issue or another tracker. Personal may retain proactive recording under its own adopted policy. Fixing a reusable agent standard does not itself require a product work item.

## Additional source findings

- Existing Infonetica `plugins/infonetica/skills/work-context/SKILL.md`, line 62, already says agent tooling receives no ADO work item. The new consent rule generalizes control over AI-originated employer product items; it should preserve that existing tooling boundary.
- Core `.agents/engineering/policy/session/SKILL.md`, lines 71 onward, instructs agents to record noticed problems. The selected profile controls record policy, but this call site does not explicitly distinguish selection from consent to create.
- The newer Infonetica source in `../infonetica.worktrees/Fix-TjAgentsDependencies/plugins/infonetica/skills/create-work-item/SKILL.md`, line 13, asks about assignment, parent and branch. It does not explicitly ask whether an AI-proposed item should exist. Its deterministic helper validates inputs, repository scope and request identity, then can POST; these are not proof of user intent.
- Both the older `create-devops-item` surface and the newer `create-work-item` surface need to be accounted for by the actual source owner. `open-pr` currently tells the agent to invoke item creation when a linked item is missing; `ship` and `implement` also compose item creation. These paths must respect the same consent policy rather than making missing linkage an independent creation authorization. An existing intended work item should be reused when applicable.
- `Concertable/agents/README.md` identifies that repository as the owner of reusable product-specific contracts, routes and hooks; its `AGENTS.md` contains explicit Personal adoption and its `.problem-records.json` selects `personal:work-item`. Its composition-testing and always-on skills demonstrate reusable instruction/routing surfaces that could benefit from standards repair. That evidence does not establish Personal adoption in every Concertable consumer; the inspected `Concertable/system` checkout had neither `.agents/plugins.json` nor `.problem-records.json` at its root.

These findings are source inspection. No live employer operation, installed-host acceptance probe or autonomous standards repair was performed. Cross-repository source references above identify the inspected local checkout; source worktree contents are not claimed to be published behavior.

## Initial source audit

Requested investigation, 22 October 2026. This records policy gaps found by source inspection; it does not authorize a workflow redesign or report an observed employer-data disclosure. Audited Core main at 412b8d11493dea9ea27ff5fff1a2cc21e5e751d7.

Current behavior: engineering:session routes user mistake callouts to engineering:self-repair after answering the direct question. Self-repair investigates whether a consumed Core standard, skill, hook, workflow or host enforcement caused or failed to prevent the mistake. It reconciles an existing repair owner, records through the selected profile, and repairs in the current session. Unrelated checkouts require a separate worktree of the standards source repository. Handoff requires the user to ask. Standing authority includes implementation, tests, review, PR, merge and source publication after that repository's gates. Explicit user limits remain binding. Shared ownership/completion/handoff/cleanup failures default to P1 and pause unrelated work and new launches until verified correction or explicit deferral. Completion currently permits repaired/tested/committed source or a recorded blocker, then resumption of the original task. Loaded sessions retain their old instructions.

Personal versus work: this is one shared Engineering workflow, applicable when Engineering is selected. Personal requires explicit personal adoption and selects personal:work-item / personal:create-work-item / personal:address-work-item backed by GitHub. Infonetica employer scope selects its qualified counterparts backed by Azure Boards and employer-native types. Employer incident evidence must remain with the employer provider; a GitHub owner, personal directory or the tj-agents/infonetica source repository does not establish personal scope. Neither installing Core nor repairing a standard authorizes adopting Personal or installing into the consuming repository. Missing/invalid/unavailable provider selection blocks recording and retains unsent facts in active task context with a resolver and resume condition; historical Markdown registers are not a fallback backlog.

## Expected boundary

The workflow should distinguish investigating a callout from establishing a source defect and explain a truthful no-source-change outcome when the existing rule is adequate. An employer incident does not automatically belong in Azure Boards: retain relevant facts within the authorized employer task, respect the Infonetica creation decision, and identify any separately authorized standards repair without copying confidential evidence. Completion should make source correction, publication and installed/fresh-session verification distinguishable.

## Findings

1. No explicit no-source-change disposition: the diagnosis step distinguishes missing, ambiguous, unenforced and ignored rules, but the next mandatory step says to fix the standard and completion names only repaired source or a blocker. It does not explain how to conclude that an adequate rule was ignored without inventing another rule.

2. Origin/source recording ambiguity: self-repair says to use the selected profile, then moves work to the source repository. The recording contract selects from the source primary checkout and protects employer-owned facts, but self-repair does not explicitly preserve the originating employer record, define a sanitized linked Core record, or state which repository supplies selection at each stage. The general confidentiality boundary exists; the cross-repository procedure is underspecified. No actual disclosure was observed.

3. Runtime verification limitation: current authored Engineering hook manifests on both hosts wire the GitHub credential-scope gate, not a callout repair gate. The old callout gate and handoff admission script were deliberately removed. Current self-repair selection and completion are instructional. Existing process-standard tests assert guidance text, not live model compliance. Restoring the removed hook is not implied by this report.

4. Source versus rollout completion: standing authority extends through publication while completion permits a tested local commit; the workflow acknowledges already-loaded instructions remain unchanged. It does not itself define installed-host or fresh-session acceptance for each kind of repair. Other repository policies may impose additional checks.

## Evidence and verification

Core source at audited commit:
- https://github.com/tj-agents/core/blob/412b8d11493dea9ea27ff5fff1a2cc21e5e751d7/.agents/engineering/workflow/self-repair/SKILL.md (trigger, repair boundary, authority and completion).
- https://github.com/tj-agents/core/blob/412b8d11493dea9ea27ff5fff1a2cc21e5e751d7/.agents/engineering/policy/session/SKILL.md (callout selection; questions/reviews alone do not authorize implementation).
- https://github.com/tj-agents/core/blob/412b8d11493dea9ea27ff5fff1a2cc21e5e751d7/.agents/engineering/resources/problem-records.md (provider selection, employer evidence retention and missing-provider behavior).
- https://github.com/tj-agents/core/blob/412b8d11493dea9ea27ff5fff1a2cc21e5e751d7/README.md#refresh-and-repository-boundaries (explicit personal adoption and employer scope).
- https://github.com/tj-agents/core/blob/412b8d11493dea9ea27ff5fff1a2cc21e5e751d7/.agents/plugins/manifests/codex/engineering-hooks.json and corresponding claude/engineering-hooks.json (current wiring).
- https://github.com/tj-agents/core/blob/412b8d11493dea9ea27ff5fff1a2cc21e5e751d7/.agents/hooks/tests/test_process_standards.py (text assertions, not behavioral host proof).

Historical context: local plans/self-repair-admission-deadlock/GOAL.md describes an older callout admission failure. plans/session-store-retention/PLAN.md records the 18 October decision to remove the callout gate, admission.py and forced handoff. Those old plan expectations must not be treated as current runtime behavior.

Validation: python -B -m unittest discover -s .agents/hooks/tests -p test_problem_records.py -v passed all 9 tests on Windows. This verifies provider resolution, primary-worktree selection and rejection paths, not a live work-to-Core repair or model compliance. Installed Personal provider inspection succeeded; existing open Core work items were listed before recording and none matched. Infonetica replacement provider skills were inspected only in the existing Fix-TjAgentsDependencies source worktree; they were not loaded as this repository's governing profile and their installed-host acceptance was not established. No employer tracker was contacted, profile changed, real agent launched, or runtime repair implemented.

## Implications

A callout can interrupt authorized product work and begin a broadly authorized Core delivery. Without explicit causal and cross-repository dispositions, agents may add unnecessary rules, mishandle the relationship between employer incidents and Core repair records, or overstate completion from source-only evidence. These are demonstrated specification gaps and verification limits, not reproduced disclosure or enforcement failures.

## Proposed resolution for a future repair

Agree and document the existing workflow's causal decision outcomes, including an adequate-rule/no-source-change result. Define origin incident versus source repair ownership and provider selection without moving employer details to Personal or presuming any new employer item should be created. Apply the user's settled Azure creation policy in the Infonetica source owner and reconcile Core callers with it. Define proportional source/publication/installed acceptance evidence and preserve explicit user limits, existing live repair ownership and monitoring-only deliveries. Verify representative personal and employer paths, including declined creation, missing providers and an adequate existing rule. Keep the broader self-repair scope redesign pending a decision; this file captures the requested investigation.

## Record publication

The selected Core provider resolves to personal:work-item. Existing open Core records were inspected successfully; none matched this investigation. Automatic approval review rejected the initial attempt to create a GitHub issue because it considered the payload, external destination and Personal-provider use insufficiently authorized. No issue was published. Tommy's subsequent direction is to investigate actual use cases and prevent AI-originated employer backlog creation without a decision. This file preserves that investigation; no publication is part of the current scope.
