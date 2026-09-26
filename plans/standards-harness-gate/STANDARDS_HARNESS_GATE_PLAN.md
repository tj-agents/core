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

- Isolated shared-core worktree: `C:\Users\TommySeery\source\repos\base-agents\.worktrees\Fix-StandardsHarnessGate`, branch `Fix/StandardsHarnessGate`, based on `origin/main` at `e56c378`.
- The shared gate now ships in the ubiquitous base plugin for both hosts. It checks every skill named by a repo route table against the native enabled-plugin registry before allowing a candidate write. Codex's matcher includes functions.exec. Tests cover base-only packaging, absent marketplaces, stale caches, and both host manifests.
- The C++ marketplace source is `C:\Users\TommySeery\source\repos\cpp-agents`, branch `Fix/StructureSourceRoute`, commit `c8354af`. Its generator now routes C++ source to cpp:structure. Focused route, package, hook, and host validation checks pass. Full local suite has WSL Bash and pre-existing Windows short-path host failures; the latter is recorded in TECH_DEBT.md.
- Codex and Claude now have cpp, msvc, and win32 installed. The sandbox route table is generated from the corrected source; both hosts resolve all ten route skills. Sandbox options were moved into a client library, built, smoke-tested, and committed as `a9e992c` on `Refactor/client-options`; nine host protocol tests pass. Unrelated sandbox working files remain untouched.
- Core's 177-test suite had one Windows shell-command selection failure in the plan-artifacts test, now corrected and passing alone. Focused core router, base-package, and host-hook suites pass; package generation check passes.
- Independent review found that a missing transcript previously allowed the second write without proof. The core gate now keeps routed writes blocked without a readable transcript. OpenAI's Codex hook documentation confirms that `PreToolUse` runs on tools called from JavaScript code mode, so the router matches the nested `apply_patch` and canonical `Bash` calls instead of the opaque outer `functions.exec` wrapper. Focused regressions pass.
- Codex plugin hooks are skipped until their current definition is trusted. A released package therefore still needs a fresh-session trust and activation check in the local Codex profile; install/enabled state alone is insufficient.
- Sandbox review found the new options library lacked its matching tests target. `client/tests/options/` now links the real library, and all 13 host CTest cases pass; committed as `51c9c8e`.
- C++ PR https://github.com/tj-agents/cpp/pull/24 merged as `55331b9`; post-merge CI and attester passed. Marketplace release https://github.com/tj-agents/cpp/releases/tag/v0.3.1 points at that exact commit.
- Core PR https://github.com/tj-agents/core/pull/41 was green at `b716360`. Its catalog is now being updated from the stale C++ v0.1.1 pin to the tagged v0.3.1 release, including nine exact package versions, skill lists and tree digests. The tagged digest check and six focused catalog tests pass; exact-head CI remains to be rerun after push.
- Sandbox PR https://github.com/tomjseery/sandbox-hwid/pull/3 remains ready (local build and 13 tests green; no CI configured).
- The isolated Codex profile installed base 2.1.9 from the branch and ran its SessionStart hooks. Its model run could not reach PreToolUse because the isolated profile lacks authentication (HTTP 401). Direct invocation of the installed PreToolUse hook with a Codex edit payload returned exit 2 and left the disposable target absent.
- Next: commit and push the core catalog update, monitor CI, land core and sandbox, publish the new core release, refresh the normal Codex and Claude profiles, trust the changed Codex hook through `/hooks`, and run a fresh-session blocked-write probe. The core package is not active in the normal profile yet.
