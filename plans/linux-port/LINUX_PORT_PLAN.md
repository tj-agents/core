# Linux port of the machine utilities

## Outcome and scope

Every machine utility and launcher in core works on Linux and Windows from one Python implementation.
Each skill keeps its name; its PowerShell script is replaced by a Python script in the same skill folder,
and the `.ps1` is deleted in the same PR that ports it. No parallel copies, no renames.

Out of scope: `.agents/sync-generated.ps1` and the repository's own test and install tooling, which are
repo maintenance rather than shipped behaviour and already run under pwsh on Linux.

## Authorization

The user authorized the whole port, one PR per step, including review and merge of each step
(2026-10-05/06). Each step ends merged before the next starts. Independent steps may run in parallel
on separate branches; each still lands as its own reviewed PR.

## Decisions and evidence

- Python, not pwsh: every hook already requires Python; pwsh would be an extra Linux dependency.
- Launchers open a tab, never a window. Detect the terminal we run inside and use its own new-tab command:
  `WT_SESSION` -> the existing `wt.exe --window 0 new-tab` path with its argument escaping; `TMUX` ->
  `tmux new-window`; `KITTY_WINDOW_ID` -> `kitty @ launch --type=tab`; `KONSOLE_DBUS_WINDOW` -> Konsole
  D-Bus `newSession`. Only with no terminal detected: open a new window and print a warning.
- On POSIX the environment changes travel inside the launched command
  (`sh -c 'cd "$1" && shift && exec "$@"' sh <dir> env -u ... AGENT_CLI_TAB_TITLE=<t> <exe> <args>`), because a
  tab is started by the terminal's own process. Launch detached with stdio on `/dev/null`. Never force or
  clear `TERM` on POSIX.
- The launched CLI always gets normal colour: `NO_COLOR` is in the cleared session environment.
- Kitty reaches its window over `listen_on unix:/tmp/kitty-{kitty_pid}` with
  `allow_remote_control socket-only`, in the user's dotfiles (tomjseery/dotfiles `a908963`). Only kitty
  processes started after that change have the socket.
- Catalog digests are generated output. PRs leave them uncommitted; CI's guard rejects them (step 1).
- On Windows with no detected terminal but `wt.exe` present, keep today's `wt.exe --window 0 new-tab`:
  still a tab, in the most recently used Windows Terminal window (user decision, 2026-10-06).
- The Windows Terminal handler runs only on Windows; `WT_SESSION` reaching WSL through `WSLENV` is ignored.

## Steps and acceptance criteria

Every step: tests pass, `pwsh .agents/sync-generated.ps1 -Check` passes, reviewed, merged; the PR lists
what still needs checking on Windows.

- [x] Shared library `.agents/machine/scripts/agent_cli.py`: environment scrub, Claude/Codex executable
  discovery, standards sync, lane lookup, Windows Terminal argument escaping (#106).
- [x] Kitty remote control in dotfiles, verified from a fresh kitty.
- [x] 1. CI guard rejects committed catalog digests, so concurrent PRs stop conflicting on them (#107).
- [x] 2. `open-claude` -> `scripts/open_claude.py` with the tab handlers; SKILL.md updated; `.ps1`
  deleted. Verified by opening a real tab in kitty on this machine (#108).
- [x] 3. `handoff-claude` -> Python, then `handoff-codex` -> Python (`codex_marketplace_sync.ps1` with it).
  `engineering:handoff` works on Linux from here; verified with a real handoff.
- [x] 4. Terminal start hooks: Python terminal-profile installers refresh standards when `claude`/`codex`
  is typed, wired for Bash on Linux and PowerShell on Windows/Linux (discovering `python3`, `python`, and
  Windows `py -3` without Store stubs); the retired PowerShell launchers are deleted.
- [x] 5. `peer-cli` -> Python: `close.py` and `finish.py` (with `finish_reaper`/`session_close` ported) let
  a merged session on Linux remove its linked worktree and branch, clear its merge-cleanup obligation,
  record verified session exit, and close its own kitty/tmux/Konsole tab; `merge_cleanup_gate`'s message
  gives the per-platform Python commands. Verified by a real merge on Linux whose own tab closes itself.
  Linux can remove a worktree out from under a live cwd, so the reaper may only be needed for the tab
  close -- confirm before porting it. Then the rest of `peer-cli` (list and close in the detected
  terminal); `reap_orphans.py` stops assuming `wt.exe` is the parent.
- [x] 6. `clip` -> Python, using the platform clipboard (#125).
- [ ] 7. `persistent-workflow`'s `delivery-continuation.ps1` -> Python, verified on Linux.
- [x] 8. Tests that failed only on Linux pass: POSIX shell collapsed the Codex snapshot loader's escaped
  backslashes into NULs (now embedded as base64); a test plugin URL only git on Windows resolves; pwsh 7
  `Split` binding skipped the installer's ancestor reparse-point check (#160).
- [x] 9. CI runs the generated-tree checks and both Python suites on Linux as well as Windows
  (`verify-linux`, #162); it blocks a PR once the repository ruleset lists it as a required check,
  which the user approved requiring on 2026-10-10; enabling it awaits a supported publishing-app exception.
- [ ] 10. Shipped instructions follow `CODE_CONVENTIONS.md`'s Supported platforms: no shipped Markdown
  under `.agents/`, `.claude/` or `.codex/` tells an agent to run bare `python`, `powershell.exe`, `pwsh`
  or `wt.exe` without naming the platform (including the session exit in `merge` Step 5 and in
  `merge-docs`' Report), every unported skill says it is Windows-only, and the PowerShell test suite of
  each shipped script retires with that script's port or gains a Linux counterpart.

## Current progress
- Worktree: `/home/tommy/projects/tj-agents/core` (primary, reused sequentially)
- Branch: `Refactor/LinuxDeliveryContinuation`
- Base: `8b656fb197771916c58aea4418934aaa7648b1c0` (verified current with origin/main)
- PR: https://github.com/tj-agents/core/pull/186 (draft, Step 7)
- Workflow run: `linux-delivery-continuation`
- Recovery owner: this single-file legacy plan; no companion roadmap/ledger is required for this slice.

Fresh Step 7 pickup was acknowledged on 2026-10-10 before implementation writes. The inherited Step 4
closeout is preserved in this substantive slice. Unrelated worktrees and sessions remain untouched.

L3 investigation selected filesystem-backed systemd user services/timers for Linux. The actual manager is
reachable (degraded by unrelated units); cron and at are absent. `Linger=no`: execution survives CLI/terminal
exit while that user manager runs, with no promise after logout/offline and no login-policy change.
Native Codex 0.162.1 and Claude 2.1.296 are installed and authenticated but absent from the manager PATH.
Registration therefore pins the native host, Python, runtime and adapter; profiles remain on disk and only
nonsecret custom profile settings enter the receipt. Existing owner state and budgets must be preserved.

Specified implementation and serial remediation used bounded native L4 workers; all write leases ended.
The first frozen candidate `6acd48a166149a3eb53c2ca6c0a1f801e44d4d64` received native/general, workflow and
L2 security review. Twelve confirmed defects are retained in `reviews/Refactor-LinuxDeliveryContinuation.md`.
The resolved repairs fail closed on observation errors, preserve stale receipts in interrupted transactions,
inspect loaded fragments/drop-ins and links before mutations, verify restoration after reload before enable,
retain lexical final unit paths, and pin platform-dependent tests. Version-2 Windows receipts support verified
migration/removal but cannot establish readiness for the retired runtime. Native host commands and Windows
profile settings are bound to actual registered definitions; owner state and child budgets remain unchanged.
The two-hour outer scheduler envelope preserves the prior Windows behavior around the 900-second child limit.
Latest worker artifacts: `/tmp/step7-final-repair-result.txt`, `/tmp/step7-post-repair-result.txt` and matching logs.

Latest focused verification passed 40 tests (one inbox-Windows skip). The actual repaired Linux fixture is
`/tmp/step7 repaired Linux continuation café`, owner `745873ebbcc1fabef269fb96`. Its timer fired on
2026-10-10 at 22:49:56 BST and resumed authenticated Codex. Native tool execution recorded nonce
`221a33428a1b4e1094c3522b78a51f48`, exact cwd and systemd invocation `031160ec206c4cb6824b87402eb3c140`.
Foreground ownership prevented a duplicate; unchanged evidence retained one launch and zero failures.
Terminal cleanup then ran inside the actual owned systemd service, removing its units, enable link and
scheduler receipt while preserving owner/result/witness. Both disposable acceptance schedulers are retired.
Artifacts under `.git/agent-workflow/runs/linux-delivery-continuation/artifacts/`:
`f4859a2b2e9c4247-repaired-live-foreground-registration.log`,
`1328bce0b8c6c15e-repaired-timer-native-witness.log`,
`e871d479e6c5f918-repaired-terminal-service-cleanup.log` and
`7b2e44e8d62c1b8d-stable-focused-scheduler-check.log`.

The old PowerShell runtime is retired. Its repository-only test entry becomes a thin wrapper for the Python
suite, preserving the existing CI workflow unchanged; Linux already discovers that suite. This retains the
CI seam without changing standing delivery authorization. Generated plugins/catalog output remain uncommitted.

Scope is 13 authored paths, roughly 2,600 added/deleted lines including runtime/test retirement.
An atomic exception covers replacement, shared Stop verification, coupled entries and scheduler tests:
splitting these would ship a broken continuation contract. Step 10 and directory organization are excluded.
The latest stable source suite passed 1,046 tests (18 platform skips); the complete hook suite passed 1,029 tests (4 platform skips).
Generation/catalog/harness/tier checks passed. A prior hook run failed after a final source edit invalidated
its catalog fixtures; output was refreshed before the fresh unchanged-source suites. Repair head `eae3ce3b22e8eb496feb0a79369a4d6a7c2475fc` is published on draft PR #186.
Incremental review completed with two additional confirmed defects (foreign link traversal and legacy JSON depth).
PR #186 Windows CI failed three canonical-path fixture comparisons; one bounded serial L4 worker owns repairs.
Both findings and the Windows fixtures are repaired. The focused suite, both complete suites and generation/catalog/harness checks passed on unchanged source before the next stable push.
Fresh incremental review and both platform CI jobs still gate this delivery. Source checks do not establish Windows desktop or
installed-host acceptance.

Previous delivery: Step 4 [#185](https://github.com/tj-agents/core/pull/185), reviewed head
`60007dafde033708d44326d99ef5320a4e8c25a9`, merge `4c07ec1335176d0867bffcf3a84e147b989cdb41`,
exact-head run 38081790127 and causal generation run 38082687124 green; published base above.
Step 5 [#181](https://github.com/tj-agents/core/pull/181) also established real native Linux self-close/cleanup;
receipt `/home/tommy/.agents-state/merge-cleanup/results/d8f69af9dfb740a0bcd44a5b083bccdf.json`.
Installed-host adoption and actual Windows desktop acceptance remain unverified.

The user approved requiring verify-linux with a GitHub Actions publishing exemption on 2026-10-10. GitHub
rejected that built-in identity with HTTP 422. Protection is unchanged; an installed publishing app or a
separately validated workflow must preserve generated publication before that approved rule is enabled.
Only TJ_AGENTS_READ_TOKEN exists as a repository secret. This administrator/publishing dependency does not
block independent Step 7 work; both platform checks still gate this port's delivery.

## Agent-host coverage

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/workflows/continuation_scheduler.py and the persistent-workflow Python adapter",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Deterministic Windows ScheduledTasks or Linux systemd wakes launch a bounded fresh claude context with exact owner/receipt identity.",
      "source": ".agents/engineering/workflow/persistent-workflow/scripts/delivery_continuation.py; .agents/workflows/continuation_scheduler.py; .agents/hooks/continuation_stop.py",
      "mapping": ".claude/skills/persistent-workflow/SKILL.md; .agents/plugins/sources.json workflows/hooks resources",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Shared adapter and Stop-hook fixtures plus complete source/hook suites passed in linux-delivery-continuation artifacts. Native Claude timer acceptance and installed-host adoption remain unverified; exact-head Windows/Linux CI and Windows desktop acceptance remain pending."
      }
    },
    {
      "host": "codex",
      "behavior": "Deterministic Windows ScheduledTasks or Linux systemd wakes launch a bounded fresh codex context with exact owner/receipt identity.",
      "source": ".agents/engineering/workflow/persistent-workflow/scripts/delivery_continuation.py; .agents/workflows/continuation_scheduler.py; .agents/hooks/continuation_stop.py",
      "mapping": ".codex/skills/persistent-workflow/SKILL.md; .agents/plugins/sources.json workflows/hooks resources",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Complete source/hook suites and shared adapter fixtures passed. Actual repaired systemd timer resumed authenticated Codex and recorded a native tool checkpoint, duplicate suppression and cleanup inside the owned service; installed-host adoption and Windows desktop acceptance remain unverified. Exact-head Windows/Linux CI remains pending."
      }
    }
  ]
}
```

## Reviews

The first full pass at `6acd48a166149a3eb53c2ca6c0a1f801e44d4d64` requested changes on ten confirmed
findings. Serial repair and focused verification are complete; the original pass identity/text/severities
remain frozen. Both full suites passed. Repairs are committed at `eae3ce3b22e8eb496feb0a79369a4d6a7c2475fc`;
fresh incremental review completed with two security findings. Native/general and workflow found no defects.
Exact-head Windows job 114323438386/run 38089699252 failed three short/long-path fixture comparisons.
The serial L4 repair lease ended. Filesystem-resolved timer targets and depth-5 legacy JSON now have regression coverage; fixtures use canonical paths.
Both complete suites passed; a fresh incremental pass follows the repair commit. Original frozen pass text and judgments are preserved. Work order: `reviews/Refactor-LinuxDeliveryContinuation.md`.
The native specialist was rejected by the account during Step 4; the declared terra/medium fallback succeeded.
Step 4's retired work order audit is `.git/agent-workflow/runs/linux-terminal-start-hooks/completed-step4-review.md`.

## Next Steps

Implementation and final actual Linux acceptance are complete; both disposable schedulers are retired.
All twelve findings and the Windows fixture failure are repaired; focused and complete suites passed.
Commit only the authored repairs/checkpoint, freeze the next delta from the completed watermark, publish the
stable candidate to PR #186 and refresh its existing owner/binding. Run fresh independent incremental review
and require both exact-head platform CI jobs before the authorized ordinary merge. Verify causal post-merge
generation, retire only this slice's binding/owner, preserve closeout in this plan and launch one fresh
Step 10 successor from the published base. The parent retains delivery ownership until launch.

Scope: current slice only; full plan remains incomplete.
Current slice: Step 7 Python delivery continuation, including actual Linux scheduler acceptance.
Remaining scope: Step 10, handed to a fresh session after Step 7 delivery.
Done when: one reviewed Step 7 PR is merged with both Windows/Linux CI green, its causal package publication
verified, actual Linux continuation evidence recorded, and the Step 10 successor launched.

The whole port remains authorized, one reviewed and merged PR per step. Keep this single-file legacy plan as
the recovery owner; preserve unrelated checkouts and sessions. Both complete tests/ and .agents/hooks/tests/
suites must pass before each stable push, including repairs. Refresh generated output for tests but never
commit plugins/* or catalog output. Use the repository implementation/review/delivery workflow, record
current-head source coverage separately from installed-host/Windows desktop evidence, and retire only this
slice's binding/owner after its terminal delivery. Then launch the Step 10 successor from the current base.

Do not enable the approved verify-linux protection rule until its publishing dependency is resolved; do not
widen the protection requirement or standing delivery-authorization table to clear a generic automation stop.
Goal authorization persists; typed delivery gates apply.
