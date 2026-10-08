# Reaper startup acknowledgement and cancellation protocol

Design artifact for [GOAL.md](GOAL.md). Lane: L1 design, implemented at L4. Revised after the
independent readiness review (2026-10-07); its two blocking findings — an unacknowledged acceptance that
could close the host with no armed reaper, and a missing launcher testability seam — are incorporated
below, along with its should-fix items.

## Reproduced defect

`plans/reaper-startup-handshake/GOAL.md` describes the incident; it was reproduced on this branch's
source (head f9f5183) with disposable fixtures on 2026-10-07: `finish.ps1` with
`AGENT_FINISH_SPAWN_TIMEOUT_SECONDS=0.05` against a scratch repo/worktree/receipt and a fake `codex.exe`
host threw `the reaper did not confirm it started within 0.05 seconds; nothing was closed`, left the
session open — and the late reaper, once the fake host tree was killed, removed the worktree anyway.
The launcher's startup wait is observation only: the detached reaper is cleanup-capable from birth, so
a spawn that misses the deadline leaves an armed process the launcher has already disowned.

## Design position

Invert the default: the reaper is **inert until explicitly accepted, and the host is closed only after
the reaper acknowledges that acceptance**. The handshake is three-phase — started (reaper), accepted
(launcher), armed (reaper) — with every phase identity-checked against this exact invocation and every
wait bounded. A launcher that aborts writes an explicit cancellation that always beats a late start, and
the reaper re-checks cancellation immediately before its first destructive action. Raising the
five-second wait alone is explicitly not the repair; deadlines are liveness knobs, not safety boundaries.

A key environmental fact (verified by the readiness review's probe on both editions): a process created
through `Invoke-CimMethod Win32_Process Create` does **not** inherit the caller's environment. Every
bound the reaper must honor therefore travels on its command line, never via environment variables.

The close path (`close.ps1` / `-CloseOnly`) is out of scope: its observer never removes worktrees or
branches, and its obligation-clearing logic is owned by the active Fix/TransferredCleanupObligation
work. `close.ps1` is untouched; `Start-DetachedReaper` keeps a falsy failure return so close.ps1's
`-not (...)` check still holds. The analogous disowned-observer window in the close path (a late
CloseOnly observer clearing obligations after a failed close) is recorded as that owner's defect in
RESULT.md, not repaired here.

## Signal channel

All signals live beside the per-invocation result file, whose GUID name is the invocation nonce — it is
generated in-process by the launcher and appears only on the spawned reaper's command line:

- `<result>.json` — reaper-owned: started record, then one terminal record (existing channel). The
  **initial started write is an exclusive create** (`[IO.File]::Move` onto a path that must not exist;
  no pre-delete): when duplicate reapers race, exactly one owns the channel and the loser exits
  immediately, touching nothing and overwriting nothing. Terminal writes by the owning reaper replace
  the file with a bounded retry (3 × 100 ms) around the delete-then-move, since evidence polls may
  briefly hold the file open.
- `<result>.json.accepted` — launcher-owned acceptance:
  `{ accepted: epoch, reaper_pid, reaper_started_at, host_pid }`, echoing the identity the launcher
  validated from the started record.
- `<result>.json.cancelled` — launcher-owned cancellation: `{ cancelled: epoch, reason }`. Counts by
  existence alone.
- `<result>.json.armed` — reaper-owned acknowledgement: `{ armed: epoch, reaper_pid }`.

All writes are atomic (temp + move, the existing `Save-ResultRecord` pattern); the launcher gets its own
atomic writer that also creates `merge-cleanup/results` when no reaper ever ran. The started record
gains identity fields: `reaper_pid` (the reaper's own `$PID`) and `reaper_started_at` (epoch double via
the existing `ConvertTo-UnixTime`; never a serialized DateTime, which round-trips differently across
editions), alongside the existing `started`, `host_pid`, `worktree` echoes.

Numeric fields cross the JSON boundary as Int32/Int64/Double/Decimal depending on edition; every
consumer compares through culture-invariant numeric coercion (a `ConvertTo-FiniteDouble`-style helper
returning `$null` on failure), never `-is [int]`/`-is [double]` type tests or `.Equals`.

## Launcher state machine (finish.ps1, cleanup mode)

The spawn-confirm-accept-armed-cancel flow lives in a named function (`Invoke-ReaperHandshake`) defined
before the top-level script flow, receiving the state directory, resolved worktree, receipt, own host,
parent shell, attachment, and result path, and taking the spawn/close operations' collaborators as
overridable functions (`Start-DetachedReaper`, `Invoke-SessionClose` resolved dynamically), so
dot-sourced tests can drive it deterministically. States:

1. **preflight** — existing fresh receipt, head/branch match, host identity, attachment and
   shared-session checks, unchanged and still before any spawn.
2. **spawn** — capture the spawn epoch **before** the spawn attempt. `Start-DetachedReaper` now returns
   `$false` on failure or a hashtable always carrying both keys:
   `@{ ProcessId = <int or $null>; Method = 'cim'|'schtasks' }` (CIM's `Create` returns ProcessId as
   UInt32, converted outside the try whose catch falls through to schtasks, so a conversion error cannot
   cause a duplicate spawn; the schtasks path writes `ProcessId = $null` explicitly). The CIM call gets
   `-OperationTimeoutSec`. The caller checks `-is [hashtable]` before member access (StrictMode). A
   reported failure may still have created a process, so a spawn failure goes through **cancel**, not a
   bare throw.
3. **confirm-wait** — poll `<result>.json` until `AGENT_FINISH_SPAWN_TIMEOUT_SECONDS` (default raised
   5 → 15 s, matching close.ps1; read by the launcher, whose environment does come from the session). A
   parsed record is validated:
   - `started` numeric and not earlier than the spawn epoch minus 2 s skew;
   - `host_pid` equals this invocation's own host pid, `worktree` normalizes equal to the target;
   - `reaper_pid` a positive integer, equal to the spawn-returned pid when one is known;
   - `reaper_started_at` numeric and positive.
   An unparsable file keeps polling (it may be mid-write). Valid → **accept**. Complete-but-invalid
   (foreign/stale identity) → **cancel** immediately. Deadline → **cancel**.
4. **accept** — re-run the receipt head/branch match and `Test-OtherLiveSessionClaimsWorktree`
   immediately before acceptance (the preflight-to-acceptance gap now includes the spawn and
   confirm-wait, so the checks are refreshed); on failure → **cancel**. Then atomically write
   `.accepted` echoing the validated `reaper_pid` and `reaper_started_at`.
5. **armed-wait** — poll ≤ `AGENT_FINISH_ARMED_TIMEOUT_SECONDS` (launcher-side env, default 10 s) for
   `.armed` with `reaper_pid` matching the accepted pid. The reaper
   polls at 100 ms, so an armed acknowledgement normally lands within a second; absence means the reaper
   exited `not-accepted`, died after starting, or never saw the acceptance — in every case the host must
   not close → **cancel**. Present and matching → `Invoke-SessionClose` wrapped in try/catch: an
   exception after arming writes `.cancelled` (the reaper re-checks it before removal) and rethrows.
6. **cancel** — atomically write `.cancelled` with the reason; when a started record exists, poll
   briefly (~1 s) for the reaper's own terminal record first, so the self-recorded `cancelled` evidence
   survives; then the best-effort kill sweep: query `Win32_Process` with WQL
   `Name = 'powershell.exe' AND CommandLine LIKE '%<guid>%'` (the 'N'-format GUID is hex-only, so no
   LIKE wildcards), exclude `$PID`, and stop each match with `-ErrorAction SilentlyContinue` only when
   its command line carries both the invocation GUID and the `finish_reaper.ps1` token — the GUID alone
   also matches a human-launched process quoting it (an operator tailing the result file), and a
   record-supplied start-time filter would trust the very record whose mismatch caused the cancel;
   throw naming the reason, keeping the literal `nothing was closed` phrasing the merge skill's
   guidance keys on. With no started record, skip the evidence poll — nothing can ever appear. Host,
   worktree and branch are untouched in every cancel path.

## Reaper state machine (finish_reaper.ps1, cleanup mode only)

1. **started** — write the started record immediately via exclusive create (`reaper_pid`,
   `reaper_started_at` included). A failed exclusive create means a sibling owns this invocation: exit
   at once, touching nothing.
2. **accept-wait** — poll every 100 ms up to the `-AcceptTimeoutSeconds` parameter (passed on the
   command line by the launcher: the session's `AGENT_FINISH_ACCEPT_TIMEOUT_SECONDS` or default 60 s;
   the parameter is authoritative because CIM children inherit no environment):
   - `.cancelled` exists → terminal `status = 'cancelled'`, exit. Checked before `.accepted` each
     iteration, so a cancellation always beats a racing acceptance.
   - `.accepted` parses with positive `reaper_pid` equal to own `$PID` and a `reaper_started_at` that
     parses and matches own start within 2 s → write `.armed`, proceed. An absent or unparsable
     `reaper_started_at` never arms — the launcher always echoes the value it validated.
   - `.accepted` parses with a positive pid that is **not** own `$PID` → exit without writing the result
     file (the accepted reaper owns the channel).
   - `.accepted` present but unparsable or incomplete → keep polling (mid-write).
   - deadline → terminal `status = 'not-accepted'`, exit. Covers a launcher that crashed or was killed
     after spawning.
   The accept-wait uses file polling only — it must not call `Test-ProcessExited`, which the
   transferred-obligation owner is reworking.
3. **host-wait and cleanup** — the existing bounded host/parent wait (`timeout` on expiry), then —
   **immediately before `git worktree remove`** — one final `.cancelled` existence check: present →
   terminal `status = 'cancelled'`, exit with nothing touched. Otherwise the existing cleanup proceeds
   unchanged: `git worktree remove` without `--force`, branch-tip protection (`branch-preserved`),
   obligation clearing on full success.

`-CloseOnly` skips the accept gate entirely; its startup record and downstream flow are unchanged,
except that its host-wait expiry and failure records now keep the close shape (`session_id`,
`host_started_at`, no reaper identity) that the shared code would otherwise have replaced with the
cleanup shape.

## Race coverage

| Race | Resolution |
|---|---|
| started lands just after the launcher deadline | launcher wrote `.cancelled` first; reaper sees it in accept-wait and exits `cancelled` |
| started lands just before the deadline | launcher validates, re-checks, accepts; reaper arms; normal closeout |
| launcher exits/dies between spawn and decision | no acceptance ever appears; reaper exits `not-accepted` at its command-line bound |
| launcher writes `.accepted` after the reaper's accept deadline (slow CIM return, machine sleep) | no `.armed` appears; launcher cancels at armed-wait; host stays open |
| reaper dies between started and acceptance | no `.armed`; launcher cancels at armed-wait; host stays open |
| launcher dies/throws after `.accepted` (close failure) | catch writes `.cancelled` and rethrows; reaper's pre-removal re-check aborts cleanup, and a host-wait expiry with a cancellation on disk records `cancelled`, not `timeout`; if the launcher died uncatchably, the armed reaper waits on a host that is still running — a live host holds its cwd, and `AGENT_FINISH_REAPER_TIMEOUT_SECONDS` bounds the wait (worktree intact). Residual: a user closing that host inside the window lets the armed reaper clean up a receipt-proven worktree without `--force`, with dirty-work and branch-tip protections still active |
| CIM created a process but reported failure, schtasks also spawned | the started exclusive create picks one owner; the sibling exits instantly; the launcher accepts exactly the pid it validated; a sibling that somehow reads a foreign-pid acceptance exits inert; the accepted reaper's terminal evidence can no longer be overwritten |
| stale/foreign record at the result path | fresh GUID path makes reuse impossible; validation additionally requires the host pid/worktree echo, recent `started`, positive `reaper_started_at`, and the spawn pid when known |
| pid reuse between acceptance and arming | acceptance echoes `reaper_pid` + `reaper_started_at`; a reused pid fails the start-time match (and an impostor would also have to be a duplicate reaper with identical arguments — harmless by construction) |
| kill sweep vs. bystanders | match requires the invocation GUID in the command line plus a start-time re-verification; the sweep is best-effort (a schtasks-launched or elevated reaper may resist it) — safety rests on the absent acceptance, never on the kill |
| reaper killed by sweep mid-write | it has made no repository change before arming; only a status record can be lost |

## Test plan (tests/finish.tests.ps1, FinishOnly section; both editions via tests/test_finish.py)

Fixture safety: every new scenario that runs `finish.ps1` end-to-end uses a uniquely named fake host
(`agent-finish-test.exe`, a copied `cmd.exe`) with `AGENT_CLI_HOST_NAMES=agent-finish-test` scoped to the
scenario — never the real `codex`/`claude` stems — so no interleaving can resolve the real session's
host. `AGENT_FINISH_CLOSE_MODE=process` keeps closes away from Windows Terminal. All fixtures are
disposable scratch repos; numeric env values use culture-safe literals (`'0'`, integers) because
`Get-EnvDouble` parses with the current culture.

New scenarios:

- **Incident regression (fails on prior source):** e2e finish with `AGENT_FINISH_SPAWN_TIMEOUT_SECONDS='0'`
  and a wrapper that keeps the fake host alive after finish.ps1 exits (batch file + ping, stderr and exit
  code captured to files) → launcher throws the cancellation error; fake host still alive; kill the host
  tree; completion is detected by **no `powershell.exe` whose command line contains the scenario's unique
  state directory remaining** (valid on both prior and repaired code), then assert the worktree and
  branch still exist and no acceptance file was written.
- **Launcher handshake units** (dot-sourced, driving `Invoke-ReaperHandshake` with overridden
  `Start-DetachedReaper`/`Invoke-SessionClose`, records built by round-tripping JSON text, never literal
  objects):
  - spawn returns `$false` → `.cancelled` written, `.accepted` absent, close never called, throw;
  - started record appears after K polls, within deadline → accepted; close called only after a test
    `.armed` is placed; `.accepted` content echoes the record identity;
  - complete-but-invalid record (wrong `host_pid`, wrong `worktree`, stale `started`, missing
    `reaper_pid`, pid mismatch against a known spawn pid) → immediate cancel, close never called;
  - valid acceptance but no `.armed` within bound → cancel, close never called.
- **Cancel after started (the tie race):** direct reaper, dead host; write `.cancelled` after the
  started record exists → terminal `cancelled`, nothing removed. Accept a `failed` record carrying the
  cancel evidence only if the delete-retry note below proves insufficient.
- **Launcher exit before accept:** direct reaper with `-AcceptTimeoutSeconds 1`, dead host, no
  acceptance → terminal `not-accepted`, nothing removed.
- **Foreign acceptance:** `.accepted` naming a different pid → reaper exits, no cleanup, result file
  still holds only the started record.
- **Duplicate started (exclusive create):** pre-place a started record, start a reaper → it exits at
  once, the pre-placed record survives byte-identical, nothing removed.
- **Sweep decoy:** during a cancel scenario, a decoy `powershell.exe` whose command line carries the
  scenario state directory but a different GUID must survive the sweep.
- **Refusal evidence:** the shared-claims refusal (existing predicate test) gains an e2e assertion that
  a refused finish leaves the results directory empty.
- **Accepted normal closeout:** existing e2e now exercises the full three-phase handshake and still ends
  `succeeded` with the worktree, branch and obligation gone, plus `.accepted` and `.armed` present.

Adapted scenarios: every existing direct reaper invocation (timeout, branch-preserve, parent-shell wait,
prefix sibling, duplicate obligations, job-breakaway) gains a `Grant-ReaperAcceptance` helper that waits
for the started record, asserts its `reaper_pid` equals the pid `Start-Process` returned, and writes
`.accepted` via temp + move; scenarios then also wait for `.armed` where arming matters. All existing
assertions are retained. Existing preflight-refusal, attachment, registry and close-only scenarios are
untouched. Keep the FinishOnly wall-clock under tests/test_finish.py's 480 s per-run budget: new direct
reaper scenarios use second-scale bounds.

Edition coverage note: every spawned launcher/reaper process is `powershell.exe` by construction (the
hard-coded reaper command line), so the pwsh pass exercises the dot-sourced units; record this limit in
RESULT.md.

## Source overlap

Fix/TransferredCleanupObligation (uncommitted, separate owner) edits `Find-ObligationPaths`,
`Test-ProcessExited`, and CloseOnly obligation clearing in finish_reaper.ps1, plus appends
`-TransferredOnlyTests` scenarios to the test file. This repair touches none of those functions, none
of the obligation semantics, and no CloseOnly control flow; the one CloseOnly-visible change is the
record-shape repair stated in the `-CloseOnly` paragraph above. Its reaper edits are the started
record, the accept-gate insertion between the startup record
and the wait loop, the pre-removal cancel re-check, the terminal-record helper, the param block
(`-AcceptTimeoutSeconds`), and the help block — the last two are the likely textual conflicts. One
non-textual conflict to reconcile at that owner's PR: any cleanup-mode reaper its tests start directly
will block in accept-wait and needs `Grant-ReaperAcceptance` (its CloseOnly observers are unaffected).
Tests for this repair live inside the FinishOnly block.

## Decisions taken

- Acceptance gate applies to cleanup mode only; CloseOnly retains the started-only confirmation because
  its observer is not cleanup-capable in the worktree/branch sense and its obligation semantics have
  another active owner. The late-CloseOnly-observer obligation window is recorded for that owner.
- Three-phase handshake (started/accepted/armed) rather than two: acceptance alone cannot prove an armed
  reaper exists, because the reaper's accept deadline is enforced in another process and the host close
  is irreversible.
- `AGENT_FINISH_SPAWN_TIMEOUT_SECONDS` default moves 5 → 15 s (matching close.ps1), reducing spurious
  cancellations; correctness comes from the handshake alone.
- The accept bound travels as the `-AcceptTimeoutSeconds` command-line parameter (launcher-side env
  override `AGENT_FINISH_ACCEPT_TIMEOUT_SECONDS`, default 60 s, clamped to at least the spawn bound plus
  30 s and at least 60 s, formatted culture-invariantly); CIM children inherit no environment. The
  accept-gate terminal records carry `reaper_pid`/`reaper_started_at` so sweeps and post-mortems keep
  the reaper's identity after the started record is replaced.
- No new scripts, no change to the documented argument-free invocation, no harness-permission changes
  (verified: `.agents/plugins/harness/machine.json` pins the exact existing command).
- Residual risks accepted (for RESULT.md): armed reaper dying before cleanup leaves the obligation to
  surface the leak; the kill sweep is best-effort by design; pwsh coverage is unit-level; the
  late-CloseOnly-observer window belongs to Fix/TransferredCleanupObligation.
