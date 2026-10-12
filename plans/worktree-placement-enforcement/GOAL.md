# Worktree placement enforcement

Status: R5 path-executable argv extraction repair verified; a new incremental review watermark and CI are next.

## Authority and ownership

The user instructed this session on 2026-10-12 to read HANDOFF.txt and execute this goal from its current checkout. Standing engineering session-guidance standards-repair authority covers diagnosis, implementation, tests, a plain GitHub PR and merge after repository gates pass. This successor owns only new worktree placement enforcement. The originating investigation and active sibling migration remain with their owners.

Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-WorktreePlacementEnforcement
Branch: Fix/WorktreePlacementEnforcement
Base: origin/main at 376df0ced5283a4ee4247d07feb10e8671b64475, refreshed before implementation.
PR: https://github.com/tj-agents/core/pull/220 (draft). Initial reviewed head: d1837ee308af71b76ffc833219bb8d6ff51c15a2; the exact current delivery head and runs are held in the existing runtime binding and owner.
Bug: BUGS.md B007

## Pickup and cause

Pickup was acknowledged here before deliverable edits. Historical launcher failures were superseded by the user's direct resumption; no launcher retry is needed.

The correct installed open-worktree prose calculates common-root/.worktrees/flattened-branch. Both host engineering manifests lacked a native creation gate. Narrowly filtered October 8 tool evidence at 2026-10-08T16:19:37.087Z contains an explicit native Git add targeting core.worktrees/Fix-ClaudePermissionArgumentPatterns. No raw transcript is committed.

The allocator producer remains owned by Feature/RepositoryOwnedLayout, including commits 6383bbc and 4fd86e3 and its repository-layout proposal. This repair does not copy that allocator or move existing active checkouts.

## Delivery slice and behavior

One independent slice adds .agents/hooks/worktree_placement_gate.py, executable regression tests, both host PreToolUse wiring, the engineering harness inventory and its source shipping map. It starts at the refreshed remote default without an allocator dependency. Expected scope stays below 1,000 substantive lines and eleven authored files.

Recognized native Git creation must use one standalone literal command with an absolute -C checkout and absolute destination following --. Bounded read-only Git establishes the common root even from a linked checkout. Only a flat child of that root's real .worktrees directory is accepted. Explicit named branches match their flattened destinations; detached start points remain usable.

Sibling/nested/existing destinations, symlink redirection, ambiguous syntax, compounds, expansion and repository routing through global options or inherited Git environment are rejected. Errors after creation recognition fail closed. Inventory and non-creation operations remain usable.

Opaque scripts or indirect wrappers and orchestration tools that emit no supported shell PreToolUse event are outside this direct-native-command gate. Source/package verification does not establish trust or adoption in an already running installed host.

## Verification

- Twenty-two focused executable creation tests complete; two symlink-capability cases skip on this Windows environment and remain for Linux CI. Both accepted primary and linked commands execute through the shell.
- Fifteen harness tests and twenty-two source-layout tests passed.
- Harness synchronization and declaration check, package generation and its consistency check passed. Regenerate the final review repair before its checkpoint.
- Agent instruction-file pairing passed in both directions with exact Claude pointer content. Plan graph passed with zero errors; its existing oversized repository-config ledger warning belongs to that separate owner.
- Workflow skill-name discovery's former-flat-layout failure is already recorded in docs/workflows/TECH_DEBT.md. The supported explicit lifecycle source-path input succeeded.
- Generated package output and catalog digests remain local test state. The PR stages only the authored hook inventory addition in the catalog, preserving baseline digests.
- Current evidence is in workflow runs worktree-placement-enforcement and worktree-placement-focused-tests-v2. First exact-head CI run 38273227680 failed only the stale expected hook inventory on both hosts; that fixture is corrected and its focused budget test passed. Prior-head CI run 38283095124 at d1 passed Windows 114924860753, Linux 114924860413 and guard 114924860584; R5 needs a new exact-head qualification.
- Linux CI run 38279872696 failed qualification when `exec_command` selected PowerShell for an argv `bash.exe` path and the post-recognition mock test accepted an internal destination before the intended failure path. R4 normalizes shell executable names for explicit and argv forms and uses a nonexisting sibling with asserted common-root and claim calls.
- R5 locally copies and normalizes supported shell argv executables before shared extraction, preserving the original event for claims. Outer `command`/`cmd`/`script`/`input` and nested `action.command`/`action.cmd` path-Bash argv forms reject a sibling and allow a direct internal destination; nested and outer backtick substitution regressions remain covered.

## Execution and continuation

Investigation selected L3. One L4 worker implemented the specified repair and has released its source/test writer lease. Review selects L4 for ordinary correctness and test-impact judgments; commit/push selects L7 for bounded clerical operations. The parent retains this goal, review synthesis and delivery ownership.

A supported continuation owner was initialized and foreground-claimed at .agents/continuation/owner.json. Its scheduler registration succeeded and an observed wake respected the live foreground writer. Keep the same owner; renew the lease while working and release/checkpoint it before a scheduled writer can act.

## Reviews

Immutable full review completed at d1837ee308af71b76ffc833219bb8d6ff51c15a2 against 376df0ced5283a4ee4247d07feb10e8671b64475 with three retained gate-correctness findings. All three are repaired and verified; a new incremental watermark is required. Descriptor is in Git-private workflow run placement-review-full. Native reviewer and one fresh workflow lens run read-only; the specialist model was unavailable and the workflow lens uses the ordinary L4 fallback. Its canonical work order is reviews/Fix-WorktreePlacementEnforcement.md; do not merge until its exact-head watermark and required checks pass.

Frozen native review at ea33aa1 completed with R4: `exec_command` argv shell classification did not normalize Bash `.exe` paths. R5 then found that shared extraction still joined a path executable wrapper. The R5 repair is checkpointed for a new incremental review watermark; no delivery action is authorized before that review and required CI.

## Next Steps

Scope: whole plan through all remaining phases and terminal delivery.
Current slice: regenerate and checkpoint the verified source/test repairs, then publish the replacement candidate to PR 220 and complete its incremental review and required CI.
Remaining scope: isolated review, exact-head Windows/Linux CI, plain GitHub PR merge and causal generated-distribution verification.
Done when: the reviewed enforcement source is merged, required CI and causal regeneration pass, generated both-host packages carry the hook, and actual installed/native limitations are recorded accurately.

1. Repair commits d1837ee and 3b57620 are preserved. Imported fresh-main conflict repair retains fixture-maintenance B006 and records placement as B007; run final generation/check before publication.
2. Run the canonical isolated review from its frozen descriptor. Resolve findings within this same slice and use incremental review for later commits.
3. Publish one stable draft PR, bind its exact head and monitor its checks through the existing continuation. Mark ready and use guarded authorized merge after review and CI pass.
4. Observe only this merge's causal regeneration; verify shipped source, dependencies and both host hook manifests. Record completion and resolve B007 with actual evidence, without claiming installation into an unrelated profile.

## Agent-host coverage

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/hooks/worktree_placement_gate.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Reject unsupported native Git allocation and verify common-root internal placement",
      "source": ".agents/hooks/worktree_placement_gate.py",
      "mapping": ".agents/plugins/manifests/claude/engineering-hooks.json PreToolUse",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "19 executable placement tests passed in workflow run worktree-placement-stable-final; primary and linked creation execute accepted commands; both host hook wiring, 15 harness tests and 22 source-layout tests passed. Two Windows symlink capability skips await Linux CI. Installed host trust/adoption is not asserted."
      }
    },
    {
      "host": "codex",
      "behavior": "Reject unsupported native Git allocation and verify common-root internal placement",
      "source": ".agents/hooks/worktree_placement_gate.py",
      "mapping": ".agents/plugins/manifests/codex/engineering-hooks.json PreToolUse",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "19 executable placement tests passed in workflow run worktree-placement-stable-final; primary and linked creation execute accepted commands; both host hook wiring, 15 harness tests and 22 source-layout tests passed. Two Windows symlink capability skips await Linux CI. Installed host trust/adoption is not asserted."
      }
    }
  ]
}
```
