# Code review â€” Fix/CLIRefreshTimeouts

**Review status:** `complete`
**Judgment:** `approved`
**Reviewed up to commit:** `3a54ecdde172a6e254c80f352dc25713851deb04`  `(2026-10-06)`
**Security-reviewed up to commit:** `bee4ce56f6db1cf60286e7f64602230be89a631b`  `(2026-10-06)`

## Review pass â€” 2026-10-03 â€” full

**Candidate base:** `06480cfbdf376fac825e4b0581f3b4b6a8e0f5a2`
**Candidate head:** `fc0d4d52af1fdba3e844675b18569229813590eb`
**Candidate branch:** `Fix/CLIRefreshTimeouts`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:85d61bda26043548066f4bd3fa397c51fb1e3e3124dc6f779fae2d892d787bfe` `(26 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\cli-refresh-timeouts\review\b25ae8b488f507bae6007ad013d470aad3c5799b9d0cd9c8eac2a9f19215b193`
**Candidate bundle identity:** `sha256:dff3b4ed1297f2a7fe4e595809dc0a7b0604a6483dc90ca10bf195565614ceed`
**Work-order path:** `reviews/Fix-CLIRefreshTimeouts.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

Native layer: Codex CLI `review --base 06480cfbdf376fac825e4b0581f3b4b6a8e0f5a2` at the frozen head, read-only.
Specialist lenses: security and workflow. Pre-review synchronization found zero missing base commits.

### Findings

- [x] **R1 - MEDIUM - native-general** - `.agents/machine/scripts/codex_marketplace_sync.ps1:9`
  Machine-plugin upgrades can remove the runner needed by subsequent refresh commands. Snapshot the runner before installing plugins.
- [x] **R2 - MEDIUM - native-general** - `.agents/machine/scripts/bounded_process.py:99`
  Default Windows pipe encodings can reject or corrupt non-ASCII command output. Coordinate explicit UTF-8 between the runner and PowerShell.

Native Codex review completed with two actionable findings. Security and workflow specialist dispatches were unavailable (HTTP 400: unsupported model); the parent completed those bounded lenses on the frozen bundle with no additional findings. Tier convention resolution selected no stack tier. No route violations.


R1 and R2 resolved by `1a7e6802da850adb216e195f61c7332ee0adb5dd`; regressions pass in both PowerShell editions and under cp1252 pipe encoding.

## Review pass - 2026-10-03 - incremental

**Candidate base:** `fc0d4d52af1fdba3e844675b18569229813590eb`
**Candidate head:** `1a7e6802da850adb216e195f61c7332ee0adb5dd`
**Candidate branch:** `Fix/CLIRefreshTimeouts`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:89a6f76a0f015567926c7fd493795cd1e0e171b79d8527d6e883479a328a62fe` `(11 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\cli-refresh-timeouts-incremental\review\f13d16c2fada027303b503187b22ba09a433fe41cab6cb47adfe06e3fca1561d`
**Candidate bundle identity:** `sha256:c49e6eef5ca56f63fdf14250feb508e8c0109a97ff12ba5999a1960911430125`
**Work-order path:** `reviews/Fix-CLIRefreshTimeouts.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

### Findings

Native incremental review timed out at 240 seconds; its process job was stopped. Per the review workflow's unavailable/timeout recovery, the parent completed native-general and workflow checks over the identical frozen descriptor and bundle. Explicit UTF-8 forwarding, caller encoding restoration, runner snapshot lifetime/cleanup and the in-memory startup gate were checked against the new regression assertions. No additional findings.

Final review: both original findings are resolved. Incremental pass has no new findings; native timeout fallback is recorded above. Original full-pass changes-requested judgment and frozen identity remain unchanged.

## Review pass - 2026-10-06 - incremental (port to current main)

**Candidate base:** `1a7e6802da850adb216e195f61c7332ee0adb5dd`
**Candidate head:** `4fd75dc22595ac6241b611034078faf20e258580`
**Candidate branch:** `Fix/CLIRefreshTimeouts`
**Candidate scope:** this branch's paths against origin/main 3cd0ecc; in range: agent-cli.ps1, claude_standards_sync.py, codex_marketplace_sync.ps1, launch-codex.ps1, .claude/settings.json, ci.yml, README.md, codex-marketplace-sync/terminal-profile tests, test_claude_standards_sync.py, test_repository_permissions.py (the rest is main's content arriving through merges 3e2bb15 and 4fd75dc)
**Candidate path-set:** `sha256:a6f180de20bd7839ae89acf234c3e8fcfd9d0afb23e2382e86b500566471ab01` `(337 paths, unscoped range)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\backlog-pr81-incremental\review\34c219acf13f690d4b0768ab1de476b86c598946ed45eef0836128acc24f4702`
**Candidate bundle identity:** `sha256:911d82e861cc484e505f5a02694749d1cde6b10237cab2009ed58d937a1b6885`
**Work-order path:** `reviews/Fix-CLIRefreshTimeouts.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

- [x] **R3 - MEDIUM - native-general, security** - `.agents/machine/scripts/codex_marketplace_sync.ps1:45`
  The hook-trust step runs `codex_hook_trust.py` directly, outside the shared `$TimeoutSeconds` deadline and the `bounded_process.py` process-tree kill every other refresh step uses, so a stuck trust handshake can hold a launch past the announced maximum. Route it through the runner snapshot with the remaining budget.
- [x] **R4 - LOW - security** - `.agents/machine/scripts/codex_marketplace_sync.ps1:99`
  The trust-snapshot removal in `finally` is the only cleanup without `-ErrorAction SilentlyContinue`; a locked temp file throws there and masks the original sync failure reported by the caller.

Native layer: Claude Code `code-review` (medium) over `1a7e680..4fd75dc` scoped to this branch's in-range paths; security lens over settings, CI workflow, both sync scripts and both launcher scripts. Two further native findings in `claude_standards_sync.py` (`external_groups` drops an owner marketplace whose installs all moved to other repositories, so its checkout is never refreshed; a git-subdir `sha` pin is ignored in favour of `ref`) sit in main's `339bc9c` code, which this branch does not change; they are routed to the standards-defect side workstream rather than this PR. Security checks of settings entries, CI expressions, snapshot naming and launcher argument quoting found nothing further.

## Review pass - 2026-10-06 - incremental (R3/R4 fixes)

**Candidate base:** `4fd75dc22595ac6241b611034078faf20e258580`
**Candidate head:** `fca059d117d561965137555fc93d89ec548465a5`
**Candidate branch:** `Fix/CLIRefreshTimeouts`
**Candidate scope:** all (3 paths: codex_marketplace_sync.ps1, codex-marketplace-sync and codex-sync-timeout tests)
**Candidate path-set:** `sha256:936575d7ce86592c0388f1aa4f6d00133bef107ca2e7b0b9448003cb9a6a8693` `(3 paths, unscoped range)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\backlog-pr81-fix\review\653dbd728d31640c6b7b4ffc05ffb3dc5f9088c2d50a2b69435a77961a183688`
**Candidate bundle identity:** `sha256:03c698a1d0aa1804279232ba0565a7a2a51d55739495867754d93688bc42eab1`
**Work-order path:** `reviews/Fix-CLIRefreshTimeouts.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

- [x] **R5 - LOW - native-general, security** - `tests/codex-sync-timeout.tests.ps1:45`
  The hung hook-trust regression accepts any error containing `trust` or `timed out`, so it also passes when an earlier step exhausts the shared budget or a raw runner stderr line surfaces instead of the trust failure; it does not prove the trust step itself is stopped on time.
- [x] **R6 - MEDIUM - security** - `.agents/machine/scripts/codex_marketplace_sync.ps1:52`
  Under Windows PowerShell 5.1 with the caller's `$ErrorActionPreference = 'Stop'` (launch-codex.ps1, both test suites), `2>&1` capture throws on the first stderr line before the exit code is read (confirmed: `RemoteException` on 5.1, normal capture on pwsh 7). `bounded_process.py` forwards child stderr even on success, so in `Invoke-CodexHookTrust` and the PR's `Invoke-CodexSyncCommand` any Codex CLI stderr line turns a successful refresh into a failure, and on failure replaces the intended `Codex could not trust tj-agents hooks: ...` / `Codex plugin sync failed: ...` message.
- [x] **R7 - LOW - security** - `tests/codex-sync-timeout.tests.ps1:49`
  The R4 check greps the script source for a literal line; it pins formatting and proves nothing about the masking behavior R4 fixed.

Native layer: Claude Code `code-review` (medium) over `4fd75dc..fca059d`; security lens over the same frozen bundle. R3 verified fixed (trust step runs under the runner with the remaining budget; a non-positive budget short-circuits to exit 124; helper children die with the job object). R4 verified fixed. Production callers do not pass the new `-HookTrustHelperScript` parameter; argument passing is array-based with no quoting regression.

## Review pass - 2026-10-06 - incremental (R5-R7 fixes)

**Candidate base:** `fca059d117d561965137555fc93d89ec548465a5`
**Candidate head:** `bee4ce56f6db1cf60286e7f64602230be89a631b`
**Candidate branch:** `Fix/CLIRefreshTimeouts`
**Candidate scope:** all (2 paths: codex_marketplace_sync.ps1, codex-sync-timeout tests)
**Candidate path-set:** `sha256:5147c42437eee84cfad76bbcf3208df68ecf9ce4092176b73a45ed836be4002c` `(2 paths, unscoped range)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\backlog-pr81-fix2\review\53438b247571a6b818b6a092512873cdfa78590b9e49c796b37b3f8027fe7fff`
**Candidate bundle identity:** `sha256:377ba8f2f24ca0b4f7cd8a55d87b6a90451ebcb27bc7b4cd83690facdbbbd6df`
**Work-order path:** `reviews/Fix-CLIRefreshTimeouts.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

- [x] **R8 - LOW - native-general** - `tests/codex-sync-timeout.tests.ps1:84`
  The `Remove-Item` stand-in for the locked-cleanup case never deletes, so `Sync-CodexStandards`' `finally` removes nothing during that test and each run leaves the runner snapshot and the trust-helper copy in the system temp folder.

Native layer: Claude Code `code-review` (medium) over `fca059d..bee4ce5`; security lens over the same frozen bundle found no defects. R6 verified fixed on both hosts: function-local `Continue` around the native call, the caller's preference untouched, nonzero exit still throws with runner timeout/OSError text, JSON parsed from stdout only. R5 now requires the trust-specific timeout with 40s budget / 70s hang / 55s bound. R7 replaced with a behavioral masking test.

## Review pass - 2026-10-06 - incremental (R8 fix)

**Candidate base:** `bee4ce56f6db1cf60286e7f64602230be89a631b`
**Candidate head:** `3a54ecdde172a6e254c80f352dc25713851deb04`
**Candidate branch:** `Fix/CLIRefreshTimeouts`
**Candidate scope:** all (1 path: codex-sync-timeout tests)
**Candidate path-set:** `sha256:7a8b1274eaede3e74243eab13220883fa6e28a785ed6484df4e5e34bcf7ad653` `(1 paths, unscoped range)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\backlog-pr81-fix3\review\474c92f110f20af3436447f374b1114ea665111f8773bb0009e5960661996b4e`
**Candidate bundle identity:** `sha256:db1aaad89dc1d61dbf7de95e014ff8ecf60ce33bfb1e282ae991ef3fe445aefb`
**Work-order path:** `reviews/Fix-CLIRefreshTimeouts.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Native layer: Claude Code `code-review` (medium) over `bee4ce5..3a54ecd` (one test line). No new findings. R8 fixed in 3a54ecd: the stand-in passes every cleanup through to the real cmdlet by module-qualified name and still raises the simulated lock on the trust-snapshot call. Runner snapshots in the system temp folder stayed at 8 across a pwsh and a Windows PowerShell 5.1 run of the suite (both passed). No security-sensitive path in range; the security marker stays at bee4ce5, the last commit a security lens covered (passes 1a7e680..4fd75dc, 4fd75dc..fca059d, fca059d..bee4ce5).
