---
name: hook-control
description: Safely disable or restore Codex hooks while preserving the previous canonical feature gate.
kind: utility
domain: machine
route: infer
---

# Codex hook control

Use this utility when hook execution must be stopped before any hook bootstrap runs. It changes only the
canonical `features.hooks` setting and records the exact previous value in an owned adjacent snapshot.

```sh
python -B '<skill-directory>/scripts/hook_control.py' status --scope global
python -B '<skill-directory>/scripts/hook_control.py' off --scope global
python -B '<skill-directory>/scripts/hook_control.py' on --scope global
```

For a project-specific setting, supply its root explicitly:

```sh
python -B '<skill-directory>/scripts/hook_control.py' off --scope project --project '<project-directory>'
```

`on` restores only a value previously saved by this utility. It never enables every hook. Restart Codex after
changing the setting; no hot reload is established. Status reports the saved layer and cannot verify the effective
state. Project, profile, command-line, or administrator settings can override either layer. A project
`.codex/config.toml` applies only when Codex trusts that repository; new or changed project hook definitions still
require hook trust. The gate covers ordinary native lifecycle hooks; builtin cleanup and legacy notify behavior are
outside it.
The utility requires Python 3.11 or newer for the standard TOML parser.
