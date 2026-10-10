# Code review — Feature/HandoffCodexPython

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `dcf86bb4791dc66d33defa8fbeef7050112e6975`  `(2026-10-10)`
**Judgment:** `approved`

## Review pass — 2026-10-07 — full

**Candidate base:** `61d4920477a313528f855babd2e4ee4ccdf3d8f6`
**Candidate head:** `a8da4019aab7d17151e1729ab76c34a3bac6d0ad`
**Candidate branch:** `Feature/HandoffCodexPython`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:7ee2d8d23b5f3625333f8285a8a38a90279c7af09cad9ea5b7f79bac1dbb7ac5` `(24 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/F9JTZ2T3-gA9i2dXGVo9Rf/taRYyeALovepw-bSajLydp`
**Candidate bundle identity:** `sha256:716620064cb068377982c6868dd9996aa39be5f0cdf0772ab60bd944db612548`
**Work-order path:** `reviews/Feature-HandoffCodexPython.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

Native layer: Claude Code `code-review` (high), 10 findings verified by the parent.

### Findings

- [x] **X1 — MEDIUM — native** — `.agents/machine/scripts/codex-profile.ps1:11` — `python3` is tried first, which on Windows is usually the Store alias stub, so every typed `codex` skips the refresh. Prefer `python` on Windows, `python3` elsewhere, and skip the WindowsApps alias. Fixed in `bdfd754`: `Find-CodexPython` orders `python`/`py -3` on Windows, `python3`/`python` elsewhere, and skips any `\WindowsApps\` candidate.
- [x] **X2 — LOW — native** — `.agents/machine/scripts/codex_marketplace_sync.py:60` — The hook-trust helper's stderr (its failure reason) is captured and dropped. Pass it through. Fixed in `bdfd754`.
- [x] **X3 — LOW — native** — `.agents/machine/utility/handoff-codex/SKILL.md:30` — Says the refresh and hook trust never block the launch; a sync failure refuses the launch (as the .ps1 did). Correct the doc. Fixed in `bdfd754`.
- [x] **X4 — MEDIUM — native** — `.agents/machine/scripts/agent_cli.py:137` — A native `codex` on PATH (distro, AUR, brew, standalone installer) is never a candidate, so non-npm installs cannot hand off. Add a native (non-script) `codex` on PATH as a candidate. Fixed in `bdfd754`: `shim` itself and its realpath are added as candidates when not a `#!` script (POSIX) / not `.exe` is excluded (Windows) is satisfied by the native check.
- [x] **X5 — LOW — native** — `.agents/machine/scripts/codex_marketplace_sync.py:47` — `codex plugin` steps have no per-step bound. Give each step its own timeout, as claude_standards_sync.py does, reporting a SyncError. Fixed in `bdfd754`.
- [x] **X6 — LOW — native** — `.agents/machine/scripts/codex_marketplace_sync.py:53` — JSON parsed from stdout+stderr joined; a stderr warning breaks a good sync. Parse stdout only. Fixed in `bdfd754`.
- [x] **X7 — LOW — native** — `.agents/machine/scripts/codex_marketplace_sync.py:134` — No null guard on `installed` entries and a missing `pluginId` raises KeyError. Skip malformed entries as the .ps1 did. Fixed in `bdfd754`.
- [x] **X8 — LOW — native** — `.agents/machine/scripts/codex_marketplace_sync.py:27` — `codex_command` and `apply_harness_permissions` duplicate codex_hook_trust.py and claude_standards_sync.py. Import them. Fixed in `bdfd754`: `codex_marketplace_sync.py` now imports `codex_hook_trust.command` and `claude_standards_sync.apply_harness_permissions`.
- [x] **X9 — LOW — native** — `.agents/machine/utility/handoff-codex/SKILL.md:135` — "Never a new window" is false when no terminal is detected (launch_tab falls back with a warning), and the tab claim is stated twice. State it once, accurately, consistently across the three launcher SKILL.md files. Fixed in `bdfd754`: one accurate tab-opening sentence (detected terminal, or a new window with a warning, or a `wt.exe` tab in the last Windows Terminal window) replaces the duplicate statements in handoff-codex, handoff-claude and open-claude.
- [x] **X10 — LOW — native** — `.agents/machine/scripts/codex-profile.ps1:16` — Passing npm's codex.ps1 shim makes each sync step a pwsh cold start. Let the sync resolve the native executable when `--codex` is a shim or omitted. Fixed in `bdfd754`: `--codex` is optional; omitted or shim-shaped, `codex_marketplace_sync.py` resolves the native executable itself via `agent_cli.resolve_codex_executable()`.

### Additional required fixes landed after this pass (not X-numbered; found by a direction-change session and confirmed by Tommy, plus a self-reported LAUNCHER_RE gap)

- [x] `agent_cli.codex_candidate_paths()` found Codex only through `shutil.which('codex')`; a session launched from a desktop entry (e.g. kitty) has no npm global `bin` on PATH, so it found nothing. Fixed in `8a44a5a`: falls back to `npm config get prefix` + `bin/codex` on POSIX, mirroring the direct `~/.local/bin/claude` check.
- [x] handoff-codex's SKILL.md claim that the launcher only spawns a Windows Terminal tab — already corrected by X9's `bdfd754` fix; verified no stale "only spawns a Windows Terminal tab" / "never a new window" text remains across the three launcher SKILL.md files.
- [x] `merge_cleanup_gate.py`'s `LAUNCHER_RE` matched only the retired `launch-codex.ps1`/`launch-claude.ps1` names, so a handoff through this PR's own `launch_codex.py`/`launch_claude.py` never stamped the merge-cleanup transfer. Fixed in `8a44a5a`, with a regression test.

## Review pass — 2026-10-09 — incremental

**Candidate base:** `49c618c5204140629df7a78dd7f8e47a0bfe749f` (origin/main; the prior watermark `a8da4019a` is still an
ancestor of HEAD, but ~40 unrelated `main`-merge commits sit between it and HEAD, so a literal
`watermark..HEAD` diff pulls in 153 paths outside this feature's own scope. Reviewed the branch's actual
diff against current `main` instead — 27 paths, matching `git diff origin/main...HEAD --stat`.)
**Candidate head:** `cb2193b66f6772cc7d101ccf34d30aba5bed71f0`
**Candidate branch:** `Feature/HandoffCodexPython`
**Candidate scope:** `all`
**Work-order path:** `reviews/Feature-HandoffCodexPython.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Native layer: Claude Code `code-review` (high) over the branch-vs-main diff, 1 finding, confirmed and fixed
(recorded above, under "Additional required fixes"). No other correctness, reuse, simplification,
efficiency, or convention issues cleared the confirm/plausible bar.

### CI failure found and fixed after this pass

- [x] PR #137's `verify` (Windows) job failed on first push after this review (run `37986734663`, job
  `114010473718`, step "Codex terminal profile tests"): `codex_marketplace_sync.py` raised "Codex plugin
  sync returned invalid JSON: plugin marketplace upgrade --json". Root cause: the test's C# relay stub
  spawns `cmd.exe` without `/d`, so GitHub's windows-latest `\AutoRun` registry value runs first and its
  output lands ahead of the batch dispatch's own JSON on stdout. Fixed in `28fbce2` (adds `/d`); also
  widened the parse-failure message to quote the unparseable text for any future repeat.
- [x] `verify` failed again after the `/d` fix (run `37988870513`/`37989927676`/`38007331240`), same
  symptom, same root cause class: the batch had no `@echo off`, so cmd echoed every executed line onto
  stdout ahead of the real JSON (`9f66024`); then the call-order comparison itself failed on a trailing
  space cmd's own echo adds to the three batch-served calls regardless of `%*` vs explicit `%1`-`%4`
  tokens (`763c4cc`, confirmed not a token-extraction issue), fixed by trimming the logged calls before
  comparison since production code never goes through cmd.exe either way (`6fb070e`). `verify` passed
  green on run `38007881871` (23m41s), alongside `verify-linux` and `guard`.

## Review pass — 2026-10-10 — incremental

**Candidate base:** `28fbce2d0874152b9ec0ffcc55f25465a7216bd5` (the prior pass's own watermark; no further
unrelated `main` merges landed in between)
**Candidate head:** `dcf86bb4791dc66d33defa8fbeef7050112e6975`
**Candidate branch:** `Feature/HandoffCodexPython`
**Candidate scope:** `all`
**Work-order path:** `reviews/Feature-HandoffCodexPython.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Native layer: Claude Code `code-review` (high) over the full branch-vs-main diff (requested when the merge
gate refused a stale-review merge attempt at `6fb070e`). 10 findings, all confirmed or plausible against
the real code; all 10 addressed in `dcf86bb`:

- [x] `agent_recovery.py`'s `_sync_codex()` still referenced the deleted `codex_marketplace_sync.ps1` via
  pwsh, silently disabling the Windows Codex-resume standards sync. Now loads the ported Python module
  in-process via the file's own `_load()` helper, with new tests (`test_sync_codex_*`).
- [x] `invoke_codex_sync_command`/`invoke_codex_hook_trust` didn't catch `OSError`, so a bad executable
  path crashed with a raw traceback instead of a clean `SyncError`; `invoke_codex_hook_trust` also had no
  outer timeout, unlike every other codex call in the file. Both fixed, with new tests.
- [x] `is_codex_shim()`'s OSError fallback returned `False` (trust as native), inverting
  `agent_cli._is_script`'s own fail-safe `True` (re-resolve). Matched the two; updated the one test that
  pinned the old (wrong) polarity, and the two `MainCliTests` fixtures that relied on a nonexistent
  placeholder path standing in for "native, use as-is."
- [x] `sync_codex_standards()` assumed codex's JSON was always an object; a bare array/scalar raised
  `AttributeError` instead of a clean `SyncError`. `invoke_codex_sync_command` now validates the shape.
- [x] `launch_codex.py` checked the `--frontier`/`--lane` conflict before `--lane L7`, reversing the
  retired `.ps1`'s order and making the adjacent comment false. L7 now wins, with a regression test for
  `--lane L7 --frontier` together.
- [x] `agent_cli.npm_global_prefix()` decoded npm's output with no explicit encoding, unlike every sibling
  call this branch adds. Pinned to `utf-8`/`replace`.
- [x] `merge_cleanup_gate.py`'s `LAUNCHER_RE` and `EXEMPT_PY_SCRIPTS` hand-duplicated the launcher names
  and had already drifted once within this PR (the earlier fix above). Both now derive from one shared
  `LAUNCHER_PY_SCRIPTS`/`LAUNCHER_PS1_SCRIPTS` source; full hooks suite re-verified green after.
- [x] `codex-profile.ps1`'s `Find-CodexPython` addition is a real `CODE_CONVENTIONS.md` violation (new
  behaviour on a PowerShell script still awaiting its port). Recorded as tracked tech debt in
  `.agents/machine/TECH_DEBT.md` rather than attempted as unscoped work here; resolves with plan step 4.
- [x] `tests/codex-terminal-profile.tests.ps1`'s blanket `.Trim()` (landed in the CI-fix pass above)
  slightly widens what the call-order assertion can catch. Accepted as-is: the comment at the call site
  already documents the tradeoff, and production code never goes through cmd.exe either way.

Full `tests/` (885) and `.agents/hooks/tests/` (985) suites green locally after every fix in this pass.
