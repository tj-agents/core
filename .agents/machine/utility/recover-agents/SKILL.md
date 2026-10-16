---
name: recover-agents
description: Inventory local Codex and Claude sessions for relevant work, then reopen only explicitly selected sessions.
kind: utility
domain: machine
route: infer
---

# Recover agent work

Use `search-codex` and `search-claude` for the requested topic or checkout, then use `open-cli` with each
relevant exact id and a concise instruction to continue; it chooses the host and focuses a live tab itself, which `recover --select` below never does. The user's recovery
request authorizes those resumes; clarify only when the relevant session or live identity is ambiguous.

Inventory both native histories first. The result groups the host, original checkout, title and exact native id.
Use the current goal or PR state to identify relevant work, then select only its returned `host:id` values. Do not
reopen every old session or infer unfinished work from a final transcript message. Run both commands below
with `python` on Windows or `python3` on Linux/macOS.

```sh
python '<skill-directory>/../../resources/machine/scripts/agent_recovery.py' recover --topic '<topic>' --checkout '<absolute-checkout>'
```

`recover` is read-only until an exact selection is supplied:

```sh
python '<skill-directory>/../../resources/machine/scripts/agent_recovery.py' recover --checkout '<absolute-checkout>' --select 'codex:<native-id>' --prompt 'Continue the requested work.'
```

Use `--codex-history-root '<profile>/sessions'` or `--claude-history-root '<profile>/projects'` for an alternate
profile. Unknown live identity requires reconciliation before a
resume, and ambiguous terminal launch results must not be retried.

## Continue a work item

When asked to continue a work item, run `work_item_sessions.py status '<feature>/<item>'`, then `resume`
on the same `<feature>/<item>`. Without `--handle` it resumes the single not-ended owner; with several
sessions and no single owner, pass `--handle`; with no sessions, start a new owner from the work item
README's `## Next Steps` and `claim` it. Run `interrupted` to find and resume sessions whose process died
without closing cleanly. See [`work-item-sessions.md`](../../resources/work-item-sessions.md) for the
session store's schema and commands.
