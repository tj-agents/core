# Workflow runtime debt

## Merge authorization was confused with approval-review execution

Workflow mistake and recovery debt, observed on 2026-10-11. Tommy had already authorized merging,
configurable auto-merge PR #188 was merged, and main declared `auto_merge: true`. This older checkout
predated that field. Repeated permission/config explanations obscured the actual host failure: the
parent and bounded subagent's scoped Git operations were rejected before execution with HTTP 400 for
`input[1].internal_chat_message_metadata_passthrough.content_item_metadata`. This was a reviewer API
failure, not missing consent or a safety rejection. A fresh normal-host benign elevated action had passed, but fresh-host Git delivery was not observed.
The exact source of the old/fresh host difference remains unproven; retained loaded configuration is
a candidate explanation. The existing P1 recovery goal stays open through actual delivery acceptance.

Resolve when delivery preserves existing merge authority through recovery, checks main/installed/local
configuration separately, distinguishes user authorization from host execution gates, and resumes the
same goal through a supported fresh host without repeatedly asking the user or repeating failed actions.

## Machine acceptance and repository delivery were reported ambiguously

Reporting mistake, observed on 2026-10-11. The approved local runtime/profile/catalog repair passed
fresh sandbox reads, automatic review and configured-default-model startup. No core runtime code was
changed. The branch contained recovery records, but responses alternated between "complete" and
"not merged" without clearly distinguishing the verified machine repair from unpublished records.
No PR or CI run had been created; the CI waiter was therefore untested, not an established broken
runtime. Returning after each blocked attempt also made Tommy repeatedly ask for progress.

Resolve when completion reports identify the actual changed artifact and observed acceptance, state
whether a code PR exists, distinguish unpublished records from an unapplied fix, and keep any genuinely
remaining authorized delivery owned until completion or an accurately documented capability gate.

## Blocked delivery was returned without a continuation owner

On 2026-10-11, sandbox recovery reached a lasting Git/approval-review blocker, but the agent returned
control without initializing the existing goal's continuation owner. Tommy had to intervene. No PR or
CI run existed yet, so this incident does not establish a CI-waiter runtime defect.

The later supported initialization attempt failed writing `.agents/continuation/owner.lock` inside
the read-only sandbox area. Its scoped escalation was rejected before execution by the old host's
automatic-review HTTP 400 for unsupported Responses metadata. No owner or scheduled wake was created.
Standards repair remains deferred under Tommy's explicit scope restriction.
Evidence and actual failed commands remain in the sandbox recovery goal; the installed scheduler
was not registered and its CI-wait behavior was not tested.

Resolve when a task that acquires a lasting delivery blocker selects supported continuation before
returning, records an actual claimed owner and registered/observed wake when available, and proves the
wake can use the repaired reviewer configuration through the existing authorized merge. A genuine
capability gate must record its resolver and resume condition without claiming a background waiter.

## Same-goal verification was launched as a handoff

On 2026-10-11, sandbox recovery opened an independent native verifier tab for normal-launch
acceptance. A fresh process was necessary, but the existing owner could have captured a child CLI's
results directly, as it did for the default-model probe. Returned artifacts were readable; the extra
session still added ownership and cleanup work to the blocking repair.

Tommy explicitly deferred standards repair until the blocking bug is finished. Keep same-goal work
with its current owner or a bounded subagent; reserve handoffs for independently owned separate work
or an actual context transfer. A dedicated Markdown record covering bugs, mistakes and tech debt is deferred until later. These
incidents remain in the existing owning records; no new recording system is started now.

Resolve when the handoff and launcher selection rules distinguish fresh-process verification from
ownership transfer, focused checks cover inline verification and bounded subagents, and the agreed
mistake-recording workflow can retain this incident without requiring another handoff.

## Slice retirement checks the broader goal's completion

The runtime's `checkpoint --state complete` calls the canonical goal's full completion check, even
when its bound slice PR is merged and a workflow handoff records a pending successor. This conflicts
with the documented foreground slice transition: the owner cannot complete while the broader goal
correctly retains unfinished acceptance. A foreground parent can retire the merged slice's scheduler
and binding, preserve its blocked owner receipts, and initialize the next slice against the same goal.

Resolve when slice retirement verifies its exact merged PR/head and handoff without declaring the
broader goal complete, and tests preserve pending successor acceptance across the foreground transition.

## PR preflight misclassifies an incremental review base

`delivery-preflight` passes its final incremental review descriptor to `review-reconcile` against `origin/main`. An incremental descriptor's base is the prior reviewed commit, so an unchanged `origin/main` can be reported as `base-changed-relevant-evidence` when the prior commit touched a path in the incremental pass. The core Windows hook PR reproduced this false blocker; preparing a cumulative base-to-head descriptor let preflight verify the already reviewed chain.

Resolve when preflight reads the canonical work order's continuous completed review passes, reconciles the original remote base against the full reviewed path and rule set, and tests an incremental pass with unchanged, disjointly moved, and relevantly moved remote bases.

## The strategic workflow stage is pinned below planning's lane

L1 now owns planning and design, but the workflow contract's `strategic` stage (architecture, major planning) is still derived from L3 in `.agents/workflows/hosts/*.json` and `STAGE_LANES`. Draft #39 repins the same stages for Codex, so the two changes would collide.

Resolve when `strategic` is derived from L1 on both hosts, `STAGE_LANES` and the host pins agree, and the workflow contract tests pass.

## Non-review workflows run helpers from the reviewed repository

The review family resolves `workflow_ops.py`, `tier_gate.py` and `docs_reachability.py` from the installed
engineering plugin root, so it runs in a repository with no `.agents/`. `plan-execution`, `feature`, `bugfix`,
`merge`, `merging`, `open-pr`, `pr-preflight`, `remote-validation` and `persistent-delivery` still name
`python .agents/workflows/workflow_ops.py`, which exists only inside core.

Resolve when each of those skills names `<engineering>/workflows/workflow_ops.py --root <repository-root>`
and the `test_review_native_layer.py` repository-helper check covers them.

## Workflow skill resolution still assumes the former flat layout

The `skills` operation defaults lifecycle names to `.agents/skills/<name>/SKILL.md`. Core now owns `feature` under `.agents/engineering/workflow/feature/`, so recording the lifecycle by name fails before producing its identity record. This predates the Sol 6.1 update and is independent of lane resolution.

Resolve when lifecycle discovery uses the canonical scope/kind layout and regression coverage proves `skills --lifecycle feature` records the shipped owner in both source and installed package layouts.

## Codex keeps a merge-cleanup obligation after a failed merge

`merge_cleanup_gate.py` records its obligation at PreToolUse, before `gh pr merge` runs. Claude reports a
failed merge through PostToolUseFailure and never blocks Stop on an unconfirmed obligation, but Codex has no
result event, so after a failed or rejected merge it nags once every 10 minutes until `--clear` or the
7-day reconcile drops the obligation.

**Resolution condition.** Codex publishes a tool-result or failure event that hooks can consume; wire the
gate's failure handler to it and delete the obligation when the merge reports no success.

## Review routing requires the write-time opt-in

`review-prepare` names the skills a review owes only through `.agents/skill-routes.json`, and carrying that
table also opts the repository into the write-time router and the red-run gate. The router blocks every
write while any routed skill is unresolved or plugin discovery fails. Core therefore carries no table, so a
review of a changed `SKILL.md` is not required to load `engineering:skill-authoring`; the description and
`AGENTS.md` are its only discovery.

Resolve when a route can apply at review time alone, without opting the repository into write-time routing
or the red-run gate, and core routes authored `SKILL.md` paths to `engineering:skill-authoring` through it,
with a test that `review-prepare` names the skill for such a path.
