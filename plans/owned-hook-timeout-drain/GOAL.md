# Drain only the owned command tree when a hook deadline expires

## Outcome and authority

Repair the shared hook subprocess wrapper so `CommandTimeout` is returned only after its owned command tree has been terminated and drained. A real binder trace observed `cmd.exe` surviving binder and hook exit. It does not prove the earlier `WinError 32` lock owner or fix redundant startup before the binding write. The standing standards-defect authorization covers this bounded source repair through review, checks, and ordinary merge. The parent rollout remains active.

Implementation and delivery of this bounded Core source defect are authorized through review, required checks, ordinary merge, and causal generated publication within Core. The source writer may checkpoint stable source locally but does not push or open a PR; the parent owns source publication and merge. No publication outside Core, normal-profile installation, unrelated PR adoption, destructive operation, or check bypass is authorized. The implementation owner changes only the source paths below and this goal.

## Source boundary and dependency

This is a sequential follow-up from freshly published Core main after the primary delivery-binding budget repair. Base: `38550a7258b6819df139300ae340088babc6098f`. Branch: `Fix/OwnedHookTimeoutDrain`.

Own only:

- `.agents/hooks/hook_runtime.py`
- `.agents/hooks/tests/test_hook_runtime.py`
- `.agents/catalog/catalog.json`
- `plans/owned-hook-timeout-drain/GOAL.md`

Existing payload consumers already ship `hook_runtime.py`. Do not add a helper module, manifest entry, schema, daemon, machine profile, or process census. Treat `.agents/workflows/continuation_runtime.py` only as a source reference for the existing Windows Job Object pattern; do not import it or make it a shipped dependency. The catalog companion is limited to package digests for this shared runtime source. Leave generated plugin/host output uncommitted and exclude `plugins/*` from the Source PR. Do not add manifest entries, inventory changes, or permissions. Reassess the complete authored slice before exceeding 1,000 substantive lines; the initial 250–500 changed-line estimate is unmeasured.

## Accepted implementation contract

Use the standard library and keep the shared wrapper compatible with its current callers. On Windows, create the command suspended, assign it to an invocation-owned Job Object configured with kill-on-close, then resume it using the supported process-resume primitive. If ownership setup or assignment fails, never resume the child; terminate and wait for it. Close only this invocation's job and process handles. On timeout, terminate the owned job and establish that its active process count reaches zero before returning `CommandTimeout` within bounded teardown.

On POSIX, start the command in a dedicated session/process group. On timeout, kill that group and drain the owned process and pipes. Never enumerate or terminate unrelated processes.

Start the monotonic deadline before ownership setup and spawn; pass only the remaining execution budget to communication. Preserve the existing 5-second and 10-second command budgets and 15-second outer binding-hook ceiling. Bound teardown within that outer allowance instead of granting a second full command timeout. Document and test the practical limit imposed by noninterruptible platform spawn behavior; do not raise hook deadlines or claim this fixes binder performance.

Preserve successful result, nonzero exit, `check`, input/output bytes and text, `cwd`, `env`, encoding, hidden Windows startup, and caller creation-flag behavior. Cleanup on exceptions must terminate and drain only owned children without masking the original failure.

## Required qualification

Use real ownership-boundary subprocess tests. A ready-handshaked owned grandchild must hold the command pipe or working directory when timeout fires. After `CommandTimeout`, both owned processes must be gone and immediate pipe or directory cleanup must work. Preserve the original timeout reason. Verify assignment failure never resumes the Windows child, POSIX group isolation does not terminate an unrelated process, and ordinary success/nonzero/check/input/output/cwd/env behavior remains intact across repeated invocations. Mocked kill calls alone are insufficient.

Both Windows and Linux CI must exercise their respective ownership branches, including paths with spaces and non-ASCII text. Source fixtures and generated mappings do not prove normal-profile activation.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/hooks/hook_runtime.py::run_command",
  "hosts": [
    {
      "host": "claude",
      "behavior": "The shared run_command wrapper owns and drains only its command tree before reporting a deadline timeout.",
      "source": ".agents/hooks/hook_runtime.py and .agents/hooks/tests/test_hook_runtime.py",
      "mapping": ".agents/plugins/sources.json maps the shared runtime into base and engineering Claude payloads.",
      "verification": {
        "level": "source",
        "result": "limited",
        "evidence": "Captured local Windows runtime 22 with one POSIX-only skip, delivery binding 38, merge review 81 with one skip, catalog 2, harness 14, compilation, and generation check passed. Real Windows regressions prove failed assignment leaves the suspended child unresumed and dead with closed pipes, and zero and delayed positive startup overruns return CommandTimeout after drainage. Linux exact-head CI and normal-profile activation remain pending."
      },
      "exception": {
        "constraint_evidence": "Local source execution covers the Windows ownership branch only; no exact-head Linux execution or installed native-host activation has occurred.",
        "supported_other_host_outcome": "Claude and Codex share this runtime and require the same exact-head Linux CI and native activation evidence; neither normal profile is claimed active."
      }
    },
    {
      "host": "codex",
      "behavior": "The shared run_command wrapper owns and drains only its command tree before reporting a deadline timeout.",
      "source": ".agents/hooks/hook_runtime.py and .agents/hooks/tests/test_hook_runtime.py",
      "mapping": ".agents/plugins/sources.json maps the shared runtime into base and engineering Codex payloads.",
      "verification": {
        "level": "source",
        "result": "limited",
        "evidence": "Captured local Windows runtime 22 with one POSIX-only skip, delivery binding 38, merge review 81 with one skip, catalog 2, harness 14, compilation, and generation check passed. Real Windows regressions prove failed assignment leaves the suspended child unresumed and dead with closed pipes, and zero and delayed positive startup overruns return CommandTimeout after drainage. Linux exact-head CI and normal-profile activation remain pending."
      },
      "exception": {
        "constraint_evidence": "Local source execution covers the Windows ownership branch only; no exact-head Linux execution or installed native-host activation has occurred.",
        "supported_other_host_outcome": "Claude and Codex share this runtime and require the same exact-head Linux CI and native activation evidence; neither normal profile is claimed active."
      }
    }
  ]
}
```

## Next Steps

1. Root checkpoints this promoted Goal from `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-OwnedHookTimeoutDrain`: `git add -- plans/owned-hook-timeout-drain/GOAL.md` followed by `git commit -m "Plan owned hook timeout drainage"`. Verify the branch, commit, and clean tracked state before dispatch.
2. Root assigns one fresh bounded L4 implementation owner. The owner first reads this Goal and current Core hook/runtime rules, then edits only the three owned paths listed above.
3. The L4 owner implements the real ownership-boundary tests, runs focused wrapper and affected-consumer tests plus generation, catalog, and harness checks, records actual Windows/Linux coverage, and measures the full authored change before the 1,000-line boundary. Commit the stable source and Goal locally; release to Root without pushing or opening a PR.
4. Root freezes and reviews that commit, runs required independent ownership/security scrutiny, opens and monitors the exact-head PR, waits for Windows/Linux CI, merges normally, verifies causal generated publication, and safely retires only this checkout.

## Execution and completion

Current slice: `run_command` now starts POSIX commands in an invocation-owned session and Windows commands suspended in an invocation-owned kill-on-close Job Object. Timeout cleanup terminates and drains the owned tree before raising `CommandTimeout`. A failed Windows Job assignment directly terminates, waits for, and drains the still-suspended unassigned child within the same teardown budget, then preserves the assignment error. The startup remaining-budget check shares the `CommandTimeout` conversion and drains once. The regression suite uses a handshaked grandchild that keeps both a pipe and working directory open, verifies immediate directory release after timeout on this Windows checkout, and preserves ordinary text and bytes input/output, nonzero, check, cwd, env, and repeated-command behavior.

Observed verification: captured Windows-local `python -B .agents/hooks/tests/test_hook_runtime.py` passed 22 tests with one POSIX-only skip on 2026-10-12. The three added real Windows cases prove that failed Job assignment leaves the child unresumed, terminates the actual child, and closes its pipes; that zero startup budget returns `CommandTimeout` after drainage; and that a 0.05-second budget with a controlled 0.15-second `Popen` delay returns `CommandTimeout` after drainage. Captured `python -B .agents/hooks/tests/test_delivery_binding_gate.py` passed 38 tests, `python -B .agents/hooks/tests/test_merge_review_gate.py` passed 81 tests with one skip, `python -B tests/test_catalog_digests.py` passed 2 tests, and `python -B tests/test_harness_manifests.py` passed 14 tests. Captured `python -B -m py_compile .agents/hooks/hook_runtime.py .agents/hooks/tests/test_hook_runtime.py`, `python -B scripts/update_catalog_digests.py`, `pwsh .agents/sync-generated.ps1`, and `pwsh .agents/sync-generated.ps1 -Check` passed. The authored catalog companion changes only the base and engineering package digests for this shared hook source; generated package output remains uncommitted. Windows local source proof is current; exact-head Linux CI and native Claude/Codex activation remain pending before delivery can claim both-host qualification.

The parent owns frozen independent review, any required security/ownership scrutiny, exact-head Windows and Linux CI, ordinary merge, causal generated publication, and safe cleanup. No `--admin`, check bypass, installation, or unrelated PR adoption is authorized.

Done when unchanged deadlines terminate and drain only the invocation's owned process tree; real regression tests prove immediate cleanup with no child surviving; both platform branches pass source review and exact-head CI; ordinary merge and causal generated publication complete; and this source checkout is safely retired without claiming normal-profile acceptance.

A merge, open PR, or started CI alone does not complete this slice. Record observed evidence and any genuine external gate, resolver, and resume condition here before transferring ownership.
