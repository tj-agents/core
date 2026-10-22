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

On Linux/macOS use `python3`. It updates only repositories with a published event, on both hosts. If it
reports `current` but a plugin is still stale, rerun with `--all` (optionally `--host claude|codex`).
`--verify` also checks native installations against remote main; `--verify-only` changes nothing.

It fails loudly on a native update that did not persist, a plugin the host lists with errors, and a
superseded marketplace registration it cannot remove; report those. It removes a superseded registration
that nothing uses.

The host entry point names how this session adopts the result.
