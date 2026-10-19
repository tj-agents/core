---
name: refresh-cli
description: Refresh selected tj-agents plugins through native Claude and Codex commands, with optional verification. Use when a skill or hook is missing or out of date after a merge, when /reload-plugins still shows old standards, or when asked to refresh, update or resync the CLI plugins.
kind: utility
domain: machine
route: infer
---

# Refresh CLI plugins

Automatic updates run in the background. For an explicit refresh request, use this skill's shipped
entry point. On Windows:

```powershell
python -B '<skill-directory>/scripts/refresh_cli.py' --project '<absolute-checkout>'
```

On Linux/macOS use `python3` with the same arguments and POSIX paths.

The default updates the selected tj-agents marketplaces and plugins through native host commands.
It prints progress for each operation and does no package generation or rolling startup preflight.
Claude installs at project scope. Codex's native installer writes a user-level enabled entry; its
installed cache can subsequently be loaded solely from a trusted project's declaration.

Pass `--host claude` or `--host codex` for one host. `--verify` additionally checks native installation
inventory and marketplace checkouts against remote main revisions. `--verify-only` runs that slower
inspection without refreshing. Neither verification mode is the default.

After refreshing, `/reload-plugins` adopts updates in an open Claude session. Start a new Codex session
to load its updated packages. A successful refresh proves the native commands completed; a fresh
session is required to prove loading.
