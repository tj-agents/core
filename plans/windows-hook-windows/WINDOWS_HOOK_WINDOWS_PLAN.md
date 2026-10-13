# Stop Windows CLI hook consoles stealing focus

- Branch: Fix/WindowsHookWindows
- Worktree: C:/Users/tommy/source/repos/tj-agents/core/.delivery/windows-hooks
- Plan: plans/windows-hook-windows/WINDOWS_HOOK_WINDOWS_PLAN.md
- Roadmap: plans/windows-hook-windows/WINDOWS_HOOK_WINDOWS_PLAN.md
- Roadmap item: windows-hook-windows
- Base: origin/main at ee1cdbcc6e400cfba33a0ae099b54cfabe4310b7
- PR: https://github.com/tj-agents/core/pull/241

## Authority and outcome

The user authorized a permanent fix for newly opened Codex and Claude CLI sessions on this Windows machine, including repository source changes and local installation. Completion requires new interactive CLI launches to run core hooks without opening extra terminal windows, with hook stdin, stdout, stderr, and exit codes intact. Publishing or changing either upstream CLI is outside this repository's control.

## Evidence and decision

- Core's Windows hook manifests start several Python hooks per startup and per tool call. The installed marketplaces also launch hooks through the CLI hosts. Core already uses `CREATE_NO_WINDOW` for subprocesses it owns, so changing hook Python scripts would miss the initial host-created shell.
- [Codex Windows daemon report](https://github.com/openai/codex/issues/44768) traces visible hook and shell windows to the shared daemon child launch. Its tested `--no-daemon` workaround avoids that path. Disabling auto-start alone is insufficient while a daemon is already running ([report](https://github.com/openai/codex/issues/48778)).
- [Claude Windows hook report](https://github.com/anthropics/claude-code/issues/35797) traces hook windows to a host-created Git Bash process without `CREATE_NO_WINDOW`. It documents a GUI-subsystem Bash proxy configured through `CLAUDE_CODE_GIT_BASH_PATH`. Another [report](https://github.com/anthropics/claude-code/issues/70200) says Claude's direct Git subprocesses can still flash; those bypass the Bash proxy.
- Assessment complete: existing marketplaces use hidden flags for their own children but provide no installed first-process proxy. Keep their hooks and selectively use the two documented host workarounds. A Python-only hook change, `pythonw`, or a manifest-only change cannot hide the host's shell. The Claude proxy is a small C implementation of the documented wrapper mechanism, built locally from tracked source.

## Delivery slice

This is one focused Windows CLI launch repair covering the user's explicitly named Codex and Claude hosts. The source-only candidate changes 13 files and about 341 lines, including platform-specific installers, launcher tests, and this plan. The two host mitigations are independent at runtime but belong in one review because one machine incident and one acceptance condition require both; splitting them would leave the requested full coverage incomplete until a second PR. No generated package files are part of the PR; CI regenerates them. This is a new review slice based on current `origin/main`; no earlier PR owns these changes.

## Progress on 2026-10-13

- Added `shell/hidden-bash.c`, an installer, and profile wiring for Claude. Built on this machine using the installed Clang and installed user environment/profile configuration. A focused child-process check observed the proxy and Bash child with main-window handles `0`; stdin/stdout and exit-code checks passed.
- Added a Codex profile wrapper that selects `--no-daemon` for interactive starts, resumes and forks; installed it in both PowerShell profiles. A fresh PowerShell loaded both mitigations. Updated the canonical Codex handoff launcher to pass `--no-daemon`.
- Existing unrelated changes in `plans/repo-declared-config/` and `plans/conditional-skill-routes/` were left untouched.
- Generated machine package synced and checked with zero drift. `tests/handoff-launchers.tests.ps1` passed, including the new no-daemon assertion; 16 source-layout tests passed. A fresh PowerShell resolved the Codex wrapper and Claude proxy environment.
- A separate Codex marketplace refresh error was observed: the configured `agent-standards` marketplace upgrade reports a returned name of `agents`. The CLI continued with installed plugins. This is a separate registry/marketplace configuration defect, not evidence that the no-window launch failed.
- The original checkout was 1021 commits behind current `origin/main`, so the source fix was ported into a clean worktree at `core/.delivery/windows-hooks` on branch `Fix/WindowsHookWindows`. The original checkout and its unrelated user edits are untouched. Its earlier checkpoint commit is `cab6ae5`; the clean branch is the delivery owner.
- Current main's Python terminal launcher now adds `--no-daemon` for Windows interactive Codex starts, prompts, resumes, and forks. Its Codex handoff launcher also passes that option on Windows. Non-interactive commands retain their arguments. The Windows Bash proxy source and installer were ported without changing the verified process-launch logic. The shell profile loader restores Claude's Git Bash environment when the proxy is installed.
- The current-main focused launcher suite passed: 61 tests (7 platform skips). Catalog digests and generated packages were refreshed locally; `sync-generated.ps1 -Check` reported zero drift. Current main forbids generated package files in a PR, so those local outputs must be left uncommitted.
- The profile wiring, source layout and agent CLI suite passed: 119 tests (20 platform skips). The installed Claude proxy and Codex profile blocks were rechecked with their `-VerifyOnly` installers. The local Codex wrapper was expanded to cover a positional prompt as well as starts, resumes and forks, and an isolated PowerShell argument probe passed. Both local installer sources now exist in the current-main worktree so checkout updates preserve the profile references.
- Draft PR #241 was published from the clean current-main branch. Source review found that `--no-daemon` conflicts with Codex `--remote` and may be absent in older CLI versions; the terminal launcher now probes installed CLI help before injecting it, the handoff launcher gates on the resolved version, and the local wrapper leaves remote sessions alone. The focused suite passed 64 tests (7 platform skips), a PowerShell remote/prompt probe passed, and generated output checked with zero drift after this correction.

## Remaining work

1. Make a source-only commit and delivery review. Keep generated `plugins/*` output out of the commit per current main policy.
2. Verify an actual fresh Codex and Claude CLI startup visually when practical. The current Codex session may remain attached to the already-running daemon until it is closed; do not stop a daemon carrying an active session.
3. Record any remaining direct host subprocess flashes as upstream-owned limitations, with the exact executable/process trace if observed.

## Reviews

Current source candidate: `reviews/Fix-WindowsHookWindows.md`.

## Next Steps

Scope: Keep new Windows Codex and Claude CLI sessions from opening hook child consoles.
Current slice: Deliver the current-main source fix and local profile installation for both hosts.
Remaining scope: Remote CI, independent review, and a fresh GUI startup observation if available.
Done when: Both mitigations are installed and verified locally, their source is merged to main, and host limitations are recorded.
Run delivery preflight against origin/main, publish a draft PR, then review exact-head checks and findings.

## Transition

The local mitigation is installed. Continue with current-main delivery and a fresh CLI launch check. No routine design decision is pending.
