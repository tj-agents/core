---
name: sync-plugins
description: Bring this CLI's tj-agents plugins up to date and into the running session. Run it yourself, without asking, whenever plugins look outdated - a skill or hook is missing or behaves like an older version, or a plugin PR just merged - or when asked to sync, reload, refresh or update the plugins.
kind: utility
domain: machine
route: infer
---

# Sync plugins

Every `claude`, `codex`, handoff and open launch already applies plugin updates published since the last
check. This runs the same check for a running session; `./sync.ps1` or `./sync.sh` at the core checkout
root runs it from a terminal. Run it on your own judgement; never ask first. On Windows:

```powershell
python -B '<skill-directory>/scripts/sync_plugins.py' --project '<absolute-checkout>'
```

On Linux/macOS use `python3`. It updates only installs whose plugin files differ from the published head, on both hosts. If it
reports `current` but a plugin is still stale, rerun with `--all` (optionally `--host claude|codex`).
`--verify` also checks native installations against remote main; `--verify-only` changes nothing.

It fails loudly on a native update that did not persist and a plugin the host lists with errors; report
those.

Treat missing, failed, timed-out or untrusted required hooks as a stop on ordinary work. A refresh must
verify installed publisher bytes, trust only the verified current hook hashes through Codex's native
configuration API, and read back hook readiness before reporting success. Never bypass hook trust or
disable a required hook to complete a refresh. Run the affected hooks and verify their successful
execution before resuming; hash trust establishes permission to run, not execution. If recovery cannot
be verified, retain the current owner and report the failed hook and exact recovery action.

The host entry point names how this session adopts the result.

Keep the same conversation through recovery. Sync verifies installed packages and hook trust before
attempting live adoption. If Codex cannot reload its owning client, sync arms the existing verified
close-and-resume mechanism automatically, including standalone `--no-daemon` clients. It waits for the
current turn to finish, confirms the exact old frontend exited, and resumes the same native conversation,
profile and checkout through the managed launcher. It preserves peer clients and shared backends.

When sync reports `relaunch: armed`, preserve the current task checkpoint and end the turn. Do not ask
the user to restart or say `continue`; the resumed client receives the continuation itself. Arming is
not successful adoption: verify the fresh client executed required startup hooks before ordinary work.
A new input, refused or cancelled close, changed frontend binding or failed startup leaves recovery
incomplete. Read the private `session-relaunch/<session-id>.json` receipt for its actual result.

If restart cannot be armed, diagnose and repair that specific ownership or launch failure under the
existing authorization. Do not focus an existing tab as a substitute for refresh, launch a duplicate live
writer, change conversation, bypass trust, or turn a capability failure into a routine manual user step.
Only a demonstrated user-owned credential or trust decision is a human gate. `--no-relaunch` explicitly
disables automatic restart; verification-only runs never close a client.
