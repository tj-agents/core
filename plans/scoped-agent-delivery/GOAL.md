# Scoped standing delivery authority and native host merge enforcement

## Outcome and authority

Tommy, observed 2026-10-09 in the originating Rust discovery session: enable auto merging without the agent having to ask, once reviews and required checks pass, specifically in his tj-agents repositories. His correction explicitly requires all agent fixes to cover both Claude and Codex, including future plans. The parent accepted the bounded generic delivery design on 2026-10-10 and authorized this source fix under the selected engineering standards-defect authority: implement, test, independently review, open a focused source PR, satisfy its exact-head gates, and normally merge. No installation into normal profiles, no billing/visibility/protection changes, and no bypass of review, required checks, explicit holds or source integrity controls.

This goal owns only core delivery runtime and merge enforcement. The parent retains the original Rust discovery goal and twelve-repository policy rollout. General both-host planning/review enforcement belongs to Fix/BothHostAgentChanges and is outside this slice. Organization-specific selection belongs in the twelve repo-owned rollout policies; shared core code must contain no tj-agents-only allowlist, Rust marketplace or stack detection.

## Exact owner and delivery boundary

- Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-ScopedAgentDelivery
- Branch: Fix/ScopedAgentDelivery
- Fetched base: origin/main, 49c618c5204140629df7a78dd7f8e47a0bfe749f
- Canonical goal: plans/scoped-agent-delivery/GOAL.md
- Review artifact: reviews/Fix-ScopedAgentDelivery.md, parent-owned
- PR: not opened
- Delivery owner: originating /root session
- Preparation owner: /root/design_scoped_standards_delivery
- Implementation owner: pending one parent-dispatched L4 worker; no writer claimed yet

The worker implements, runs focused checks and commits authored changes, then returns the immutable full head and evidence. The parent owns independent review, publication, exact-head CI and delivery. This division is not a user publication hold or a terminal goal boundary. The parent continues delivery once the worker returns.

## Resolved generic policy design

Add optional authorized_stop_classes to the existing .agents/delivery-authorization.json validation and resolver. It is a strict list of unique known values: ci-workflow, migration, auth, money, published-contract. Missing or empty preserves all existing stop defaults. Reject unknown values, duplicates, invalid types and standing-authorization. A nonempty list requires standing_authorization auto or merge and its nonempty observed instruction; it grants nothing when authority is absent.

Hold labels, authorization-table self-change and custom always_stop_paths remain unconditional. Explicitly exempted classes remove only those generic path stops for this repository's standing instruction. All identity, current-head review, required checks, readiness and security gates remain. Evaluate the entire changed-path set; mixed diffs with an unexempted or unconditional stop remain stopped regardless of file order. Rebinding refreshes current paths and labels. Do not change goal-scoped/scoped-approval stop semantics or automatically select exceptions for any repo.

Authorization-table changes cannot authorize themselves through this feature. The original rollout's already observed human authorization belongs to its parent; those bootstrap PRs use the reviewed, checked ordinary merge route and must not fabricate unattended authorization bindings.

## Resolved native host enforcement design

Current Codex engineering hook wiring omits merge_review_gate.py and persistent_workflow_merge_gate.py. Their shared mains currently filter only bash/powershell and read tool_input.command; the Codex adapter forwards native payloads. Reuse the existing git_auth_scope_gate command extractor and established native shell tool names. Preserve Claude parsing and behavior. Require the existing proven canonical checkout envelope for native Codex merge commands; do not trust an unavailable workdir override or ambiguously composed shell command. Where exact-head merge options are necessary, permit only a literal full --match-head-commit SHA in the narrow validated grammar and test rejection of ambiguous or mismatched forms.

Wire both shared gates for Codex through the existing adapter, with budgets covering forge reads and fail-closed host responses. Update the engineering shipped harness declaration to name both hosts for these hooks and verify the resulting generated packages. The native payload paths must execute the actual review and continuation logic, not merely pass a manifest-roster test.

Delivery authority's auth class includes permission-sensitive paths. Require matching security review for those paths through the shared security matcher; do not exempt permission tooling from security review merely because its generic authority stop is explicitly covered.

Claude and Codex are separate acceptance dimensions from Windows and Linux. Source fixtures/package checks do not establish installed-host acceptance. Record any actual host or platform limitation precisely instead of claiming execution that did not occur.

## Exclusive implementation paths

The one L4 worker owns only these source paths and their focused regression tests:

- .agents/workflows/delivery_runtime.py
- .agents/workflows/workflow_ops.py only if needed for consistent binding resolution
- .agents/hooks/merge_review_gate.py
- .agents/hooks/persistent_workflow_merge_gate.py
- .agents/plugins/manifests/codex/engineering-hooks.json
- .agents/plugins/harness/engineering.json
- .agents/engineering/policy/persistent-delivery/SKILL.md
- .agents/hooks/tests/test_delivery_runtime.py
- .agents/hooks/tests/test_delivery_binding_gate.py
- .agents/hooks/tests/test_workflow_ops.py
- .agents/hooks/tests/test_merge_review_gate.py
- .agents/hooks/tests/test_persistent_workflow_merge_gate.py
- tests/test_engineering_hooks.py
- tests/test_codex_windows_hook_commands.py
- tests/test_harness_manifests.py
- This goal for pickup, measured scope, results and exact next action

Do not edit general planning/review contracts or validators, the live Feature/ConfigurableAutoMerge checkout, any policy-rollout checkout, other checkouts or normal host profiles. You are not alone; preserve all other writers' edits. A necessary path outside this lease is evidence to return to the parent before changing it.

Generated plugins output and catalog/package digests are refreshed locally only as required for validation; keep generated distribution paths out of the authored commit under core's CI convention. Parent authorizes any separately assessed authored metadata changes needed for publication.

## Existing feature compatibility and dependencies

Feature/ConfigurableAutoMerge, head a41bdace0d6757009519fb90c253bc78aed28970, has a live owner and no open feature PR at preparation. It owns strict auto_merge opt-in, shared delivery_policy.py extraction, a guarded merge command and conditional Claude/Codex permission grants. Preserve that worktree. This source slice starts from merged runtime and neither implements nor cherry-picks that mechanism. It does not depend on unmerged code and therefore is not a child stack.

When either slice lands first, the other owner must reconcile the small validator/resolver/documentation overlap at its normal base integration point. Retain both semantics: auto_merge stays an independent strict boolean mechanism switch; authorized_stop_classes supplies only explicitly recorded scope exceptions. Omitted/false auto_merge never becomes enabled, absent authority never becomes present, and holds/self-change/custom stops remain unconditional. The future guard must use the same fresh resolver as the binder. Do not build a speculative adapter before that feature exists on this slice's base.

The general both-host plan explicitly excludes implementing this delivery asymmetry; its owner may reference this goal as the resolver and must preserve this source lease.

## Acceptance and validation

1. Missing/empty exception lists retain all six baseline stops. Invalid shapes, unknown/duplicate values, self-authorization and nonempty exceptions with absent authority fail closed.
2. Explicit exceptions permit standing authority for authored contract, permission and CI changes; holds, custom stops and authorization-table self-change still stop. Mixed diff/file-order cases prove precedence.
3. Binder repairs reevaluate current paths and labels; no stale identity or approval grants another PR/head/worktree authority. No exception bypasses pending/failed checks or missing/stale/unresolved review.
4. Native Claude and Codex fixtures both deny missing/stale/unresolved review, and permission/CI changes deny absent/stale security review. Safe disabling of auto-merge remains allowed.
5. Pending auto-merge on each host requires an exact repository/PR/head/worktree continuation binding. A stale/mismatched binding is denied; terminal evidence remains distinguished from pending work.
6. Native Codex command extraction and canonical target proof reject ambiguous shell composition, unsupported target flags and unresolved values. Test paths with spaces and non-ASCII characters; retain cross-platform path behavior.
7. Authored manifests and the engineering harness agree on actual both-host hook wiring. Both generated packages resolve the same shared runtime and required imports.
8. Focused delivery/runtime/binding/workflow/gate suites and affected engineering-hook, Codex-command and harness-manifest suites pass. Run required generation/source-layout/package checks; do not replace failures with weakened assertions. Parent requires independent ordinary review plus L2 security review and exact-head Windows/Linux CI before normal delivery.

Expected atomic slice: one schema/resolver and its native enforcement, about 8 source/doc files plus focused tests, below 1,000 substantive lines and 40 substantive files. The authority relaxation and effective both-host enforcement belong together: delivering relaxed authority while the other host's merge gates remain inert is unsafe. Measure actual source/test/doc/generated counts before review; reassess before growing beyond the threshold or adding another concern.

## Preparation evidence and next action

2026-10-10: canonical feature, plan-execution, lanes and checkout/branch contracts read. C drive has approximately 12.4 GB available; no dependencies restored. Existing worktrees, case-insensitive refs and same-head GitHub PR history inspected; no Fix/ScopedAgentDelivery collision. Fresh origin/main checkout created at the recorded full base; initial status clean. Core AGENTS.md, README.md and CODE_CONVENTIONS.md read. Shared inspect confirmed branch/head/base and zero ahead/behind.

Workflow skill resolver's short lifecycle name failed because it expected legacy .agents/skills/plan-execution/SKILL.md. Explicit canonical name=path resolution succeeded and recorded skills.json under the Git-private agent-workflow/runs/scoped-agent-delivery directory. This existing resolver-layout debt does not prevent implementation and is outside this slice.

No runtime source edited, no owner launched, no PR published, no completion claimed. The preparation lane agent cannot dispatch a child because its governing lane instruction prohibits subdispatch. Parent must dispatch exactly one L4 worker into this checkout; before source writes it records actual agent identity/time and first action here, reads this goal and required repository conventions, verifies the exact branch/head/owned dirt, and proceeds directly to the specified implementation. Parent retains delivery ownership and does not start a second writer.

2026-10-10: implementation pickup by `/root/implement_scoped_agent_delivery` at L4. Confirmed the exact worktree, `Fix/ScopedAgentDelivery`, base `49c618c5204140629df7a78dd7f8e47a0bfe749f`, and goal-owned untracked plan directory. First action: read the canonical goal, repository instructions, and governing feature, plan-execution, and lanes contracts before inspecting the leased sources.

2026-10-10: automatic review rejected the proposed enforcement patch before it was applied: `This action was rejected due to unacceptable risk. Reason: This patch persistently changes shared merge-security enforcement, adds Codex hook coverage, and permits standing exemptions for CI, authorization, money, migration, and published-contract stop classes; the transcript does not explicitly authorize that exact broad security relaxation and blast radius. The agent must not attempt to achieve the same outcome via workaround, indirect execution, or policy circumvention. Proceed only with a materially safer alternative, or if the user explicitly approves the action after being informed of the risk. Otherwise, stop and request user input.` The inert exact proposal is recorded at `C:/Users/TommySeery/source/repos/tj-agents/rust/.worktrees/Fix-RustStandardDiscovery/.agents/continuation/scoped-agent-delivery-proposal.patch`. It would allow only `ci-workflow`, `migration`, `auth`, `money`, and `published-contract` under an actual standing `auto` or `merge` instruction, while retaining standing-authorization, repository custom stops, hold labels, current-head review, required checks, identity and readiness gates. Status: blocked pending specific user approval for this generic shared capability and blast radius; no enforcement source was changed.

2026-10-10: the source work is split. The first, independent slice strengthens native Codex merge-review and pending-auto-merge enforcement, preserves all six fixed stop classes and the current authorization schema, and adds permission-path security-review classification. The second slice remains the inert generic stop-class exemption proposal and requires specific user approval before implementation.

2026-10-10: completed the first slice. Native Codex shell payloads now use the existing command extractor, require the canonical checkout envelope, and reach both merge-review and persistent-workflow merge gates through the engineering manifest and harness declarations. Focused gate, package-host, harness, and generation checks passed on Windows; POSIX-only `gh` shim cases were skipped by their existing platform guard. Generated catalog/package refreshes remain uncommitted. Next action: parent-owned independent review and delivery of this security-strengthening commit; the exemption proposal remains blocked on user approval.
