---
name: reload-plugins
description: Load the latest published tj-agents plugins into this CLI, named after Claude Code's native /reload-plugins. Run it yourself, without asking, whenever plugins look outdated - a skill or hook is missing or behaves like an older version, or a plugin PR just merged - or when asked to reload, refresh or update the plugins.
kind: utility
domain: machine
route: infer
---

# Reload plugins

Every `claude`, `codex`, handoff and open launch already applies plugin updates published since the last
check. This runs the same check for a running session. Run it on your own judgement; never ask first.
On Windows:

```powershell
python -B '<skill-directory>/scripts/reload_plugins.py' --project '<absolute-checkout>'
```

On Linux/macOS use `python3`. It updates only repositories with a published event, on both hosts. If it
reports `current` but a plugin is still stale, rerun with `--all` (optionally `--host claude|codex`).
`--verify` also checks native installations against remote main; `--verify-only` changes nothing.

The host entry point names how this session adopts the result.
