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
- Independent review found that arbitrary `functions.exec` JavaScript hides nested file writes from the router and that a missing transcript previously allowed the second write without proof. The core gate now rejects that opaque wrapper in standards-managed repos and keeps routed writes blocked without a readable transcript. Focused regressions pass. This is a host limitation for Codex Desktop's current wrapper: direct host tool hooks or nested-tool mediation are needed to permit that wrapper safely.
- Sandbox review found the new options library lacked its matching tests target. `client/tests/options/` now links the real library, and all 13 host CTest cases pass; committed as `51c9c8e`.
- Next: commit reviewed core changes, open PRs, monitor their checks, land authorized changes, and verify fresh-host activation. Do not claim the opaque wrapper is usable until the host exposes nested writes to PreToolUse.
