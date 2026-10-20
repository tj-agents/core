---
name: reload-plugins
description: Load the latest published tj-agents plugins into this CLI, named after Claude Code's native /reload-plugins. Use when a skill or hook is missing or out of date after a merge, or when asked to reload, refresh or update the plugins.
kind: utility
domain: machine
route: infer
---

# Reload plugins

Plugins update automatically in the background on both hosts. This skill is the on-demand path when a
session must pick up a just-published change now. Each host's entry point names the native mechanism to
use; this shared script covers a host that lacks one. On Windows:

```powershell
python -B '<skill-directory>/scripts/reload_plugins.py' --host codex --project '<absolute-checkout>'
```

On Linux/macOS use `python3` with the same arguments and POSIX paths. `--verify` additionally checks the
native installations against remote main revisions; `--verify-only` inspects without changing anything.

A successful reload proves the native commands completed; only a fresh or reloaded session proves the
plugins loaded.
