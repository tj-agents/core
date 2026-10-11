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
- [x] 7. `persistent-workflow`'s `delivery-continuation.ps1` -> Python, verified on Linux (#186).
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
- Branch: `Refactor/LinuxPlatformInstructions`
- Base: `1bb1c130b2d1762bce07b599bb0fbb7e311c6749` (current main, containing the verified Step 7 publication)
- PR: [#191](https://github.com/tj-agents/core/pull/191), draft; update to final reviewed head and exact-head Windows/Linux CI pending
- Workflow run: `linux-platform-instructions`
- Recovery owner: this single-file legacy plan; no companion roadmap/ledger is required.
- Transfer: Step 10 pickup acknowledged in this context before deliverable writes.
- Step 10 pickup: confirmed `/home/tommy/projects/tj-agents/core` on
  `Refactor/LinuxPlatformInstructions` at `b4e6f1020b4c1edcfea8e21d6dae2ba5ebdb8a5e`; the only
  pre-existing worktree change is this plan's Step 7 closeout and Step 10 handoff checkpoint.
- Step 10 source audit is implemented across canonical instructions. All Python examples identify
  `python` for Windows and `python3` for Linux/macOS; `wt.exe` references are Windows-scoped. No
  unported skill entrypoint remains; the sole PowerShell file in a utility skill is the Windows Terminal
  UI Automation helper. Python test counterparts exist for the ported runtimes, and the retained
  `tests/delivery-continuation.tests.ps1` delegates to `tests/test_delivery_continuation.py`.
- Verification: `pwsh .agents/sync-generated.ps1 -Check` passed (509 package files); the complete `tests/`
  suite passed 1,057 tests (18 skips), and complete `.agents/hooks/tests/` suite passed 1,048 tests
  (4 skips), both with Python bytecode writes disabled on `3c93546`. Generated plugin/catalog output was restored.
  Workflow artifacts are under `.git/agent-workflow/runs/linux-platform-instructions/`.
- Review: the first docs pass reviewed `b4e6f1020b4c1edcfea8e21d6dae2ba5ebdb8a5e` through
  `838990937acc9f1d39d9799471a8b6293e159183`; its Windows command and audit-count findings were fixed.
  The remediation pass approved the source candidate at `0dbaa9adb801dd0173f1e30c5d59249574dd0a79`.
  Later plan checkpoints received separate incremental reviews. After synchronizing to current main,
  the final platform-instruction and README candidate at `69071e1a4ddaffd3bd1e20f103c1d42d901bfa57`
  was approved; exact-head Windows/Linux CI is still required.
- Step 10 slice assessment: one independent final-step PR with no stack dependency. Its initial source candidate
  was based on `b4e6f1020b4c1edcfea8e21d6dae2ba5ebdb8a5e`; before final review the branch was synchronized to
  current `origin/main` at `1bb1c130b2d1762bce07b599bb0fbb7e311c6749`. The initial reviewed source candidate at
  `0dbaa9adb801dd0173f1e30c5d59249574dd0a79` contains 32 authored files, 185 insertions and 146
  deletions; it contains platform-qualified instruction text and the plan, with no runtime code or
  generated output. The later plan-only checkpoints received separate incremental reviews; head
  `fd9dc5a1ab862bad07cc9ba0cd63e801db0f9185` was approved before main moved. Draft PR #191 was opened from
  that head. After synchronizing to current main and resolving the review findings, final platform
  instructions and README were approved at `69071e1a4ddaffd3bd1e20f103c1d42d901bfa57`; this final plan
  checkpoint is reviewed before the PR is updated and exact-head CI runs.

Step 7 [#186](https://github.com/tj-agents/core/pull/186) is delivered. Reviewed head
`66dcb2f054bdcf9a6ce67d85c3463faba3eccb21`, merge `9209cce2c4c03eeba81ec9fde88c10d1354673c5`;
exact-head Windows/Linux CI run 38090584793 passed. Causal push run 38091538187 passed both platform jobs
and regeneration. Published commit `eeb369732b34334be41fd602dadcd186ba565c19` directly parents that merge,
contains only generated output, and carries three byte-identical Python entry copies and the shared scheduler;
the retired PowerShell entries are absent. An adjacent merge is now on main; its automation remains with its owner.

Stable local checks passed: focused scheduler 40 tests (one Linux skip), source 1,046 (18 skips), hooks
1,029 (four skips), generation/catalog/harness/tier invariants. All twelve findings were repaired and the
final native/general, workflow and security pass approved the exact head with zero new findings.
Completed review audit: `.git/agent-workflow/runs/linux-delivery-continuation/completed-step7-review.md`.
Publication hashes: `.git/agent-workflow/runs/linux-delivery-continuation/publication.json`.

Actual Linux acceptance used `/tmp/step7 repaired Linux continuation café`, owner `745873ebbcc1fabef269fb96`.
The timer resumed authenticated native Codex at 22:49:56 BST on 2026-10-10, tool execution recorded nonce
`221a33428a1b4e1094c3522b78a51f48` and invocation `031160ec206c4cb6824b87402eb3c140`; duplicate suppression
kept one launch and zero failures. Cleanup inside its own systemd service removed units/link/receipt.
Both disposable schedulers are retired. On final source, the real slice timer also suppressed a pending-PR
launch, then resumed one authenticated headless publication context. Its valid waiting receipt recorded
success, one launch and zero failures. The parent joined it before retirement.

The Step 7 binding and scheduler are removed. Its complete owner/results/logs remain at
`.git/agent-workflow/runs/linux-delivery-continuation/retired-owner/`. Only the merged Step 7 local/remote
branch was deleted; the primary checkout is retained and unrelated worktrees/sessions are untouched.
This closeout rides uncommitted into the substantive Step 10 PR. The full port remains incomplete.

Linux uses the existing systemd user manager with `Linger=no`; no login-policy change or offline promise.
Native Codex 0.162.1 and Claude 2.1.296 were authenticated; pins and nonsecret profile paths preserve
credentials on disk and existing owner budgets. Actual Windows desktop scheduling, native Claude timer
acceptance and installed-host adoption remain unverified; source/CI evidence does not establish those.

Previous delivery: Step 4 [#185](https://github.com/tj-agents/core/pull/185), head
`60007dafde033708d44326d99ef5320a4e8c25a9`, merge `4c07ec1335176d0867bffcf3a84e147b989cdb41`,
exact-head run 38081790127 and causal generation run 38082687124 green. Step 5 [#181](https://github.com/tj-agents/core/pull/181)
established native Linux self-close/cleanup; receipt `/home/tommy/.agents-state/merge-cleanup/results/d8f69af9dfb740a0bcd44a5b083bccdf.json`.

The user approved requiring verify-linux with a GitHub Actions publishing exemption on 2026-10-10. GitHub
rejected that identity with HTTP 422. Protection is unchanged; a supported publishing exception must be
validated before enabling the approved rule. Do not widen the standing delivery-authorization table or
adopt unrelated automation to clear this administrator dependency. Both platform checks gate this port.

## Step 10 agent-host evidence

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents canonical skill instructions for platform-qualified interpreter examples and Windows-only helpers",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Shipped Python command examples name the Windows interpreter and the Linux/macOS interpreter; Windows Terminal commands identify Windows.",
      "source": ".agents/base/policy/plan-artifacts/SKILL.md; canonical engineering workflow and utility SKILL.md command examples; canonical machine utility SKILL.md command examples",
      "mapping": ".claude/skills adapter entries; .agents/plugins/sources.json skills and resources",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Audited 248 Markdown files across .agents, .claude and .codex. Python test counterparts cover ported runtimes; tests/delivery-continuation.tests.ps1 delegates to tests/test_delivery_continuation.py. On synchronized head 3c93546, complete source suite passed 1,057 tests (18 skips), complete hook suite passed 1,048 tests (4 skips), and generated check found 509 package files current. Exact-head Windows/Linux CI remains required; installed-host adoption was not exercised."
      }
    },
    {
      "host": "codex",
      "behavior": "Shipped Python command examples name the Windows interpreter and the Linux/macOS interpreter; Windows Terminal commands identify Windows.",
      "source": ".agents/base/policy/plan-artifacts/SKILL.md; canonical engineering workflow and utility SKILL.md command examples; canonical machine utility SKILL.md command examples",
      "mapping": ".codex/skills adapter entries; .agents/plugins/sources.json skills and resources",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Audited 248 Markdown files across .agents, .claude and .codex. Python test counterparts cover ported runtimes; tests/delivery-continuation.tests.ps1 delegates to tests/test_delivery_continuation.py. On synchronized head 3c93546, complete source suite passed 1,057 tests (18 skips), complete hook suite passed 1,048 tests (4 skips), and generated check found 509 package files current. Exact-head Windows/Linux CI remains required; installed-host adoption was not exercised."
      }
    }
  ]
}
```

## Reviews

Step 7 final review approved `66dcb2f054bdcf9a6ce67d85c3463faba3eccb21` after twelve repairs;
original pass identities, finding texts/severities and completed judgments are retained in its retired audit.
The native specialist was account-unavailable; the declared terra/medium fallback succeeded.
Step 10 requires its own fresh review/work order; never carry Step 7's watermark or binding forward.

## Next Steps

The Step 10 source audit and local checks are complete. Findings were fixed in commits `d1a7679` and
`0dbaa9a`; the source candidate's incremental review approved `0dbaa9adb801dd0173f1e30c5d59249574dd0a79`.
The later plan checkpoints were incrementally reviewed; head
`fd9dc5a1ab862bad07cc9ba0cd63e801db0f9185` was approved and published as draft PR #191. Main advanced with
a change to one overlapping canonical instruction file, so the branch was synchronized to current main at
`1bb1c130b2d1762bce07b599bb0fbb7e311c6749`. The synchronized platform instructions and README were reviewed
and approved at `69071e1a4ddaffd3bd1e20f103c1d42d901bfa57`. Review this final plan checkpoint, then push
its exact approved branch head and update draft PR #191; require its Windows/Linux CI, perform the authorized
ordinary merge, and verify only the merge's causal generated publication before plan closeout. Keep generated
`plugins/` and catalog output out of the authored PR diff.

Lane: L5, because the remaining instruction and test-reference cleanup is already decided and mechanical.
Route any necessary runtime implementation judgment through L4; keep this one Step 10 slice focused.
Read README/CODE_CONVENTIONS and skill-authoring before any relevant structural/runtime/skill decision.
Use canonical `.agents/` sources and thin host adapters. Do not author or commit generated plugins/catalog
output; refresh it for tests only. The legacy single-file goal remains the recovery owner: perform preflight
inline or without a ledger parameter when the helper expects newer ledger headers.

The full port remains authorized, one reviewed and merged PR per step, including this final Step 10 PR.
The complete source and hook suites have passed; rerun both before every stable push after a source change.
Review the exact candidate through the repository workflow, publish one stable PR, require both exact-head
platform CI checks, perform the authorized ordinary merge, verify only its causal generated publication,
and retire only its own review/binding/owner/branch.
Use a fresh durable owner if a future decision needs continuation; keep one active writer. Preserve
unrelated worktrees/sessions and do not adopt their healthy pending automation.

Scope: Step 10 platform-qualified shipped instructions and ported-test retirement/counterparts.
Remaining scope: this final step; earlier delivery evidence is recorded above.
Done when: the audited corpus and tests satisfy Step 10, one reviewed Step 10 PR is merged with both
platform CI jobs green, its causal publication is verified, and this plan has an honest closeout and
completion evidence. Maintain the canonical completion record before a full-goal complete receipt.

Actual Windows desktop acceptance, native Claude timer acceptance, installed-host adoption and the
publishing-exemption administrator dependency remain separately identified gaps. Do not enable the
approved verify-linux protection rule until its publishing dependency is resolved, or widen its scope or
standing authorization to clear a generic automation stop. Goal authorization persists; typed gates apply.
