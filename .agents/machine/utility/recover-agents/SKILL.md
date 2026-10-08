---
name: recover-agents
description: Inventory local Codex and Claude sessions for relevant work, then reopen only explicitly selected sessions.
kind: utility
domain: machine
route: infer
---

# Recover agent work

Inventory both native histories first. The result groups the host, original checkout, title and exact native id.
Use the current goal or PR state to identify relevant work, then select only its returned `host:id` values. Do not
reopen every old session or infer unfinished work from a final transcript message.

```sh
python '<skill-directory>/../../resources/machine/scripts/agent_recovery.py' recover --topic '<topic>' --checkout '<absolute-checkout>'
```

`recover` is read-only until an exact selection is supplied:

```sh
python '<skill-directory>/../../resources/machine/scripts/agent_recovery.py' recover --checkout '<absolute-checkout>' --select 'codex:<native-id>' --prompt 'Continue the requested work.'
```

Use `--codex-history-root '<profile>/sessions'` or `--claude-history-root '<profile>/projects'` for an alternate
profile. On Windows use `python`; elsewhere use `python3`. Unknown live identity requires reconciliation before a
resume, and ambiguous terminal launch results must not be retried.
