# Work-item session registry and plan migration

## Tommy decision — 2026-10-14

Begin the remaining migration now. A work-item README is the single durable plan and current execution surface: it owns purpose, design, decisions, compact material delivery state and `## Next Steps`. SQLite is the source of work-item status and session ownership. Do not create or maintain append-only progress dumps, separate progress ledgers, `Status:` headers, or `ACTIVE_SESSIONS.md`. Git, PRs, CI and reviews retain history. Legacy plans remain readable through the staged dual-read path until their conversion slices land.

This authorizes S2 onward under this goal and standing delivery authority. Start from current `origin/main`, deliver one reviewable slice at a time, and do not bulk-rewrite consumer repositories.

## Objective and authorized outcome

Replace ad hoc worktree/progress-dump recovery with a Core-owned convention for resuming the exact native Claude or Codex session for a work item through the guarded host command, including after safe worktree cleanup. Core owns portable guidance, runtime, tests, generated host adoption and release. Repositories consuming the Core plans convention adopt through explicit, versioned migrations under their own goals.

Tommy authorized implementation, tests, review, PRs and merge after repository gates pass on 2026-10-12. This excludes destructive worktree/user-data cleanup, profile installation, bypassing checks and bulk consumer edits without their reviewed migration and ownership gates. Do not modify controller-association PR #209 or its checkout, the merged S1 checkout, or separate self-repair/session-registration repairs.

## Current design and boundaries

New repository plans use this path grammar:

```text
plans/features/<feature>/README.md
plans/features/<feature>/work-items/<work-item>/README.md
plans/features/<feature>/work-items/<work-item>/<SUPPORTING>.md  (optional)
```

`<feature>` and `<work-item>` are lowercase kebab-case; the work-item key is `<feature>/<work-item>`. The feature README explains the feature and links each work item with delivery state/PRs. The work-item README owns purpose, scope, authorization, design or supporting-doc links, delivery slices, compact current state, verification, reviews, decisions and `## Next Steps`. It replaces plan/progress pairs and repository `plans/<goal>/GOAL.md` for new work. Keep standalone non-repository tasks unchanged. A 200-line/16 KB budget applies to work-item READMEs. Existing plan, ledger and roadmap forms remain readable during migration; create no new instances of those forms after the convention lands.

The central local SQLite store at `~/.agents-state/sessions.db` owns session and work-item status/ownership. It is hook-written through `.agents/machine/scripts/session_store.py`; `work_item_sessions.py` and guarded `agent_recovery.open_session` provide work-item operations and resume. The S1 redesign and implementation removed the Markdown session-registry design. Do not reintroduce it. Termboard is not a prerequisite.

Retention decision (Tommy, 2026-10-12): a done work item keeps its README and delivery slices until the whole feature is terminal; then delete the feature folder. Git is the archive.

### S2 handoff boundary — 2026-10-14

S2 accepts `plans/features/<feature>/work-items/<item>/README.md` only at that strict canonical path; legacy plan/ledger reads continue. Require `Worktree:`, `Branch:`, `## Next Steps` and its four scope fields (`Scope:`, `Current slice:`, `Remaining scope:`, `Done when:`). The feature README must contain exactly one checklist marker for the work-item key `` `<feature>/<item>` ``. Do not add a `Status:` header or `ACTIVE_SESSIONS.md`.

For Workflow v2, the work-item README is both `artifacts.plan` and `artifacts.ledger`; its feature README is `artifacts.roadmap`. `plan_graph.py` and `plan_handoff_stop.py` validate the documents and transfer boundary without database access. `RepositoryStateProvider` reads SQLite read-only. It returns explicit errors for a missing/corrupt database, unsupported schema, missing/conflicting work-item rows, or a mismatch between stored status and the README's leading action; it never falls back to inferred session ownership. Check for an existing owner conflict before reporting an actionable state. Use a packaged shared repository-identity helper so the source checkout and packaged runtime resolve the same repository identity instead of treating sibling package paths as separate repositories.

Map SQLite status to Workflow v2 state and enforce the matching Next Steps action: `proposed`, `active` and `delivery-gated` map to `active` and allow local `continue` or `Transfer:`; `blocked` maps to `blocked` and requires leading `Blocked:`; `paused` maps to `paused` and requires leading `Paused:`; `done` maps to `complete` and requires leading `Complete:`. A missing or mismatched action is an explicit provider error. Delivery-gated work may continue locally under the established plan semantics.

## Migration map

S2 must address the legacy readers as one focused runtime slice, with tests:

- `.agents/hooks/plan_graph.py`: discovery and structural validation.
- `.agents/hooks/plan_handoff_stop.py`: claimed-plan discovery and Stop transfer gate.
- `.agents/workflows/workflow_runtime.py`: repository state provider and workflow artifacts.
- `.agents/workflows/workflow_ops.py`: repository inspection and delivery preflight.

The remaining retirement surface is broader and must be mapped against source before deletion: Workflow v2 `artifacts.ledger` contract/schema/examples/provider; `engineering:plans`, `plan-checkpoint`, handoff format and plan/workflow skills; templates, fixtures, tests and rename/legacy checks; generated `plugins/*` (regenerate only, never commit generated output in this worktree). Prior source inventory and concrete reader/test references are in Git history before this compaction. The three live Core ledgers previously identified are `plans/conditional-skill-routes/CONDITIONAL_SKILL_ROUTES_PROGRESS.md`, `plans/merge-worktree-cleanup/MERGE_WORKTREE_CLEANUP_PROGRESS.md` and `plans/repo-declared-config/REPO_DECLARED_CONFIG_PROGRESS.md`.

S4 converts the three named plan/progress/roadmap groups after reconciling each owner: compact plan plus current ledger becomes the canonical work-item README, roadmap becomes the feature README, and actual incoming references follow the replacement. Existing repository `GOAL.md` owners resume in place; do not create a competing README or migrate/delete unrelated goals.

The exact legacy progress dump is the engineering `<NAME>_PROGRESS.md` ledger. `GOAL.md`, `.agents/continuation/*` runtime state and `cli-session-recovery/` vault data are not deletion targets. Preserve the staged order: runtime bridge; convention/templates; Core plan migration; then legacy-ledger/parser removal under Workflow v3. Never delete a similarly named artifact without source and consumer evidence.

S5 version classification is resolved by the published Workflow v2 support matrix: removing formerly valid ledger inputs changes provider-operation semantics and requires v3. Keep `artifacts.ledger` as an alias to the same README; no cosmetic field rename is needed. Publish honest v3-only support at retirement, preserve released v2/history, and leave existing single-file GOAL execution outside the ledger provider unchanged. This does not waive the recorded consumer-adoption gate.

## Delivery slices and gates

| Slice | Outcome | Route / dependency |
|---|---|---|
| S1 | SQLite session/work-item store, hooks, guarded work-item recovery and tests | Delivered in PR [#228](https://github.com/tj-agents/core/pull/228); local `origin/main` history contains its merge. |
| S2 | Runtime dual-read for work-item README and legacy plan/ledger, with exact validation/provider/Stop/preflight contract and focused tests | Delivered by PR #251 at `110b5bc`; exact-head Windows/Linux CI and all review gates passed. Landing run `38603568458` passed Windows/Linux; generated commit `2a248d4` has merge `110b5bc` as its parent. |
| S2b | Workboard reads canonical work-item READMEs and SQLite status while retaining legacy reads | Separate bridge from generated base `2a248d4`; L4 implementation, L2 migration review, normal tested merge and causal generation. |
| S3 | Convention and templates switch after S1/S2/S2b | `merge-docs` unless runtime tests are changed; L4 implementation and L2 migration review selections pending. |
| S4 | Migrate Core plans after S3 | `merge-docs`; L4 implementation and L2 migration review selections pending. |
| S5 | Remove legacy ledger support and publish Workflow v3 after S4 and recorded consumer migrations | `merge` with tests; L4 implementation and L2 migration review selections pending. |
| S6+ | Each consumer repository migrates under its own goal and gates; no sweeping rewrite from Core | Repository owner selects route and lane. |

Read-only consumer audit confirmed Concertable/agents as a declared Core package/convention consumer and tj-agents/dotnet as an engineering:plans selector client. No direct external call to Core legacy parser/provider was established. Concertable product parser copies are separately owned; current README adoption is unverified and requires its own migration assessment before S5. Dotnet keeps the same selector and has no demonstrated legacy-input conversion requirement.

Consumer package guidance may propagate automatically, but consumer plan content is never rewritten by Core. Track adoption and require evidence before removing compatibility. Earlier S1 review/test history and superseded design are retained in Git and PR #228, not copied here.

## Acceptance

- New Core plans follow the approved feature/work-item path grammar and use the work-item README for durable execution state and `## Next Steps`.
- S2 resolves work-item READMEs and legacy plan/ledger inputs consistently across validation, provider, Stop and preflight paths, with focused regression coverage and a documented precise contract.
- SQLite remains the source of status and ownership; session recovery resumes only through the existing guarded host-specific path.
- Core conversion and legacy retirement follow S3–S5 in order. The exact legacy ledger and its readers are migrated or removed without dangling source/generated references.
- Consumer migration is explicit, tracked and separately owned; S5 does not remove compatibility before recorded consumer migrations land.
- Required Windows/Linux checks, source-layout checks, package-generation gates, independent review and normal delivery gates pass for each slice.

## Current state and next action

S1 is delivered by PR #228. Its chronology and detailed review/test evidence remain in Git, PR and review artifacts.

Lane record: L5 covered mechanical compaction and package generation; L3 resolved the S2 cross-reader boundary; L4 completed implementation and the import regression repair. L2 is selected for migration review because the candidate reads stored work-item status and native ownership across the compatibility boundary.

S2 is reviewed and merged by PR [#251](https://github.com/tj-agents/core/pull/251) at `110b5bc7f424b0680ec66b6de630b14ee732ef76` (2026-10-14). Candidate `9e50f9763c6ebe9a237b9973cde622223e0de85c` passed Windows/Linux CI run `38600608523`, native review, fresh L2 API-contract and ordinary workflow review, parent synthesis and source host coverage. All ten findings have committed fixes. Stop ran 35 tests with one Linux-only Windows skip; all 19 provider tests passed including non-ASCII common-Git-directory parity. Landing-triggered run `38603568458` passed, including regeneration; bot commit `2a248d4df293b07aacbd885f5567151ecdf75ef1` publishes the generated packages with merge `110b5bc` as its parent. The separate workboard bridge is implemented and entering review on `Feature/WorkItemWorkboardBridge` from that published base in this exact checkout. S3 global guidance has not begun.

Source checks passed: graph 27; Stop 35 (one Linux-only skip on Windows, POSIX case passed Linux CI); ownership 10; launcher 15; RepositoryStateProvider 19; inspect 5; delivery-preflight delivery-gated 1; RepositoryIdentityTests 21; real registration 1; copied verify/help 2; provider NULL-PR preflight 1; and `tests/test_work_item_sessions.py` 43. Helper import/static mapping assertions passed. Packaging checks passed: generated payload self-containment 1, HarnessManifestTests 7, tier-payload, catalog digest check and harness-manifest check. The package sync invocation's exit result was not observed; its follow-up check verified all 556 files with 0 changes and 0 pruned. Isolated generated `session_store`, `workflow_runtime` and `workflow_ops` imports passed from a temporary working directory with the checkout root absent from `sys.path`. Independent review, exact-head CI and PR merge passed as recorded above. Causal generated publication is verified; installed consumer-host adoption is unverified. Preserve legacy reads through the remaining staged migration.

The workboard bridge owns only the Gather implementation in `.agents/engineering/utility/workboard/SKILL.md`, its exact-script tests in `tests/test_workboard.py`, and verification of existing shipped harness coverage in `.agents/plugins/harness/engineering.json`, plus this maintained goal. The existing harness declaration already includes its own workflow runtime and needs no redundant source-root change. Final source suite passed 46 tests; the twelve status tests include missing API and missing own-contract failures, key filtering and canonical casing with preserved Windows legacy traversal. Local package generation and generated payload self-containment passed; generated output remains uncommitted. The completed first review retained feature-key filtering, Windows physical-directory casing and POSIX installed-command fixes. All three are repaired and the final suite passed 46 tests in 44.613 seconds; derived package generation passed. Original-head CI succeeded; repaired-head incremental review and CI are next.

## Next Steps

Lane: a bounded L4 worker owns the specified workboard bridge; L2 will assess its read-only status/compatibility boundary. Workflow v2 has no implementation-stage writer capability; the invalid proposed dispatch was closed and the supported lane-worker fallback retains one exact serialized source lease. The branch-bound continuation state was archived while inactive and reinitialized through its CLI on the bridge branch, preserving logical owner `eee19c5839c54ea23aa45b8a`, authority and remaining deadline/failure/launch limits; foreground ownership remains in this native session.

1. Complete the scoped workboard bridge specified by common Git artifact `agent-workflow/runs/work-item-sessions-s2/artifacts/s3-reader-preparation.json`; verify source and packaged reads, review, publish, merge and verify causal generation.
2. Switch global planning guidance and templates in a separate S3 slice, retaining legacy read compatibility and standalone non-repository tasks.
3. Continue S4 Core conversion and S5 retirement after their dependencies and recorded consumer adoptions are satisfied.

- Scope: whole plan through all remaining phases and terminal delivery.
- Current slice: the separate workboard status-reader bridge.
- Remaining scope: workboard bridge and S3–S5 in Core; confirmed consumer migrations under their own goals.
- Done when: the legacy progress ledger is removed from Core with no dangling references, and every recorded consumer migration has landed.
```agent-host-coverage
{"schema_version":1,"shared_source":".agents/engineering/utility/workboard/SKILL.md","hosts":[{"host":"claude","behavior":"Discover canonical work-item READMEs and show read-only SQLite status alongside legacy plans, within the invoking repository group.","source":".agents/engineering/utility/workboard/SKILL.md; .agents/workflows/workflow_runtime.py","mapping":"Generated engineering skills/workboard delegates to the canonical definition and anchors engineering workflows in its own package.","verification":{"level":"source","result":"passed","evidence":"Final exact Gather suite passed 46 tests, including source and both isolated packaged layouts; local regeneration and payload self-containment passed. Installed host acceptance is separate."}},{"host":"codex","behavior":"Discover canonical work-item READMEs and show read-only SQLite status alongside legacy plans, within the invoking repository group.","source":".agents/engineering/utility/workboard/SKILL.md; .agents/workflows/workflow_runtime.py","mapping":"Generated engineering codex-skills/workboard delegates to the canonical definition and anchors engineering workflows in its own package.","verification":{"level":"source","result":"passed","evidence":"Final exact Gather suite passed 46 tests, including source and both isolated packaged layouts; local regeneration and payload self-containment passed. Installed host acceptance is separate."}}]}
```
