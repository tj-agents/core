# Validation efficiency findings

Investigated on 16 October 2026 against Core main `8bddc8ef158f02704377656ce7c6dce6dfa44979`, confirmed through the remote branch API. Scope: investigation and proposal only. No runtime, hook, CI, plugin installation or consumer changes were made.

## What explains the elapsed time

The recent slowdown fix was active. The [established six-file comparison](proportionality-comparison.json) for Core #268 matches the installed package and the delivering session's hook snapshot. Rechecking package version labels would not explain this incident.

This was nine delivered PRs across four repositories, including a new tracker, retry handling, a provider protocol, packaging and installed acceptance on both native hosts. Useful review and live checks caught retry duplication, body/kind integrity failures, adoption rollback races, foreign-provider preflight, helper discovery and host receipt binding. Those were substantive repairs, not unnecessary review churn.

There was also avoidable owner overhead: command/path errors, repeated small documentation cycles, two record-only PRs, and preparing versioned adoption while #269 already owned its replacement. The docs delivery checkpoint and work-items M002 record these observations. The supplied artifacts do not contain complete host timing/token telemetry, so an exact allocation of all four hours among implementation, inference, hook execution, environment friction and waiting would be invented.

CI is a large measured component. The two relevant Core PRs produced four distinct successful runs, all attempt 1:

| Candidate/event | Run | Windows job | Linux job | Event window |
|---|---:|---:|---:|---:|
| #272 PR, `1b9e948a` | 38832163141 | 18m43s | 4m20s | 18m50s |
| #272 main, `6aea302b` | 38834317856 | 13m27s | 4m24s | 13m29s |
| #273 PR, `02aa2c51` | 38837295696 | 19m40s | 4m02s | 19m44s |
| #273 main, `944cc2aa` | 38840514845 | 19m22s | 3m38s | 19m25s |

The event windows total **71m28s**. They are non-overlapping remote validation windows, not 71 minutes of exclusive agent idleness; marketplace delivery and other work overlapped the final run. The earlier monitor's 1,020-second wait is part of that final window and must not be added again. PR and main validate different commits; these are not duplicate same-head reruns. They repeatedly execute many unchanged subsystems because selection is absent.

The two record-only work-items PRs (#6 and #8) occupied 3m56s and 8m08s from creation to merge: **12m04s combined**, including human/agent/review/merge time. Their four PR/main CI windows total only 3m29s. Removing their publication cycles saves orchestration as well as CI; it cannot account for hours by itself.

Evidence: [delivery timing summary](delivery-timing-summary.json), four saved Core job responses, and historical `*-runs.json` / `*-pulls.json`. Run windows use API creation/update timestamps; job durations use start/completion timestamps.

## Where Windows spends its time

For run 38840514845:

| Step | Windows | Linux |
|---|---:|---:|
| Source layout/package suite, 1,191 tests | 5m58s (356.141s test runner) | 1m07s (65.246s test runner) |
| Shared runtime suite, 1,183 tests | 12m19s (737.509s test runner) | 2m19s (138.304s test runner) |
| Remaining job time | about 1m05s | about 12s |

The two serial suites consume about **94%** of Windows job time. Four checkouts take 24 seconds; generation and its immediate check take four seconds. There is no demonstrated dependency-download bottleneck to solve with a cache first.

Timestamped verbose output points to `test_workflow_ops` (~177s of completion gaps on Windows versus ~7s Linux), `test_continuation_runtime` (~95s/29s), `test_merge_cleanup_gate` (~84s/11s) and `test_workflow_contracts` (~76s/23s). These are approximate intervals around emitted test completions, including fixtures and output boundaries, not instrumented per-test timings. See [test timing summary](test-timing-summary.json) and the saved Windows/Linux logs.

Source inspection supports repeated process/filesystem setup as an optimization target: `test_workflow_ops.RepositoryFixture.setUp` initializes/configures/commits a Git repository for each inherited test; cleanup tests construct repositories and worktrees; `tests/test_source_layout.py` copies three authored trees per fixture; standards-sync tests repeatedly create bare repositories, clones and commits. Continuation tests also intentionally exercise waits and process termination. The evidence does not isolate Windows process startup, filesystem scanning, runner contention or antivirus into separate causal shares. Do not remove timeout/concurrency coverage based on these estimates.

## Rule → mechanism → observed behavior

| Trigger | Current rule and executable mechanism | What the evidence shows |
|---|---|---|
| Local coherent checkpoint | `engineering/contract/committing/SKILL.md`: focused green checks then a local commit. Inspected hook manifests do not launch the CI matrix on commit. | Adapter repairs were committed at `70b88b5`, `8576e5c`, `fb463ab`; each changed behavior. No full matrix per local commit is required. |
| Stable push / PR | Committing and remote-validation require batching stable candidates. `.github/workflows/ci.yml` runs unconditionally on every PR event and main push; it has no impact classifier or cancellation group. | Each delivered Core PR has one observed PR run and a later main run. Batching was used for those runtime candidates; broad unrelated suites still ran. |
| Review | Frozen preparation and incremental review bind base/head, paths, rules and security coverage. Routine docs mode selects one focused lens only after semantic assessment. | Adapter work order has four successive changed candidates, each with real integrity/adoption findings. It also records preserving the final reviewed head across disjoint main movement. Repeating that entire review on unchanged inputs would violate the reuse rules; these four passes do not establish that violation. |
| Review proof at merge | `merge_review_gate.py` and `auto_merge.py` prefer the committed work order and fall back to the local file. `workflow_ops.py` and `delivery_runtime.py` also consume work-order evidence. | A local review is already readable at merge, and committing guidance already says to keep it local. The remaining debt is a consistent private ordinary-review contract, not a universal requirement to push a review stamp. |
| Bookkeeping / record capture | Committing excludes bookkeeping-only pushes; review-lifecycle retains local proof through merge and forbids review-only cleanup commits. | Two record-only PRs were delivered despite intended factual-record batching. Provider adoption should remove Markdown publication from ordinary personal capture; adoption remains separately pending. |
| Forge wait / shell tools | `forge_poll_gate.py` suppresses unchanged polling; compact-output captures validation; delivery controls bind PR/head/authority; manifests start several separate Python hooks/adapters. | The final exact-run monitor records useful bounded waiting. Hook startup overhead is plausible but unmeasured here. No evidence supports blaming hooks for the whole elapsed time or disabling their safeguards. |

Source paths above are beneath `.agents/` unless explicitly `.github/`. Core's workflow has no `merge_group` trigger or E2E job: generic queue guidance is not evidence that Core has an additional queue validation tier. Branch-protection API returned “Branch not protected”; rulesets were not audited. A future selector must establish an actual required successful aggregate and corresponding merge checks, rather than assuming skipped jobs prove coverage. `auto_merge.green_exact_head` currently accepts completed skipped/neutral checks.

## Prioritized proposal

These were the investigation proposals before Tommy authorized implementation on 16 October 2026. The implementation outcome below records what subsequently shipped.

| Priority / change | Owner and source | Cost addressed / benefit retained | Acceptance and coordination |
|---|---|---|---|
| 1. Finish impact-selected CI using the existing goal | Core `.github/workflows/ci.yml`, selector tests and delivery check configuration; existing `Fix/RoutineReviewAndImpactCi` goal | Broad PR/main validation windows of 13–20 minutes. Keep generated-source integrity, relevant regressions and real platform checks. | Deterministic changed-surface selection; unknown paths/ranges and broad infrastructure changes fall back to full coverage. A successful aggregate must require every selected job; failure or missing classification fails closed. Test docs, skills, focused runtime, shared infrastructure, rename/deletion and unknown-range cases. Reconcile the old owner before execution; CI changes retain their approval gate. |
| 2. Apply batching and evidence reuse already required | Delivery owner; `committing`, `remote-validation`, `review` and `docs-review` | Two record PRs consumed 12m04s of lifecycle windows; command mistakes and repeated prose cycles have no trustworthy minute total. Retain actual defect review and local recoverability. | Ordinary factual capture causes no standalone PR/matrix; several local repair commits lead to one stable push; unchanged candidate/rules reuse valid evidence; routine prose uses the existing focused mode when eligible. Coordinate personal provider adoption with #269's owner. No new enforcement hook is proposed. |
| 3. Reconcile the existing ordinary-review proof proposal | Core review/review-lifecycle/docs-review contracts; `merge_review_gate.py`, `auto_merge.py`, `workflow_ops.py`, `delivery_runtime.py` and host adapters/tests | Removes work-order ceremony and stamp transport; a separate measured saving is unavailable. Preserve independent review, exact candidate, security coverage, findings and authorization. | One private ordinary-review proof accepted consistently by all consumers; missing, stale, tampered and wrong-repository/branch proofs reject; supported resume recovers proof without weakening checks. Big/staged reviews retain durable Markdown. Reuse the existing goal; do not cherry-pick its two edits as a complete solution. |
| 4. Optimize the expensive test fixtures, then consider isolated shards | Core `.agents/hooks/tests/test_workflow_ops.py`, `test_continuation_runtime.py`, `test_merge_cleanup_gate.py`, `test_workflow_contracts.py`; `tests/test_source_layout.py`, `test_claude_standards_sync.py`; CI | Serial suites consume 18m17s on the measured Windows run. Retain real Git/process/lock/timeout behavior and Windows/Linux coverage. | First record per-test/fixture timing during a required CI run, not another reproduction matrix. Reduce redundant immutable setup with isolated writable fixtures; shard only modules proven not to share mutable state. Preserve the same discovered cases/skips and negative assertions. Recheck selector ownership to avoid overlapping CI rewrites. |

A credible focused path would distinguish inert prose/navigation from executable agent guidance, then map changed behavior to test modules. For #273, plugin-lock/adoption tests, schema validation, generation/manifest checks and relevant host/package composition are credible starting surfaces on Windows and Linux. Discovery must include consumers such as current selection and host settings. This is a proposed coverage map, not a proven equivalent selector. A small security/launcher/shared-bootstrap change can still require broad coverage; size alone never grants a skip. Large changes, uncertain dependency closure or changes spanning generation, permissions and delivery surfaces retain the full matrix. Keep the full matrix on main initially while proving PR selection; assess main selection separately from published-package acceptance.

Cache only immutable inputs after timing demonstrates worthwhile savings. Do not cache green behavioral results across changed runtime, rules, environment or platform identities. Batching is the cheapest immediate improvement; selection avoids irrelevant work; fixture reuse reduces necessary work. Parallelizing the two Windows suites alone has an ideal upper saving near the shorter six-minute suite, before added setup and contention. It is a secondary option, not a promised speedup. Remove redundant record publication and ordinary work-order transport, not review/security/authorization checks.

## Reconciliation and decision

The overlap checkout is 88 commits behind current main and contains only 13 insertions/37 deletions across `merge_review_gate.py` and `auto_merge.py`. It switches proof reads to the local file and tightens head equality; it has no CI selector, shared proof format, migration, recovery implementation or accompanying new tests. Current main has since delivered #268's stable-push/reuse guidance and explicit routine-docs review. Preserve those delivered behaviors and the old goal's outcome; supersede its claims that every ordinary review must be committed and every Markdown candidate needs full review. Its implementation remains incomplete. Revalidate ownership before resuming; do not start a competing branch or adopt its earlier implementation authority here.

Already fixed: active proportionality guidance, focused routine-docs mode, retry receipts, body/kind integrity, adoption locking/preflight, helper discovery and host binding. Still worth updating: CI breadth, consistent private ordinary-review proof, expensive repeated test setup, and delivery-owner compliance with batching. #269's selection cutover and consumer adoption remain with their existing owners.

The requested investigation was completed and returned before Tommy authorized implementation on 16 October 2026. The existing implementation goal was reconciled and reused; the old checkout's two unfinished source edits were preserved.

## Implementation outcome

The authorized follow-up delivered three reviewed PRs on 16 October 2026:

- PR #274 (`621c7a21`): impact-selected PR CI with conservative full fallback and a fail-closed `ci-required` aggregate. Main retains full Windows/Linux validation. Exact-head full CI `38902959829` and causal main CI `38905321932` passed.
- PR #275 (`f572ed65`): shared private ordinary-review proof and consistent consuming gates, with stale/tampered/foreign evidence and incomplete reviews rejected. Exact-head full CI `38912304559` and causal main CI `38915378822` passed. Generated packages refreshed at `946e53c3`; installed-host upgrade and consumer adoption are separate.
- PR #276 (`8834fc4c`): immutable per-class Git seeds copied into isolated writable workflow fixtures. All 96 test methods and negative assertions remain unchanged. Required CI `38916073108` selected that module on Windows/Linux; jobs passed in 2m6s/15s. Direct isolation and independent reviews passed. [Fixture measurements](fixture-results.md) record the approximately 77% reduction in the measured local setup/cleanup operation, with no whole-job speedup promise.

The completed goal files are retired by this closeout. Existing stable-push and factual-record batching guidance continues to apply. PR #269, broad consumer adoption and global hook installation remain with their existing owners.
