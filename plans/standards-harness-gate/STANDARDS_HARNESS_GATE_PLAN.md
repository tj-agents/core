# Standards harness gate

## Authorized outcome

Find why this Codex session could edit sandbox-hwid without the required C++ standards, and repair enforcement for tj-agents marketplaces in Codex and Claude. Then correct the sandbox-hwid code layout once its C++ standards are available.

## Current evidence

- sandbox-hwid declares cpp:structure and other C++ skills, but this Codex session lists no C++ marketplace skills.
- A local code edit to client/src/main.cpp succeeded anyway.
- The active base plugin contained no write router, while the engineering package carrying it was absent. The old router's Codex matcher also omitted the exposed functions.exec wrapper and checked routed skills only after finding a write target.
- The generated sandbox-hwid route table applies cpp:structure to CMake files but not C++ source.

## Work

1. Reproduce and repair the shared gate so a missing routed marketplace stops writes in both Codex and Claude, including the Codex wrapper payload. Add focused regression coverage and verify generated manifests.
2. Establish the C++ marketplace source and correct its route generation so source files require cpp:structure. Install and verify availability in both local hosts.
3. Move sandbox-hwid option logic to the standard location, build and test.
4. Review and deliver the three repository changes. Verify the released gate in fresh Codex and Claude sessions; record any host hook limitation explicitly.

## Progress

- `tj-agents/cpp` PR #24 merged as `55331b9`; release `v0.3.1` includes `cpp:structure` for C++ source paths. Codex and Claude now install cpp/msvc/win32 from that Git marketplace; both native registry checks resolve all sandbox routes.
- `tomjseery/sandbox-hwid` PR #3 merged as `13672b5`; the options domain lives under `client/libs/options`, the app entry point under `client/app/src`, and the client build passes all 13 CTest cases. Unrelated local sandbox edits remain untouched.
- `tj-agents/core` PR #41 merged as `1c9ba93`; release `v2.1.9` moves the route gate into ubiquitous base, verifies routed plugin availability against the native host registry, and fails closed when required transcript proof is missing. Core CI and release attestation passed. Both native host profiles installed the release.
- A fresh Claude probe in an isolated repository requiring `missing-marketplace:never-shipped` blocked `Write` before a file was created.
- The first fresh Codex probe created a file while its `PreToolUse` hooks failed. `codex doctor` and the sandbox log traced the first failure to a 288-character generated CUA cache path rejected by the Windows sandbox helper. Two exact cache directories were moved to a reversible local quarantine; `codex sandbox` then launched successfully.
- A second fresh Codex probe still created a file. Directly running the installed router in the sandbox blocked correctly, exposing another cause: every Codex `commandWindows` used `${PLUGIN_ROOT}`, but Codex invokes commands through `cmd.exe`, which expands `%PLUGIN_ROOT%`. The existing package test had run the Windows command through Bash and missed the defect.
- Follow-up branch `Fix/CodexWindowsHookCommands` corrects the canonical base, engineering and machine hook commands, regenerates packages, adds a native `cmd.exe` blocked-write test, and bumps the proposed release to `v2.1.10`. Focused native tests, the complete 179-test local suite, package synchronization check, and catalog digest check pass. Delivery remains in progress.

## Next steps

1. Commit the verified fix, review, open the PR, monitor exact-head CI, merge, and publish `v2.1.10`.
2. Update Codex and Claude profiles from the new release; verify trusted hook activation and repeat the fresh Codex missing-marketplace probe.
3. Keep the Codex host limitation tracked in `.agents/plugins/TECH_DEBT.md`: failed or skipped hooks and specialized tool paths can continue. Marketplace code alone cannot guarantee a complete write boundary until the host provides fail-closed managed enforcement.
