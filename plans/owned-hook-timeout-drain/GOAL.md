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
      "source": ".agents/hooks/hook_runtime.py",
      "mapping": "The canonical shared hook runtime is included in the Claude base package payload.",
      "verification": {
        "level": "planned",
        "result": "pending",
        "evidence": "Implementation and Windows/Linux CI have not run."
      }
    },
    {
      "host": "codex",
      "behavior": "The shared run_command wrapper owns and drains only its command tree before reporting a deadline timeout.",
      "source": ".agents/hooks/hook_runtime.py",
      "mapping": "The canonical shared hook runtime is included in the Codex base package payload.",
      "verification": {
        "level": "planned",
        "result": "pending",
        "evidence": "Implementation and Windows/Linux CI have not run."
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

Current slice: `run_command` now starts POSIX commands in an invocation-owned session and Windows commands suspended in an invocation-owned kill-on-close Job Object. Timeout cleanup terminates and drains the owned tree before raising `CommandTimeout`; setup failures do not resume an unassigned Windows child. The regression suite uses a handshaked grandchild that keeps both a pipe and working directory open, verifies immediate directory release after timeout on this Windows checkout, and preserves ordinary text and bytes input/output, nonzero, check, cwd, env, and repeated-command behavior.

Observed verification: `python .agents/hooks/tests/test_hook_runtime.py` passed 20 tests with one POSIX-only skip on 2026-10-11. `python .agents/hooks/tests/test_delivery_binding_gate.py` passed 38 tests, and `python .agents/hooks/tests/test_merge_review_gate.py` passed 81 tests with one skip. `python -m py_compile .agents/hooks/hook_runtime.py .agents/hooks/tests/test_hook_runtime.py` and `git diff --check` passed. `python -B scripts/update_catalog_digests.py`, `pwsh .agents/sync-generated.ps1`, `pwsh .agents/sync-generated.ps1 -Check`, and `python tests/test_harness_manifests.py` passed. The authored catalog companion changes only the base and engineering package digests for this shared hook source; its CRLF-only generator rewrite was normalized back to repository LF. Generated package output remains uncommitted. The full authored slice measures 435 additions and 17 deletions from the recorded base, below the 1,000-line reassessment boundary. Windows and Linux CI remain required before delivery can claim both-host qualification.

The parent owns frozen independent review, any required security/ownership scrutiny, exact-head Windows and Linux CI, ordinary merge, causal generated publication, and safe cleanup. No `--admin`, check bypass, installation, or unrelated PR adoption is authorized.

Done when unchanged deadlines terminate and drain only the invocation's owned process tree; real regression tests prove immediate cleanup with no child surviving; both platform branches pass source review and exact-head CI; ordinary merge and causal generated publication complete; and this source checkout is safely retired without claiming normal-profile acceptance.

A merge, open PR, or started CI alone does not complete this slice. Record observed evidence and any genuine external gate, resolver, and resume condition here before transferring ownership.
