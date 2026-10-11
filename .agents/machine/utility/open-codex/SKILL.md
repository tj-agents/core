---
name: open-codex
description: Reopen one exact native Codex session in its recorded directory with its native TUI.
kind: utility
domain: machine
route: infer
---

# Open a Codex session

Search first, then reopen only the chosen exact native id. Verify its recorded cwd and profile before opening;
use `machine:search-codex` against the selected profile when that evidence needs reconciliation. The launcher
verifies native resume support, preserves the recorded cwd, refreshes supported Codex startup standards and
uses the native executable directly.
Run the helper with `python` on Windows or `python3` on Linux/macOS:

```sh
python -B '<skill-directory>/../../resources/machine/scripts/agent_recovery.py' open --host codex --id '<native-id>' --codex-history-root '<selected-profile>/sessions' --prompt 'Continue the requested work.'
```

If status is unknown, reconcile it first. `--confirm-closed` is an explicit acknowledgement that no live writer
exists, not evidence that the source owner released its work. A verified live session cannot be resumed. For
task recovery, state the actual coordination blocker and ask the exact owner to acknowledge or release its work
and reconcile any child writer before conflicting writes. A launched tab neither delivers a follow-up nor restores
transport. Never retry after an ambiguous terminal result.
