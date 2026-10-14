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

The exact legacy progress dump is the engineering `<NAME>_PROGRESS.md` ledger. `GOAL.md`, `.agents/continuation/*` runtime state and `cli-session-recovery/` vault data are not deletion targets. Preserve the staged order: runtime bridge; convention/templates; Core plan migration; then ledger/parser removal and workflow-contract decision. Never delete a similarly named artifact without source and consumer evidence.

## Delivery slices and gates

| Slice | Outcome | Route / dependency |
|---|---|---|
| S1 | SQLite session/work-item store, hooks, guarded work-item recovery and tests | Delivered in PR [#228](https://github.com/tj-agents/core/pull/228); local `origin/main` history contains its merge. |
| S2 | Runtime dual-read for work-item README and legacy plan/ledger, with exact validation/provider/Stop/preflight contract and focused tests | Implementation and source checks passed; independent L2 migration/native/security review, exact-head CI, PR/merge and causal generation pending. |
| S3 | Convention and templates switch after S1/S2 | `merge-docs` unless runtime tests are changed; L4 implementation and L2 migration review selections pending. |
| S4 | Migrate Core plans after S3 | `merge-docs`; L4 implementation and L2 migration review selections pending. |
| S5 | Remove legacy ledger support and decide Workflow contract version after S4 and recorded consumer migrations | `merge` with tests; L4 implementation and L2 migration review selections pending. |
| S6+ | Each consumer repository migrates under its own goal and gates; no sweeping rewrite from Core | Repository owner selects route and lane. |

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

S2 runs on refreshed base `eded20b2014d46dd65b9bfc9bdb49d23f422fc1c`; workflow run id: `work-item-sessions-s2`. Draft PR [#251](https://github.com/tj-agents/core/pull/251) contains implementation `95c309f` and repair `8d5fa24`, which resolves all eight findings in the completed review at `95c309f`. Exact-head CI run `38553329155` passed Windows and packaging gates; Linux failed one POSIX-reference fixture among 1,156 shared-runtime tests. That fixture incorrectly supplied read-only tool prose, which Stop intentionally excludes. The bounded L4 inline correction supplies a genuine user message; the focused Windows Stop suite ran 33 tests with one existing Linux-only skip and passed. Fresh incremental native and independent L2 migration review from `95c309f`, followed by exact-head CI, merge and causal generation, remain pending.

Source checks passed: graph 27; Stop 33 (one Windows skip; the POSIX case awaits Linux CI); ownership 10; launcher 15; RepositoryStateProvider 17; inspect 5; delivery-preflight delivery-gated 1; RepositoryIdentityTests 21; real registration 1; copied verify/help 2; provider NULL-PR preflight 1; and `tests/test_work_item_sessions.py` 43. Helper import/static mapping assertions passed. Packaging checks passed: generated payload self-containment 1, HarnessManifestTests 7, tier-payload, catalog digest check and harness-manifest check. The package sync invocation's exit result was not observed; its follow-up check verified all 556 files with 0 changes and 0 pruned. Isolated generated `session_store`, `workflow_runtime` and `workflow_ops` imports passed from a temporary working directory with the checkout root absent from `sys.path`. Installed-host acceptance, independent review, exact-head CI, PR merge and post-merge causal generation remain pending. Preserve legacy reads; do not begin bulk Core or consumer conversion before S2 is reviewed and merged.

## Next Steps

Lane: the small L4 fixture follow-up preserves Stop ownership semantics; native and independent L2 incremental migration review is next.

1. Review the fixing commit incrementally from completed watermark `95c309f5b50a8cf87c6f073a1bb7d4fec21e9928`; no separate security layer is required by the frozen path classification.
2. Rerun exact-head CI, update and merge draft PR #251 after review and repository gates, then complete post-merge causal generation.
3. After S2 merges, merge the scoped workboard read bridge identified by common Git artifact `agent-workflow/runs/work-item-sessions-s2/artifacts/s3-reader-preparation.json` as a normal separate merge before starting the separate global guidance/template S3 switch. S3 implementation has not begun; continue S4 and S5 only after their dependencies and recorded consumer adoptions are satisfied.

- Scope: whole plan through all remaining phases and terminal delivery.
- Current slice: S2 work-item README dual-read and compact-current-state contract.
- Remaining scope: S2–S5 in Core; consumer migrations under their own goals.
- Done when: the legacy progress ledger is removed from Core with no dangling references, and every recorded consumer migration has landed.
```agent-host-coverage
{"schema_version":1,"shared_source":".agents/workflows/workflow_runtime.py","hosts":[{"host":"claude","behavior":"Resolve work-item READMEs and legacy plans through shared graph, provider and preflight paths; enforce Stop transfer through the packaged plan handoff launcher.","source":".agents/hooks/plan_graph.py; .agents/workflows/workflow_runtime.py; .agents/workflows/workflow_ops.py; .agents/hooks/plan_handoff_stop_launcher.py","mapping":"The shared .agents graph/provider/preflight runtime is packaged in engineering hooks and workflows; Claude Stop transfer is wired through plan_handoff_stop_launcher.","verification":{"level":"source","result":"passed","evidence":"Source graph 27, provider 17, inspect/preflight 6, Stop 33 and launcher 15 passed; generated payload self-containment passed. Installed Claude host acceptance remains pending."}},{"host":"codex","behavior":"Resolve work-item READMEs and legacy plans through shared graph, provider and preflight command paths.","source":".agents/hooks/plan_graph.py; .agents/workflows/workflow_runtime.py; .agents/workflows/workflow_ops.py","mapping":"The .agents runtime packages shared graph/provider/preflight command paths in engineering hooks and workflows. Current plan-transfer Stop wiring is Claude-only; no native Codex Stop gate is claimed.","verification":{"level":"source","result":"passed","evidence":"Source graph 27, provider 17 and inspect/preflight 6 passed; generated payload self-containment passed. No native Codex plan-transfer Stop gate or installed-host acceptance is claimed."}}]}
```
