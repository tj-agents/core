# Validation efficiency investigation

## Outcome and authority

On 16 October 2026 Tommy requested a separate handoff to investigate why the personal work-items delivery took roughly four hours, whether recent Core slowdown fixes were actually used, and which remaining checks or workflows should change. This is an investigation and proposal, with authority to read source/history/CI evidence, run proportionate non-destructive measurements, and maintain this goal. Return findings for discussion. Do not implement runtime or workflow changes, disable hooks, edit CI, open a proposal-only PR, install plugins, or expand consumer adoption under this goal.

Success means a short evidence-based explanation and prioritized concrete recommendations: what was necessary work, which safeguards caught real defects, what was agent overhead, what remains Core/tool overhead, and the smallest worthwhile changes. It is acceptable to recommend no change to a useful safeguard. Do not justify the whole four hours from one CI measurement or assume all hooks are harmful.

## Identity and ownership

- Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Investigate-ValidationEfficiency
- Branch: Investigate/ValidationEfficiency
- Baseline: fetched origin/main 8bddc8ef158f02704377656ce7c6dce6dfa44979
- Work item: validation/efficiency
- Dispatching session: codex:01a1415f-6448-7123-8b17-c7fb67aee637
- Lane: L3, bounded open investigation with unresolved alternatives.
- Local writer budget: one successor, owning only this goal and investigation artifacts beneath plans/validation-efficiency/. Other source paths are read-only.
- Pickup: acknowledged by codex:01a1447f-62b8-70e0-a7a3-20a040f97690 at 2026-10-16T11:37:57Z. This successor is the sole writer beneath plans/validation-efficiency/.
- First substantive observation: the checkout is on Investigate/ValidationEfficiency with only the handed-off goal untracked. The goal explicitly limits this task to investigation; the existing proportionality comparison is accepted, and no runtime implementation is authorized. The advertised session_store.py exposes hook ingestion only, so the supported work-item claim entry point must be resolved before claiming ownership.
- The docs session retains the original problem-management rollout; this side task does not complete or transfer it.

## Existing context to carry forward

The cross-repository owner is C:/Users/TommySeery/source/repos/tj-agents/docs/plans/problem-management/PLAN.md. Read its Delivery and headache checkpoint, Remaining dependency and requested reflection, and Reflection for the requested discussion sections. It records nine delivered PRs across Template, work-items, Core and marketplace, with all causal main CI passing. Tooling is delivered; broad personal adoption and legacy-record migration are not complete. Work-items primary MISTAKES.md M002 retains the slowdown incident. This is not a second repair dispatch for that record.

Recent proportionality fixes WERE used: all six skill files changed by Core PR #268 (WorkflowProportionality), commit 2380644a, matched both the installed package and this session's hook snapshot byte-for-byte. Evidence: C:/Users/TommySeery/AppData/Local/Temp/work-items-slowdown-fix-comparison.json. Directory version 2.1.16 alone is not evidence of stale instructions. Carry this established comparison forward; reopen only for a concrete contradiction.

The current committing, feature, review and plan-execution contracts already call for focused checks, natural local commits, batched stable pushes, concurrent review lenses and reuse of valid evidence. They do not require a full Windows/Linux matrix for every local commit. Determine whether remaining cost comes from executable enforcement, repository CI, agent choices, or a mismatch among them.

Measured Core main run 38840514845, after PR #273: verify-windows 02:27:29-02:46:51 UTC (19m22s), verify-linux 02:27:29-02:31:07 UTC (3m38s), both passed. The exact-run monitor observed 1,020 seconds of remote waiting during its window, not the whole session. The Windows shared-runtime suite started at 02:34:21 and was still running at 02:44. Fetch step/test timings and logs before choosing caching, parallelism or selection changes. Do not re-run the broad suite merely to reproduce an already evidenced duration.

Useful checks found genuine issues: immediate-create retry duplication; body integrity and record-kind binding; adoption serialization/rollback and foreign-provider preflight; helper import/discovery; native-host receipt binding. Preserve those protections and stale-head/security/authorization guarantees.

Avoidable orchestration included guessed paths/command errors, an unchecked dependent native exit (M001), repeated small README review cycles, two record-only Markdown PRs, and implementing current-lock compatibility concurrently with an existing replacement. Distinguish these agent choices from unavoidable Core requirements. Personal factual records should batch; do not create another standalone record PR. GitHub provider adoption should remove Markdown-record publication overhead after rollout.

## Existing work and exclusions

There is already unfinished overlap at C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-RoutineReviewAndImpactCi/plans/routine-review-evidence-and-impact-ci/GOAL.md, branch Fix/RoutineReviewAndImpactCi, baseline 3af7ad74. It specifies ephemeral routine review proof and impact-selected CI. Its dirty .agents/hooks/merge_review_gate.py and .agents/workflows/auto_merge.py are preserved. No PR or registry owner was found on 16 October; native recovery returned this docs session and closed codex:01a13aab-ca88-71d1-8703-dbf0d0ec8970 as contextual matches, not verified ownership. Read the existing proposal and inspect its delta without editing or resuming it. Compare its assumptions with current main and recommend reuse, supersession or coordination. Do not create a competing implementation or silently inherit its older broad implementation authority.

Also inspect already delivered docs-review proportionality work before proposing the same fix again. Consult installed/source guidance via advertised paths; do not guess canonical skill directories.

Core PR #269 remains separately owned by codex:01a13fa0-a1c6-7051-b3ce-a63fb26916da. Its Fix/RollingPluginSync worktree is C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-AlwaysLatestPlugins. Do not edit, claim, close or merge it, or edit Core primary. It owns unversioned plugin selection/current-source refresh. The docs plan records prospective integration and six current merge conflicts. Treat versioning work as a dependency, not a new repair. Do not migrate 35 consumers or user profiles here.

Do not touch Infonetica/Azure DevOps policies, credentials, global configuration, generated plugins output, other owners' worktrees or live continuation state. Source documentation alone does not authorize runtime changes. No general web survey is needed to resume this measured investigation; reuse established research unless a specific unresolved technical question needs primary-source verification.

## Investigation and completion criteria

1. Trace actual local commit, stable push, review, bookkeeping and CI triggers. Map rule -> executable gate -> observed behavior. Identify repetitions with unchanged relevant inputs. Explain whether the existing proportionality fix is obeyed.
2. Account for costs using available timestamps and logs. Report measured durations separately from estimates and unknowns; avoid fabricated precision for the four-hour total.
3. Explain the slow Windows steps. Recommend the smallest credible focused-check path for ordinary changes, while retaining Windows/Linux coverage for large, risky or materially cross-platform changes. Do not use a size label alone as a safety bypass.
4. Compare batch/reuse/cache/parallelism/selection/removal options. Each recommended change needs source owner/path, observed cost, retained benefit, acceptance check and coordination dependency. Prefer fewer mandatory steps to another layer of hooks/checklists.
5. End with a concise prioritized proposal for Tommy, explicit what is already fixed and what still needs updating. Mark this investigation complete only when that report is saved here and returned. Runtime implementation remains a separate decision.

## Investigation progress

- Supported claim attempted through `.agents/machine/scripts/work_item_sessions.py claim validation/efficiency --host codex --role owner --status active --title ... --plan-path plans/validation-efficiency/GOAL.md`. It exited 1: `could not verify the current native codex session: cannot resolve a verified registry attachment for this host and current directory; do not force-close the host`. The CLI was run with host-side access after sandbox inspection. No forced registration, global configuration or continuation state was changed. Native identity comes from CODEX_SESSION_ID/CODEX_THREAD_ID, and the originating goal independently verifies this successor's pickup. The investigation continues foreground-only.
- Historical job metadata and Windows/Linux logs for Core run 38840514845 are saved under this goal. Windows source/package tests: 356.141s for 1,191 tests; shared runtime: 737.509s for 1,183 tests. Corresponding Linux durations: 65.246s and 138.304s. No broad suite was rerun.
- Remote main remains the handed-off 8bddc8ef baseline. The overlap checkout is 88 commits behind its tracked main with exactly two dirty source files, preserved read-only. Its changes affect review lookup/staleness only; it contains no CI selector.

## Completion and proposal

The report is saved in [FINDINGS.md](FINDINGS.md) and is the requested result for discussion. Investigation complete; no runtime implementation, publication, installation or adoption is authorized by this completion. The final response returns its concrete findings and this goal's absolute path.

- Measured: four relevant Core PR/main validation windows total 71m28s; other work overlapped them. The last Windows job spends about 94% in two serial Python suites. No full-suite rerun was used. The original four-hour total has no complete host telemetry in the supplied evidence; its remaining shares are explicitly unknown.
- Reconciled: #268 was active and routine docs proportionality is already delivered. The preserved overlapping checkout contains incomplete local-review lookup edits and no CI selector; reuse its goal after ownership/baseline reconciliation, not a competing implementation.
- Proposed: prioritize impact-selected PR CI with an explicit successful aggregate and safe fallback; apply existing stable-push/factual-record batching; separately coordinate private ordinary-review proof; optimize expensive fixtures after timing. Retain meaningful review, Windows/Linux coverage, security, stale-head and authority checks.
- Verification: linked report artifacts exist; all saved JSON parses; the four-run sum is 4,288 seconds; all six established installed/snapshot comparisons are true. Source inspected against confirmed current main. No product/runtime tests were required for this investigation-only output.
- Runtime limitations: supported session-store claim could not verify the native registry attachment. No active delivery or delayed external result is owned here; no continuation was installed or claimed, and existing live continuation state was left untouched.

## Next Steps

Return the saved findings for Tommy's discussion. This investigation has no further execution action. A separate user decision is required to implement the proposed CI/review changes. If authorized, first reconcile ownership and current-main baseline of Fix/RoutineReviewAndImpactCi, then define/test its coverage mapping and required aggregate. PR #269 and personal adoption remain separately owned.

```completion
{
  "outcome": "Investigated validation and orchestration costs and saved concrete prioritized recommendations for discussion.",
  "acceptance": [
    {
      "id": "trace",
      "criterion": "Map rules, executable gates, observed review/commit/push behavior and overlapping work.",
      "evidence": [
        {
          "source": "plans/validation-efficiency/FINDINGS.md",
          "result": "Trigger comparison and existing-goal reconciliation recorded against main 8bddc8ef."
        }
      ],
      "owner": "codex:01a1447f-62b8-70e0-a7a3-20a040f97690",
      "next_action": "Discuss the saved findings; implementation requires a separate decision."
    },
    {
      "id": "timing",
      "criterion": "Separate measured validation costs from estimates and unknown portions of the reported four hours.",
      "evidence": [
        {
          "source": "plans/validation-efficiency/delivery-timing-summary.json",
          "result": "Four relevant event windows total 4288 seconds; final Windows step and test timings saved with explicit limits."
        }
      ],
      "owner": "codex:01a1447f-62b8-70e0-a7a3-20a040f97690",
      "next_action": "No further measurement required for this proposal."
    },
    {
      "id": "proposal",
      "criterion": "Give prioritized source-owned recommendations with safeguards, acceptance checks and coordination dependencies.",
      "evidence": [
        {
          "source": "plans/validation-efficiency/FINDINGS.md",
          "result": "Four recommendations compare batching, reuse, selection, fixture optimization, parallelism, caching and removal; runtime implementation remains outside authority."
        }
      ],
      "owner": "codex:01a1447f-62b8-70e0-a7a3-20a040f97690",
      "next_action": "Await a separate implementation decision."
    }
  ],
  "deliveries": [],
  "open_tasks": []
}
```
