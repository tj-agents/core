# CLI Session Recovery

This folder owns Tommy's Windows recovery system for Claude Code and Codex CLI conversations. It exists so Windows Terminal can be force-killed when it hangs without losing the resumable conversations.

`AGENTS.md` provides the Codex operating rules for this directory, and `CLAUDE.md` provides the equivalent Claude Code entry point. To continue troubleshooting in a fresh context, open this directory as the working folder and describe the current symptom; the agent must read those files before acting.

## User workflow

- Automatic recovery runs continuously after installation. It captures conversations already open when the listener starts, reacts to new transcripts and CLI process changes, and performs a five-minute safety reconciliation if an event is missed.
- `SAVE CLI SESSIONS` is an immediate checkpoint before killing Windows Terminal. It atomically pins the latest completed automatic recovery set and does not inspect processes, transcripts, or Terminal windows, so a frozen Terminal or stuck autosave cannot block it.
- After restarting Terminal, run `RESTORE CLI SESSIONS`. It opens only missing conversations and recreates their saved Terminal window groups.
- Do not run scripts manually from the frozen Terminal.
- The shortcuts have no keyboard hotkeys. The desktop shortcuts are the supported interface.

The installed shortcut targets are:

- `SAVE CLI SESSIONS.lnk` -> `wscript.exe "C:\Users\TommySeery\save-sessions-hidden.vbs"`
- `RESTORE CLI SESSIONS.lnk` -> Windows PowerShell running `C:\Users\TommySeery\restore-sessions.ps1`

## Recovery invariant

Recovery is conversation-based, not a byte-for-byte clone of every Terminal tab.

- Save one entry for each distinct, currently live Claude/Codex resumable session ID.
- Discover session IDs from verified top-level transcript files held open by each live CLI writer. Reject helper and subagent transcripts.
- Do not register recovery lifecycle hooks. Save is authoritative and must work from live writer evidence alone.
- Never restore the same session ID twice. Duplicate live processes with the same current ID are deliberately deduplicated.
- Do not save a newly opened blank CLI prompt until it has a resumable session ID. There is no conversation to recover yet.
- Remove sessions whose owning CLI process has closed.
- When Terminal is responsive, require each writer to map back to a currently visible tab. A leftover process from a closed tab is not open. If Terminal is frozen or the complete tab probe cannot be verified, preserve the writer-based set rather than risk a partial save.
- Preserve the Terminal window group for every saved conversation.
- Never replace the last good recovery set with an empty set. If metadata for only some live conversations is unavailable, save every recoverable conversation, salvage missing entries from prior recovery data, and record the unsaved IDs explicitly.
- Restore only sessions that are not already running.
- Keep automatic state in `autosave.json` and manual desktop state in `pinned.json`. Treat an unconsumed manual pin as authoritative over later background registry changes. After Restore consumes it, use the newest complete recovery set again.
- Skip a saved conversation whose transcript or working directory has been deleted, and restore the rest.
- A busy registry lock must never lose a save. Only an empty or unverifiable set may.
- A CLI counts as running only when its live, creation-time-valid parent chain reaches a live `WindowsTerminal.exe`. Killing Terminal can leave detached Claude/Codex processes behind; those processes must not block restoration.

On 4 August 2026, 14 visible CLI tabs correctly produced 12 saved conversations: two Claude processes shared one current post-`/clear` session ID, and one Codex tab was a blank prompt with no session ID. The 12 saved conversations were the complete logical recovery set. Do not change the system to process-instance recovery merely because the visible tab count is higher.

## Architecture

The source of truth is this repository. `install-cli-session-recovery.ps1` validates and deploys the files into `C:\Users\TommySeery`, backing up the previous live scripts first.

- `cli-session-hook.ps1` is a silent no-op for sessions that cached an old registration. The installer removes its Codex and Claude hook registrations.
- `cli-session-vault.psm1` contains transcript-writer discovery, registry fallback, process matching, atomic JSON, window detection, and recovery selection logic.
- `configure-cli-session-autosave.ps1` creates or repairs the recurring scheduled-task watchdog and can start the listener immediately.
- `save-sessions.ps1 -AutoSave` reconciles live CLI writers and atomically prepares `autosave.json`; `save-sessions.ps1 -Pin` only copies the newest completed state to `pinned.json`.
- `restore-sessions.ps1` validates a recovery set, deduplicates by `tool + session ID`, skips sessions already running, and invokes Windows Terminal.
- `start-saved-cli.ps1` starts `codex resume <id>` or `claude --resume <id>` inside the normal Windows PowerShell profile.
- `probe-cli-window.ps1` maps CLI console processes to Windows Terminal windows.
- `reconcile-live-sessions.ps1` is the explicit repair utility for the active registry.

Runtime state is under `C:\Users\TommySeery\.cli-session-vault` and must never be committed. Important files are `active.json`, `closed.json`, `autosave.json`, `pinned.json`, `observed.json`, `shutdown.json`, `last-open.json`, `last-save.txt`, `last-restore.txt`, `snapshots-v3\`, `deployment-backups\`, and `reconciliation-backups\`. Existing `closed.json` tombstones remain honored. Closed conversations leave the next snapshot because their Terminal-attached writers and transcript handles are no longer live.

`CLI Session AutoSave` is a one-minute recurring watchdog task. While its long-running listener is healthy, duplicate triggers are ignored. The listener saves after new transcripts or CLI process-set changes and performs a full window-group verification every five minutes. If the listener exits or is killed, the next trigger starts it again; Task Scheduler also retries failures every minute. The installer recreates the task and starts it, so automatic protection does not depend on a task left over from an earlier manual setup.

## Safety rules for future changes

1. Never close, restart, restore, or overwrite Tommy's real recovery vault while investigating.
2. Reproduce with read-only process and JSON inspection first.
3. Run the unit tests.
4. Test saves against a disposable vault and verify the previous real vault hashes did not change.
5. Verify distinct live session IDs, saved entries, restore dry-run counts, and window-group counts separately. Visible Terminal tab count is not the expected saved count.
6. Deploy through the installer so the current live files are backed up.
7. Run a real save only after the disposable test is correct.

Regression test:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tests\cli-session-vault.tests.ps1
```

Install:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install-cli-session-recovery.ps1
```

Read-only restore preview:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\restore-sessions.ps1" -DryRun
```

## Historical failure modes

- Hook-only snapshots became stale when a CLI closed or `/clear` replaced its logical conversation.
- Session saves run inside Windows Terminal were unusable during a Terminal hang; the desktop save shortcut therefore runs out-of-process.
- Restores originally placed every tab in one window; recovery entries now carry stable window groups and `wt.exe -w <group>` recreates them.
- Restored tabs originally used generic command icons because `wt.exe` launched a command directly. They now launch through the Windows PowerShell profile GUID and then run the CLI launcher.
- A live process missing from the active registry used to fail the entire save. Save now recovers its metadata from prior recovery sets when possible; if that is impossible, it protects the remaining conversations and records the unsaved `tool + session ID` values in both the snapshot and save status.
- Transcript discovery once read the machine-wide Windows handle table separately for every Claude/Codex process. On a busy system, saves could consume CPU indefinitely without reaching the recovery write. Automatic discovery now takes one handle-table snapshot for all CLI writers in a disposable worker and stops only that worker if inspection exceeds 45 seconds. Desktop Save no longer enters discovery at all.
- The Terminal window probe once marked itself complete merely because it attempted every process. If UI Automation failed to inspect most tabs, Save treated every unresolved writer as a closed tab and replaced a broad recovery set with the one writer it happened to map. A probe is now complete only when every attempted process produced conclusive visible-or-absent evidence; any probe failure preserves the writer-based set.
- Claude CLI stopped keeping its active transcript file open and retained only the project-local `.claude` directory handle. Guessing from recent transcripts collapsed multiple Claude processes opened in the same repository and saved only two of four live Claude conversations on 18 August 2026. Save now reads Claude's own `.claude\sessions\<PID>.json` registration, validates its recorded process start time against the live process to prevent PID reuse, and resolves that exact top-level transcript without lifecycle hooks.
- Task Manager can end `WindowsTerminal.exe` without ending its CLI processes. Restore now distinguishes those detached processes from usable tabs by walking the current process ancestry and rejecting dead or PID-reused Terminal parents.
- Save held the global registry mutex while enumerating processes and probing Terminal through UI Automation. With 22 sessions that lasted minutes, so every hook and every competing save hit the fixed 10-second wait and reported `Timed out waiting for the CLI session registry lock`. Slow work now runs lock-free and the mutex only covers the JSON write.
- A lock holder killed with Terminal left the mutex abandoned, and the unhandled `AbandonedMutexException` failed the next save. An abandoned mutex now counts as acquired.
- Save gave up entirely when the lock was busy. It now waits 30 seconds, then writes anyway because its JSON writes are atomic and its set is recomputed from live processes; the status line records that it did.
- Re-probing sessions whose window group was already saved cost about two minutes and returned the same answer. Save now probes only sessions with no known window; `-VerifyWindowGroups` forces the full sweep after tabs are dragged between windows.
- A truncated probe let a duplicate tab title reassign a session to the wrong window. A saved window group now outranks the tab-title heuristic.
- One conversation whose transcript had been deleted failed the validation of the entire recovery set, so Restore opened nothing. Restore now skips only the unusable entries and reports them.
- Claude can emit `SessionEnd` before its process has fully exited. Save previously rediscovered that lingering process from an older snapshot and reopened the deliberately closed conversation. SessionEnd now writes a tombstone; Save, Restore, and reconciliation all exclude tombstoned IDs until a later SessionStart explicitly reopens one.
- Recovery relied on lifecycle hooks to associate a generic `codex.exe` process with its conversation. When the hook script was missing, Save omitted an active transcript; Restore then launched the same ID again and Codex rejected it because the original writer still owned it. Save now enumerates transcript handles from every live Codex writer and fails loudly if a still-live writer cannot be inspected. Hook metadata can improve grouping but cannot override the verified writer ID.
- Codex processes also hold guardian-subagent transcripts open. Treating every open transcript as a Terminal conversation caused 12 guardian sessions to be restored as tabs on 13 August 2026. Writer discovery accepts only transcript metadata with top-level `source: cli`, and Restore repeats that validation so an older polluted snapshot cannot launch helper sessions.
- Recovery lifecycle hooks created unnecessary helper consoles and could expose raw event JSON in a Terminal tab. The installer removes all CLI recovery hooks from both Codex and Claude while preserving unrelated settings and hooks.
- Restore previously chose a newer `active.json` over the desktop snapshot even after the user explicitly clicked Save. An unconsumed `pinned.json` now wins until Restore marks it consumed, preventing sessions opened or left stale after the save from changing the requested recovery set.
- A replacement transcript discovered after `/clear` could lose its prior window when Terminal was already frozen. Transcript recovery inherits a saved group only from the same tool, PID, and creation time.
- Deployed transcript-discovery changes once existed only in the installed user-profile scripts, leaving the repository and regression suite behind the live behavior. The deployed implementation is now source-controlled and installer tests verify its configuration.
- Manual saves reused old window-group values, allowing recovery sets to drift from 4 real Terminal windows to 9 or more stale groups. Manual and shutdown saves now refresh every resolvable live tab's actual window, and an existing `cli-recovery-*` target remains stable across later restore cycles.
- PowerShell represented an uninitialized empty registry as `$null`; the first hook update then tried to treat that placeholder as a session and failed before registering anything. Hook calls now use named binding and the registry update functions normalize null collections before processing them.
- The regression suite originally shared the live vault mutex, so a running recovery process could make the lock test fail and the test could delay a real Save. Tests now use a unique mutex name while production keeps its stable mutex.
- Windows Terminal could leave a CLI writer alive after its tab disappeared. Automatic discovery requires a complete process-to-visible-tab probe before excluding writers with no tab; an incomplete or frozen probe never replaces a good set with partial evidence.
- Automatic recovery was described as installed but depended on a pre-existing logon task that the installer never created or repaired. The listener then exited, its cleanup error hid the original failure, and no watchdog restarted it; the installed `save-sessions.ps1` was later missing as well. The installer now restores every required file and repairs a one-minute recurring watchdog, the listener captures already-running CLIs immediately, retries failed saves without exiting, and reconciles every five minutes even if a transcript event is missed.
- Terminal title discovery once ran UI Automation inside the save process before the bounded window-probe worker started. When UI Automation hung, autosave held the save-wide mutex indefinitely and every desktop Save failed with `Another CLI session save is already running`. All Terminal UI Automation now runs inside the bounded worker.
- The desktop Save shortcut once remained an old inline hidden-PowerShell command even though the installed VBS launcher had been fixed. The installer now backs up and replaces both desktop shortcuts on every deployment, and the Save launcher keeps refreshing visible progress while its hidden worker runs.
- Desktop Save once reran two process inventories, transcript-handle discovery, and Terminal UI Automation while sharing the autosave mutex. Any slow or stuck background save therefore made the emergency control hang or reject the click. Automatic discovery and manual authority are now separate: autosave prepares `autosave.json`, desktop Save atomically pins that completed state to `pinned.json` without either mutex, and its launcher terminates only its own worker if the constant-time operation exceeds ten seconds. Regression coverage holds the autosave mutex while requiring the pin to complete within five seconds.
