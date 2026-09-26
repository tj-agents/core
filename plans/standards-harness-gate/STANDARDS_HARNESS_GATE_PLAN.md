# Standards harness gate

## Authorized outcome

Find why a Codex session could edit sandbox-hwid without its C++ standards, repair the shared marketplace gate in Codex and Claude, and correct the sandbox-hwid client layout under the C++ standard.

## Root causes

- The original Codex session lacked the C++ marketplace. The base plugin did not carry the write router, so no active ubiquitous hook checked required skills. The older engineering router also missed the Codex wrapper payload.
- The C++ route generator applied `cpp:structure` to CMake files but omitted C++ source paths.
- Codex runs hook commands through the session's selected shell. This Windows profile selects PowerShell. Codex expands `${PLUGIN_ROOT}` before invoking it; cmd's `%PLUGIN_ROOT%` does not expand there.
- PowerShell's `-Command` process reported exit code 1 when a child Python hook exited 2. Codex treated code 1 as a failed hook and dispatched the write. A JSON deny response on stdout with process exit 0 survives that shell translation.
- Codex requires trust for each current plugin hook definition. The 2.1.11 command changes invalidated prior hashes. A fresh headless session skipped the 13 pending definitions and wrote the disposable probe file. Reviewing and trusting them through `/hooks` activated the gate; a second fresh session blocked the same routed write.

## Delivered work

- `tj-agents/cpp` PR #24 merged as `55331b9`; `v0.3.1` routes C++ source through `cpp:structure`. Codex and Claude resolve all sandbox routes.
- `tomjseery/sandbox-hwid` PR #3 merged as `13672b5`; options moved to `client/libs/options`, app entry to `client/app/src`, and all 13 client CTest cases passed. Unrelated local sandbox edits were preserved.
- `tj-agents/core` PR #41 merged as `1c9ba93`; `v2.1.9` put the route gate in base and verified native plugin availability and transcript proof. A fresh Claude missing-marketplace write probe blocked before file creation.
- Codex's Windows sandbox helper initially failed on generated CUA paths longer than 260 characters. Two exact cache directories were moved to reversible local quarantine; `codex sandbox` then passed. This was separate from the hook protocol failure.
- `tj-agents/core` PR #43 merged as `bf482fe`; `v2.1.10` switched Windows commands to `%PLUGIN_ROOT%` based on a cmd-only test. Fresh live Codex probes still wrote files. The release checks lacked a selected-shell probe.
- `tj-agents/core` PR #44 merged as `04d626b`; `v2.1.11` restores host-expanded `${PLUGIN_ROOT}` and packages one Codex Windows PreToolUse adapter into base and engineering. The adapter returns a valid JSON denial for child exit 2 or operational failure. The reviewed shell regression runs under PowerShell 7, Windows PowerShell and cmd when available. PR CI and post-merge Windows CI passed.
- Normal Codex base, engineering and machine packages now report 2.1.11; the matching Claude packages report `04d626b3e8ea`. The disposable candidate marketplace was removed. After Codex `/hooks` trust review, fresh normal-profile Codex and Claude sessions each blocked a missing-marketplace write before file creation; independent checks confirmed both probe files absent.

## Remaining platform constraint

The packaged gate works when the host executes its trusted hook. Codex still dispatches writes when the adapter itself cannot start, a hook is untrusted or disabled, or a tool path bypasses hooks. The owning condition and required host capability are recorded in `.agents/plugins/TECH_DEBT.md`. A new hook definition must be reviewed and trusted in `/hooks` before claiming normal-profile enforcement.

The delivery preflight limitation discovered during incremental review is tracked in `docs/workflows/TECH_DEBT.md`.
