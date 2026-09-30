# Work ownership and positive standards

## Outcome and authority

The user explicitly requests a separate core handoff to fix the generic workflow mistakes exposed by
the Party Foundation repair. Implement a durable, coherent ownership model in existing standards and
supported runtime. Standards should explain the intended responsibilities, lifecycle and decisions
positively. Explicit prohibitions are reserved for important invariants that actually need them.
Avoid accumulating incident-specific instructions, duplicate warnings and unnecessary policy machinery.
This is implementation authority for the core repair, not merely a request for a proposal.

## Ownership

- Repository: tj-agents/core.
- Existing checkout: C:/Users/TommySeery/source/repos/tj-agents/core.worktrees/Fix-InSessionLaneExecution.
- Current branch observed: Docs/SequentialDelivery; previously recorded head 0550098bd3767d92f72e6227e0670c8a039e5759. Verify current identity before edits.
- Preserve existing sequential-delivery work, reviews/Docs-SequentialDelivery.md, and unrelated untracked plans/in-session-lane-execution/.
- This core successor exclusively owns generic workflow/standards changes in this checkout. A separate successor owns B2B/.NET naming and DDD; do not edit those checkouts or launch another owner.
- Consumer installation and merge are held. Reuse an established owning review when publishing corrections; first inspect the actual repository/branch/PR relationship. A checkout without its own PR does not establish new work scope.
- Lane L1: selecting the smallest sound ownership model and its canonical enforcement boundary requires design judgment. One core successor only.

## Evidence and failure mechanism

During an authorized B2B naming correction, an agent created local correction commits in
Refactor/PartyFoundationQuality. Those commits were already merged into the existing review branch
Refactor/PartyFoundationApplicationBooking, PR #38. When the user asked to see the corrected PR, the
agent treated the correction branch as a new deliverable, opened redundant PR #43, and retargeted #38
to it. It performed a branch-local PR-existence check instead of resolving the existing owner of the
work. It had loaded open-pr/push/pr-preflight, so merely adding more prose is not proven prevention.
The error cost another round of PR edits and explanations.

Recovery is already complete on the product side: #43 is CLOSED, #38 is OPEN/draft on main at
7069315a783bfea463abf64f098fcc9ded43cb0b and contains the corrected commits and full naming table.
Children #39–#42 and dotnet standards #31 now link to #38. This core task must preserve that recovery;
the PR numbers above are evidence, never identifiers to hardcode into shared behavior.

The earlier assistant proposed a blanket PR-creation rejection rule. The user explicitly corrected
that direction: they want standards which make the correct behavior follow from a clear model,
with minimal bloat, rather than a collection of "don't do X" clauses. An executable guard is useful
only when it enforces the established general model through a real supported entry point. Do not
claim that adding instructions or an easily bypassed wrapper guarantees host enforcement.

## Next Steps

1. Commit the verified local repair and complete an incremental review in
   `reviews/Docs-SequentialDelivery.md`, preserving the earlier pass. Resolve any findings locally.
2. Publication remains pending identification of the owning core standards review. The current branch
   has no PR; open #32, #54, #55 and #58 have distinct recorded scopes. No evidence binds this correction
   to them. Once ownership is established, integrate the correction into that review and return its URL.
   Merge and consumer installation remain explicitly held.

## Completed implementation and verification

- `git-branching` owns the outcome/slice/review model and correction integration. Open-pr, preflight,
  push, plan execution and handoff reference that decision before selecting publication mechanics.
- The existing ledger `PR:` header now survives repository-provider resolution as the optional
  `artifacts.pull_request` field. Existing state without that field remains valid. A URL identifies the
  review; explicit `not opened` identifies an assessed slice awaiting its first review.
- `workflow_ops.py delivery-preflight` resolves that record, an explicit owning URL, or an existing
  delivery binding against GitHub, then checks the branch's PR when no review was recorded. It routes
  update, integration, separate creation, scope assessment and closed/fork review reconciliation.
  Contradictory owners and foreign repositories fail before publication. Blocked routes return nonzero.
- `docs-and-debt` owns the positive standards-authoring guidance. This repair changes existing owners
  rather than introducing a new registry, wrapper, hook or scope ledger. Guidance and its state/runtime
  implementation are one coupled repair; splitting them would deliver a contract without its decision path.
- 202 targeted Python tests passed: workflow operations 43, workflow contracts 62, process standards 19,
  plan/handoff ownership 10, delivery runtime 28, delivery binding hook 21, source layout 16, catalog 2,
  agent-file delivery 1. Tests include a correction on another branch, a successor in another worktree,
  preserved transfer state, existing binding, legitimate separate work, stack base, conflicting/foreign
  owners and forge failure. Skill packaging, instruction pairing, generated output, harness/catalog,
  documentation reachability and tier payload checks passed.
- Three stale prose assertions from the preserved sequential-delivery commit were reconciled with its
  unchanged merge/techdebt behavior. Initial workflow-contract failures were stale generated resources;
  generation and catalog refresh resolved them. No runtime test was disabled or weakened.
- Coverage is the supported preflight/provider path and documented publication workflow. Semantic scope
  assessment and patch containment remain agent responsibilities. No universal interception of gh commands,
  host adoption, remote CI, release, merge or consumer installation is claimed.

## Acceptance

The existing workflow resolves correction work to its owning review before branch-based publication;
legitimate new work still follows the normal review path. Shared standards have one clear source owner,
explain the positive lifecycle, and do not acquire incident-specific identifiers or repetitive bans.
Relevant tests prove the ownership decision and discovery/packaging remain consistent. Claims about
host enforcement match observed coverage. The plan records concrete completed changes and any real
remaining gates, without asking the user to re-orchestrate routine work.

## Coordination and current status

The core successor read this plan and accepted sole writing ownership on 2026-09-30 in the named
checkout. Branch identity was verified at 0550098. Main was fetched and merged as 169b4c4;
the conflicts were derived digests/output, regenerated from the combined authored sources.
Sequential-delivery work and its review, and the unrelated in-session-lane-execution plan, are preserved.

Publication ownership: Docs/SequentialDelivery has no PR in any state. The open core reviews are #32,
#54, #55 and #58; their scopes do not establish an owning review for this correction. Finish and commit
the local repair. A new PR is not inferred from the checkout's missing PR. Merge and installation remain held.

Implementation decision: `git-branching` owns work/slice/review selection; branches and checkouts are
execution locations. Reuse the ledger's existing `PR:` field in portable workflow state and resolve it
against forge state in `delivery-preflight` before publication. Preserve that field during handoff.
`docs-and-debt` owns positive standards authoring. Focused tests will exercise provider continuity and
preflight routing, including separate work. These supported flows do not intercept arbitrary gh commands.

The separate B2B/.NET owner uses:
C:/Users/TommySeery/source/repos/Concertable/b2b/.worktrees/Refactor-PartyFoundationLegacyBindings/plans/party-foundation/PARTY_FOUNDATION_PROGRESS.md.
Read that record only as evidence; do not edit it concurrently. Actual product review:
https://github.com/Concertable/b2b/pull/38. .NET naming/DDD review:
https://github.com/tj-agents/dotnet/pull/31. Those repairs have their own tests and external CI/Docker
gates; they are not this core task's implementation scope.
