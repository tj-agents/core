# Diagnose sandbox setup read failure

## Authority

Tommy explicitly requested a separate handoff on 2026-10-10 to determine why sandboxed reads of a known text file and repository skill files are recorded as `exit -1` before the requested command runs.

Checkout: `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-SandboxSetupReadFailure`
Branch: `Fix/SandboxSetupReadFailure`
Investigation lane: L3, because the execution-host failure source was unresolved. Resolved from the
installed engineering package's `.agents/lanes/codex.json`: `gpt-6.1-sol`, high reasoning effort.

## Outcome

Establish the concrete cause, owner, and repair route for the pre-process sandbox setup failure. Do not confuse it with a failed file read: the same `Get-Content -Raw` calls succeeded when run through scoped elevated execution.

## Scope

Investigate the Codex execution environment's setup-refresh/helper path, including available hook output and reproducible command evidence. Make no repository-product changes unless evidence shows a core-owned source defect. Do not bypass hook trust or weaken sandboxing.

## Next Steps

Diagnosis complete on 2026-10-10. Return the findings below to the originating session. A host runtime
update is a separate machine installation action outside this investigation's scope. After an authorized
update to a build containing OpenAI's fix, repeat the sandboxed read below and check the matching setup
log for a successful refresh with runtime processes still active.

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

## Safe repair route and remaining gate

- Resolver: the machine owner selects an official Codex runtime containing PR #51822, or OpenAI
  backports the fix into the desired stable channel. Verify the selected package's source includes
  the directory-only guard before installation; 0.162.1 alone does not supply it.
- Blocked action: restore ordinary sandboxed execution in the current host. This goal authorizes
  diagnosis, not replacement of installed runtimes or disruption of other active sessions.
- Concrete unblock action: authorize and install a verified official build containing the fix, then
  restart the affected Codex sessions so they use that build's setup helper.
- Observable resume condition: the ordinary sandboxed `Get-Content -Raw` above exits 0 while runtime
  processes remain active, with a successful setup refresh for the same attempt.
- Next action after that condition: resume the originating session's repository work under its
  existing authorization.

No sandbox settings, hook trust, runtime binaries, ACLs, or active processes were modified during the
investigation. No host repair is claimed. The requested diagnosis and repair route are complete.
