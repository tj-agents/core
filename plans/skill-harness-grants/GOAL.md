# Automatic grants for skill-owned harness capabilities

Status: first schema compatibility slice locally verified; review and delivery next.

## Outcome and authority

Tommy clarified the required behavior on 2026-10-08 in the repository-layout owner session:
"any kind of skill oriented harness should be injected via the harness grant, meaning hanresses are
ubiquitious and you never need to ask for permission for these things".
He explicitly rejected routine approval questions for this setup and directed that the broken harness
be fixed. Implement and deliver the repair through focused reviewed PRs and normal CI/merge. Apply the
shipped repair through supported host installation/bootstrap to the affected trusted personal scopes
and prove native acceptance. Do not substitute another recommendation or a hand-edited local allowlist.
Standing engineering:session-guidance also authorizes this bounded standards-defect source repair.

The required rule is general: every selected skill's required harness capabilities come from its shipped
owner declaration and are injected automatically in both hosts. A missing grant or bootstrap bridge is
a source defect to repair. The user must not assemble machine-local approvals or answer routine prompts
for already-authorized skill workflows. Startup and child-host launch must be included in acceptance.
Keep grants constrained to the declared capability, verified package and authorized target; changing the
host's global security mode is not an implementation of skill-scoped grants. Preserve the user's existing
Infonetica commit/publish policy and separate credential-copy hold, which are outside this defect.

## Ownership

Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-SkillHarnessGrants
Branch: Fix/SkillHarnessGrants
PR: not opened
Fresh base: d3c88e839f9ddbce80e38aaa6ecaaef1f3c78c7d (fetched origin/main, 2026-10-08)
Owning goal: plans/skill-harness-grants/GOAL.md in this checkout.
Launch lane: L1 to decide the host/manifest/bootstrap mechanism; route implementation to L4 afterward.
Execution owner: Codex session 01a11b14-2ce8-71b1-95c5-0a97f5d383a6, PID 45392.
Current base: 73fb99cd91a2b7786912c85eea1feb99fcd9724e after a verified fast-forward on 2026-10-08.
This explicitly assigned goal remains the single progress owner; no roadmap or competing plan is created.
Parent: Codex session 01a11794-26f3-7fb2-accb-0df87faa5180, Feature/RepositoryOwnedLayout.
Parent retains the full repository-layout and adoption goals. You own only this grant source repair and
its native acceptance. Do not edit or close the parent's checkout, plan, ledger or session.
Write pickup and actual first-action evidence to .agents/continuation/skill-grants-pickup.json; include
session ID, host, branch, head and UTC timestamp. Return result/PR/merge/native proof in this goal and
plans/skill-harness-grants/RESULT.md. Launcher submission alone does not prove pickup.

## Confirmed gap and relevant source

- Current main's .agents/hooks/harness_grant.py only grants three strict Git patterns: merge the remote
  default into a feature branch, verified worktree removal, and verified branch deletion. It runs as
  Claude PreToolUse and explicitly excludes Codex. It does not generally consume skills' harness manifests.
- .agents/plugins/harness/*.json and harness.schema.json already declare skill-owned permissions and
  host requirements. machine/bootstrap-capabilities/scripts/repo_config.py renders selected Claude allow
  rules and Codex rules/settings. Use and complete this ownership chain instead of inventing a second one.
- The new marketplace checkout's Claude launch was observed at its native initial folder-trust screen
  before session pickup. This is startup gating, before a PreToolUse hook can grant a tool. Inspect the
  real supported native bootstrap/launch interface and prove how declared trusted scope reaches it.
- The exact stalled checkout is C:/Users/TommySeery/source/repos/tj-agents/marketplace/.worktrees/Feature-CoreCatalogAdoption,
  titled TJ Agents aggregate adoption. Its goal is plans/core-catalog-adoption/GOAL.md. The parent owns
  recovery of that existing session; do not launch another agent there or change that checkout.
- Native Claude source owners for core PR #133 and #136 encountered automatic classifier denials
  labelled Merge Without Review for a post-merge fetch and a ScheduleWakeup monitor/merge request.
  Distinguish missing grant injection from a real review gate. Approved skill execution must carry its
  existing authority/provenance through the supported host boundary. Do not weaken review/CI checks.
- Parent source snapshot at 4fd86e3 has a completed allocator and its own review. It is unrelated to your
  implementation paths; do not absorb that branch. Source generation is not native adoption evidence.

## Existing ownership to reconcile

You are not alone in this repository. Preserve and accommodate others' work.
- PR #100 Refactor/MachineAgnosticHarness is OPEN. Its commit 2aed1a4 adds the base:harness policy that
  grants, hooks and trust boundaries ship with plugins/repositories instead of hand-typed user settings.
  Its checkout .worktrees/Refactor-MachineAgnosticHarness is at 573b106 with generated-only local changes.
  Reconcile that existing policy PR as the intended contract rather than creating another policy owner.
- .worktrees/Fix-HandoffWorkflowGrant is clean at old 8b5aedd, no matching PR in the recent inventory and
  no established active owner. Its inherited root GOAL.md is unrelated stale history. Preserve it;
  this fresh checkout is the sole writer for the new explicit repair scope.
- PR #137 Feature/HandoffCodexPython is OPEN and owns the Codex launcher Python port. Inspect its exact
  current diff before changing shared launch code; coordinate/stack to preserve that owner, not duplicate it.
- PR #99 Feature/SecretRefreshGrant is OPEN and owns credential-refresh behavior. Do not absorb it or
  copy credentials as a shortcut. Other running cleanup/lane/status owners remain separate.

## Design and delivery boundary

Load plan-execution, lanes, git-branching and applicable standards. Read current source and host contracts
before deciding the smallest mechanism. Keep canonical source under .agents, host differences in their
adapters, and generated plugins outside PRs. Update shipped harness/schema/manifest declarations atomically
when capabilities change. Use focused PR-sized slices, serialize dependency delivery and retain ownership
until the full repair's observed acceptance passes. A policy-only PR does not complete this defect.

Required acceptance:
- A fresh ordinary consumer of selected skills gets all required skill harness grants on Claude and Codex
  without manually assembling a settings file or repeatedly approving the declared operation.
- A fresh linked worktree and an authorized independent native handoff inherit the same capability set;
  include startup/trust handling through supported host interfaces, not only a mocked hook response.
- Reproduce the current missing-grant/startup failure, then demonstrate it repaired in disposable trusted
  fixtures and in the affected normal installation. Record exact versions, package identities and receipts.
- Unselected, modified or unrelated executable commands do not acquire the declared skill grant.
  Existing repository-specific authority, actual review requirements and unrelated host settings survive.
- Updating/removing a selected skill reconciles its owned grants deterministically. Both hosts' supported
  limitations must be verified from local CLI/runtime or primary documentation, not guessed.
- Every substantive source slice passes focused regression tests, generated/harness checks, native review
  and exact-head CI. Report the genuine installed result, not merely that scripts or manifests exist.

## Delivery slices and mechanism

The loaded standards are the root instructions, harness directory instructions, plan-execution, lanes,
git-branching, plans, plan-checkpoint and committing. Shared source stays under `.agents/`; generated
packages remain uncommitted. Parent retains ownership with bounded workers; no fresh top-level owner
is needed for these connected slices.

1. Schema compatibility, current branch based on `73fb99cd91a2b7786912c85eea1feb99fcd9724e`.
   Change `.agents/plugins/harness.schema.json` and focused manifest tests only, estimated under 200
   substantive lines. Both pattern entries and match/not_match examples already accept string lists
   in the runtime and shipped declarations, but the published schema accepts only strings. Each item
   must use this schema shape, preserving legacy strings and rejecting nested/empty/nonstring lists:

   ```json
   {"oneOf":[{"type":"string","minLength":1},
     {"type":"array","minItems":1,"items":{"type":"string","minLength":1}}]}
   ```

   Consumer: existing harness manifests and catalog references to the published schema. Verify all
   three shipped manifests through an actual JSON Schema validator plus positive/negative examples,
   focused manifest tests, harness sync check, independent review and exact-head CI. No unused API.
2. Verified selected package and complete invocation grants for the existing command inventory.
   Deliver selection/provenance checks, argument/target contracts, native hook adapters, owned static
   grant removal and tests together; the concrete mechanism remains under L1/L2 review. A package's
   availability never proves user authority for publication or another checkout's mutation.
3. Remaining skill declarations and startup/handoff integration, preserving PR #137's launcher owner,
   followed by shipped installation and native acceptance. Reassess exact boundaries after slice 2
   design. Preserve PR #100 as the shared policy owner; do not create another harness policy.

The intended runtime chain is active host selection, verified package bytes and owner declaration,
complete command/argument match, authorized absolute target validation, existing operation gates,
then the native per-call allow response. Receipts record evidence; they cannot invent user authority.
Reject unselected, modified and unrelated commands. Keep real deny/review checks authoritative.

## Native capability evidence

Read-only investigation verified Claude 2.1.282 and the active npm Codex 0.160.0. The active Codex
binary is `C:/nvm4w/nodejs/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe`.
Its supported PermissionRequest decision runs before automatic approval review; PreToolUse alone
cannot approve elevation. Its shell payload lacks actual execution workdir and requested sandbox
permissions, so grants cannot infer targets from session cwd. The exact release contracts are
[approval routing](https://raw.githubusercontent.com/openai/codex/rust-v0.160.0/codex-rs/core/src/tools/approvals.rs)
and [hook construction](https://raw.githubusercontent.com/openai/codex/rust-v0.160.0/codex-rs/core/src/hook_runtime.rs).

Claude provides PreToolUse grants and turn-scoped skill allowed-tools. Its documented workspace trust
inherits from an accepted main repository into linked worktrees, but no supported arbitrary fresh-clone
interactive pretrust switch was found. Print-mode execution does not prove interactive startup
acceptance. See [workspace trust](https://code.claude.com/docs/en/permissions#project-allow-rules-and-workspace-trust).
Do not use global security bypasses, undocumented trust-file edits or copied credentials as substitutes.
Native acceptance probes have not run yet.

## Current progress

Verified pickup and first-action evidence is in `.agents/continuation/skill-grants-pickup.json`.
The continuation owner is initialized and claimed by PID 45392; its Windows task is registered and
an observed wake retained the active foreground lease. Schema correction and real JSON Schema
regressions are complete: 13 focused manifest tests pass, all three harness declarations pass the sync
check, and `git diff --check` is clean. The source/test delta is 85 additions and three deletions.
Native acceptance probes have not run. Runtime design and independent L2 security readiness review
continue; these tests do not establish installed grant behavior.

The current sync scans cached packages without enabled-selection or integrity checks and writes
global rules. The replacement must resolve verified active selection before projecting grants.
`scripts/sync_harness_manifests.py --check` passes for all three declarations at the current base.
Workflow skill recording's default path is obsolete; its supported explicit `name=canonical/path`
input avoids that default. The parent retains ownership of the broader repository-layout repair.

## Next Steps

Scope: this automatic skill-harness grant repair through design, source delivery and native acceptance.
Current slice: correct the consumed harness schema and qualify its declarations with actual schema
validation, then review and deliver this preparation before the runtime grant slice.
Remaining scope: full plan incomplete; source repair, reviewed delivery and native adoption remain.
Done when: selected skill-owned capabilities reach supported host startup/execution automatically and
the native regression scenarios pass with the repair shipped and adopted in the affected trusted scopes.

1. Commit the verified schema candidate, obtain independent review and deliver through the normal
   repository gates. PR #100 remains open
   at 573b106023dc1f316053646aecb06486f87a4f9c and PR #137 at
   a8da4019aab7d17151e1729ab76c34a3bac6d0ad; their ownership is preserved.
2. Reproduce the grant-delivery gaps on safe fixtures, decide the minimal shared mechanism and obtain
   focused readiness/security review where required. Keep source trust/provenance explicit.
3. Use L4 implementation, meaningful native/focused tests and serial review fixes; deliver focused PRs
   through the normal repository gates. Ordinary authorized steps need no new user confirmation.
4. Verify actual host adoption and return exact outcome evidence in RESULT.md. Retain responsibility for
   unsupported native behavior by resolving it within scope or recording precise capability evidence;
   do not hand a routine permission/configuration checklist back to Tommy.
