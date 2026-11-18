# Preserve dependent PRs during merged-branch cleanup

## Ownership and authorization

Canonical goal: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-DependentPrBranchCleanup/plans/dependent-pr-branch-cleanup/GOAL.md
Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-DependentPrBranchCleanup
Branch: Fix/DependentPrBranchCleanup
Base: last synchronized origin/main at a7d91c0e4b37c456b4119512ffae2b773ae148a1
PR: https://github.com/tj-agents/core/pull/190 (draft; published exact head adc50e3d42a7723887107e9992612662148c006f; corrective working tree in final verification)
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

Publication checkpoint: PR190 is open draft and local/remote/PR heads all equal 6fd7c127919cf0055e9f9b67f41b0cb21aaf5591. Authoritative body validation passed. Immutable descriptor/work order are prepared, and both-host review coverage validation passed. Native specialist was unavailable and native fallback could not read the candidate; neither result is accepted as clean. Two independent read-only L4 native-general and workflow readers completed the same frozen bundle. Both confirmed command-safety defects: option-prefixed branch names and undeclared raw remote deletion. The completed review watermark is 6fd7c127919cf0055e9f9b67f41b0cb21aaf5591 with changes requested; serial L4 remediation completed the tightly coupled fixes. The eight remote-action safety cases passed (156.060s); leading-dash refusal, local cleanup and both-host manifest inventory also passed. The action rechecks actual-origin PR evidence and uses a saved-head lease. Required generated checks, checkpoint and fresh incremental review follow. Exact-head CI run 38094491279 completed successfully: guard, verify-windows and verify-linux all passed at 6fd7c127919cf0055e9f9b67f41b0cb21aaf5591. The correction will require its own exact-head CI. The same continuation owner is rebound to PR190/head6fd7 and foreground claimed. Scoped merge authorization is recorded in the delivery binding.

## Next Steps

Scope: whole plan through all remaining phases and terminal delivery.
Current slice: one atomic dependent-PR cleanup safety repair against origin/main, including shared proof, primary and linked instructions, grant safety, offline regressions and host packaging.
Remaining scope: serial R4/R9-R11 repair and final focused verification, new exact-head immutable review/CI, authorized merge, causal regeneration and safe cleanup.
Done when: the guard is merged with all required gates and causal regeneration green, and the isolated checkout is safely retired or intentionally retained for a verified live dependency.

1. Completed R1/R2 command-safety repair in 5f41a47 and integrated main in da794afde95e02a10aa137f52786a7db7cd1941f. The second frozen review completed with changes requested and exact-head CI finished red; all six R3-R8 findings are in the exclusive corrective implementation/verification lease.
2. Corrective checkpoint490a810 and main integrationadc50e3 are committed and published to existing PR190; local/remote/PR heads match. Focused verification and required generated/harness checks passed. The same owner is rebound and foreground claimed.
3. Third frozen review da794af..adc50e3 is complete with changes requested; both-host coverage validation passed. CI38135803091 finished red on both platforms only in two remote-action fixtures; source/package and generated gates passed. Monitor23325 completed and its exact terminal result was reconciled. The exclusive writer owns remaining R4/R9-R11 code/fixture corrections and meaningful focused verification. Then checkpoint one stable head, publish existing PR190, rebind this same owner and run fresh incremental review/exact CI.
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
        "level": "source",
        "result": "passed",
        "evidence": "Offline primary/linked dependency, grant and process regressions and generated host package checks passed. Independent full review completed with command-safety findings now in serial repair; exact-head CI remains pending. This does not prove installed adoption."
      }
    }
  ]
}
```

The active canonical goal remains a working file through the terminal delivery gate; it is removed from the publication candidate to keep this born-and-done implementation plan out of main. This does not delete its local owner or change authorization.

CI blocker: exact head da794af run38097456853 finished red on both platforms in the two auto-merge permission-sync fixtures. Both consume the real engineering manifest; focused reproduction fails. Required generated/catalog/harness/packaging and guard jobs passed. Isolated final workflow/security review remains owned at this frozen head; validate concrete findings then serialize the correction and new exact-head review/CI. No check bypass or rerun of unchanged failing head.

Final corrective review completed at da794af with six actionable findings (manifest loader compatibility/platform coverage, push destination identity, ambient forge repository override, post-observation live claimant race, and required remote-action completion). R3-R8 are recorded in reviews/Fix-DependentPrBranchCleanup.md. This is the same atomic cleanup authority boundary; splitting the helper, permission declaration or local/reaper enforcement would publish an unsafe incomplete route. If final measured lines exceed 1,000, retain this bounded atomic correction exception rather than ship mismatched source contracts. No unrelated auto-merge policy or sandbox implementation is adopted.

Exclusive serial L4 remediation lease assigned to the existing cleanup writer for R3-R8. Parent decisions: use supported helper wildcard declarations without changing the permission validator; central origin-bound forge observation; capture and verify the effective push destination; record remote-action completion before any local cleanup; repeat target/live-claimant checks after blocking observations. Required offline fixtures remain test-only. No other source writer or broad permission change is authorized.

Continuation recovery: a package refresh removed the pinned legacy delivery-continuation.ps1 while this owner was active. The exact old scheduler receipt/task was verified and retired through its shipped hook-snapshot adapter; the current delivery_continuation.py registered the SAME owner/task name with the existing native Codex executable. Registration succeeded and a real wake returned working without launching another context. Legacy evidence is preserved at C:\Users\TOMMYS~1\AppData\Local\Temp/cleanup-scheduler-migration-xPebw6/legacy-scheduler.json. Supported current remove command owns terminal task cleanup; no normal-profile/runtime installation or other session/task change occurred.

Atomicity assessment before further publication: working candidate measured against actual main1bb1c13 is currently 13 paths, 984 additions and 120 deletions (1,104 total; final regression additions still pending). Rejected a shared-helper-only preparation slice because it would ship a dead API/resource without the mandatory callers. Rejected separate workflow/permission publication because it would instruct or approve a missing runtime route; rejected separate local/reaper publication because it would retain a route that can act without the new repository and remote-completion proof. Keep this one safety-contract cutover with meaningful offline tests. Validation plan remains focused affected cases, actual manifest load, generated/catalog/harness/package invariants, fresh independent frozen review, then exact Windows/Linux CI and causal post-merge regeneration. Capture final measured size at the next committed checkpoint.

R3-R8 focused checkpoint: real manifest validation/inventory and permission-sync suites are green, as are corrected remote-action marker and seven receipt authorization cases. Initial verification failures were fixture setup and a missing math import, repaired before those green results. Required additional regressions for foreign/multiple push destinations, ambient forge overrides, claimant arrival during observation and skipped/mismatched remote completion remain in the same exclusive writer lease; no corrective head has been published or claimed green CI.

Before checkpoint, parent caught process receipt fixtures missing the now-required top-level repository identity. The exclusive writer corrected the fixtures, restored retained-dependency verdict handling ahead of remote-marker validation, and bounded future remote-marker times. Actual process verification then caught a fixture origin-switch ordering error (GitHub identity was selected before the local bare merge push); that fixture order is corrected and only the affected process cases are rerunning. No failing result is counted as green.

Final corrective checkpoint ready: R3-R8 source fixes and boundary regressions passed; ReceiptSafetyTests (3), real reaper process (1,16.000s), and real finish-entrypoint process (1,19.070s) passed. Final catalog/generated refresh/check and package checks passed; harness and payload checks passed. Generated verification output was restored and excluded. Measured authored PR against main1bb1c13: 13 paths, 1047 additions, 125 deletions (1172 total). The existing atomic safety-contract exception remains justified; source/runtime/manifest enforcement cannot be independently landed. All encountered failures are fixed here, owned by the existing sandbox handoff, or covered by existing preflight debt; no new unrelated work is adopted.

Corrective source checkpoint490a810 is integrated with current main a7d91c0 in adc50e3d42a7723887107e9992612662148c006f. One merge-instruction conflict was reconciled by retaining incoming platform-specific python3 commands together with mandatory HEAD/BASE evidence and the explicit saved-identity primary route. Required integrated generation and full manifest inventory passed. Frozen incremental preparation owns da794af..adc50e3; one mechanical publisher is updating existing PR190. AllR3-R8 findings have verified corrective evidence, and the prior completed judgments remain unchanged pending new independent synthesis.

Third immutable review completed at adc50e3 with changes requested. Parent validated native-general/workflow evidence (no findings) and risk-specific security probes; independently reproduced double Git URL rewriting without network or persistent config. Existing R4 is reopened for transport re-expansion; R9 binds receipt repository/primary to the receiving checkout, R10 repeats native-grant target identity after blocking observations, and R11 fixes the null-repository offline action fixture exposed by final strict annotation. One bounded serial source lease will fix these remaining consumers and run their exact regressions. Exact-head CI38135803091 remains owned by monitor23325; no new head is pushed before its terminal state is reconciled.

Remaining corrective verification: the final eight remote-action cases passed (cd39675c4ef96475-remote-action-final2.log, 293.865s). Runtime origin/primary and post-observation grant checks are implemented. A fresh bounded L4 test owner has the sole writer lease for the real chained Git rewrite regression and final grant/finish fixture verification. Previous grant runner attempts had no terminal result and no matching active Python process; neither is accepted as green. Parent retains checkpoint, immutable review, CI, merge and causal publication ownership.

Final local boundary verification: remote action8 passed (293.865s); real command-scoped chained Git rewrite regression1 passed (1.453s); receipt grant13 passed (84.112s); receipt safety3 passed (0.756s); direct cleanup observer process1 passed (10.219s). The scheduled finish process test failed startup observation locally, with its observer process starting63.743s before publishing the startup record. Its attempted timeout fixture change was applied to a different fixture and did not establish configured-timeout behavior; the entire unsuccessful experiment was removed. No further local retry is owned. The underlying Windows process enumeration/scheduler startup code is unchanged by this repair. Exact CI must resolve this platform execution gate; no failure is treated as green. Required final catalog refresh/check, generated refresh/check, harness, tier payload and skill packaging passed. Source is ready for checkpoint, single current-base synchronization, publication and new immutable review.

User steering2026-10-11: use only one or two relevant focused local checks; run the remaining full validation once in CI for each stable candidate. Stop broad/repeated local validation in this repair. Permanent workflow enforcement debt is recorded in docs/workflows/TECH_DEBT.md under Small repairs repeat full validation locally and in CI. Remaining source publication/review/CI/merge/causal cleanup ownership is unchanged.

CI repair 2026-10-11: exact head adc50e3 failed only because two remote-action fixtures did not supply the repository identity now required by the R9 receipt binding. The corrective fixture setup preserves the expected origin identity; current focused checks passed for both former failures, the chained Git rewrite guard, and the new foreign receipt, branch-advance, and worktree-switch denial cases. The source checkpoint remains awaiting commit, a fresh incremental review, and exact-head CI; no prior red result is counted as green.
