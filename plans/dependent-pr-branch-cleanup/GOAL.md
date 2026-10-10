# Preserve dependent PRs during merged-branch cleanup

## Ownership and authorization

Canonical goal: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-DependentPrBranchCleanup/plans/dependent-pr-branch-cleanup/GOAL.md
Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-DependentPrBranchCleanup
Branch: Fix/DependentPrBranchCleanup
Base: synchronized origin/main at b4e6f1020b4c1edcfea8e21d6dae2ba5ebdb8a5e (original diagnosis base 8b656fb197771916c58aea4418934aaa7648b1c0)
PR: not opened
Originating work-plugin session: 01a12650-0c24-7573-9dc1-d0fa28c71a6c

This is one bounded standards-defect side workstream under engineering:session-guidance's standing authorization: diagnose and repair a broken consumed standard, implement, test, commit, open the owning PR and merge after required gates pass. The originating work-plugin goal is already delivered and stays with its originating session. Do not adopt, rewrite or close that goal or any work-repository PR/checkout. No normal-profile installation or user-scope enablement, billing change, visibility change, package-feed publishing, unsafe deletion or check bypass is authorized here. Preserve every other core/work checkout and writer.

Lane: L3 for the bounded diagnosis of the missing guard and primary-versus-linked cleanup route; reroute specified implementation to L4, security review to L2 only if its stakes require it, mechanical delivery lower. The independent checkout isolates this concurrent repair. A separate successor is launched once; launcher submission alone does not prove pickup.

## Observed defect and source

On 2026-10-10 tj-agents/work PR1 merged at 3b021cab6943a422870772de88266b9323d494d9 after all required CI passed. The merged branch Feature/WorkCommunications was still the base for two different owners' OPEN PRs: PR2 at e7082075dc5c82c03b9319e0402b20a5e5deb564 and PR3 at fa0055956fb0704f19ed62196160e9243bf22707. Ordinary git push origin --delete Feature/WorkCommunications unexpectedly closed both PRs rather than applying GitHub's documented automatic base retargeting. Immediate recovery restored the remote parent at ad8296a63f60c4565b32b15169f9f0a63c4d725e and reopened both original PRs with their original heads and base. They are now OPEN; their checkouts/code were preserved. The original primary checkout is on current main with green PR and causal main CI. Do not delete that retained dependency branch again or modify these child PRs.

Consumed engineering:merge Step5 insists the spent branch be removed without a required dependent-base check. The canonical .agents/engineering/workflow/merge/scripts/cleanup_proof.py queries only gh pr list --state open --head branch (lines411-423 in current main); it does not detect open PRs using the branch as BASE. git-branching advises confirming retargeting, but merge cleanup lacks a positive safety guard and a legitimate retained-dependency outcome. The primary-checkout branch deletion route also needs protection; adding a linked-worktree-only guard would leave the incident route open.

Source scope: .agents/engineering/workflow/merge/SKILL.md, its scripts/cleanup_proof.py, existing relevant .agents/hooks cleanup gate/tests and engineering policy guidance only as needed for the same guard. Host manifests change only when shipping a real changed requirement. Do not edit generated plugins payloads as authored source; refresh for verification per core guidance. Consult the actual existing helper/hook mechanisms before adding anything new. This defect is distinct from existing transferred-cleanup-obligation PR142 and fresh-worktree-audit PR101; coordinate if a source overlap is discovered instead of overwriting another owner.

## Completion expectation

The same shared cleanup behavior protects both Claude and Codex. Before deleting a local/remote merged branch, authoritative open-PR evidence must distinguish HEAD users from BASE dependents; unknown/failed forge evidence preserves rather than deletes. Another owner's live base dependency preserves the branch and records that owner's dependency without blocking completion of an otherwise delivered source PR or forcing adoption/closure of the child. Any authorized retarget/restack must be verified before deletion. Meaningful offline regressions reproduce open-base protection, the allowed no-dependent case and observation failure; no real repository branches or PRs are deleted to test this. Complete required source/generated validation, independent immutable review, exact-head CI, ordinary merge and causal generated publication. Never claim installed adoption or never-again guarantees from source checks alone.

## Delivery slice

The missing guard and its primary/linked workflow routes form one safety boundary. Keep the shared helper, workflow contract, permission-grant changes and offline regressions in one slice; shipping instructions ahead of unavailable runtime support or runtime support without mandatory primary-route use would leave the incident route open. No unrelated guidance or sandbox-runtime repair belongs in this candidate. Estimate: fewer than 15 substantive source/test files and 1,000 lines; reassess measured scope before review if exceeded.

## Progress

Pickup acknowledged by session 01a127b0-7047-7e30-af8c-c861898d7e5b on 2026-10-10. Checkout code was clean at 8b656fb197771916c58aea4418934aaa7648b1c0, with only this goal directory untracked. Existing linked worktrees were inventoried and preserved. Read README and CODE_CONVENTIONS; loaded plan-execution as the existing goal owner and bugfix technical guidance.

Diagnosis lane L3: missing open-BASE evidence confirmed in cleanup_proof.py and a primary checkout route that skips linked-worktree proof. Specified implementation assigned to bounded L4 worker; parent keeps serial goal/checkpoint/review/delivery ownership.

Independent recurring sandbox setup failure: ordinary commands cannot start, including login:false. Existing isolated Fix/SandboxSetupReadFailure goal already identified upstream OpenAI ACL bug PR51822; no host repair had occurred. One renewed machine:handoff-codex submission succeeded through scoped elevated execution, launching codex-cli 0.162.0 for that existing checkout. Prompt: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-DependentPrBranchCleanup/plans/dependent-pr-branch-cleanup/sandbox-repair-followup-prompt.txt. Successor pickup was observed in the existing sandbox goal; it authenticated and staged the fixed alpha runtime and retained the concrete installation gate. No runtime installation or successful ordinary-command acceptance has been observed. This session retains dependent-PR cleanup ownership.

Focused validation: the original cleanup proof run passed 21 of 22 offline cases; its sole new empty-squash fixture defect was repaired. The primary-route selection then passed all three cases (saved branch deletion, open BASE retention, default-branch refusal). The fresh-receipt current HEAD/BASE grant case and detached reaper dependency case passed. Payload invariant and instruction-file pairing passed. Receipt selection passed. The changed finish surface passed 22 of 24 tests; both failing Windows offline process fixtures were repaired and their targeted rerun passed (2 tests, 27.757s). The scheduled observer now receives its test-only offline forge stub as a staged fixture resource; no production observation bypass was added. Logs: core/.git/agent-workflow/runs/dependent-cleanup/artifacts. Authored checkpoint 8538879 was synchronized with unrelated origin/main continuation changes in merge 5045210. Catalog refresh, generated refresh/check, catalog check, harness check and skill packaging all passed after correcting source-root ordering.

## Next Steps

Scope: whole plan through all remaining phases and terminal delivery.
Current slice: one atomic dependent-PR cleanup safety repair against origin/main, including shared proof, primary and linked instructions, grant safety, offline regressions and host packaging.
Remaining scope: focused and required generated/harness validation, immutable independent review, exact-head Windows/Linux CI, ordinary merge, causal regeneration and safe cleanup.
Done when: the guard is merged with all required gates and causal regeneration green, and the isolated checkout is safely retired or intentionally retained for a verified live dependency.

1. All encountered fixture and packaging failures are repaired with focused green reruns. Checkpoint those corrections, freeze the synchronized candidate, publish the draft for exact-head CI and complete independent review.
2. Complete immutable independent review, addressing confirmed findings through a new verified checkpoint. Preserve unrelated source and other owners.
3. Add meaningful offline regression tests for this exact safety boundary, run focused affected checks and core-required generated/harness validation, then commit the source slice and complete independent review at its immutable head. Both hosts must be covered explicitly.
4. Publish one stable candidate through plain Git/gh, preserve current review and CI gates, normally merge when authorized and green, verify only the causal generated publication, and clean up this isolated checkout safely under the repaired dependency guard. Record the actual outcome and any real gate in this same goal. Do not ask for routine continuation approval or report launch as completion.

## Host coverage

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/engineering/workflow/merge/SKILL.md and its shared cleanup proof with .agents/hooks branch dependency observation",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Preserve local and remote merged branches used as open PR bases; primary and linked cleanup require authoritative HEAD and BASE evidence",
      "source": ".agents/engineering/workflow/merge/SKILL.md; .agents/engineering/workflow/merge/scripts/cleanup_proof.py",
      "mapping": ".agents/plugins/sources.json maps the canonical engineering scope to plugins/engineering/skills/merge plus packaged shared resources",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Offline linked/primary dependency proof and fresh-receipt grant cases passed; generated host packages, catalog, harness and skill packaging checks passed. This verifies source and generated resources, not installed host adoption; independent review and exact-head CI remain."
      }
    },
    {
      "host": "codex",
      "behavior": "Preserve local and remote merged branches used as open PR bases; primary and linked cleanup require authoritative HEAD and BASE evidence",
      "source": ".agents/engineering/workflow/merge/SKILL.md; .agents/engineering/workflow/merge/scripts/cleanup_proof.py",
      "mapping": ".agents/plugins/sources.json maps the canonical engineering scope to plugins/engineering/codex-skills/merge plus packaged shared resources",
      "verification": {
        "level": "planned",
        "result": "pending",
        "evidence": "Run offline cleanup proof primary/linked dependency regressions, shared grant regressions, and generated package tests for both host entry points before independent frozen-head review"
      }
    }
  ]
}
```
