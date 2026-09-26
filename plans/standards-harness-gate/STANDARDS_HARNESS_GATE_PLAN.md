# Standards harness gate

## Authorized outcome

Find why a Codex session could edit sandbox-hwid without its C++ standards, repair the shared marketplace gate in Codex and Claude, and correct the sandbox-hwid client layout under the C++ standard.

## Root causes

- The original Codex session lacked the C++ marketplace. The base plugin did not carry the write router, so no active ubiquitous hook checked required skills. The older engineering router also missed the Codex wrapper payload.
- The C++ route generator applied `cpp:structure` to CMake files but omitted C++ source paths.
- Codex runs hook commands through the session's selected shell. On this Windows profile it is PowerShell, which does not expand cmd's `%PLUGIN_ROOT%`. Codex itself expands `${PLUGIN_ROOT}` before shell execution.
- PowerShell's `-Command` process reports exit code 1 when a child Python hook exits 2. Codex treats code 1 as a failed hook and dispatches the write. A Codex JSON deny response on stdout with process exit 0 avoids that translation.

## Delivered work

- `tj-agents/cpp` PR #24 merged as `55331b9`; `v0.3.1` routes C++ source through `cpp:structure`. Codex and Claude resolve all sandbox routes.
- `tomjseery/sandbox-hwid` PR #3 merged as `13672b5`; options moved to `client/libs/options`, app entry to `client/app/src`, and all 13 client CTest cases passed. Unrelated local sandbox edits were preserved.
- `tj-agents/core` PR #41 merged as `1c9ba93`; `v2.1.9` put the route gate in base and verified native plugin availability and transcript proof. A fresh Claude missing-marketplace write probe blocked before file creation.
- Codex's Windows sandbox helper initially failed on generated CUA paths longer than 260 characters. Two exact cache directories were moved to reversible local quarantine; `codex sandbox` then passed. This was separate from the hook protocol failure.
- `tj-agents/core` PR #43 merged as `bf482fe`; `v2.1.10` switched Windows commands to `%PLUGIN_ROOT%` based on a cmd-only test. Fresh live Codex probes still wrote files. Release checks lacked a selected-shell probe.

## Current slice

- Branch `Fix/CodexWindowsHookShell` starts from `bf482fe`. It restores Codex's host-expanded `${PLUGIN_ROOT}` and packages one canonical Codex PreToolUse adapter into base and engineering. The adapter converts a child hook's exit 2 or operational failure into Codex's JSON deny response with process exit 0.
- The focused regression passes with plugin paths containing spaces under PowerShell 7 and cmd. It covers a missing marketplace and a child hook crash.
- A disposable local candidate marketplace at version `2.1.11` blocked a fresh Codex `apply_patch` before file creation, naming `missing-marketplace:never-shipped`. This live probe used a temporary hook-trust bypass for the candidate package.

## Next steps

1. Run the repository validation gates, review the candidate, and deliver the exact-head core PR and `v2.1.11` release.
2. Install the released plugins in normal Codex and Claude profiles, trust the current Codex hooks, and repeat the fresh Codex missing-marketplace write probe without bypass.
3. Remove the disposable candidate marketplace, reconcile the core plan and host debt with final evidence, and report the remaining Codex host coverage limit.