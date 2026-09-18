# CLI Session Recovery Agent Instructions

These instructions apply to every file in this directory.

Read `README.md` completely before investigating or changing anything. It is the persistent handoff from earlier debugging contexts and contains the architecture, installed paths, user workflow, recovery invariant, known failure modes, and verification commands.

## Objective

Maintain a reliable Windows recovery system for Tommy's Claude Code and Codex CLI conversations. The user must be able to save from the desktop while Windows Terminal is unresponsive, terminate Terminal, and restore every distinct resumable conversation into the correct Terminal windows.

## Non-negotiable invariants

- Recovery is based on distinct `tool + session ID`, not raw process or tab count.
- Save discovers session IDs from transcript files held open by each live CLI writer; hooks are not required.
- Deduplicate identical session IDs. Never reopen duplicate copies merely because multiple processes report the same current ID.
- A blank prompt without a session ID is not a resumable conversation.
- Closed sessions must not return in later recovery sets.
- A CLI counts as running only when its creation-time-valid process ancestry reaches a currently live `WindowsTerminal.exe`.
- A detached Claude/Codex PID left after Terminal is killed must not block Restore.
- Preserve the saved Terminal window grouping.
- Never replace a good recovery set with an empty, partial, or unverified set.
- Never automatically terminate processes unless Tommy explicitly authorizes that destructive behavior after the exact targets and risk are explained.

## Safety procedure

1. Do not close or restart Terminal, Claude, Codex, PowerShell, or related processes while diagnosing.
2. Lead with read-only evidence from the installed scripts, recovery JSON, process ancestry, and Terminal windows. Do not run Save or Restore against the real vault until that evidence establishes the expected session IDs and counts.
3. Inspect `C:\Users\TommySeery\.cli-session-vault` read-only. Hash important JSON files before any deployment or real save.
4. Reproduce using module functions or `-DryRun` first.
5. Run `tests\cli-session-vault.tests.ps1` and parse every deployable PowerShell file.
6. Deploy only with `install-cli-session-recovery.ps1`; it creates a timestamped backup of the live scripts.
7. Prove recovery-state JSON hashes did not change during deployment.
8. Run the installed Restore dry run and check saved, running, missing, detached, and window counts.
9. Only then perform the requested real Save or Restore.

Visible tabs, live CLI processes, distinct resumable IDs, detached processes, saved entries, and Terminal window groups are six different counts; never treat the visible tab count as the expected saved count. Compare distinct live resumable IDs with saved IDs. On 4 August 2026, 14 visible CLI tabs correctly represented 12 recoverable conversations because one Claude ID was duplicated and one Codex prompt was blank.

## Source and deployment

- Repository: `C:\Users\TommySeery\source\repos\base-agents`
- Source: `cli-session-recovery`
- Tests: `cli-session-recovery\tests\cli-session-vault.tests.ps1` from the repository root, or `tests\cli-session-vault.tests.ps1` from this directory
- Installer: `cli-session-recovery\install-cli-session-recovery.ps1` from the repository root, or `install-cli-session-recovery.ps1` from this directory
- Installed scripts: `C:\Users\TommySeery\*.ps1` plus the hidden-save VBS launcher
- Runtime vault: `C:\Users\TommySeery\.cli-session-vault` — never commit it
- Desktop interface, and the only supported way for Tommy to run this: `SAVE CLI SESSIONS.lnk` and `RESTORE CLI SESSIONS.lnk`. Never have him run a script by hand from a frozen Terminal.

The repository is the source of truth. Modify the existing filenames; do not create `v1`, `v2`, `working`, or similar copies. Git history provides rollback.

## Required regression cases

Document every newly discovered failure mode in `README.md` and add a regression test before deploying. Keep tests covering at least:

- `/clear` replaces only the previous conversation in the same terminal.
- Delayed predecessor events do not remove the replacement.
- Saving excludes closed sessions.
- Duplicate session IDs remain deduplicated.
- A dead Terminal parent makes a CLI detached, not running.
- A live PowerShell-to-Windows-Terminal ancestor chain makes a CLI running.
- PID reuse cannot cause a newly created Terminal to adopt an older orphan.
- Claude Desktop is never classified as Claude CLI.
- Multiple saved window groups restore separately.
- Restored tabs use the normal Windows PowerShell profile.
- A CLI process with no resume argument can expose multiple open transcript IDs without Restore launching a duplicate writer.
- A handle-inspection failure for a still-live CLI fails Save instead of silently producing a partial recovery set.

## Current detached-process behavior

Restore ignores detached processes and successfully reopens the saved conversations. It reports the detached count but deliberately does not force-kill those processes. Changing that behavior requires Tommy's explicit approval because process-tree termination is destructive.

