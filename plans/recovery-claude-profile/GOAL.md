# Recovery launcher and worktree-gate defects

Status: active
Branch: Fix/RecoveryClaudeProfile
Worktree: C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-RecoveryClaudeProfile
PR: not opened

## Outcome

Resuming an exact Claude session through `machine:recover-agents` / `machine:open-claude --resume` reopens that session with the user's normal Claude configuration and reports success only once the session has actually started. The worktree placement gate no longer blocks shell commands that do not create a worktree.

## Authorization

Standing standards-defect authorization in `engineering:session-guidance`: diagnose, implement, test, open the PR and merge once this repository's gates pass. Tommy also asked on 2026-10-12 for this bug to be reported and fixed. Installing into any other scope, publishing outside this repository and destructive operations stay gated. Do not delete `~/.claude/.claude.json` (see evidence); report it for Tommy to decide.

Side workstream launched by recovery session `claude:cec3b609-c328-4482-b813-3c35719a8032`, which keeps no write ownership here.

## Defects and evidence (2026-10-12)

### D1 Resume sets `CLAUDE_CONFIG_DIR` for the default profile

`.agents/machine/scripts/agent_recovery.py` `open_session` sets `CLAUDE_CONFIG_DIR` to the recorded profile (`c:\users\tommyseery\.claude`) for every Claude resume. With that variable set, Claude Code reads its global config from `<CLAUDE_CONFIG_DIR>/.claude.json` instead of `~/.claude.json`, so the resumed tab opens the first-run onboarding (theme picker) without the user's login, onboarding, trust or MCP state and never resumes the session.

- 22:34 resume of `claude:c27c07bf-a274-466a-a10e-10ef96f36841`: receipt recorded `launched`; the session never re-registered (registry pid unchanged). Created `C:\Users\TommySeery\.claude\.claude.json` (1,518 bytes) beside the real `C:\Users\TommySeery\.claude.json` (248,423 bytes).
- 22:55 retry: Tommy's screenshot shows the onboarding theme picker in tab `Claude c27c07bf`; its process command line was `claude.exe --resume c27c07bf-... "Read the file at ..."`.
- Control: the same resume through the shipped `agent_cli.open_claude_tab` with `CLAUDE_CONFIG_DIR` unset registered immediately (pid 21676).
- Codex is unaffected in practice: `CODEX_HOME` set to the default `~/.codex` is the directory Codex already uses.

Fix direction: set `CLAUDE_CONFIG_DIR` only when the recorded profile is not the default Claude profile, and unset an inherited value when it is. Check every other launcher that sets it (`grep -rn CLAUDE_CONFIG_DIR .agents`).

### D2 Launch success is reported without a started session

`open_session` writes the `launched` receipt and returns success as soon as the tab command is submitted. In D1 the session never started, the caller reported success, and the stale `launched` receipt then refused a retry ("A prior launch ... pending or ambiguous"). Success should require evidence that the resumed session registered (SessionStart registry entry for that id with `started_at` after the launch), within a bounded wait, and report an unverified launch distinctly otherwise. Do not verify by listing processes.

### D3 Worktree placement gate false positives

The PreToolUse worktree placement gate blocked, with "worktree creation must not be hidden in a compound shell command", commands that create no worktree:

- Bash: `cd <core>/.worktrees/Feature-WorkItemSessions && git add <file> && git commit ... && git push`.
- Bash: `python -B - <<'EOF' ... EOF` and `cat > file <<'EOF' ... EOF` writing plain Python with no git command.
- PowerShell: `$w = "<core>\.worktrees\..."; git -C $w add <file>; git -C $w commit ...; git -C $w push`.

Fix direction: match only an actual `git worktree add` (any spelling the gate already supports), with tests for these false positives. Deliver as its own PR from a fresh branch off updated `origin/main` (for example `Fix/WorktreeGateFalsePositives`), after D1–D2 merge.

## Acceptance

- Unit tests cover D1 (default profile leaves `CLAUDE_CONFIG_DIR` unset and clears an inherited one; a non-default profile still sets it) and D2 (unregistered launch is not reported as success; a registered one is) on Windows and Linux.
- D3 tests show the three commands above pass the gate and a real hidden `git worktree add` is still blocked.
- Each PR reviewed, CI green, merged through the repository gates; generated `plugins/*` untouched.

## Current progress

- 2026-10-12: D1 and D2 are implemented in `.agents/machine/scripts/agent_recovery.py`. Default Claude profiles now clear inherited `CLAUDE_CONFIG_DIR`; alternate profiles still set it. Resume success now requires a newer matching SessionStart registry entry, otherwise the receipt becomes `ambiguous` and the command reports a launch timeout.
- Focused source verification passed: `python -m unittest tests/test_agent_recovery.py` — 21 tests.
- The repository workflow audit could inspect this checkout but could not resolve the canonical `plan-execution` skill body; its source defect is recorded as B008 in `BUGS.md`. Execution continues through the documented native fallback.

```agent-host-coverage
{"schema_version":1,"shared_source":".agents/machine/scripts/agent_recovery.py","hosts":[{"host":"claude","behavior":"Resume an exact Claude session with the user's default configuration and verify it started before reporting success.","source":".agents/machine/scripts/agent_recovery.py","mapping":"machine:recover-agents and machine:open-claude --resume delegate to open_session.","verification":{"level":"source","result":"passed","evidence":"tests/test_agent_recovery.py verifies default-profile environment cleanup, alternate-profile forwarding, successful new registration, and an unregistered launch reported as ambiguous."}},{"host":"codex","behavior":"Resume an exact Codex session with CODEX_HOME for its recorded profile and verify it started before reporting success.","source":".agents/machine/scripts/agent_recovery.py","mapping":"machine:recover-agents and machine:open-codex delegate to open_session.","verification":{"level":"source","result":"passed","evidence":"tests/test_agent_recovery.py verifies a Codex resume returns only after a new matching registry entry."}}]}
```

## Next Steps

Lane: L4 (specified fixes with tests). D1 and D2 implementation and focused verification are complete. Commit the source, test and current-goal update; review, push, open the PR and merge through `engineering:merge`. Then fix D3 on a fresh branch from updated `origin/main` the same way.

- Scope: whole plan through all remaining phases and terminal delivery.
- Current slice: D1 and D2 review and delivery.
- Remaining scope: D3 after the D1/D2 PR merges.
- Done when: both PRs are merged and this goal records their PRs and evidence.
