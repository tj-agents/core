# Diagnose sandbox setup read failure

## Authority

Tommy explicitly requested a separate handoff on 2026-10-10 to determine why sandboxed reads of a known text file and repository skill files are recorded as `exit -1` before the requested command runs.

Checkout: `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-SandboxSetupReadFailure`
Branch: `Fix/SandboxSetupReadFailure`
Investigation lane: L3, because the execution-host failure source was unresolved. Resolved from the
installed engineering package's `.agents/lanes/codex.json`: `gpt-6.1-sol`, high reasoning effort.

## Outcome

Restore ordinary sandboxed execution while preserving sandbox settings, ACLs, hook trust and live peers, or reach a concrete external installation gate with the exact official fixed candidate and verification prepared. The renewed request owns repair completion; the previous diagnosis alone is not recovery.

## Scope

Investigate the Codex execution environment's setup-refresh/helper path, including available hook output and reproducible command evidence. Make no repository-product changes unless evidence shows a core-owned source defect. Do not bypass hook trust or weaken sandboxing.

## Next Steps

Completed on 2026-10-11 by fixed-runtime successor `01a12aec-7f71-7c73-aeaf-5fca3d754103`. Both original reads exited 0 through ordinary sandboxed `exec_command`, and their setup refreshes used the fixed helper with `errors=[]`. Verification is recorded below. Finish the local goal checkpoint and report both outcomes to Tommy. No further repair, installation, sibling-checkout writes or publication is required by this machine recovery task.

## Status and next use

Completed on 2026-10-11: the approved isolated runtime installation, fresh-host acceptance and fixed-runtime successor verification passed. The original text-file and canonical skill-file reads were separately executed through the actual sandboxed command runner with exit code 0. Their matching setup refreshes used the installed fixed helper and completed with errors=[].

Existing sessions still use their original runtime. Reopen with the installed executable and invocation-local compatibility catalog shown below to use the repair. Global npm/PATH selection was not changed.

## Cause and owner

Codex CLI 0.162.0's Windows sandbox setup attempts to open a running computer-use runtime executable
with `MAXIMUM_ALLOWED` during a root-only ACL repair. Windows rejects that access with
`ERROR_SHARING_VIOLATION` (32). Setup exits with status 1 before the requested PowerShell process starts;
the host reports `helper_unknown_error: setup refresh had errors`. A recorded `exit -1` is therefore a
process-launch failure, not a `Get-Content` exit status.

The failing binary is OpenAI's `codex-windows-sandbox-setup.exe`, shipped with the installed npm
`@openai/codex` runtime. The source owner is `openai/codex`, specifically
`codex-rs/windows-sandbox-rs/src/acl.rs`, function `ensure_allow_mask_aces_with_inheritance_impl`.
No core source defect was established. The existing machine debt entry
[A locked Codex runtime executable can disable every sandboxed command](../../.agents/machine/TECH_DEBT.md#a-locked-codex-runtime-executable-can-disable-every-sandboxed-command)
already owns the local dependency on host recovery support.

## Local evidence

- Native executable `C:/nvm4w/nodejs/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe --version`
  returned `codex-cli 0.162.0`; the npm package manifest also reports `0.162.0`.
- Sandboxed `Get-Content -LiteralPath '.agents/continuation/sandbox-setup-read-failure-prompt.txt'`
  failed before process creation. The same command with scoped `require_escalated` execution exited 0.
- A second sandboxed reproduction,
  `Get-Content -Raw -LiteralPath 'plans/sandbox-setup-read-failure/GOAL.md'`, failed at the same
  process-creation gate. Its elevated equivalent exited 0 and returned the goal contents.
- `C:/Users/TommySeery/.codex/.sandbox/setup_error.json` contains
  `{"code":"helper_unknown_error","message":"setup refresh had errors"}`.
- `C:/Users/TommySeery/.codex/.sandbox/sandbox.2026-10-10.log` records the prompt-read attempt at
  16:09:44 local / 15:09:44 UTC, setup spawning at 16:09:44.736, the runtime failure at
  15:09:45.020205700 UTC, and helper exit status 1 at 16:09:45.935 local.
- The exact fatal message names
  `C:/Users/TommySeery/AppData/Local/OpenAI/Codex/runtimes/cua_node/426e88130fe66c7e/bin/node_repl.exe`:
  `runtime read/execute validation failed ... open ACL target for root-only update ... (os error 32)`.
  The earlier user-profile read-attributes warning explicitly continues setup; the runtime validation
  failure is the error that causes the helper to exit. Read-ACL-only work completes separately.
- A process snapshot found 29 `node_repl.exe` processes executing that exact runtime path. Their
  immediate parents were `codex.exe` processes from installed OpenAI runtimes. This identifies an active
  shared runtime, not one orphan process that can safely be terminated without affecting other sessions.
- A non-mutating `CreateFileW` probe on that executable used `OPEN_EXISTING`,
  `FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE`, and `FILE_FLAG_BACKUP_SEMANTICS`.
  `MAXIMUM_ALLOWED` failed with error 32; `READ_CONTROL | WRITE_DAC` succeeded. Every successful
  handle was closed. No ACL or file content was changed. A separate probe also found read access
  succeeds and generic read/write access fails with error 32.
- Available SessionStart hook output delivered the standards normally. The fatal log path is in the
  execution host's setup helper, not in a core or installed-plugin hook.

## Upstream repair and release boundary

[OpenAI PR #51822](https://github.com/openai/codex/pull/51822) merged on 2026-10-07. It restricts
`MAXIMUM_ALLOWED` opens to directories and requests `READ_CONTROL | WRITE_DAC` for files only when
repair is needed, preserving sandbox permissions and denials. Its Windows regression test keeps the
runtime executable open during repair and revalidation.

Source inspection on 2026-10-10 confirms the defective unconditional root-only open in
[0.162.0](https://github.com/openai/codex/blob/rust-v0.162.0/codex-rs/windows-sandbox-rs/src/acl.rs#L528)
and [0.162.1](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/windows-sandbox-rs/src/acl.rs#L528).
The directory check exists in
[0.163.0-alpha.1](https://github.com/openai/codex/blob/rust-v0.163.0-alpha.1/codex-rs/windows-sandbox-rs/src/acl.rs#L530).
These are content checks; a higher version or newer release date alone does not prove inclusion.

## Recovery boundary

Tommy approved the isolated official candidate installation with "yeah go?" on 2026-10-11. Installation and actual fresh-host acceptance are complete. No installation approval remains pending. Existing hosts cannot hot-swap their running binary; their next session must explicitly select the installed runtime.

No sandbox settings, ACL policy, hook trust or existing runtime binaries were manually changed. No peer process was terminated by this repair.

## Renewed ownership and progress

Tommy explicitly renewed this same repair through `sandbox-repair-followup-prompt.txt` on 2026-10-10. Peer registry verification finds prior session `01a1265c-a31b-7431-a8b3-aa47101ff0c9` not live and current repair session `01a127ec-ae44-7353-95d7-436f4fccfd74` live in this checkout. The parent remains sole writer of `Fix-DependentPrBranchCleanup`; this task neither edits that checkout nor adopts its goal.

Phase: L3 diagnosis and recovery preparation, using the canonical Codex lane resolution already recorded above. The existing investigation goal remains the progress owner.

- Ordinary `exec_command` still fails before PowerShell creation with `helper_unknown_error: setup refresh had errors`. Node REPL filesystem reads and native processes remain usable under their existing controls.
- A scoped elevated diagnostic was approved and exited 0; there was no automatic approval rejection. It confirms the active npm package and native executable still report `0.162.0`.
- The current host PID is `53192`, using the npm runtime. The matching setup logs name its `codex-resources/codex-windows-sandbox-setup.exe` and the locked shared `node_repl.exe`.
- The repository runtime resolver, run in the normal machine environment, selects `0.162.0`. Node REPL children intentionally lack `LOCALAPPDATA` and the Codex/npm PATH entries, so their empty candidate inventory does not establish a launcher defect.
- The desktop runtime checked directly reports `0.151.0-alpha.7.1`; it is below the launcher minimum and is not a verified fixed alternative.
- Official npm `latest` remains `0.162.1`. Direct source checks still find the unconditional file `MAXIMUM_ALLOWED` open there, and the directory-only guard in official `0.163.0-alpha.1`.

The installed candidate inventory is complete: npm `0.162.0`, desktop `0.148.0-alpha.21`, and desktop `0.151.0-alpha.7.1`. Both desktop candidates fall below the launcher minimum `0.154.0`. The same resolver implementation on current `origin/main` ranks these candidates by semantic version. No eligible installed fixed runtime exists; no causal core-owned launcher selection or recovery defect was established, so no runtime source or regression-test change was made. The existing machine debt entry continues to own future launcher health recovery.

## Prepared official candidate

- Release: [OpenAI Codex 0.163.0-alpha.1](https://github.com/openai/codex/releases/tag/rust-v0.163.0-alpha.1), a prerelease rather than stable.
- Platform package: `@openai/codex@0.163.0-alpha.1-win32-x64`, selected by the official top-level `@openai/codex@0.163.0-alpha.1` manifest.
- Archive: `C:/Users/TOMMYS~1/AppData/Local/Temp/codex-sandbox-repair-sG4Nyj/codex-0.163.0-alpha.1-win32-x64.tgz`. All 47 regular-file/directory entries were staged before approval; the vendor runtime is now installed at the approved isolated path, without changing PATH.
- Archive SHA-256: `59486e550eba4ffe7bcaed01e5925c97fba59345a590896b884a72c85b9b62ac`.
- Registry SHA-512 integrity matched, and both npm registry ECDSA signatures verified against the registry key `SHA256:DhQ8wR5APBvFHLF/+Tc+AYvPOdTpcIDqOhxsBHRwC7U`.
- The published SLSA subject digest matches the same package bytes. Its DSSE signature verifies with the bundled certificate naming OpenAI's `rust-release.yml` workflow and `rust-v0.163.0-alpha.1` tag. Independent Sigstore certificate-chain/transparency-log verification was not performed; this is not claimed as complete Sigstore verification.
- Source commit: `cb36b210bcb28dba454289d9b1789351e40821fa`. The [immutable ACL source](https://raw.githubusercontent.com/openai/codex/cb36b210bcb28dba454289d9b1789351e40821fa/codex-rs/windows-sandbox-rs/src/acl.rs) contains both the directory-only `MAXIMUM_ALLOWED` guard and file-specific `READ_CONTROL | WRITE_DAC`. Source SHA-256: `2b4685cb4a3ed79e124c113b5ded7c4fcc6fd5456c7e44a73df145d0fd25c666`.
- Staged native CLI `--version` exited 0 with `codex-cli 0.163.0-alpha.1`, using an isolated temporary `CODEX_HOME` solely for that version probe.
- Native CLI SHA-256: `3ac95e7bbb5f51d9fcda76d013a04e22456bd67eafde88eb04feafd71590933f`. Setup helper SHA-256: `2e9d81d128494f8499d6de27cca354aa94dcd1a17314ed35f29c79c6ecd78932`.
- Full verification record: `C:/Users/TOMMYS~1/AppData/Local/Temp/codex-sandbox-repair-sG4Nyj/verification.json`. Downloaded runtime payloads and machine-specific verification state remain outside Git.

## Approved machine action and recovery verification

The installation approval gate was resolved by Tommy's "yeah go?" on 2026-10-11.

The approved proposal selected a side-by-side installation at `C:/Users/TommySeery/.local/share/codex/runtimes/0.163.0-alpha.1`; that path was absent before installation. Approval permits copying the complete authenticated vendor runtime there and using its native `bin/codex.exe` for a fresh repair verification session. The global npm runtime, desktop caches, existing PATH, sandbox configuration, ACL policy, hook trust and live peer processes remain preserved. Do not overwrite an unexpectedly existing target.

After approval, recheck archive/binary integrity, install the complete vendor payload at that exact path, verify `--version`, and select it for this repair using an invocation-scoped PATH and launcher minimum `0.163.0-alpha.1`. Perform any actual session transfer through the installed `engineering:handoff` workflow, with verified pickup and one writer; do not infer success from launcher submission. Preserve normal hook trust; do not use bypass or sandbox-disabling flags.

Acceptance requires a fresh fixed-runtime host to run ordinary `exec_command` with:

```powershell
Get-Content -Raw -LiteralPath 'plans/sandbox-setup-read-failure/GOAL.md'
```

It must exit 0 while the shared `node_repl.exe` processes remain active. Capture the matching setup-refresh log showing the fixed helper path and `errors=[]`, and verify that the parent and other peer sessions remain live. A standalone `codex sandbox` probe can provide supplementary evidence but does not replace success through the actual host command runner.

Approval, installation and fresh-host acceptance are complete under the existing sandbox settings.

The current foreground session remains sole writer. No unattended writer or wake has been registered. Recovery acceptance passed with observed ordinary command-runner success.


## Approved installation progress (2026-10-11)

Authority: Tommy's "yeah go?" approves the previously proposed side-by-side alpha installation and recovery test. This revokes the pending installation gate for the named candidate and path; it does not authorize replacing the global runtime, modifying desktop caches, changing global PATH, disabling sandboxing or bypassing hook trust.

Lane selection: installation is L5 (the archive, target and copy operation are already specified), performed as a small inline follow-up; recovery verification is L3 (actual host acceptance remains unresolved). Canonical lane resolution is unchanged. No in-session model switch is claimed.

The first ordinary shell read on resumption failed before process creation. The staged archive was rechecked and installed at the approved path; Git confirmed the same checkout and branch.

Installation evidence: `C:/Users/TOMMYS~1/AppData/Local/Temp/codex-sandbox-repair-sG4Nyj/installation.json` records 45 vendor files installed at the approved exact path and verified byte-for-byte against the authenticated archive. The installed native binary `--version` returned `codex-cli 0.163.0-alpha.1` with exit 0. No existing runtime or global PATH was replaced.

The optional standalone `codex sandbox --cd ...` probe exited 2 before executing a command because this build requires an explicit permission profile or sandbox-state JSON; the saved user configuration uses legacy `sandbox_mode="workspace-write"`. No profile was invented and no sandbox control changed. The recovery test therefore proceeds through a fresh actual `codex exec` host using the unchanged saved configuration. The fresh child is read-only; it has no goal or repository writer ownership.

The first fresh fixed-runtime host started thread `01a12aa2-8990-73b0-97be-825c103620b1` but exited 1 before any tool execution: the Responses backend rejected `input[1].internal_chat_message_metadata_passthrough.content_item_metadata` (HTTP 400). No sandbox acceptance is claimed from that launch. Startup also logged upstream system-skill directory sharing/access errors; no local directory, ACL or trust was manually altered to address them.

Recovery diagnosis remains L3. Immutable upstream `client.rs` strips content-item metadata when `ModelInfo.use_responses_lite` is false. This account's selected model cache advertises it as true. Upstream exposes `model_catalog_json` as an authoritative process-local catalog using `StaticModelsManager`; it preserves auth filtering. A supported invocation-scoped catalog at `C:/Users/TOMMYS~1/AppData/Local/Temp/codex-sandbox-repair-sG4Nyj/responses-compatible-models.json` copies the existing catalog and changes only the selected model's `use_responses_lite` to false for ordinary Responses compatibility. Sandbox, approval, node tool review metadata, hooks, TLS, auth and global configuration are unchanged. The focused retest uses that official override and preserves original failed-launch evidence.

## Completed recovery acceptance (2026-10-11)

Fresh fixed-runtime thread `01a12aa5-e595-7542-934c-bad2fc45f33e` ran ordinary sandboxed PowerShell `Get-Content -Raw -LiteralPath 'plans/sandbox-setup-read-failure/GOAL.md'` with exit code 0. The native host also exited 0. The matching sandbox log records the installed `0.163.0-alpha.1/codex-resources/codex-windows-sandbox-setup.exe` and `setup refresh: processed 2 write roots (read roots delegated); errors=[]` at 2026-10-11T11:08:23.527575100 UTC.

The parent dependent-cleanup session and this repair session remained live; 20 pre-existing shared node runtime processes remained active. No process termination or restart was issued by the repair. Other peers can change independently, so unchanged status for every peer is not claimed.

The invocation-local compatibility catalog is saved at `C:/Users/TommySeery/.local/share/codex/runtimes/0.163.0-alpha.1/responses-compatible-models.json`. It changes only the selected model's Responses compatibility flag. Persistent verification, installation, acceptance summary and successful setup excerpt are in that runtime's `repair-evidence/` directory. The alpha's initial API-metadata failure was resolved for the tested invocation; global configuration remains unchanged.

From this checkout, open the fixed runtime with:

```powershell
$codexLane = (Get-Content -Raw -LiteralPath '.agents/lanes/codex.json' | ConvertFrom-Json).lanes.L3
& 'C:\Users\TommySeery\.local\share\codex\runtimes\0.163.0-alpha.1\bin\codex.exe' --model $codexLane.model --config ('model_reasoning_effort=' + $codexLane.reasoning_effort) --config 'model_catalog_json="C:/Users/TommySeery/.local/share/codex/runtimes/0.163.0-alpha.1/responses-compatible-models.json"' --cd 'C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-SandboxSetupReadFailure'
```

No core runtime source defect was established and no core code change was required. The approved installation and verification scope is complete. The originating repository session retains its own work and writer ownership.

## Historical session reopening blocker (2026-10-11; resolved)

The packaged launcher exited 1 before tab submission: marketplace refresh could not back up engineering@base-agents because Windows returned Access is denied (os error 5). No successor was submitted by that failed attempt. The predecessor retained this repair goal and writer ownership until the successful normal-preflight transfer below.

Automatic approval review rejected a proposed direct-native fallback because it would skip the failed packaged plugin-refresh and hook-trust preflight and that bypass was not specifically authorized. No alternate launch is permitted while that rejection stands. A direct-launch approval request was pending while the normal refresh failure was investigated. Normal preflight recovery subsequently resolved the launch gate; this verification used the normal launcher and required no direct-launch exception.

Blocked action: open a fixed-runtime successor through the normal launcher.
Resolver: plugin-cache recovery under existing safeguards, or Tommy explicitly authorizing the described direct launch.
Unblock action: successful normal preflight, or explicit direct-launch approval accepted by automatic review.
Resume condition: one native fixed-runtime tab is submitted, then its goal acknowledgement and both original file-type read results are observed.

## Normal preflight recovery

The full official `plugin marketplace upgrade --json` through the existing stable 0.162.0 native management CLI exited 0 with errors=[] and refreshed base-agents. No cache, ACL, hook or plugin configuration was manually bypassed. The prior packaged launcher attempt definitively failed before tab submission, so a single new attempt through the normal packaged launcher is authorized after this observed prerequisite recovery. The direct-native fallback remains unexecuted; no bypass of automatic review is used. Predecessor stops owned-path writes at packaged launcher invocation and observes pickup read-only.

## Fixed-runtime successor pickup (2026-10-11)

Session `01a12aec-7f71-7c73-aeaf-5fca3d754103` acknowledges the transfer through `fixed-runtime-handoff.txt` from this exact checkout and branch `Fix/SandboxSetupReadFailure`. The command runner reports `CODEX_VERSION=0.163.0-alpha.1`; ordinary sandboxed reads of the handoff and this goal exited 0. This successor became the sole writer of this goal. The sibling dependent-cleanup goal remains with its original owner.

Phase: L3 recovery verification, because actual execution on both original paths and matching setup-refresh evidence required host observation. The installed engineering package's `.agents/lanes/codex.json` resolves L3 to `gpt-6.1-sol` with high reasoning effort, matching this session's launch selection. No model switch is claimed.

## Original-path verification (2026-10-11)

Both commands ran through ordinary `exec_command` with its default sandbox permissions, without elevation or an alternate reader:

| Read | Actual exit code | Tool output |
|---|---|---|
| `Get-Content -Raw -LiteralPath 'C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-DependentPrBranchCleanup/plans/dependent-pr-branch-cleanup/sandbox-repair-followup-prompt.txt'` | 0 | Chunk `6729ac`; original prompt returned |
| `Get-Content -Raw -LiteralPath '.agents/engineering/workflow/plan-execution/SKILL.md'` | 0 | Chunk `b8e7fc`; complete canonical skill returned |

Matching evidence is in `C:/Users/TommySeery/.codex/.sandbox/sandbox.2026-10-11.log`. The command START records appear at 13:28:02.455 and 13:28:02.929 local (12:28:02 UTC). Their helper-spawn records at 13:28:03.109 and 13:28:03.720 local both name `C:/Users/TommySeery/.local/share/codex/runtimes/0.163.0-alpha.1/codex-resources/codex-windows-sandbox-setup.exe` and this exact checkout. The concurrent completion records have interleaved log text but contain both UTC timestamps, `2026-10-11T12:28:10.745911700+00:00` and `2026-10-11T12:28:10.745906500+00:00`, and two `setup refresh: processed 2 write roots (read roots delegated); errors=[]` results. Both subsequently select `codex-command-runner-0.163.0-alpha.1.exe` at 13:28:12.748 local. The command runner's independent exit results establish each read's success; the shared log does not provide a per-command identifier for ordering the simultaneous completions.

The same shared log also contains failures from the older npm helper in other sessions. Those records name the npm runtime and different setup invocations; they do not negate the fixed session's successful reads. Existing hosts still require reopening with the fixed runtime, as recorded above. Nonfatal profile ACL/visibility warnings continue without preventing these reads.

Read-only installed `machine:peer-cli` verification returned live entries for the originating dependent-cleanup session `01a127b0-7047-7e30-af8c-c861898d7e5b` (PID 30996), the predecessor repair session `01a127ec-ae44-7353-95d7-436f4fccfd74` (PID 53192), and this successor (PID 49228). The predecessor remains an observer after writer transfer. Ordinary `Get-Process -Name node_repl` found 24 active shared runtime processes. No peer was stopped or restarted. No sandbox setting, hook trust, ACL policy, global runtime selection or sibling-checkout content was changed by this verification.

An optional sandboxed WMI process diagnostic was denied with `0x80041003`; it changed no controls or processes. Direct command-runner environment and installed peer inspection supplied runtime and liveness evidence. Incorrect guessed skill-file locations returned ordinary file-not-found errors; their actual adapter-linked canonical files were then read. These were diagnostic-command errors, not renewed sandbox setup failures.

Phase: L5 for the small evidence reconciliation, followed by L7 for the local Git checkpoint; both are tiny inline follow-ups under the lanes contract, with no claimed session model switch. The duplicate pickup block was consolidated into this single record. Review is a direct consistency check against observed command exits, log timestamps, live-peer evidence and the original authorization; no repository code was changed, so no code test suite or PR delivery is selected. The existing machine debt entry continues to own recovery support for older runtimes.

Outcome: the requested fixed-runtime host recovery and both original file-type reads are verified. The previous normal-launcher blocker is resolved by the successful normal-preflight launch and this observed pickup; no direct-launch bypass was used. Remaining action: local checkpoint and concise completion report. The checkout remains available as the durable evidence owner.
