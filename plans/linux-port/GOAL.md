# Linux Port Step 10 — Completion

Status: terminal for the authorized Step 10 scope.

## Outcome

Shipped instructions identify platform-specific commands and interpreter requirements across the canonical
agent sources and host adapters. The ported test references and final delivery evidence are recorded here.

## Acceptance evidence

- Audited 248 Markdown files across `.agents/`, `.claude/`, and `.codex/`; updated platform-qualified
  commands in canonical `.agents/` sources and preserved thin host adapters. The retained PowerShell
  test wrapper `tests/delivery-continuation.tests.ps1` delegates to its Python counterpart
  `tests/test_delivery_continuation.py`.
- Source and hook suites passed on source head `3c935462232621801b3dad4c522c31fbc359a8ea`: 1,057 tests
  with 18 skips and 1,048 tests with 4 skips, respectively. Generated-output check found 509 package files
  current. The later commits through the reviewed delivery head changed README and plan documentation only.
- PR [#191](https://github.com/tj-agents/core/pull/191) was approved at reviewed head
  `6faf483a3b9750b6d767ce0efa26e314402b9946` and merged as
  `12d4adedd23ff69ce49940d65c6c476cfe846421`. Its exact-head Windows and Linux CI jobs both passed in
  [run 38097735106](https://github.com/tj-agents/core/actions/runs/38097735106).
- The merge-triggered push run [38098594191](https://github.com/tj-agents/core/actions/runs/38098594191)
  ran `regenerate` successfully. Its log records 509 package files verified, 36 generated files committed
  at `cc227809571d4a49e3f10192c54740f85fc093f2`, and pushed directly after merge commit `12d4adedd23ff69ce49940d65c6c476cfe846421`.

## Separately identified gaps

Windows desktop acceptance, native Claude timer acceptance, installed-host adoption, and the publishing-exemption
administrator dependency remain outside this Step 10 acceptance scope. The approved verify-linux protection
rule remains disabled until its publishing dependency is resolved.

## Completion record

```completion
{
  "outcome": "Step 10 shipped platform-qualified agent instructions, passed exact-head Windows and Linux CI, and published its generated distribution.",
  "acceptance": [
    {
      "id": "platform-instructions",
      "criterion": "The audited instruction corpus identifies platform-specific commands and interpreter requirements, with ported test references recorded.",
      "evidence": [
        {
          "source": "PR #191 reviewed head 6faf483a3b9750b6d767ce0efa26e314402b9946",
          "result": "Reviewed Step 10 instruction and README changes; the 248-file audit and test counterpart evidence are recorded."
        },
        {
          "source": "PR CI run 38097735106",
          "result": "verify-windows and verify-linux completed successfully on the reviewed PR head."
        }
      ],
      "owner": "Step 10 execution owner",
      "next_action": "None; acceptance evidence is complete."
    },
    {
      "id": "generated-publication",
      "criterion": "The merge-triggered generated publication is verified as a causal consequence of PR #191.",
      "evidence": [
        {
          "source": "Push workflow run 38098594191 and regenerate job log 114349616273",
          "result": "The run head was merge commit 12d4adedd23ff69ce49940d65c6c476cfe846421; regenerate succeeded, verified 509 package files, and pushed generated commit cc227809571d4a49e3f10192c54740f85fc093f2 with the merge commit as its sole parent."
        }
      ],
      "owner": "Step 10 execution owner",
      "next_action": "None; publication evidence is complete."
    }
  ],
  "deliveries": [
    {
      "repository": "tj-agents/core",
      "pr": 191,
      "head": "6faf483a3b9750b6d767ce0efa26e314402b9946"
    }
  ],
  "open_tasks": []
}
```
