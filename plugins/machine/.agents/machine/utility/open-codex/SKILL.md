---
name: open-codex
description: Reopen one exact native Codex session in its recorded directory with its native TUI.
kind: utility
domain: machine
route: infer
---

# Open a Codex session

Search first, then reopen only the chosen exact native id. The launcher verifies native resume support, preserves
the recorded cwd, refreshes supported Codex startup standards and uses the native executable directly.

```sh
python '<skill-directory>/../../resources/machine/scripts/agent_recovery.py' open --host codex --id '<native-id>' --prompt 'Continue the requested work.'
```

If status is unknown, reconcile it first. `--confirm-closed` is an explicit acknowledgement that no live writer
exists. Never retry after an ambiguous terminal result.
