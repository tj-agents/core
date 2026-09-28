# Choose the planning-to-execution owner by work size and context

## Request and scope

Tommy explicitly requested a core handoff to correct unnecessary handoffs after planning. He first clarified that the Sandbox HWID correction was the same bounded work in the same checkout, where the parent could continue with an appropriate lane worker. His later clarification governs the general rule: small and medium plans usually continue in the same CLI; a massive plan can make planning a substantial phase and should normally hand execution to a fresh harness after a durable phased plan, even in the same repository. Use judgment for plans between those cases.

This task fixes the planning-to-execution decision boundary. Preserve existing behavior for a genuinely different directory/repository/worktree. Do not broaden this into a rewrite of directory retargeting or remove `base:cd`'s handoff fallback.

The requested result is a concrete core guidance fix, relevant regression coverage, regenerated distribution output, validation and normal repository delivery. This is the one explicitly requested core handoff. Do not create another terminal session merely to execute this plan.

## Ownership and observed state

- Repository: https://github.com/tj-agents/core (marketplace identity remains `base-agents`).
- Owning checkout: `C:/Users/TommySeery/source/repos/tj-agents/core.worktrees/Fix-InSessionLaneExecution`.
- Branch: `Fix/InSessionLaneExecution`.
- Fetched base and initial HEAD: `61b5b1ee19f7660ad881839525693fa7387809be`, current `origin/main` when this worktree was created.
- The worktree was created and verified clean before writing this plan. The initial candidate is committed at `44dd87e6e4d4861da22f8c5c27521e39bb30c9e3`; the user correction is currently in progress in the same checkout.
- The ordinary core checkout and older base-agents checkout have unrelated work. Leave them and their plans untouched. Existing core PR #32 concerns resuming an in-flight roadmap item; its changed owner is `continue-roadmap`, so do not repurpose it for this fix.
- The Sandbox HWID guide correction has its own existing continuation. This core task does not adopt, stop, duplicate or edit that guide work.

## Reproduction and evidence

In Sandbox HWID, the parent designed a bounded guide revision and then launched an independent Codex terminal session for its implementation. After Tommy asked to remove unnecessary code examples, the parent launched another terminal session for that small correction. Tommy wanted the parent to retain the conversation and task, using delegated lanes when useful. The first guide handoff had been explicitly recorded in an earlier plan; do not turn that fact into a permanent rule that every plan or lane change demands another session.

Confirmed current-main guidance:

1. `.agents/machine/handoff-codex/SKILL.md` says: “Split a job that designs and then delivers. Hand the plan or design off on L1, then its execution on the rung the build needs”. The same paragraph exists in `.agents/machine/handoff-claude/SKILL.md`. This wording confuses routing work to a lane with starting an independent session.
2. `.agents/engineering/contract/lanes/SKILL.md` already says to re-route per phase and describes delegated lane agents. Clarify that selection of model/effort is separate from transfer of task ownership.
3. `.agents/engineering/contract/plans/SKILL.md` already says to continue in the current context by default, and a phase boundary alone is not context degradation. That rule needs a massive-plan exception based on a substantial design phase and an actionable durable checkpoint. `.agents/engineering/workflow/plan-execution/SKILL.md` says not to transfer merely because a phase or commit completed; keep that distinction while recognizing the separate massive-plan reason.
4. `.agents/base/cd/SKILL.md` separately governs actual directory changes. Leave that behavior intact per Tommy's correction; do not misdiagnose all directory-driven handoffs as wrong.

## Required behavior

- After a small or medium plan for the same authorized work in the current checkout, usually continue execution under the same parent session.
- After a massive plan whose design was a substantial phase, produce a durable phased execution plan and normally transfer execution to one fresh harness, even in the same checkout. The successor becomes the execution owner. A plan's length alone is not a mechanical trigger; use its complexity, the weight of the planning phase, remaining execution and the usefulness of current context.
- For plans between those cases, record the reason for retaining or transferring ownership.
- Choose an appropriate lane independently for each bounded phase. A parent can dispatch implementation, review or other bounded work to a lane sub-agent and keep ownership, acceptance decisions and communication with Tommy. Select the lane using the existing definitions; Tommy's L2/L3 example is not a request to reprice or rewrite the lane tables.
- A lane worker returns its work to the parent. The parent reconciles the result, verifies it and continues. Delegate with explicit path/responsibility ownership; preserve other writers and do not overlap edits. Do not automatically transfer the whole plan to the worker.
- For tiny work, direct execution can be cheaper than delegation overhead. If a chosen lane/agent capability is unavailable, use the documented fallback within the current owner rather than launching an external session solely to obtain a cheaper model. Respect genuine host restrictions; this is not permission to bypass a policy or invent a native in-place model switch.
- A finished plan, a phase boundary, a cheaper desired model, or a planned L1-to-implementation transition alone is not a handoff trigger. An actionable plan file is not itself a transfer request. A massive plan's substantial design and durable execution checkpoint normally supply an additional transfer reason.
- A separate session remains appropriate when explicitly requested, when genuinely moving to another owning directory/workstream, when the massive-plan default applies, or when evidence shows another real context/ownership need under the existing transfer contract.
- An explicit handoff still launches exactly one successor and reports launch evidence. Existing prompt-only requests remain prompt-only. Do not weaken independent review requirements or actual directory-removal/retargeting safety.

## Implementation boundaries

Expected authored scope is the two machine launcher SKILL.md files, the engineering lanes contract, and a small clarification in the owning handoff/plans/execution contract only where needed to remove contradictory instructions. Update associated behavioral regression tests and generated payloads. Prefer one clear source owner and short cross-references rather than copying another long policy into every skill.

Read the checkout's `AGENTS.md`, `README.md`, `SOURCE_LAYOUT.md` and relevant local guidance. `.agents/` is canonical, host adapters are under `.codex/` and `.claude/`, and `plugins/*` is generated. Do not patch installed plugin-cache copies. Do not change lane model mappings, machine profiles, `base:cd`, directory ownership rules, or unrelated skills merely to fit this fix.

This should remain one focused reviewable core change. Keep generated output accounted for separately from authored changes. Preserve paired AGENTS.md/CLAUDE.md files; no new instruction files are expected.

## Acceptance and validation

Use existing test owners, including relevant suites under `.agents/hooks/tests/`, to establish these contrasting scenarios without relying solely on one exact sentence assertion:

1. Same checkout and small or medium authorized plan: design completes; parent continues and may use a bounded implementation lane. No external launcher call is selected merely because planning ended.
2. Small follow-up correction in that active work: parent handles it directly or through an appropriate lane and retains ownership.
3. Lane delegation unavailable: no external handoff merely to change cost/model; supported in-session fallback is used.
4. Massive plan with a substantial design phase: the durable phased plan supports normally handing execution to one fresh harness, even in the same checkout.
5. Intermediate plans require judgment using complexity, remaining execution and context usefulness; size alone is not an unconditional handoff.
6. User explicitly requests a handoff: exactly one successor remains the expected behavior.
7. Work genuinely changes owning directory/repository: the existing retargeting/handoff guidance is preserved.
8. Real context degradation or an independently justified transfer: handoff remains available; no blanket ban on handoffs.

Inspect and run the repository-supported focused validation commands. After authored/package changes, follow README's digest/generation order: `python -B scripts/update_catalog_digests.py` when package bytes change, then `pwsh .agents/sync-generated.ps1`, and require `pwsh .agents/sync-generated.ps1 -Check`. Run appropriate focused tests and `git diff --check`. Broaden only for failures or affected contracts. Verify generated Codex and Claude launch instructions agree with the canonical rule.

Report which conflicting wording changed and evidence for same-session continuation versus explicitly requested/cross-directory handoffs. Do not claim a machine's installed plugins adopted the change solely because source/generation checks pass.

## Current status

The originating session located core, inspected both matching launcher paragraphs and the existing phase-continuation contracts, fetched main, checked open core PRs, and created the clean isolated worktree above. The user narrowed the scope before this plan was written. The explicitly requested handoff launched this session once; `handoff-launch.txt` records the receipt. This session acknowledged the plan and retained ownership through implementation.

Initial commit `44dd87e6e4d4861da22f8c5c27521e39bb30c9e3` replaced the automatic design-to-execution handoff paragraph in both machine launcher skills and clarified in the lanes contract that phase routing can keep the parent owner. Before publication, Tommy added the massive-plan distinction. The current edits reconcile the launcher, lanes, plans and execution contracts with that correction and expand `test_process_standards.py` to cover both sizes and intermediate judgment. No directory guidance or lane mappings changed.

Validation observed for the corrected candidate: `test_process_standards.py` 19 passed; `test_lane_tables.py` 22 passed; `test_plan_workflows.py` 19 passed; `pwsh .agents/sync-generated.ps1 -Check` reported 0 changed and 0 pruned; docs reachability reported 0 errors and 0 warnings; `git diff --check` passed. The previous frozen review applies only to initial commit `44dd87e6e4d4861da22f8c5c27521e39bb30c9e3`, so review the corrected commit before delivery. Source completion does not imply installed plugins on this machine adopted the new payload.

## Next Steps

1. Commit the corrected source, tests, generated output and this plan. Re-review the new exact head.
2. Deliver through core's personal-repository PR workflow. Retire transient launcher metadata before preflight and record the final commit and PR identity here.
3. Report the actual outcome to Tommy, distinguishing source completion from any local installed-plugin adoption.

## Transfer

Selected lane: L4, because the desired policy and boundaries above are specified; the remaining work is implementation, regression coverage and validation. The user explicitly requested this core handoff. The originating session will invoke the installed `machine:handoff-codex` launcher once, with this checkout and `plans/in-session-lane-execution/handoff-prompt.txt`.

The launch receipt is `plans/in-session-lane-execution/handoff-launch.txt`. Successful submission proves launch only; the successor must acknowledge reading the plan. On successful launch the originating session releases this core task and does not edit it concurrently. Preserve these files as continuation evidence until the repository's normal plan lifecycle retires them; do not publish transient launcher metadata as product content unnecessarily.
