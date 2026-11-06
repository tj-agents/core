# Completion and skill identity cutover

## Recovery — 2026-11-03

Current owner: `codex01a19c96-ebdd-7d42-8186-d1f8c3abf92a`. Native observation closed the old owner and
its exact old registration was previously removed; no unattended continuation is claimed. Preserve the
history below and the dirty prior goal recovered from stash
`aab256f6600355dd7ff9f17e27de1e42ccb1d8eb`; current main is merged at
`98a442d6`. Tommy explicitly prioritized two investigations and their correction over the bot rollout,
which remains paused.

Investigation one found `aeb36e4a` deliberately narrowed the replacement into a split, while committed
removal `605feed` remains unmerged in PR #521 with red native CI Core #524 and the committed Skill roster
removal still missing. Investigation two found tests demanding the old identity and a generator that checks
only consistency, allowing a retained narrower policy; no literal compatibility forwarder was found.
Workflow now owns run, continue, evidence, and authority; Engineering owns technical checks. Reuse the
existing lifecycle and code: add no orchestration component or PR. Recover PR #521, then complete source
and generated-host old-name removal, Workflow-only continuation transport and package integration,
authored-caller scan, focused Windows/Linux and fresh known-native installed cutover after shipping. Do
not record migration complete until installed acceptance is observed. Existing shared startup/close-API
work remains with its prior owner. Current source router tests pass 35; regenerated completion tests pass 22; transport tests pass 46 with
6 platform skips; standards routing tests pass 18. Full exact-head remote and installed acceptance remain
pending. Next action: complete package checks, freeze source review, then push the existing PR #521.
Native source review and fresh Workflow/API and security readers found no actionable introduced defect
at `21008147092ca498489f7d6f2e2223752ad0da9f`; the canonical private receipt records that completed pass.
Exact-head CI `41621767120` passed startup/discovery on Windows and Linux, then failed the same two
packaging fixture assumptions on both platforms. The targeted fixture repairs now pass locally (2 tests):
preserve the shipped Codex continuation directory when copying source and verify continuation identity
rather than an obsolete hard-coded skill count. Next action: commit and incrementally review that delta,
push the same PR, and observe fresh exact-head CI before guarded merge and installed-host acceptance.
The broad local workflow-contracts run hit inherited Git environment and concurrent temporary-directory
copying failures; it is not reported green. Source-host coverage remains distinct from installed evidence.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/workflow/workflow/continue/SKILL.md",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Workflow owns continuation and resumes the authorized goal after approval; superseded discovery identities are absent",
      "source": ".claude/skills/workflow/continue/SKILL.md",
      "mapping": "plugins/workflow/skills/continue/SKILL.md",
      "verification": {
        "level": "planned",
        "result": "pending",
        "evidence": "Generated source routing checked locally; fresh installed native admission follows the source publication"
      }
    },
    {
      "host": "codex",
      "behavior": "Workflow owns continuation and resumes the authorized goal after approval; superseded discovery identities are absent",
      "source": ".codex/skills/workflow/continue/SKILL.md",
      "mapping": "plugins/workflow/codex-skills/continue/SKILL.md",
      "verification": {
        "level": "planned",
        "result": "pending",
        "evidence": "Generated source routing checked locally; fresh installed native admission follows the source publication"
      }
    }
  ]
}
```

Recovery close-repair-20261028-template53, 2026-10-28: same native owner
01a17e30-2baa-7343-8416-c212cbd2f523, PID6408 and its recorded process start verified live.
The Windows Terminal focus refusal is not authority to start another writer or close a peer.

Template52 and53 are merged and published at main8de27ca70c99e205024a33e197f304608d14c541.
The current public authoring names are skill:new, skill:check and skill:update. Earlier create references
below record the original request and prior candidate evidence; active callers are being retired together.
Agent34's authored caller and Core521's authoring convention now use skill:new. Marketplace42's producer
gate is satisfied; caller synchronization and current-head review remain before activation.

New separately reviewable runtime slice: Agent Fix/CompletionDecision, basec18a4ee2f6e1f9e934f5fc328e8cba9345470586,
PR: not opened. It reuses close_lifecycle and agent_close preparation; no new module, runtime repository,
close CLI operation or duplicate host implementation. Source commit06dbdda188a6055975e65401eeeb6f73cb4eeeb4.
This session remains its parent and Core521's existing owner. The slice is independent of Agent34's catalog
cutover, so it can be reviewed against current Agent main while publication waits on ordinary approval.

Demonstrated omission: Template53 session01a18220-c242-7ca0-83d6-b79166c3048f finalized without
selecting agent:close. It also reported its own blocked temporary-profile cleanup, so safe closure was
not established. Core521's independent-follow-up boundary cannot prevent omitted selection. The runtime
repair requests the missing assessment through the existing Stop hook, once per native reentry cycle;
prepare records selection without arming a watcher. Actual cleanup, unanswered questions, approval and
unfinished owned work preserve the session. Neither Stop nor a merged cwd proves completion.

Core524 was re-read on 2026-10-28 and remains OPEN. Core38f native startup CI remains red; latest main
was merged locally as8c3528a7 for fresh validation rather than assuming upstream launch changes resolve524.
Snapshot-authenticity PR526 is now on that baseline. The existing continuation owner remains blocked
without a scheduler registration; local foreground work is authorized by explicit resumption. Do not
claim unattended continuation or edit its identity files directly while its supported rebind is pending.

Next action: finish Agent assessment review and remote validation, then synchronize the skill:new callers
and their existing reviews, refresh Core521 review/CI, and reconcile publication/install acceptance.

Authority: Tommy requested the reusable completion repair, rejected retaining the former continuation
identity, and explicitly requested skill:create and skill:update with the current host native creator and
no compatibility aliases. These four linked source slices are owned here. Agent20 and GitHubActions34
remain independently owned publisher work and are not added to this goal.

Current source map:
- Core PR521: completion follow_up boundary; workflow:continue sole discovery identity; existing delivery
  contract and Codex transport moved to resources; current binding filename; all active callers migrated.
- Template PR52: sibling Skill plugin from the existing Template repository, native creator delegation,
  create/update routing, clean identity retirement, authored hook and package tests.
- Marketplace PR42: Skill source/dependency registration and generated native catalogs.
- Agent PR34: committed producer snapshot and authoring callers.
All four repository selections and host configurations explicitly select Skill using the existing selector.
No new repository, service, runtime module or duplicate continuation implementation was added.

Delivery order: Template52 must merge and its post-merge generated plugins/skill path must exist on main
before Marketplace42 can activate the dependency. Then reconcile Agent34's pinned roster against the
merged Marketplace document, refresh known exact repository selections, and finish Core521. All four are
draft while current-head review, CI or publication gates remain. Required approvals stay with Tommy.

Source validation: Template layout/reference checks, Ruff format/check and mypy pass; affected tests pass
178 with one Windows symlink skip and three subtests. Core completion22, continuation adapter46(6skips),
continuation runtime43, generation contracts27(3skips), process standards19 and auto-merge bindings pass.
Marketplace18tests, generation/check and Claude manifest validation pass. Agent required5/retired9/adoption5
tests, snapshot freshness and package generation/check pass. Local Windows full workflow-contract and Agent
suite failures reproduce the recorded inherited Git environment issue; current-head clean CI owns the full
platform matrix. Native quick_validate rejects house extended frontmatter; Template validates that schema.

The old scheduler registration for this exact Core owner was removed before moving its adapter path. No
current unattended registration is claimed. Preserve that owner's pending evidence, rebind through the
supported checkpoint operation after updating the exact delivery binding, and register the new resource
path only with the same explicit native host pin. A slice owner cannot transfer itself to another PR or
checkout; the foreground parent owns each dependency transition under workflow:run. Keep one active writer.
Never treat a source commit or a passed generator as proof of native installed cutover. Do not overwrite
any dirty primary checkout or another session's shell/ or publisher work.

Current heads and completion gates:

```completion
{
  "outcome": "Repair completion ownership and finish the clean skill:create/skill:update and workflow:continue identity cutover.",
  "acceptance": [
    {
      "id": "completion-regression",
      "criterion": "Independent follow-up cannot block a verified owned delivery, while actual acceptance and owned PR gates remain blocking.",
      "evidence": [
        {
          "source": ".agents/hooks/tests/test_completion.py",
          "result": "22 tests pass at current main synchronization; continuation adapter tests pass46 with6platformskips."
        }
      ],
      "owner": "Current delivery parent",
      "next_action": "Retain regression evidence through current-head CI."
    },
    {
      "id": "current-review",
      "criterion": "All four current source candidates have completed independent review and addressed actionable findings.",
      "evidence": [
        {
          "source": "canonical Git-private review work orders and exact-head review-record receipts",
          "result": "Core38f4764, Template176590c, Marketplace078969c and Agentca4a66e independently reviewed; actionable source findings addressed."
        }
      ],
      "owner": "Current delivery parent",
      "next_action": "Retain review proof through merge and review any subsequent source delta."
    },
    {
      "id": "published-cutover",
      "criterion": "The source package, catalog and all owned consumer changes are merged and published in dependency order.",
      "evidence": [],
      "owner": "Current delivery parent",
      "next_action": "Publish Template52 first, then Marketplace42, then reconcile Agent34 and Core521. Never bypass required GitHub review."
    },
    {
      "id": "installed-cutover",
      "criterion": "Known selections and this exact live continuation binding use only the current names; fresh supported hosts load them and supported runtime behavior is verified.",
      "evidence": [],
      "owner": "Current delivery parent",
      "next_action": "After producer/catalog publication refresh exact repositories; verify fresh native discovery/admission, scheduler registration and Windows/Linux runtime paths. Source tests alone do not satisfy this item."
    }
  ],
  "deliveries": [
    {
      "repository": "tj-agents/core",
      "pr": 521,
      "head": "38f4764b254e3429200096723e8c3227d2ab8d78"
    },
    {
      "repository": "tj-agents/template",
      "pr": 52,
      "head": "176590c51262c365af7719c4ca2870ed4d923dc2"
    },
    {
      "repository": "tj-agents/marketplace",
      "pr": 42,
      "head": "078969c442586341c1aa373cc42c6fb5dc9ea805"
    },
    {
      "repository": "tj-agents/agent",
      "pr": 34,
      "head": "ca4a66e56e0fb6eed173e570c3e3d8ed383a7fdd"
    }
  ],
  "open_tasks": []
}
```

Current exact-head CI: Template176, Marketplace078 and Agentca4 pass on Windows/Linux. Core38 fails native startup acceptance. The merged HookPurge baseline has no startup acknowledgement writer while managed Agent startup still requires it; investigate and retain this separate baseline defect before claiming installed acceptance. Core main CI and PR520 skipped native validation, so their green status is not baseline runtime proof.

Baseline startup regression is now canonical bug tj-agents/core#524 (https://github.com/tj-agents/core/issues/524), stable recording request core-direct-hook-startup-ack-20261027. Issue creation succeeded; board placement reported GitHub POST access/auth failure, so board membership is not established. This is separate from existing feature500 and from the skill naming source change. Native snapshot-content authentication observation remains unverified outside the native review reproduction; retain it in the Core review without claiming a newly proven introduced defect.

All four source candidates have completed independent review and exact-head private receipts. Template52 is ready for review and its required checks are green; GitHub ruleset25790628 requires one approval. Marketplace42 and Agent34 remain draft until the producer package/catalog publication gates. Core521 remains draft with native CI red. No auto-merge is armed for these held consumers. No claim of completed installed naming cutover is made.

Exact live owner reconciliation: supported checkpoint rebind advanced the same owner058197ea523add7f61b4a43e and its delivery binding to Core38f4764. Current resource adapter registration succeeded and a verified wake returned working with the live foreground lease, without launching a second writer. At the genuine producer-review/startup gate the owner was checkpointed blocked and scheduler removal was attempted. The first removal failed because the inbox PowerShell scheduler command was unavailable; pending goal/evidence and receipts remain. The focused retry succeeded with action=remove, removed=true; the exact task is now removed and no unattended continuation is claimed at this gate. This verifies the moved runtime entry point, not fresh installed discovery or unattended transfer to another PR.


Recovery checkpoint 2026-10-28, close-repair-20261028-template53: same native owner01a17e30-2baa-7343-8416-c212cbd2f523 retained; no second writer or peer closure. Current owned source heads: Core5216425650de5de0effa363562f54990d435aa0e74f; Marketplace42b15f51eb90d760c5d3515fe13777a15390b06432; Agent34413a87a359b139ef3788436681c6cde06ff1b566; Agent3620627320c8780c32b79c0d0fe08ddd2a2efdfa5e. Template52/53 main8de27ca70c99e205024a33e197f304608d14c541 is published with skill:new/check/update. Agent34 retires its old caller; Agent36 bases on Agent34 to avoid copying that migration.

Agent36 implements missing close assessment in the existing lifecycle module. Preparation records the current native input without arming; Stop requests missing assessment once. D-01 canceled-request masking was fixed and independently re-reviewed. Both hosts retain exact completion guards, unfinished work/questions/cleanup holds and reentry safety. Template53's omission did not establish safe closure because it also reported unfinished cleanup.

Exact-head Agent34/36 and Marketplace42 Windows/Linux CI pass; Agent hosts checks pass. Current Core642 CI40732721213 fails native startup acceptance with Core524, which remains open. Core/Agent source review results and limitations are preserved in canonical private work orders; selected Skill standards admission remains unresolved before catalog publication. Snapshot Python3.9 support mismatch and inherited Agent35 degraded handshake verification remain source-owner follow-up concerns, not claims of repaired baseline behavior.

Next actions: required Marketplace42 GitHub review/publication; fresh selected Skill admission; reconcile source-owner baseline concerns; land Agent34 before child36; repair Core524 and revalidate Core521. The original continuation owner remains blocked at its historical38f4764 binding, scheduler removed; no unattended progress or new owner is claimed. Do not bypass its identity guard or infer completion from a merged checkout.

Before this reply, exact-session prepare was attempted from the Agent36 authored source path and failed before assessment: host_sessions imports claude.sessions but that source command did not have a claude module on its runtime path (ModuleNotFoundError). No close watcher was armed. Preserve this native/source invocation-path observation for package-root diagnosis; CI host admission alone does not establish this command worked. Session remains open for the question and unfinished delivery gates.


2026-10-29 authorized merge checkpoint: Tommy approved and requested merging. Marketplace42 merged at c6df0d81dc95dfb2f6455c3c577c779e7560b1b6; main CI40865405715 passed. Agent34 merged at b0954763799140baf091badec134c2d7a9dc66f2; main CI40867044865 and publication40867044820 passed. Agent36 retargeted main after parent landing; parent and new main trees both6a23d3130f29e6a917edd3ee8d148c6927c21e3c, so reviewed/tested child source stayed unchanged. Agent36 merged at aa8c71a93de6bb660f863aaecff81c3b99b1ba1a; publication40867338241 passed. Primary Agent main was fast-forwarded while preserving unrelated local work.

Correction to previous invocation-path observation: running prepare from the projected Agent package succeeded against exact native session01a17e30-2baa-7343-8416-c212cbd2f523 on2026-10-29, target Temp/close-repair-20261029-assessment.json. The prior raw source path lacked projected Claude/Codex resources. No packaged import failure reproduced, and no watcher was armed. Do not treat that invocation error as an outstanding product defect.

Fresh Codex standards resolution after catalog refresh has no diagnostics for Agent34, Agent36 and Marketplace42, including Skill. Final native/independent source review syntheses and exact-head Agent34/36 receipts are preserved in canonical Git-private work orders. Native Codex publisher-byte verification passed. Full Claude verification failed on stale Base/Engineering registrations, including old version and stage entries; Claude selected standards still lack python/github-actions/skill/template visibility in the current resolver. Preserve this installed-cutover failure rather than claim full supported-host rollout. Refresh used no-relaunch and did not create or close a conversation.

Core521 remains open/draft at6425650 with required startup CI red, despite owner approval. Core524 remains open. Fresh independent read at this frozen head finds acceptance still demands preloaded Base task-routing text/digest after HookPurge intentionally removed policy preloading (test_task_routing asserts that contract). Separately Agent startup_participants recognizes hook_dispatch handlers while Base now invokes tier_gate directly. Reconcile lazy-loading acceptance and startup acknowledgement without restoring a duplicate dispatcher or weakening real execution evidence; inspect observer artifact before claiming either caused the other. No competing Core524 PR was found. The existing Core continuation binding stays blocked at38f4764 with its scheduler removed; no second owner or unattended work is claimed. Remaining source owner: this session for Core521, Core524 is the separately recorded startup gate; unresolved host cutover evidence remains retained.

2026-10-29 close-api-finish-20261029: Light automatic plugin refresh, native thread
01a17e30-2baa-7343-8416-c212cbd2f523, retains responsibility through installed acceptance and merge.
Agent36 is already merged; its missing-assessment guard remains required. The caller audit found no
maintained workflow that requires public cli:close or cli:closeout. Consolidate lifecycle selection as
agent:close and agent:closeout; move deterministic implementation into the existing typed tj-cli
distribution, remove the old skill entries and migrate authored callers together. Preserve exact process
identity, native input cancellation, unfinished-work holds, and closeout's separately evidenced worktree
eligibility. No aliases, foreign checkout imports or second authored implementations.

Necessary dependent work uses CLI Refactor/CloseApi from verified PR17 head
5f705f76d45d023a53b9e0ae50882cdc0ddb23c3 and Agent Refactor/CloseApi from verified PR29 head
c1d3550530371656a67ce959cef80d7cd227be4b, each merged with current main in its own isolated checkout.
These parents already own shared distribution delivery; the child needs that shipping mechanism to prove
installed close APIs while producer review is pending. Their PRs and existing branches remain untouched.
The recorded store has no owner bound to either foundation branch; occupied CLI primary and unrelated
Agent work are preserved. Land required parents before children and review each child delta separately.

Core524 artifacts now confirm both Windows and Linux observer state unconfirmed and absent loaded Base
contract, despite expected 401 completion. Repair acknowledgement at the direct hook boundary and update
acceptance to exercise lazy native skill loading. Do not restore startup policy preloading or a dispatcher.

Current next action: move CLI close mechanics into its typed package, preserving behavioral coverage,
then bind Agent's lifecycle scripts to that installed API and implement agent:closeout. Acceptance also
requires Core521/Core524 validation, independent review, dependency-ordered merge/publication, retirement
of old installed discovery, and actual supported installed Windows/Linux execution. CI alone is insufficient.
