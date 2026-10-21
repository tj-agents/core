# Symmetric plugin currency for Claude and Codex

Proposed 2026-10-21. Implemented on PR #328; awaiting review.

## Problem

core#320 and 40cab461 (2026-10-19) removed the `claude`/`codex` profile launchers because they ran a
30–98 s network refresh (71 subprocesses) before every start. The replacement made the hosts diverge:

- Claude: native marketplace auto-update plus `/reload-plugins` in a session.
- Codex: only the hourly `plugin_autoupdate.py`, which skips Codex while any Codex session runs.
- Handoff/open launchers perform no refresh.

## Requirements (Tommy)

- No background job or poller. Update only when a publish event has actually happened; otherwise run nothing.
- New launch: a script, no model, no tokens. Never the old ~90 s.
- No per-prompt hooks. In a running session, `reload-plugins` is a utility the agent runs on its own
  judgement whenever it thinks plugins are outdated, without asking.
- Same command names and behaviour on both hosts; only the native step underneath differs.

## Design

1. Event source: publisher repositories already post a hint to the machine's ntfy topic on merge
   (`machine_events.py`, `configure_publishers`). Keep the publish side; drop the long-running subscriber.
2. Launch check, one shared script behind the terminal `claude`/`codex` functions and the
   `handoff-*`/`open-*` launchers: a single non-blocking ntfy poll for events since the stored cursor.
   - No events: start the CLI immediately.
   - Events: update only the named repositories' marketplaces and enabled plugins, in parallel, advance
     the cursor, then start.
   - Poll fails (offline): start anyway, keep the cursor.
3. `reload-plugins` runs the same check-and-update for a running session. The agent may run it whenever it
   judges plugins outdated (a skill missing or behaving like an old version, after merging a plugin PR).
   Then Claude needs native `/reload-plugins`; Codex resumes the conversation in a fresh process.
4. Codex sessions bind their own plugin generation, so an update never waits for every Codex session to
   close.
5. Retire the hourly scheduled task and the ntfy subscriber service. Keep Claude's native auto-update as a
   harmless extra.
6. In-process subagents share their parent's plugins; out of scope.

## Acceptance

- No-event launch: one HTTP poll, no other subprocess; measured overhead well under 1 s.
- After a merge, the next `claude` and `codex` launch updates only that repository, with Codex sessions open.
- No hook runs on any prompt.

## Progress

Delivery: on PR #328 (`Remove/RollingPlugins`), per Tommy. `machine_events.py` and `configure_publishers` exist only on
main (#327), which #328 predates, so main was merged in first; that also clears #328's merge conflict
(`.agents/plugins/harness/machine.json`).

- [x] Merge main; resolve the harness manifest conflict.
- [x] `launch_check.py`: one poll, per-host applied cursor, update only named repositories, both hosts in parallel.
- [x] Codex: hook snapshots taken before an upgrade replace the blanket running-session deferral.
- [x] `startup_binding.py` runs the check, so `handoff-*`, `open-*` and `open-cli` launches get it.
- [x] `setup_machine.py`: installs the terminal `claude`/`codex` functions, retires the listener service.
- [x] `reload-plugins`: same check; agent runs it on its own judgement.
- [x] PR #328 body; CI green in full mode on 34f8b8f8 (verify-windows, verify-linux, guard, ci-required).
- [ ] Tommy: review and merge #328, then run `./setup.ps1` once per machine (it retires the listener and
  installs the functions); this delivery did not run setup or touch the real profile or tasks.

## Decisions

- One cursor for the machine, so any launch updates both hosts: a `claude` launch that consumed an event
  must not leave Codex stale. Within a host, marketplaces update sequentially (native CLIs rewrite one
  config file); the two hosts run in parallel.
- The cursor (`machine-events-cursor.json`, the retired listener's file) advances only when both hosts
  succeed. A host that succeeded records the last applied message, so a retry reruns only the failed host,
  at most hourly unless a new event arrives.
- Terminal functions run the check, then call the real executable resolved with
  `Get-Command -CommandType Application, ExternalScript` (PowerShell) or `command` (bash/zsh), so they never
  recurse, and arguments and the exit code pass through natively. The Python path is fixed at setup.
- `reload-plugins` defaults to the check; `--all` keeps the full refresh for a stale plugin with no event,
  and an unconfigured machine falls back to it.
- Merge-policy reconciliation left with the listener. Setup still catches up once; after a policy change
  run `machine_events.py --repo <owner/name>`. Launches stay plugin-only.

## Measurement (this Windows machine, 2026-10-21)

No-event `python -I -B launch_check.py` against a fresh ntfy.sh topic, 15 runs: median 732 ms (672-842).
Bare `python -I -B -c pass` on the same machine: median 140 ms. An audit hook recorded no process creation
and no cursor write. Phases of one poll: stdlib imports ~85 ms, DNS+TCP connect ~200 ms (in a thread, overlapped
with `ssl` import and the Windows certificate store ~130 ms), TLS handshake ~100 ms, HTTP request ~90 ms;
ntfy.sh is ~95 ms away, so three round trips set the floor. The first version (`http.client`, serial connect)
measured 892 ms. A native PowerShell `Invoke-WebRequest` took 1.1-1.3 s on a shell's first call, so the poll
stays in Python. This machine has no topic configured (setup has not run here); the measurement used a
temporary state directory, and the real profile, tasks and cursor were not touched.

Not yet verified on a live machine: an event-path launch against real marketplaces with Codex sessions open.
Fixtures cover it (`tests/test_launch_check.py`, `tests/test_plugin_autoupdate.py`).

## Codex running-session finding

Why the skip existed: 4b66aa7a deferred Codex upgrades "so running hooks never load a half-rewritten
cache". Codex hook commands embed their package digest and keep their original cache path for the session
(edac04b4's removed-cache probe). The loader snapshots a package into
`plugins/data/<plugin>-<marketplace>/hook-snapshots/<sha256(root, digest)>` on its first hook call. Under a
running session an upgrade broke two things:

1. A package whose first hook runs after the upgrade cannot snapshot its old digest, so the integrity check
   exits 2. Engineering's only hook is a lazy PreToolUse gate, so a running session's next shell command is
   blocked, and every one after it. On this machine engineering's newest snapshot is five days older than
   machine's.
2. The bootstrap read the loader from the cache before the snapshot, so an upgrade that changes
   `codex_hook_snapshot.py` fails the loader hash for every hook of every older session (UserPromptSubmit,
   Stop).

Fix: before `codex plugin marketplace upgrade`, `plugin_autoupdate` snapshots each installed hook package
at its current digest with that package's own loader, at the exact key Codex uses (verified against this
machine's existing snapshot keys). The generated bootstrap now reads the snapshot's loader first. The
deferral remains only while an installed package still has the cache-first bootstrap, so the first upgrade
to this release waits for open Codex windows once; after that upgrades never wait. Not verified: whether
Codex re-reads hook commands per event; if it does, a hook that starts during the seconds of a rewrite can
fail once, then the new digest snapshots normally.
