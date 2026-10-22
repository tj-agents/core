# Tech debt — machine

## The Codex plugin cache is not reconciled

`~/.codex/plugins/cache/` accumulates orphaned plugin payloads exactly as the Claude cache did, and
`scripts/prune_plugin_cache.py` does not touch it.

Registry-is-truth, the rule the reconcile rests on, does not hold for Codex. Its registry is
`~/.codex/config.toml`, whose plugin entries record `enabled = true` and no install path at all, so a
cached directory cannot be matched to a live install. Those entries are also stale in their own right —
they still name plugins that were renamed away — which makes that registry the wrong copy rather than
the authoritative one. Pruning against it would preserve dead payloads and could remove live ones.

Left deliberately rather than guessed: the alternative is inventing a liveness rule for a source
already verified to be incorrect, shipped in the same change as the reconcile it would undermine.

**Resolution condition.** Either the Codex registry records a per-plugin install path, or its plugin
entries are reconciled against the marketplaces it actually resolves so the installed set can be
trusted. When either holds, add a Codex registry reader behind the same report-by-default,
fail-closed contract and delete this entry.

## Claude keeps a superseded plugin directory for 14 days, not for a session's lifetime

On 2026-09-22 every stop hook in a live session failed with `Plugin directory does not exist` after an
update. Claude Code 2.1.282 instead writes `.orphaned_at` into the superseded version directory and
deletes it 14 days later, so hooks keep their loaded path
([cleanup](https://code.claude.com/docs/en/plugins/loading#cleanup-of-previous-versions)); eight such
directories per core plugin were still present on 2026-09-28. `prune_plugin_cache.py --apply` keeps them
inside that window and `--pin` covers the live sessions it records. A session running longer than 14
days can still lose its hooks, and nothing in this repository sits between the host and its own cleanup.

**Resolution condition.** The host keeps a session's resolved plugin directory for that session's
lifetime, or exposes the resolved set so a supervisor can.

## Codex records no pin

The pin is written by the Claude SessionStart hook only. Codex's `machine-hooks.json` runs
`register_session.py` and not the reconcile, because the reconcile does not read Codex's cache at all
(above). Resolving that entry resolves this one with it.

## Launcher terminal detection trusts inherited environment variables

`agent_cli.launch_tab` picks the terminal from `TMUX`, `KITTY_WINDOW_ID` and `KONSOLE_DBUS_WINDOW`.
A GUI program started from a terminal inherits them, so a launcher run inside, for example, VS Code
started from Konsole opens its tab in that Konsole window, or fails if the window has closed.

Resolve when detection confirms the variable belongs to the terminal the caller is attached to, for
example by matching the terminal's own record of its sessions against the caller's process ancestry,
with a test for an inherited variable.

## A locked Codex runtime executable can disable every sandboxed command

Codex's sandbox setup opens ACLs on its bundled `node_repl.exe` before it starts a command. When Windows
returns a sharing violation for that executable, setup refresh fails and even a read-only command cannot
start. The launcher chooses among installed runtimes by version but has no command-runner health check, so
it cannot select a healthy desktop runtime when the CLI runtime is locked.

**Resolution condition.** Codex's sandbox setup tolerates a transient runtime-file lock or exposes a
supported health probe and runtime selection mechanism; then the launcher detects the unhealthy runtime,
uses a healthy supported runtime when available, and has regression coverage for the fallback.

## Windows Terminal option values may be escaped for a parse they never get

`agent_cli._launch_windows_terminal` passes every
`wt.exe` argument through `terminal_argument`, including `--title` and `--startingDirectory`, which are
Windows Terminal's own option values rather than the launched command's arguments. The escaping
`terminal_argument` applies models the second argv parse the tab's command arguments get after Windows
Terminal's own `;`-split re-joins them (`CommandLineToArgvW` quote/backslash rules) — a parse option
values may never receive at all, if Windows Terminal reads them off its own command line after only the
`;` split. If so, a title or starting directory containing a quote or a trailing backslash would show its
escapes literally in the tab (visible cosmetically, not a lost launch, since `;` is still escaped either
way and nothing else in that value is Windows-Terminal-significant).

Left unresolved rather than guessed: changing the escaping for option values without observing the real
behaviour risks trading a cosmetic defect for a functional one.

**Resolution condition.** A real `wt.exe` launch with a `--title` and a `--startingDirectory` containing a
quote and a trailing backslash confirms whether Windows Terminal parses its own option values the same
way as the tab's command arguments. If it does not, give option values their own escaping (likely just the
existing `;` handling, with no `CommandLineToArgvW`-style quoting), with a test pinned to the confirmed
behaviour.

## clip offers one clipboard flavour per copy on Linux

`copy_draft.py`'s POSIX backend sets a clipboard flavour through `wl-copy`/`xclip`, and each of those
tools accepts only one MIME type per invocation. Default mode therefore copies `text/html` only when
the tool supports it — nothing a plain-text target (a terminal, a plain text field) can read from that
same copy. The skill documents the split instead: default mode is for rich targets (Teams, email);
`--plain-only` for everything else. Windows is unaffected — CF_HTML and CF_UNICODETEXT are set in the
same clipboard transaction, so both flavours are always available together there.

`tests/test_copy_draft.py`'s `LinuxSingleFlavourTechDebtTests` pins today's one-call, HTML-only default
so a future change here is deliberate rather than accidental.

**Resolution condition.** A single copy can offer both `text/html` and `text/plain` on Linux — for
example, a small persistent Wayland (`wlr-data-control`) or X11 data source that goes on answering
selection/data-control requests for either MIME type from the same in-memory text, rather than a
one-shot `wl-copy`/`xclip` invocation that exits once the data is handed off. When one exists (or is
written here), default mode copies both flavours from one call and this entry is deleted, with a test
proving a `text/plain` read-back succeeds right after a default-mode copy.

## The pre-launch standards sync has no overall deadline

`agent_cli.sync_claude_standards` runs `claude_standards_sync.py` before every Claude launch and waits
for it with no outer limit, as the PowerShell launcher did. The script bounds each of its own steps
(180 seconds per marketplace update, 120 per plugin, 20 per `git ls-remote`), but those add up across
plugins, and on Windows a `claude plugin` grandchild that keeps the output pipe open can hold the wait
past its own step limit. A slow or wedged check therefore delays the tab, and the launch it was meant
never to block. A plain outer `subprocess` timeout is not the fix: it kills a check that is still
within its own budgets and leaves the grandchild running.

Resolve when the sync runs under one overall deadline that stops its whole process tree on expiry on
both Windows and POSIX, reports a `standards:` line and then launches, with a test that a hung
grandchild cannot hold the launch past that deadline.

## A shared parent shell can keep the worktree locked after finish

`finish.py` stops a parent shell only when it is this session's dedicated wrapper. When the CLI was started
by hand from a long-lived shell whose current directory is inside the worktree, that shell survives, Windows
keeps the directory locked, and the reaper records a failed removal; the cleanup reminder then surfaces it.

**Resolution condition.** The reaper can read another process's current directory, or the host records it,
so finish can tell a shell that pins the worktree from one that does not.

## Platform-specific machine integrations lack an explicit source boundary

Windows-only installers, shell profiles and terminal integration currently sit beside shared machine
code. As Linux integration grows, explicit `.windows` and `.linux` adapter directories would make
platform ownership easier to find. Shared Python implementations and capability definitions retain
their canonical home in `.agents`; platform folders should contain only OS-specific integration.

**Resolution condition.** Document the platform adapter layout in `SOURCE_LAYOUT.md`, move the
OS-specific integration into its owning directories, and update installation, packaging and imports
with Windows and Linux verification. Keep this structural change separate from the functional Linux
port so each delivery remains reviewable.

## Own-session closure can fail before the exit observer confirms startup

On 2026-10-10, after core PR #184 merged and its full causal main CI passed, the canonical Windows `peer-cli/scripts/close.py` ran from the retained Rust host checkout and refused with `session exit observer did not confirm startup`. The source worktree and branch had already been safely removed, and the terminal continuation task and binding were absent. The session remained open. Record this host failure separately from continuation enforcement under Tommy's direction to note unrelated host issues as debt. No startup cause is established and no process-identity check was bypassed.

**Resolution condition.** A fresh native Windows own-session close confirms the matching observer startup and armed receipts, records exit of the exact registered host identity, closes its uniquely identified tab when supported, and preserves other sessions and the retained checkout. Diagnose the failed handshake before changing timeout or ownership checks.

## D-MACHINE-TASK-TITLES: Terminal names must explain the current task

- **Kind:** debt.
- **Observed/reported:** 2026-10-11, Tommy could not identify the agents by their names. On 2026-10-12
  he clarified the exact visible symptom: `Read handoff...`. Inspection confirms two native Codex names,
  `Read handoff instructions` and `Read and follow handoff instructions`, despite descriptive titles in
  launcher arguments and the peer registry. The earlier record was too vague and did not check this surface.
- **Impact and priority:** P2; generic labels obscure independent tasks and force chat inspection.
- **Source owner:** core machine launch/resume naming contract; engineering handoff supplies the task name.
- **State:** open.
- **Repair link:** [BUGS.md B006](../../BUGS.md#b006-native-handoff-sessions-display-generic-read-instruction-names)
  owns the concrete native-name failure and its evidence. This debt owns the naming/acceptance convention;
  it does not create another runtime repair. Worktree names remain separately owned by
  [D-ENGINEERING-WORKTREE-NAMES](../engineering/policy/git-branching/TECH_DEBT.md#d-engineering-worktree-names-worktree-and-branch-names-must-describe-the-active-change).
- **Next action:** require concrete task names and verification of the native session list and actual
  visible terminal labels after startup/resume. Stop treating a correct launch argument or registry value
  as proof that the user sees that name.
- **Resolution condition:** new and resumed contexts visibly describe their work; the convention rejects
  generic `Read handoff...`/`Read the file...` names and preserves the exact existing context when renaming.
  Verify native names and visible terminal labels on supported hosts, linked to B006's runtime evidence.
- **Verification evidence:** user correction, two native-index matches, launcher and peer-registry titles,
  and inspected launch/resume code. Both convention correction and runtime acceptance remain outstanding.
  Repeated 2026-10-14: Tommy reports that open-CLI and handoff terminal names still do not
  explain the session purpose.

## D-MACHINE-SQLITE-OWNER-DISCOVERY: Review work has no discoverable work-item association

- **Kind:** bug. **Observed/reported:** 2026-10-21 while locating the owner of review-skill trimming,
  injected-standards selection and the unfinished big-review rename.
- **Evidence:** a read-only query of `~/.agents-state/sessions.db` found 11 work items and 93 sessions,
  no review work item, and one review-related session whose `work_item` and `role` were null. The local
  checkout's recovery helper scans native histories; current `origin/main` already documents SQLite-first
  discovery. This establishes missing association and stale helper use, not a failed SQL engine.
- **Impact and priority:** P2; owner discovery requires history searches instead of a direct work-item,
  checkout and native-session lookup.
- **Source owner:** Core machine session registration and recovery. **State:** deferred at Tommy's explicit
  request; repair separately from the review capability changes.
- **Next action:** identify why this work was not registered, reconcile its exact existing owner, and
  verify that the active discovery entry point uses the published SQLite-first implementation. Assess
  registration and migration coverage before selecting a repair; do not invent an owner association.
- **Resolution condition:** a topic query finds the actual review work item, its current worktree and
  exact native owner through SQLite, with explicit ambiguity or missing-registration results and no
  duplicate owner launched. Verify both supported hosts and retain native history only as fallback.

## D-MACHINE-STALE-MARKETPLACE-INVENTORY

Observed 2026-10-21 during review-capability delivery: `codex plugin list --json` failed because cpp-agents points to `C:/Users/TommySeery/source/repos/tj-agents/cpp.worktrees/Feature-ExplanationSkill`, which has no supported marketplace manifest. The launcher returned exit zero despite the typed CLI failure. This blocks native inventory and review; repair the configuration and exit-status propagation in their owning runtime work, then verify installed review. Keep this outside the review capability PR.

## D-MACHINE-REVIEW-LENS-MODEL

Observed 2026-10-21: the review_lens agent failed before starting because gpt-5.3-codex-spark is unsupported with this ChatGPT account. A lane_l4 read-only reviewer started successfully. Resolve by selecting a supported review model and observing a completed dispatch rather than treating spawn acceptance as execution.

## D-MACHINE-REVIEW-PREPARE-CACHE-COST

Observed 2026-10-21: review-prepare took many minutes before returning a candidate while the shared Git-private runs tree held 499 descriptors. The restricted attempt ultimately reported Access denied for its run directory, and duplicated recovery was stopped. Investigate the exact slow operation and permission boundary; candidate preparation should not stall behind unrelated historical review housekeeping. Keep this outside the review capability PR.

## D-MACHINE-WINDOWS-EMPTY-GIT-CONFIG-ENV

Observed 2026-10-21: test_stack_tiers had two Git fixture failures with missing GIT_CONFIG_VALUE_1 after unittest environment restoration. All 34 passed in a child fixture environment without inherited command-line Git configuration. The inherited environment contains empty Git config values; investigate Windows restoration of those values without changing production Git configuration or weakening any tests.

## D-MACHINE-PR-MONITOR-MERGE-STATE-NOISE

Observed 2026-10-21 during review/capability, PR #338 at 7809ddcf. Reconnecting the existing PR monitor returned a nonterminal material-transition when merge_state alternated unknown/unstable while state=open, auto_merge=false and the same two Windows checks remained pending. That creates active model work without a useful delivery transition. Investigate normalization/debouncing of transient forge merge state in a separate automation task; preserve real queue/merge/failure transitions. No monitor fix belongs in this review capability PR.

## D-MACHINE-AUTO-REVIEW-MERGE-TIMEOUT

Observed 2026-10-21 while landing review/capability, PR #338. Automatic permission approval review exceeded its deadline for a combined verification-and-merge command before executing it. A fresh read proved all exact-head checks green; base reconciliation passed; the permitted one-time retry with only the pinned merge command succeeded. Investigate review latency for bounded multi-step commands separately. Do not treat an approval timeout as evidence that an authorized merge is unsafe.

## D-MACHINE-PRIMARY-SYNC-PRESERVATION

During review/capability closeout on 2026-10-21, a safe primary fast-forward from 1bb1c130 to merged main aborted because existing tracked and untracked local notes overlap incoming files. All local edits were preserved and only the two isolated delivery worktrees were removed after cleanup proof. Handle primary sync as separate preservation/reconciliation work; do not reset or discard those notes.

## D-MACHINE-WORK-ITEM-RETIRED-PLAN-PATH

The work-item done command rejected --plan-path after the plan was deleted in merged closeout PR #341. Recovery used the frozen reviewed helper from the primary checkout containing the preserved local completion record; review/capability is now done and its owner session is finished. Reconcile plan-retirement ordering and historical plan references in separate workflow work so closing a delivered item does not depend on a retired repository file being present in the current checkout.

## D-MACHINE-PREAWARD-PLUGIN-READINESS

2026-10-21 follow-up to review/capability, handed to the separate plugin freshness/launch work described by Tommy (SYMMETRIC_PLUGIN_LAUNCH.md). Do not restore the retired expensive per-launch network wrapper as an incidental review fix.

Observed: the installed Codex engineering review entry was still kind=workflow after source PR #338 and generated publication. The native refresh installed the new kind=utility entry and shipped selected-rules helper. Current Preaward selection at infonetica/cris-preaward/.agents/plugins.json is excluded by .git/info/exclude and declares base, dotnet, engineering, infonetica, machine, react and work from tj-agents. The refreshed review_rules.py now resolves this exact selection successfully with no diagnostics, returning .NET, relevant employer and other applicable conventions. This was a standards-scope preflight, not a code review or a fresh Codex-session adoption test.

Repaired a concrete inventory blocker through the native marketplace add command: the global cpp-agents source pointed to the nonexistent tj-agents/cpp.worktrees/Feature-ExplanationSkill. The canonical tj-agents/cpp publisher has the same cpp-agents marketplace identity and was registered in its place. The prior native configuration was backed up under ~/.agents-state/repair-backups/review-preaward. Native plugin inventory now works.

Remaining automation evidence for that owner: the default reload utility read the merged native enabled list and stopped on kit@tj-agents, which is absent from the current marketplace despite not being selected by Preaward. A bounded recovery reused the shipped helper functions limited to the seven exact project-selected identities; all seven native refresh commands completed. The full native-byte verification then reported dotnet@tj-agents differs from its marketplace publisher bytes. Marketplace checkout and remote main both were 2aa887fbc590baa8e03ff6f7e762180414bf90be. No root cause inferred: check mutable local-version cache reuse, source revision changes during verification, and selected-scope handling. Do not label package freshness or already-open session adoption as verified. No updater/wrapper implementation was changed here; that separate agent owns freshness, launch symmetry and running-session behavior. Tommy should not have to execute refresh maintenance manually.
